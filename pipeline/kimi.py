# entropy_builder/pipeline/kimi.py
import json
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from .models import JobConfig, VaultFile, GapItem

logger = logging.getLogger(__name__)

_CODE_FENCE_RE = re.compile(r"```(?:json|ndjson)?\s*([\s\S]*)```", re.DOTALL)
_OPEN_FENCE_RE = re.compile(r"^```(?:json|ndjson)?\s*", re.DOTALL)


def _strip_fence(raw: str) -> str:
    """Strip markdown code fences from a model response.

    Handles both fully-fenced (```...```) and truncated responses where the
    opening fence exists but the closing fence was cut off by max_tokens.
    """
    text = raw.strip()
    if not text.startswith("```"):
        return text
    m = _CODE_FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    # Unclosed fence (truncated response) — strip only the opening fence
    return _OPEN_FENCE_RE.sub("", text, count=1).strip()

_TFY_URL = "https://tfy.promptlens.trilogy.com/v1/chat/completions"
_TFY_MODEL = "claude-group/claude-sonnet-4-6"
# Sonnet 4.6 supports 64K output; 32K was insufficient — chunks consistently
# hit finish=length mid-content, dropping the entire wiki silently. See bd-trn.
_TFY_MAX_TOKENS = 64000

_FW_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
_FW_MODEL = "accounts/fireworks/models/deepseek-v4-pro"
_FW_MAX_TOKENS = 131072

CHUNK_SIZE = 80_000  # chars — stay under model context limit per call
MAX_PARALLEL_CHUNKS = 8
MAX_INPUT_CHARS_PER_FILE = 8000  # chars from each ingested file fed to each topic chunk

# Base system prompt — shared format/style rules across all topic chunks.
_PASS1_BASE_SYSTEM = """You are building a personal knowledge wiki ("Second Brain") for a professional.

Given their interview answers and uploaded notes, generate structured Obsidian markdown files.

CRITICAL OUTPUT FORMAT — newline-delimited JSON (NDJSON):
- Emit one complete JSON object per line: {"path": "<relative path>", "content": "<full file contents>"}
- No preamble, no commentary, no markdown code fences — just JSON objects, one per line.
- Newlines inside content MUST be JSON-escaped as \\n.
- Each line is independent — finish each file before starting the next.

Every file MUST start with YAML frontmatter:
---
type: <book|concept|framework|principle|person|quotes|moc|mental-model|profile>
description: <one line>
tags: [<2-4 relevant tags>]
aliases: [<alternate names if any>]
---

FILE PATH CONVENTION (strict):
- All file names use Hyphenated-Title-Case. No spaces in file names.
- Examples: "Concepts/Pattern-Recognition.md", "Mental-Models/First-Principles.md", "Books/Atomic-Habits.md".
- The category folder is also hyphenated: "Mental-Models" not "Mental Models".

WIKILINK INTEGRITY (strict):
- Only emit [[wikilinks]] to paths you are actually generating in THIS output. Never link to a path you don't produce.
- Wikilink the exact path (without .md), e.g. [[Concepts/Pattern-Recognition]], [[Mental-Models/First-Principles]].
- Do NOT invent placeholder links like [[CustomerName]], [[Target]], [[YYYY-MM-DD]], [[Related Note]] — those are generic example tokens, not files.
- A wikilink without a corresponding generated file is worse than no wikilink. When in doubt, write the term as bold *text* instead.

Generate substantive content — minimum 3 paragraphs per file. Be thorough across the breadth of the source material — produce one file per distinct topic, do not consolidate distinct ideas into a single file."""

# Each topic chunk owns one slice of the output namespace. Every chunk sees the
# full ingested input — only the output scope differs. This eliminates the
# cross-chunk duplication that the old round-robin sharding produced.
TOPIC_CHUNKS: list[tuple[str, str]] = [
    ("profile", """Generate ONLY these files in your output, nothing else:

- "User-Profile.md": ONE file — psychological calibration profile (thinking style, strengths, blind spots, growth edges, AI behavior rules). Distill the assessments (Kolbe, Working Genius, MBTI, StrengthsFinder, etc.) and identity material into a single coherent profile. Do NOT emit multiple variants.
- "MOCs/{Topic}-MOC.md": Maps of Content — one per major theme the user cares about (e.g., Sales-MOC, Productivity-MOC, Philosophy-MOC, Customer-Success-MOC). Each MOC should list 5+ related items via wikilinks across Books/Frameworks/Concepts/Principles/People."""),

    ("books", """Generate ONLY files of this type, nothing else:

- "Books/{Title}.md" — one per book referenced anywhere in the source material. Include: summary, key concepts, memorable quotes, application notes, wikilinks to related Concepts/Frameworks/People. Aim for breadth — if a book is named or excerpted, generate a file for it. Do NOT generate multiple files for the same book."""),

    ("quotes", """Generate ONLY files of this type, nothing else:

- "Quotes/{Source}-Quotes.md" — one file per source (book, person, transcript). Each file is a curated list of memorable lines from that source with brief context for each quote."""),

    ("frameworks", """Generate ONLY files of this type, nothing else:

- "Frameworks/{Name}.md" — one file per distinct actionable system or methodology mentioned in the source material (e.g., MEDDICC, GTD, Blue Ocean ERRC, OKRs, Sandler, Question-Based Selling, Habit Loop, Four Laws of Behavior Change). For each: what it is, how to apply, when to use, wikilinks. Do NOT create multiple framework files for the same methodology under different names — pick the most canonical name."""),

    ("concepts", """Generate ONLY files of this type, nothing else:

- "Concepts/{Name}.md" — one file per distinct extracted idea. Aim for breadth: 40+ concept files spanning the entire source corpus (sales, psychology, productivity, philosophy, decision-making, etc.). Each file: definition, examples, wikilinks. Concepts are atomic ideas, NOT frameworks (which are systems) or principles (which are universal truths)."""),

    ("mental_models", """Generate ONLY files of this type, nothing else:

- "Mental Models/{Name}.md" — one file per thinking tool from the source material (e.g., First Principles, Inversion, Second-Order Thinking, Map vs Territory, System 1/2, Circle of Competence). Each: description, when to use, concrete example."""),

    ("principles", """Generate ONLY files of this type, nothing else:

- "Principles/{Name}.md" — one file per universal truth or operating rule the user holds or that the source material asserts. Each: statement, why it's true, examples, wikilinks. Principles are durable rules ("Always do X", "Never do Y") — not concepts and not frameworks."""),

    ("people", """Generate ONLY files of this type, nothing else:

- "People/{Name}.md" — one file per author, mentor, or notable figure referenced in the source material. Each: who they are, their key ideas, notable works, why they matter to the user, wikilinks."""),
]

_PASS2_SYSTEM = """Analyze a personal knowledge wiki for gaps against this standard structure:
- User-Profile.md (psychological profile)
- 3+ Books
- 5+ Frameworks
- 5+ Concepts
- 1+ MOC per major topic area the person cares about
- 3+ Principles
- 3+ People

Return ONLY a JSON array of gap objects. Empty array if no gaps.
Each gap object: {"category": "psych_profile|frameworks|books|concepts|moc|principles|people", "description": "specific gap found", "prompt": "precise question to ask user", "upload_accepted": true|false}

Prompts must be specific. Bad: "Add more frameworks." Good: "What systems do you use to prioritize your work? (e.g., GTD, Eisenhower Matrix, OKRs)"
Be concise — 3 gaps maximum."""


def _call_kimi(
    api_key: str,
    system: str,
    user_content: str,
    url: str = _FW_URL,
    model: str = _FW_MODEL,
    max_tokens: int = _FW_MAX_TOKENS,
) -> tuple[str, int, str | None]:
    """Returns (generated_text, total_tokens, finish_reason).

    finish_reason is the last non-null value reported by the API (e.g. "stop",
    "length"). None means the stream ended without an explicit reason — usually
    a network truncation, which also produces broken JSON.
    """
    payload: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0.6,
        "stream": True,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
    }
    if url == _FW_URL:
        # Fireworks-specific sampling params not accepted by Claude/TrueFoundry
        payload.update({"top_p": 1, "top_k": 40, "presence_penalty": 0, "frequency_penalty": 0})
    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    last_exc = None
    for attempt in range(3):
        if attempt > 0:
            time.sleep(2 ** attempt)  # 2s, 4s
        try:
            # stream=True + per-chunk read timeout: timeout resets on every token,
            # so a 20-minute generation never hits the wall-clock limit.
            resp = requests.post(
                url, headers=headers, json=payload,
                timeout=(10, 120), stream=True,
            )
            resp.raise_for_status()
            parts = []
            usage_tokens = 0
            finish_reason: str | None = None
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                choices = chunk.get("choices", [])
                if not choices:
                    usage = chunk.get("usage") or {}
                    if usage.get("total_tokens"):
                        usage_tokens = usage["total_tokens"]
                    continue
                choice = choices[0]
                delta = (choice.get("delta") or {}).get("content") or ""
                parts.append(delta)
                fr = choice.get("finish_reason")
                if fr:
                    finish_reason = fr
            result = "".join(parts)
            tokens = usage_tokens or ((len(user_content) + len(result)) // 4)
            return result, tokens, finish_reason
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code < 500 and e.response.status_code != 429:
                raise  # don't retry 4xx except 429
            last_exc = e
        except requests.RequestException as e:
            last_exc = e
    raise last_exc


def _parse_ndjson(text: str) -> tuple[list[VaultFile], dict]:
    """Parse NDJSON wiki output: one JSON object per line, each {path, content}.

    Truncation-resilient — a cut-off final line is discarded but earlier
    files are recovered. Returns (files, meta) with line_count/lines_failed/
    values_dropped_non_str counters.
    """
    meta = {"extraction_path": "ndjson", "error": None,
            "line_count": 0, "lines_failed": 0, "values_dropped_non_str": 0}
    files: list[VaultFile] = []
    last_error: str | None = None
    for line in text.split("\n"):
        line = line.strip().rstrip(",")  # tolerate trailing commas from old JSON-envelope habit
        if not line or not line.startswith("{"):
            continue
        meta["line_count"] += 1
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            meta["lines_failed"] += 1
            last_error = f"line {meta['line_count']}: {type(e).__name__}: {e}"
            continue
        if not isinstance(obj, dict):
            meta["values_dropped_non_str"] += 1
            continue
        path = obj.get("path")
        content = obj.get("content")
        if isinstance(path, str) and isinstance(content, str):
            files.append(VaultFile(path=path, content=content))
        else:
            meta["values_dropped_non_str"] += 1
    if not files:
        meta["extraction_path"] = "failed"
        meta["error"] = last_error or "no valid NDJSON lines found"
    return files, meta


def _parse_json_envelope(text: str) -> tuple[list[VaultFile], dict]:
    """Legacy single-JSON-object parser. Kept as a fallback if the model
    regresses to emitting one big object instead of NDJSON."""
    meta = {"extraction_path": "failed", "error": None, "values_dropped_non_str": 0}
    last_error: str | None = None
    for label, attempt in (("envelope_direct", text),
                           ("envelope_extract_object", _extract_json_object(text))):
        if attempt is None:
            continue
        try:
            data = json.loads(attempt)
        except (json.JSONDecodeError, AttributeError) as e:
            last_error = f"{type(e).__name__}: {e}"
            continue
        if isinstance(data, dict):
            meta["extraction_path"] = label
            meta["values_dropped_non_str"] = sum(1 for v in data.values() if not isinstance(v, str))
            return ([VaultFile(path=k, content=v) for k, v in data.items() if isinstance(v, str)], meta)
        last_error = f"TypeError: top-level JSON is {type(data).__name__}, not dict"
    meta["error"] = last_error
    return [], meta


def _parse_wiki_response_with_meta(raw: str) -> tuple[list[VaultFile], dict]:
    """Parse model output and return (files, diagnostics).

    Tries NDJSON first (current prompt format), falls back to the legacy
    JSON-envelope parser. Diagnostics report which path succeeded and any
    silent drops along the way.
    """
    text = _strip_fence(raw.strip())
    files, meta = _parse_ndjson(text)
    if files:
        return files, meta
    # NDJSON yielded nothing — try the legacy envelope format
    envelope_files, envelope_meta = _parse_json_envelope(text)
    if envelope_files:
        return envelope_files, envelope_meta
    # Both failed — return the NDJSON diagnostics since that's the current format
    return [], meta


def _parse_wiki_response(raw: str) -> list[VaultFile]:
    files, _ = _parse_wiki_response_with_meta(raw)
    return files


def _extract_json_object(text: str) -> str | None:
    """Find the outermost {...} block in text, handling nested braces."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _backend(config: JobConfig) -> tuple[str, str, str, int]:
    """Return (api_key, url, model, max_tokens) — TrueFoundry if available, else Fireworks."""
    if config.truefoundry_api_key:
        return config.truefoundry_api_key, _TFY_URL, _TFY_MODEL, _TFY_MAX_TOKENS
    return config.fireworks_api_key, _FW_URL, _FW_MODEL, _FW_MAX_TOKENS


def _build_input_block(config: JobConfig, ingested_files: list[VaultFile]) -> str:
    """Single shared input block fed identically to every topic chunk."""
    block = f"INTERVIEW ANSWERS:\n{json.dumps(config.interview_answers, indent=2)}\n\n"
    for f in ingested_files:
        block += f"FILE: {f.path}\n{f.content[:MAX_INPUT_CHARS_PER_FILE]}\n\n"
    return block


_WIKILINK_RE = re.compile(r"\[\[([^\[\]\|\n]+?)(\|[^\[\]\n]+)?\]\]")


def _path_set_for_links(merged: dict[str, str]) -> set[str]:
    """Set of valid wikilink targets — paths with and without the .md extension,
    plus the bare basename (Obsidian resolves [[Foo]] to any file named Foo.md)."""
    targets: set[str] = set()
    for path in merged:
        targets.add(path)
        if path.endswith(".md"):
            targets.add(path[:-3])
            targets.add(path.rsplit("/", 1)[-1][:-3])
    return targets


def _strip_dangling_wikilinks(merged: dict[str, str]) -> dict[str, int]:
    """Replace [[wikilinks]] whose targets don't exist with the visible label
    formatted as bold text. Mutates merged in place. Returns per-file counts of
    links stripped (for diagnostics)."""
    targets = _path_set_for_links(merged)
    stripped_counts: dict[str, int] = {}

    def _repair(match: re.Match) -> str:
        target = match.group(1).strip()
        alias = match.group(2)
        # Normalize for lookup: handle anchor fragments like "Foo#Heading"
        bare = target.split("#", 1)[0]
        if bare in targets or bare.lstrip("/") in targets:
            return match.group(0)  # keep — target exists
        # Dangling: render the visible text as bold instead of a link
        visible = alias[1:].strip() if alias else target.rsplit("/", 1)[-1]
        return f"**{visible}**"

    for path, content in list(merged.items()):
        new_content, n = _WIKILINK_RE.subn(_repair, content)
        replaced = sum(1 for _ in _WIKILINK_RE.finditer(content)) - sum(1 for _ in _WIKILINK_RE.finditer(new_content))
        if replaced > 0:
            stripped_counts[path] = replaced
            merged[path] = new_content
    return stripped_counts


def _build_traversal_index(merged: dict[str, str]) -> str:
    """Generate TRAVERSAL-INDEX.md deterministically from merged file paths.

    Pulls each file's `description:` frontmatter line for the index. Avoids
    making the model invent an index that's blind to what the other topic
    chunks produced."""
    desc_re = re.compile(r"^description:\s*(.+)$", re.MULTILINE)
    lines = ["---", "type: index", "description: Flat traversal index for the wiki", "---", "", "# Traversal Index", ""]
    for path in sorted(merged.keys()):
        if path == "TRAVERSAL-INDEX.md":
            continue
        m = desc_re.search(merged[path])
        desc = m.group(1).strip() if m else ""
        link = path[:-3] if path.endswith(".md") else path
        lines.append(f"- [[{link}]] — {desc}" if desc else f"- [[{link}]]")
    return "\n".join(lines) + "\n"


def generate_wiki(
    config: JobConfig,
    ingested_files: list[VaultFile],
    on_chunk=None,
    debug_dir: str | None = None,
) -> list[VaultFile]:
    """Pass 1: generate wiki from interview answers + ingested content.

    Topic-based chunking: every chunk sees ALL input files and owns ONE slice
    of the output namespace (User-Profile, Books, Frameworks, Concepts, etc.).
    This eliminates the cross-chunk duplication that round-robin sharding
    produced (8x rewrites of User-Profile.md, etc.) while preserving full
    input visibility for every topic.

    on_chunk(chunk_index, total_chunks, tokens) is called as each topic call
    completes. When debug_dir is set (or env var ENTROPY_WIKI_DEBUG_DIR),
    writes chunk_{i}.json per chunk for offline replay analysis.
    """
    api_key, url, model, max_tokens = _backend(config)

    debug_dir = debug_dir or os.environ.get("ENTROPY_WIKI_DEBUG_DIR") or None
    debug_path: Path | None = None
    if debug_dir:
        debug_path = Path(debug_dir)
        debug_path.mkdir(parents=True, exist_ok=True)

    if not ingested_files:
        logger.warning("[wiki] no ingested files — skipping wiki generation")
        return []

    user_content = _build_input_block(config, ingested_files)
    input_file_paths = [f.path for f in ingested_files]

    merged: dict[str, str] = {}
    lock = threading.Lock()
    completed = [0]
    total = len(TOPIC_CHUNKS)

    def _process(i: int, name: str, system: str) -> tuple[int, str, str, int, str | None]:
        raw, tokens, finish_reason = _call_kimi(
            api_key, system, user_content, url=url, model=model, max_tokens=max_tokens
        )
        return i, name, raw, tokens, finish_reason

    with ThreadPoolExecutor(max_workers=min(total, MAX_PARALLEL_CHUNKS)) as pool:
        futures = {
            pool.submit(_process, i, name, _PASS1_BASE_SYSTEM + "\n\n" + topic_prompt): i
            for i, (name, topic_prompt) in enumerate(TOPIC_CHUNKS)
        }
        for future in as_completed(futures):
            i, name, raw, tokens, finish_reason = future.result()
            files, parse_meta = _parse_wiki_response_with_meta(raw)

            logger.info(
                "[wiki] chunk %d/%d topic=%s tokens=%d raw_chars=%d finish=%s "
                "parse=%s files=%d dropped_non_str=%d error=%s",
                i + 1, total, name, tokens, len(raw), finish_reason or "none",
                parse_meta["extraction_path"], len(files),
                parse_meta["values_dropped_non_str"], parse_meta["error"] or "none",
            )

            if debug_path:
                artifact = {
                    "chunk_idx": i,
                    "total_chunks": total,
                    "topic": name,
                    "input_chars": len(user_content),
                    "input_files": input_file_paths,
                    "raw_response": raw,
                    "raw_chars": len(raw),
                    "tokens": tokens,
                    "finish_reason": finish_reason,
                    "parse": {
                        "files_count": len(files),
                        "files": [vf.path for vf in files],
                        "extraction_path": parse_meta["extraction_path"],
                        "error": parse_meta["error"],
                        "values_dropped_non_str": parse_meta["values_dropped_non_str"],
                    },
                }
                (debug_path / f"chunk_{i:02d}_{name}.json").write_text(json.dumps(artifact, indent=2))

            with lock:
                completed[0] += 1
                if on_chunk:
                    on_chunk(completed[0], total, tokens)
                # Same-path collisions inside a topic are rare; keep the longest
                # version rather than concatenating, so we never recreate the 8x
                # bloat that motivated this refactor.
                for vf in files:
                    existing = merged.get(vf.path)
                    if existing is None or len(vf.content) > len(existing):
                        merged[vf.path] = vf.content

    # Strip dangling wikilinks BEFORE generating the traversal index, so the
    # index reflects only the surviving link graph.
    stripped = _strip_dangling_wikilinks(merged)
    if stripped:
        logger.info(
            "[wiki] dropped %d dangling wikilinks across %d file(s)",
            sum(stripped.values()), len(stripped),
        )

    # Generate TRAVERSAL-INDEX from the merged set — gives a complete, accurate
    # index regardless of what each topic chunk produced.
    merged["TRAVERSAL-INDEX.md"] = _build_traversal_index(merged)

    logger.info("[wiki] merge complete: %d unique files from %d topic chunks", len(merged), total)
    return [VaultFile(path=k, content=v) for k, v in merged.items()]


def analyze_gaps(config: JobConfig, wiki_files: list[VaultFile]) -> list[GapItem]:
    """Pass 2: identify gaps in the generated wiki."""
    api_key, url, model, max_tokens = _backend(config)
    file_list = "\n".join(f"- {f.path}" for f in wiki_files)
    raw, _, _ = _call_kimi(
        api_key,
        _PASS2_SYSTEM,
        f"GENERATED FILES:\n{file_list}",
        url=url, model=model, max_tokens=max_tokens,
    )
    try:
        data = json.loads(_strip_fence(raw))
        if not isinstance(data, list):
            return []
        gaps = []
        for g in data:
            if isinstance(g, dict):
                try:
                    gaps.append(GapItem(**g))
                except TypeError:
                    continue
        return gaps
    except json.JSONDecodeError:
        return []
