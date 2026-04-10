from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set

import requests
from pydantic import BaseModel, Field

from logutil import Colors, get_logger, setup_logging

log = get_logger(__name__)

# Desktop app entry: run `python lmwiki.py` from the repository root (not this file).

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

    def list_raw_markdown_files(self) -> List[str]:
        """Sorted list of *.md basenames under raw_dir (not recursive)."""
        d = self._config.raw_dir
        if not d.is_dir():
            return []
        return sorted(f for f in os.listdir(d) if f.endswith(".md"))

    def load_raw_file_contents(self, filename: str) -> str:
        """Read one raw markdown file; filename must be a basename under raw_dir."""
        filepath = self._config.raw_dir / filename
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def safe_filename_stem_from_raw(filename: str) -> str:
        """Slug from raw filename (no path) for output, e.g. 'My Note.md' -> 'my_note'."""
        stem = filename[:-3] if filename.lower().endswith(".md") else filename
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

    def __init__(self, config: SynthesizerConfig) -> None:
        self._config = config

    def generate(
        self,
        context_data: str,
        system_prompt: str,
        existing_tags: Set[str] | None = None,
        *,
        source_label: str | None = None,
    ) -> SynthesisOutput | None:
        """Send the prompt to Gemini API and parse the structured response."""
        key = self._config.gemini_key
        if not key:
            log.error("GEMINI_KEY is not set.")
            return None

        label = f" ({source_label})" if source_label else ""
        log.info(f"  -> Calling Gemini API{label}...", color=Colors.CYAN)
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
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash:generateContent?key={key}"
        )

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            llm_text = data["candidates"][0]["content"]["parts"][0]["text"]

            log.info(
                "  -> Received raw text from LLM. Attempting structured parsing...",
                color=Colors.CYAN,
            )
            try:
                parsed_data = LlmJsonParser.parse_json_from_llm(llm_text)
                parsed_data = LlmJsonParser.normalize_synthesis_parsed(parsed_data)
                return SynthesisOutput(**parsed_data)
            except json.JSONDecodeError as e:
                log.warning("PARSING FAILED: Could not parse JSON from the model response.")
                log.warning(f"   {e.msg} (at char {getattr(e, 'pos', '?')})")
                if e.doc and isinstance(e.doc, str) and getattr(e, "pos", None) is not None:
                    pos = min(e.pos, len(e.doc))
                    lo = max(0, pos - 80)
                    hi = min(len(e.doc), pos + 80)
                    log.warning("   Context around error: %r", e.doc[lo:hi])
                else:
                    log.warning("   Raw LLM Output Snippet: %s", llm_text[:800])
                return None

        except requests.exceptions.RequestException as e:
            log.error("API CONNECTION ERROR: Could not connect to Gemini API.")
            if hasattr(e, "response") and e.response is not None:
                log.error(
                    f"   Response status: {e.response.status_code}. Detail: {e.response.text}"
                )
            else:
                log.error(f"   Error: {e}")
            return None


# --- Orchestration ---


class WikiSynthesizer:
    """
    One raw .md file -> one API call -> one concept -> one file in concepts_dir;
    then move raw file to raw/processed/.
    """

    SYSTEM_PROMPT = """
        You are a Master Knowledge Synthesizer Agent for an Obsidian Wiki. You are given ONE raw Markdown document (see CONTEXT DATA).
        Produce exactly ONE synthesized knowledge concept for this document only in JSON format.
        Do not ommit important info in the original markdown. Keep it mostly intact when info is important.
        Your output MUST strictly adhere to the provided JSON schema. Do not include any conversational text outside of the final JSON object.
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
        """Process every *.md in raw_dir (CLI-style batch)."""
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

        existing_tags = self.repo.collect_existing_tags()
        log.info(
            f"Existing vault tags from [concepts]: {len(existing_tags)} tags found",
            color=Colors.GREEN,
        )

        raw_files = self.repo.list_raw_markdown_files()
        if not raw_files:
            log.error("No .md files in %s", raw_dir)
            raise SystemExit(1)

        log.info(
            f"Processing {len(raw_files)} raw file(s), one concept per file",
            color=Colors.CYAN,
        )

        for raw_name in raw_files:
            log.info(f"  -> Processing RAW: {raw_name}", color=Colors.GREEN)
            try:
                body = self.repo.load_raw_file_contents(raw_name)
            except OSError as e:
                log.error("  -> Could not read file: %s", e)
                continue

            context = f"SOURCE FILE: {raw_name}\n\n{body}"
            synthesis_result = self.gemini.generate(
                context,
                self.SYSTEM_PROMPT,
                existing_tags,
                source_label=raw_name,
            )

            if not synthesis_result or not synthesis_result.concepts:
                log.warning("\tNo concept produced; skipping.")
                continue

            if len(synthesis_result.concepts) > 1:
                log.warning(
                    f"\tModel returned {len(synthesis_result.concepts)} concepts; "
                    "using only the first for one-to-one mode.",
                )

            concept = synthesis_result.concepts[0]
            out_stem = WikiRepository.safe_filename_stem_from_raw(raw_name)
            self.repo.write_concept_file(concept, output_stem=out_stem)

            try:
                target_dir = raw_dir / "processed"
                target_dir.mkdir(parents=True, exist_ok=True)
                src_path = raw_dir / raw_name
                shutil.move(str(src_path), str(target_dir / raw_name))
            except OSError as e:
                log.warning("   OS Error during file move for %s: %s", raw_name, e)

            for t in TagUtils.normalize_list(concept.tags) or ["wiki"]:
                existing_tags.add(t)

        log.info("\nSynthesis run finished.")
