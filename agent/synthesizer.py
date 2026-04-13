from __future__ import annotations

import json
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Callable
from typing import List, Set

import requests
from pydantic import BaseModel, Field, ValidationError

from logutil import Colors, get_logger, setup_logging

log = get_logger(__name__)

# Desktop app entry: run `python lmwiki.py` from the repository root (not this file).

# Top-level raw/ inputs (not recursive); concept output is always .md under concepts/.
_RAW_SOURCE_SUFFIXES: tuple[str, ...] = (".md", ".txt")
# Companion assets: same dir, basename `{raw_stem}_<suffix>.<ext>` (raw_stem = filename without .md/.txt).
_IMAGE_EXTENSIONS: tuple[str, ...] = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
)


class SynthesisCancelled(Exception):
    """Raised when cancel_check is true during Gemini retries or backoff wait."""

# --- Data models (Pydantic) ---


class Concept(BaseModel):
    """A single synthesized Knowledge concept"""

    title: str = Field(description="the concise title of the core idea")
    summary_markdown: str = Field(
        description="a complete markdown article summarizing this concept. must be self contained and ready for obsidian viewing"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="3-8 short lowercase slug tags (letters, digits, hyphens only in output); reuse existing vault tags when relevant; omit # in JSON",
    )


class SynthesisOutput(BaseModel):
    """Wrapper for the LLM JSON; for one-to-one mode use exactly one concept per call."""

    concepts: List[Concept] = Field(
        description="exactly one concept when synthesizing a single raw document; array must hold one object",
    )

@dataclass
class SynthesizerConfig:
    """Paths for the wiki vault and optional Gemini API key (from env if omitted)."""

    root: Path = field(default_factory=lambda: Path(__file__).parent.parent.resolve())
    gemini_key: str | None = None

    def __post_init__(self) -> None:
        if self.gemini_key is None:
            self.gemini_key = os.environ.get("GEMINI_KEY")

    @property
    def raw_dir(self) -> Path:
        return self.root / "raw"

    @property
    def concepts_dir(self) -> Path:
        return self.root / "concepts"

    @property
    def wiki_dir(self) -> Path:
        return self.root / "wiki"

class LlmJsonParser:
    """Parse JSON from Gemini responses (fences, preamble, trailing junk)."""

    @staticmethod
    def strip_outer_code_fence(text: str) -> str:
        """Remove a single leading ``` / ```json fence and matching trailing ``` only."""
        text = text.strip()
        if not text.startswith("```"):
            return text
        first_nl = text.find("\n")
        if first_nl == -1:
            return text
        body = text[first_nl + 1 :].rstrip()
        if body.endswith("```"):
            body = body[:-3].rstrip()
        return body.strip()

    @staticmethod
    def parse_json_from_llm(text: str):
        """
        Parse the first JSON object or array from model output.
        Handles preamble text, optional markdown fences, and trailing junk after valid JSON.
        """
        normalized = LlmJsonParser.strip_outer_code_fence(text.strip())

        try:
            return json.loads(normalized)
        except json.JSONDecodeError:
            pass

        start = next((i for i, c in enumerate(normalized) if c in "[{"), None)
        if start is None:
            raise json.JSONDecodeError(
                "No JSON object or array found in model output", normalized, 0
            )

        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(normalized, start)
        return obj

    @staticmethod
    def normalize_synthesis_parsed(parsed_data) -> dict:
        """Accept {concepts: [...]}, a bare array, or a single concept object."""
        if isinstance(parsed_data, list):
            return {"concepts": parsed_data}
        if isinstance(parsed_data, dict):
            if "concepts" in parsed_data:
                return parsed_data
            if "title" in parsed_data:
                return {"concepts": [parsed_data]}
        return parsed_data


class TagUtils:
    """Normalize tags and build Obsidian link lines."""

    @staticmethod
    def normalize_list(tags: List[str]) -> List[str]:
        """Lowercase slug tags, dedupe preserving order; allow a-z 0-9 hyphen."""
        seen: Set[str] = set()
        out: List[str] = []
        for raw in tags:
            t = (raw or "").strip().lstrip("#").lower()
            t = re.sub(r"[^a-z0-9-]+", "-", t).strip("-")
            if not t or t in seen:
                continue
            seen.add(t)
            out.append(t)
        return out

    @staticmethod
    def links_markdown(tags: List[str]) -> str:
        """Single-line Obsidian links block after normalized tags."""
        norm = TagUtils.normalize_list(tags)
        if not norm:
            return ""
        return "Links: " + " ".join([f"[[{t}]]" for t in norm]) + "\n\n"


class WikiRepository:
    """Raw notes and concept markdown under a configured vault root."""

    def __init__(self, config: SynthesizerConfig) -> None:
        self._config = config

    @property
    def raw_dir(self) -> Path:
        return self._config.raw_dir

    def list_raw_source_files(self) -> List[str]:
        """Sorted list of *.md and *.txt basenames under raw_dir (not recursive)."""
        d = self._config.raw_dir
        if not d.is_dir():
            return []
        return sorted(
            f
            for f in os.listdir(d)
            if f.lower().endswith(_RAW_SOURCE_SUFFIXES)
        )

    def load_raw_file_contents(self, filename: str) -> str:
        """Read one raw file (.md or .txt); filename must be a basename under raw_dir."""
        filepath = self._config.raw_dir / filename
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def list_companion_image_basenames(self, raw_basename: str) -> List[str]:
        """
        Image files beside the raw source: `{Path(raw_basename).stem}_*.<image_ext>`
        under raw_dir (top-level only), sorted alphabetically by basename.
        """
        d = self._config.raw_dir
        if not d.is_dir():
            return []
        stem = Path(raw_basename).stem
        prefix = f"{stem}_"
        found: list[str] = []
        for name in os.listdir(d):
            path = d / name
            if not path.is_file():
                continue
            low = name.lower()
            if not any(low.endswith(ext) for ext in _IMAGE_EXTENSIONS):
                continue
            if not name.startswith(prefix):
                continue
            rest = name[len(prefix) :]
            if "." not in rest:
                continue
            base_part, _ext = rest.rsplit(".", 1)
            if not base_part:
                continue
            found.append(name)
        return sorted(found)

    @staticmethod
    def safe_filename_stem_from_raw(filename: str) -> str:
        """Slug from raw basename for concept filename, e.g. 'My Note.md' -> 'my_note'."""
        stem = Path(filename).stem
        s = "".join(c for c in stem.lower() if c.isalnum() or c in (" ", "_")).replace(
            " ", "_"
        )
        return s if s else "note"

    def collect_existing_tags(self) -> Set[str]:
        """
        Scan *.md under concepts_dir. The first non-empty line of each file may be
        'TAGS: #a #b ...' (case-insensitive). Parse hashtags and merge into a set.
        """
        found: Set[str] = set()
        concepts_dir = self._config.concepts_dir
        if not concepts_dir.is_dir():
            return found
        for name in os.listdir(concepts_dir):
            if not name.endswith(".md"):
                continue
            path = concepts_dir / name
            try:
                with open(path, encoding="utf-8") as f:
                    for line in f:
                        stripped = line.strip()
                        if not stripped:
                            continue
                        m = re.match(r"^TAGS:\s*(.*)$", stripped, re.IGNORECASE)
                        if m:
                            for raw in m.group(1).split():
                                tok = raw.lstrip("#").lower()
                                if tok:
                                    found.add(tok)
                        break
            except OSError:
                continue
        return found

    def write_concept_file(self, concept: Concept, output_stem: str) -> None:
        """Write one concept to concepts_dir/{output_stem}.md."""
        concepts_dir = self._config.concepts_dir
        concepts_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{output_stem}.md"
        filepath = concepts_dir / filename
        tags_line = "TAGS: " + " ".join(
            f"#{t}" for t in TagUtils.normalize_list(concept.tags)
        )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(tags_line + "\n\n")
            f.write(TagUtils.links_markdown(concept.tags))
            f.write(concept.summary_markdown)
        log.info(f"  -> Wrote {filename} ({concept.title})", color=Colors.GREEN)


# --- Gemini API ---


class GeminiSynthesisClient:
    """Call Gemini generateContent and return structured SynthesisOutput."""

    #: Failures (HTTP, parse, schema, etc.) are retried this many times after the first try.
    MAX_RETRIES = 3
    RETRY_BACKOFF_SEC = 10
    MODEL_PRIMARY = "gemini-2.5-flash"
    MODEL_FALLBACK = "gemini-2.5-flash-lite"

    def __init__(self, config: SynthesizerConfig) -> None:
        self._config = config

    @staticmethod
    def _generate_content_url(model: str, api_key: str) -> str:
        return (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )

    @staticmethod
    def _http_status_suggests_fallback(status_code: int) -> bool:
        return status_code in (429, 500, 502, 503, 504)

    @staticmethod
    def _api_error_suggests_fallback(payload: dict) -> bool:
        err = payload.get("error")
        if not isinstance(err, dict):
            return False
        code = err.get("code")
        status = err.get("status", "")
        if isinstance(status, str) and status.upper() in (
            "RESOURCE_EXHAUSTED",
            "UNAVAILABLE",
            "DEADLINE_EXCEEDED",
        ):
            return True
        if code in (429, 500, 502, 503, 504):
            return True
        msg = str(err.get("message", "")).lower()
        hints = (
            "quota",
            "rate limit",
            "resource exhausted",
            "too many requests",
            "overload",
            "unavailable",
            "try again later",
            "capacity",
        )
        return any(h in msg for h in hints)

    @staticmethod
    def _log_retry_countdown(
        seconds: int,
        label: str,
        cancel_check: Callable[[], bool] | None,
    ) -> None:
        """One log line per second; sleeps ``seconds`` total unless cancel_check is true."""
        for remaining in range(seconds, 0, -1):
            if cancel_check is not None and cancel_check():
                log.warning(
                    "  -> Retry countdown aborted%s (cancelled).",
                    label,
                )
                raise SynthesisCancelled
            log.info(
                f"  -> Retry countdown{label}: {remaining}s…",
                color=Colors.CYAN,
            )
            time.sleep(1)

    def _execute_generate_attempt(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict,
        label: str,
    ) -> tuple[SynthesisOutput | None, bool]:
        """
        Single HTTP round-trip + parse.
        Returns (output, try_fallback_model). Second element True when failure looks like
        quota, rate limit, or model/API unavailability (caller may try secondary model).
        """
        try:
            response = requests.post(url, headers=headers, json=payload)
            status = response.status_code
            data: dict | None
            try:
                parsed = response.json()
                data = parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError as e:
                log.error("API body is not JSON%s: %s", label, e)
                return None, self._http_status_suggests_fallback(status)

            if not response.ok:
                try_fb = self._http_status_suggests_fallback(status) or (
                    data is not None and self._api_error_suggests_fallback(data)
                )
                if try_fb:
                    log.warning(
                        "Gemini HTTP %s%s — quota/unavailable; may try fallback model. %s",
                        status,
                        label,
                        (response.text[:500] + "…") if len(response.text) > 500 else response.text,
                    )
                else:
                    log.error(
                        "Gemini HTTP %s%s: %s",
                        status,
                        label,
                        response.text[:800],
                    )
                return None, try_fb

            if data is None:
                log.error("Gemini response JSON was not an object%s.", label)
                return None, False

            if "error" in data:
                try_fb = self._api_error_suggests_fallback(data)
                if try_fb:
                    log.warning(
                        "Gemini error payload%s (quota/unavailable); may try fallback: %s",
                        label,
                        data.get("error"),
                    )
                else:
                    log.error("Gemini error in response body%s: %s", label, data.get("error"))
                return None, try_fb

            try:
                llm_text = data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError) as e:
                log.error("Unexpected Gemini response shape%s: %s", label, e)
                log.error("   Top-level keys: %s", list(data.keys()))
                return None, False

            log.info(
                "  -> Received raw text from LLM. Attempting structured parsing...",
                color=Colors.CYAN,
            )
            try:
                parsed_data = LlmJsonParser.parse_json_from_llm(llm_text)
                parsed_data = LlmJsonParser.normalize_synthesis_parsed(parsed_data)
            except json.JSONDecodeError as e:
                log.error(
                    "JSON parse failed from model output%s (char %s): %s",
                    label,
                    getattr(e, "pos", "?"),
                    e.msg,
                )
                if e.doc and isinstance(e.doc, str) and getattr(e, "pos", None) is not None:
                    pos = min(e.pos, len(e.doc))
                    lo = max(0, pos - 80)
                    hi = min(len(e.doc), pos + 80)
                    log.error("   Context around error: %r", e.doc[lo:hi])
                else:
                    log.error("   Raw LLM output snippet: %s", llm_text[:800])
                return None, False

            try:
                return SynthesisOutput(**parsed_data), False
            except ValidationError as e:
                log.error("Schema validation failed on model JSON%s: %s", label, e)
                return None, False

        except requests.exceptions.RequestException as e:
            log.error("API CONNECTION ERROR: Could not connect to Gemini API%s.", label)
            if hasattr(e, "response") and e.response is not None:
                sc = e.response.status_code
                log.error(
                    "   Response status: %s. Detail: %s",
                    sc,
                    e.response.text[:800],
                )
                return None, self._http_status_suggests_fallback(sc)
            log.error("   Error: %s", e)
            return None, False

    def generate(
        self,
        context_data: str,
        system_prompt: str,
        existing_tags: Set[str] | None = None,
        *,
        source_label: str | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> SynthesisOutput | None:
        """Send the prompt to Gemini API and parse the structured response (with retries)."""
        key = self._config.gemini_key
        if not key:
            log.error("GEMINI_KEY is not set.")
            return None

        label = f" ({source_label})" if source_label else ""
        existing_tags = existing_tags or set()
        if existing_tags:
            tag_section = (
                "\n\nExisting tags already used in this vault (reuse when relevant): "
                + ", ".join(sorted(existing_tags))
                + "\n"
            )
        else:
            tag_section = (
                "\n\nNo existing tags have been recorded in concept notes yet; "
                "introduce sensible new tags as needed.\n"
            )
        full_system_prompt = system_prompt + tag_section
        user_message = f"CONTEXT DATA:\n{context_data}"

        headers = {"Content-Type": "application/json"}
        payload = {
            "systemInstruction": {"parts": [{"text": full_system_prompt}]},
            "contents": [{"parts": [{"text": user_message}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }
        url_primary = self._generate_content_url(self.MODEL_PRIMARY, key)
        url_fallback = self._generate_content_url(self.MODEL_FALLBACK, key)

        max_attempts = 1 + self.MAX_RETRIES
        for attempt in range(1, max_attempts + 1):
            if cancel_check is not None and cancel_check():
                log.warning("  -> Gemini attempt cancelled before try%s.", label)
                raise SynthesisCancelled
            log.info(
                f"  -> Gemini API{label} attempt {attempt}/{max_attempts} "
                f"({self.MODEL_PRIMARY} then {self.MODEL_FALLBACK} if needed)…",
                color=Colors.CYAN,
            )
            sub_primary = f"{label} [{self.MODEL_PRIMARY}]"
            result, try_fallback = self._execute_generate_attempt(
                url_primary, headers, payload, sub_primary
            )
            if result is not None:
                return result
            if try_fallback:
                log.info(
                    f"  -> Primary model unavailable or limited; trying {self.MODEL_FALLBACK}{label}…",
                    color=Colors.CYAN,
                )
                sub_fb = f"{label} [{self.MODEL_FALLBACK}]"
                result_fb, _ = self._execute_generate_attempt(
                    url_fallback, headers, payload, sub_fb
                )
                if result_fb is not None:
                    return result_fb
            if attempt >= max_attempts:
                log.error(
                    "  -> Gemini failed after %s attempt(s)%s; giving up.",
                    max_attempts,
                    label,
                )
                return None
            if cancel_check is not None and cancel_check():
                log.warning("  -> Gemini retries cancelled%s; not waiting.", label)
                raise SynthesisCancelled
            log.warning(
                "  -> Gemini attempt %s/%s failed%s; %ss wait then retry (up to %s more).",
                attempt,
                max_attempts,
                label,
                self.RETRY_BACKOFF_SEC,
                max_attempts - attempt,
            )
            self._log_retry_countdown(
                self.RETRY_BACKOFF_SEC,
                label,
                cancel_check,
            )


# --- Orchestration ---


class WikiSynthesizer:
    """
    One raw .md or .txt file -> one API call -> one concept -> one file in concepts_dir;
    companion images (same stem + _*) move to concepts_dir with the .md; raw source moves to raw/processed/.
    """

    SYSTEM_PROMPT = """
        You are a Master Knowledge Synthesizer Agent for an Obsidian Wiki. You are given ONE raw document (Markdown or plain text; see CONTEXT DATA).
        Produce exactly ONE synthesized knowledge concept for this document only in JSON format.
        Do not ommit important info in the original markdown. Keep it mostly intact when info is important.
        Your output MUST strictly adhere to the provided JSON schema. Do not include any conversational text outside of the final JSON object.
        Do not add Obsidian image embeds (![[...]]) for companion screenshot files; those are appended automatically from files next to the source.
        The 'concepts' array MUST contain exactly one object, with:
        1. 'title': a concise title for the core idea in this document.
        2. 'summary_markdown': a complete, high-quality Obsidian-ready Markdown article for this concept. Use [[Wikilinks]] where helpful. Do not include a TAGS line in summary_markdown; tags belong only in the 'tags' array.
        3. 'tags': an array of 3-8 short lowercase slug strings (letters, digits, hyphens), grounded in this document; prefer reusing existing vault tags when listed below; in JSON use plain strings without #.
        The Output must adhere strictly to JSON format and must be parseable as a json document.
    """

    def __init__(self, config: SynthesizerConfig | None = None) -> None:
        self.config = config or SynthesizerConfig()
        self.repo = WikiRepository(self.config)
        self.gemini = GeminiSynthesisClient(self.config)

    def run_manual_batch(self) -> None:
        """Process every *.md and *.txt in raw_dir (CLI-style batch)."""
        setup_logging()

        if not self.config.gemini_key:
            log.error(
                "GEMINI_KEY environment variable is not set. Please export it before running."
            )
            raise SystemExit(1)

        raw_dir = self.config.raw_dir
        if not raw_dir.is_dir():
            log.error("Raw directory not found: %s", raw_dir)
            raise SystemExit(1)

        raw_files = self.repo.list_raw_source_files()
        if not raw_files:
            log.error("No .md or .txt files in %s", raw_dir)
            raise SystemExit(1)

        self.process_raw_files(raw_files)

        log.info("\nSynthesis run finished.")

    def process_raw_files(
        self,
        raw_names: List[str],
        *,
        cancel_check: Callable[[], bool] | None = None,
    ) -> None:
        """
        Synthesize each listed raw basename (.md or .txt, top-level raw/ only).
        Skips duplicates (first occurrence wins). Logs and returns if nothing to do.
        If cancel_check is set and returns True before a file, stops after the previous
        file (current in-flight API call is not aborted).
        """
        if not raw_names:
            log.warning("No raw files to process.")
            return

        if not self.config.gemini_key:
            log.error(
                "GEMINI_KEY environment variable is not set. Please export it before running."
            )
            return

        raw_dir = self.config.raw_dir
        if not raw_dir.is_dir():
            log.error("Raw directory not found: %s", raw_dir)
            return

        ordered_unique: List[str] = []
        seen: Set[str] = set()
        for name in raw_names:
            if name in seen:
                continue
            seen.add(name)
            ordered_unique.append(name)

        existing_tags = self.repo.collect_existing_tags()
        log.info(
            f"Existing vault tags from [concepts]: {len(existing_tags)} tags found",
            color=Colors.GREEN,
        )

        log.info(
            f"Processing {len(ordered_unique)} raw file(s), one concept per file",
            color=Colors.CYAN,
        )

        available = set(self.repo.list_raw_source_files())
        total = len(ordered_unique)
        for idx, raw_name in enumerate(ordered_unique, start=1):
            if cancel_check is not None and cancel_check():
                log.warning(
                    "Synthesis cancelled; stopped before file %s/%s (%s completed).",
                    idx,
                    total,
                    idx - 1,
                )
                break
            if raw_name not in available:
                log.warning(
                    "[%s/%s] Skip %r: not in raw directory or not .md/.txt",
                    idx,
                    total,
                    raw_name,
                )
                continue

            log.info(
                "[%s/%s] Synthesizing: %s",
                idx,
                total,
                raw_name,
                color=Colors.CYAN,
            )
            try:
                body = self.repo.load_raw_file_contents(raw_name)
            except OSError as e:
                log.error(
                    "[%s/%s] Read failed for %s: %s",
                    idx,
                    total,
                    raw_name,
                    e,
                )
                continue

            context = f"SOURCE FILE: {raw_name}\n\n{body}"
            try:
                synthesis_result = self.gemini.generate(
                    context,
                    self.SYSTEM_PROMPT,
                    existing_tags,
                    source_label=raw_name,
                    cancel_check=cancel_check,
                )
            except SynthesisCancelled:
                log.warning(
                    "[%s/%s] Synthesis cancelled for %s (Gemini attempt/backoff); stopping batch.",
                    idx,
                    total,
                    raw_name,
                )
                break

            if not synthesis_result or not synthesis_result.concepts:
                log.error(
                    "[%s/%s] Synthesis produced no concept for %s (API or parse error; see messages above).",
                    idx,
                    total,
                    raw_name,
                )
                continue

            if len(synthesis_result.concepts) > 1:
                log.warning(
                    "[%s/%s] %s: model returned %s concepts; using only the first.",
                    idx,
                    total,
                    raw_name,
                    len(synthesis_result.concepts),
                )

            concept = synthesis_result.concepts[0]
            companion_images = self.repo.list_companion_image_basenames(raw_name)
            if companion_images:
                tail = "\n".join(f"![[{b}]]" for b in companion_images)
                concept = concept.model_copy(
                    update={
                        "summary_markdown": concept.summary_markdown.rstrip()
                        + "\n\n"
                        + tail
                    }
                )

            out_stem = WikiRepository.safe_filename_stem_from_raw(raw_name)
            out_path = self.config.concepts_dir / f"{out_stem}.md"
            try:
                self.repo.write_concept_file(concept, output_stem=out_stem)
            except OSError as e:
                log.error(
                    "[%s/%s] Write concept failed for %s -> %s: %s",
                    idx,
                    total,
                    raw_name,
                    out_path,
                    e,
                )
                continue

            for t in TagUtils.normalize_list(concept.tags) or ["wiki"]:
                existing_tags.add(t)

            concepts_dir = self.config.concepts_dir
            concepts_dir.mkdir(parents=True, exist_ok=True)
            for img_name in companion_images:
                img_src = raw_dir / img_name
                if not img_src.is_file():
                    continue
                try:
                    shutil.move(str(img_src), str(concepts_dir / img_name))
                except OSError as img_err:
                    log.error(
                        "[%s/%s] Move companion image to concepts failed for %s: %s",
                        idx,
                        total,
                        img_name,
                        img_err,
                    )

            processed_path = raw_dir / "processed" / raw_name
            move_ok = False
            try:
                target_dir = raw_dir / "processed"
                target_dir.mkdir(parents=True, exist_ok=True)
                src_path = raw_dir / raw_name
                shutil.move(str(src_path), str(target_dir / raw_name))
                move_ok = True
            except OSError as e:
                log.error(
                    "[%s/%s] Move raw file failed for %s (concept written to %s): %s",
                    idx,
                    total,
                    raw_name,
                    out_path,
                    e,
                )

            if move_ok:
                img_note = (
                    f"; moved {len(companion_images)} image(s) to {concepts_dir}"
                    if companion_images
                    else ""
                )
                log.info(
                    "[%s/%s] Finished %s: wrote %s%s; moved raw to %s",
                    idx,
                    total,
                    raw_name,
                    out_path,
                    img_note,
                    processed_path,
                    color=Colors.GREEN,
                )
