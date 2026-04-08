import re
import requests
import json
import os
import shutil
from pydantic import BaseModel, Field
from typing import List, Set

from logutil import get_logger, setup_logging, Colors


from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, OptionList, RichLog
from textual.widgets.option_list import Option
from textual.containers import Vertical

log = get_logger(__name__)

# --- 1. CONFIGURATION ---
LM_STUDIO_API = "http://127.0.0.1:1234/v1/chat/completions" # Standard OpenAI-compatible endpoint for LM Studio
RAW_DIR = "/Users/svenpohle/Desktop/Wiki/raw"
CONCEPTS_DIR = "/Users/svenpohle/Desktop/Wiki/concepts"
WIKI_DIR = "/Users/svenpohle/Desktop/Wiki"

# --- 2. DATA STRUCTURE DEFINITION (Pydantic) ---
# This tells the LLM EXACTLY what format to return, making parsing reliable
class Concept(BaseModel):
    """A single synthesized Knowledge concept"""
    title: str = Field(description="the concise title of the core idea")
    summary_markdown: str = Field(description="a complete markdown article summarizing this concept. must be self contained and ready for obsidian viewing")
    tags: List[str] = Field(
        default_factory=list,
        description="3-8 short lowercase slug tags (letters, digits, hyphens only in output); reuse existing vault tags when relevant; omit # in JSON",
    )

class SynthesisOutput(BaseModel):
    """Wrapper for the LLM JSON; for one-to-one mode use exactly one concept per call."""
    concepts: List[Concept] = Field(
        description="exactly one concept when synthesizing a single raw document; array must hold one object",
    )


class SynthApp(App):
    CSS = """
        #output-box {
            height: 75vh;
            border: panel;
            background: $boost;
        }

        #menu-box {
            height: 25vh;
            border-top: solid $primary;
        }

        OptionList {
            background: $surface;
        }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        yield RichLog(id="output-box", highlight=True, markup=True)

        with Vertical(id="menu-box"):
            yield OptionList(
                Option("1. List Raw Notes", id="list_raw"),
                Option("2. Synthesize Raw Notes", id="synth_raw"),
                Option("3. Exit System", id="exit"),
                id="menu"
            )

        yield Footer()

    def on_mount(self) -> None:
        """Sets focus to the menu as soon as the app starts."""
        self.query_one("#menu").focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Called when user highlights an option and presses Enter."""
        option_id = event.option.id
        
        if option_id is None:
            return
        
        # Mapping IDs to specific function calls
        actions = {
            "list_raw": self.list_raw_notes,
            "synth_raw": self.synthesize_raw_notes,
            "exit": self.exit_app
        }
        
        action_func = actions.get(option_id)
        if action_func:
            action_func()

    def list_raw_notes(self):
        out = self.query_one("#output-box", RichLog)
        out.write("Listing raw notes...")
    
    def synthesize_raw_notes(self):
        out = self.query_one("#output-box", RichLog)
        out.write("Starting synthesis of raw notes...")

    def exit_app(self):
        self.exit()
        

# --- 3. CORE FUNCTIONS ---

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


def parse_json_from_llm(text: str):
    """
    Parse the first JSON object or array from model output.
    Handles preamble text, optional markdown fences, and trailing junk after valid JSON.
    """
    normalized = strip_outer_code_fence(text.strip())

    try:
        return json.loads(normalized)
    except json.JSONDecodeError:
        pass

    start = next((i for i, c in enumerate(normalized) if c in "[{"), None)
    if start is None:
        raise json.JSONDecodeError("No JSON object or array found in model output", normalized, 0)

    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(normalized, start)
    return obj


def list_raw_markdown_files() -> List[str]:
    """Sorted list of *.md basenames under RAW_DIR."""
    if not os.path.isdir(RAW_DIR):
        return []
    return sorted(f for f in os.listdir(RAW_DIR) if f.endswith(".md"))


def load_raw_file_contents(filename: str) -> str:
    """Read one raw markdown file; filename must be a basename under RAW_DIR."""
    filepath = os.path.join(RAW_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def safe_filename_stem_from_raw(filename: str) -> str:
    """Slug from raw filename (no path) for output, e.g. 'My Note.md' -> 'my_note'."""
    stem = filename[:-3] if filename.lower().endswith(".md") else filename
    s = "".join(c for c in stem.lower() if c.isalnum() or c in (" ", "_")).replace(" ", "_")
    return s if s else "note"


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


def collect_existing_tags(concepts_dir: str) -> Set[str]:
    """
    Scan *.md under concepts_dir. The first non-empty line of each file may be
    'TAGS: #a #b ...' (case-insensitive). Parse hashtags and merge into a set.
    If the first non-empty line is not TAGS:, that file contributes no tags.
    """
    found: Set[str] = set()
    if not os.path.isdir(concepts_dir):
        return found
    for name in os.listdir(concepts_dir):
        if not name.endswith(".md"):
            continue
        path = os.path.join(concepts_dir, name)
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


def normalize_tag_list(tags: List[str]) -> List[str]:
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


def generate_tag_links(tags: List[str]) -> str:
    """Generates a single-line string of Obsidian links based on normalized tags."""
    norm = normalize_tag_list(tags)
    if not norm:
        return ""
    # Format: Links: [[tag1]] [[tag2]] ... followed by two newlines for separation from body content.
    links = "Links: " + " ".join([f"[[{t}]]" for t in norm]) + "\n\n"
    return links


def call_lmstudio_api(
    context_data: str,
    system_prompt: str,
    existing_tags: Set[str] | None = None,
    *,
    source_label: str | None = None,
) -> SynthesisOutput | None:
    """Sends the prompt to LM Studio and attempts to parse the structured response."""
    label = f" ({source_label})" if source_label else ""
    log.info(f"  -> Calling LM Studio API{label}...", color=Colors.CYAN)
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

    # The user message combines the instructions with the data (context_data)
    user_message = f"{full_system_prompt}\n\n---\nCONTEXT DATA:\n{context_data}"

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "your_loaded_model_name", # IMPORTANT: Replace this with the name of the model you loaded in LM Studio!
        "messages": [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.1, # Keep temperature low for deterministic knowledge extraction
        # Long JSON + markdown in strings; default caps often truncate mid-string and break JSON.
        "max_tokens": 16384,
    }

    try:
        response = requests.post(LM_STUDIO_API, headers=headers, json=payload)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        
        # LM Studio returns a structure similar to OpenAI's response
        data = response.json()
        llm_text = data['choices'][0]['message']['content']

        log.info("  -> Received raw text from LLM. Attempting structured parsing...", color=Colors.CYAN)
        try:
            parsed_data = parse_json_from_llm(llm_text)
            parsed_data = normalize_synthesis_parsed(parsed_data)
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
        log.error(
            "API CONNECTION ERROR: Could not connect to LM Studio server at 127.0.0.1:1234."
        )
        log.error(
            "   Ensure the model is loaded and the server is running in LM Studio. Error: %s",
            e,
        )
        return None


def write_concept_file(concept: Concept, output_stem: str) -> None:
    """Write one concept to CONCEPTS_DIR/{output_stem}.md (stem is slug, no extension)."""
    if not os.path.exists(CONCEPTS_DIR):
        os.mkdir(CONCEPTS_DIR)
    filename = f"{output_stem}.md"
    filepath = os.path.join(CONCEPTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        # 1. Write Tags (using the old format for consistency with existing files)
        f.write("TAGS: " + " ".join(f"#{t}" for t in normalize_tag_list(concept.tags)) + "\n\n")
        # 2. Write Obsidian Links based on tags
        f.write(generate_tag_links(concept.tags))
        # 3. Write the main summary content
        f.write(concept.summary_markdown)
    log.info(f"  -> Wrote {filename} ({concept.title})", color=Colors.GREEN)


# --- 4. MAIN EXECUTION BLOCK ---

def manual_synth():
    setup_logging()

    # One raw .md file -> one API call -> exactly one concept -> one file in CONCEPTS_DIR
    # Output filename is derived from the raw filename (e.g. foo.md -> foo.md in concepts).

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

    if not os.path.isdir(RAW_DIR):
        log.error("Raw directory not found: %s", RAW_DIR)
        exit(1)

    existing_tags = collect_existing_tags(CONCEPTS_DIR)
    log.info(f"Existing vault tags from [concepts]: {len(existing_tags)} tags found", color=Colors.GREEN)

    raw_files = list_raw_markdown_files()
    if not raw_files:
        log.error("No .md files in %s", RAW_DIR)
        exit(1)

    log.info(f"Processing {len(raw_files)} raw file(s), one concept per file", color=Colors.CYAN)

    for raw_name in raw_files:
        log.info(f"  -> Processing RAW: {raw_name}", color=Colors.GREEN)
        try:
            body = load_raw_file_contents(raw_name)
        except OSError as e:
            log.error("  -> Could not read file: %s", e)
            continue

        context = f"SOURCE FILE: {raw_name}\n\n{body}"
        synthesis_result = call_lmstudio_api(
            context,
            SYSTEM_PROMPT,
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
        out_stem = safe_filename_stem_from_raw(raw_name)
        write_concept_file(concept, output_stem=out_stem)

        try:
            # Define and create target directory
            target_dir = os.path.join(RAW_DIR, "processed")
            os.makedirs(target_dir, exist_ok=True)

            # Move the original raw file
            src_path = os.path.join(RAW_DIR, raw_name)
            destination_path = os.path.join(target_dir, raw_name)
            shutil.move(src_path, destination_path)
        except OSError as e:
            log.warning("   OS Error during file move for %s: %s", raw_name, e)

        for t in normalize_tag_list(concept.tags) or ["wiki"]:
            existing_tags.add(t)

    log.info("\nSynthesis run finished.")

if __name__ == "__main__":
    app = SynthApp()
    app.run()
