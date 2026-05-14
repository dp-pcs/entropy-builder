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

_PASS1_SYSTEM = """You are building a personal knowledge wiki ("Second Brain") for a professional.

Given their interview answers and uploaded notes, generate structured Obsidian markdown files.

CRITICAL OUTPUT FORMAT — newline-delimited JSON (NDJSON):
- Emit one complete JSON object per line: {"path": "<relative path>", "content": "<full file contents>"}
- No preamble, no commentary, no markdown code fences — just JSON objects, one per line.
- Newlines inside content MUST be JSON-escaped as \\n.
- Each line is independent — finish each file before starting the next.

Example (two files):
{"path": "User-Profile.md", "content": "---\\ntype: profile\\n---\\n\\n# Profile\\n\\nContent here."}
{"path": "Books/Atomic Habits.md", "content": "---\\ntype: book\\n---\\n\\n# Atomic Habits"}

Generate these files (skip a type only if there is truly no relevant content):
- "User-Profile.md": psychological calibration profile — thinking style, strengths, blind spots, growth edges, AI behavior rules
- "Books/{Title}.md": one per book — summary, key concepts, quotes, wikilinks to related concepts/frameworks
- "Concepts/{Name}.md": extracted ideas — definition, examples, wikilinks
- "Frameworks/{Name}.md": actionable systems — what it is, how to apply, when to use, wikilinks
- "Principles/{Name}.md": universal truths — statement, depth, examples, wikilinks
- "People/{Name}.md": authors, mentors — who they are, key ideas, notable works, wikilinks
- "Quotes/{Source}-Quotes.md": memorable lines from each source
- "MOCs/{Topic}-MOC.md": thematic maps — only create if 5+ related files exist for the topic
- "Mental Models/{Name}.md": thinking tools — description, use case, example
- "TRAVERSAL-INDEX.md": flat list "- [[path/file]] — one sentence description" for every file generated

Every file MUST start with YAML frontmatter:
---
type: <book|concept|framework|principle|person|quotes|moc|mental-model|profile>
description: <one line>
tags: [<2-4 relevant tags>]
aliases: [<alternate names if any>]
---

Use wikilink syntax [[File Name]] for ALL cross-references. Generate substantive content — minimum 3 paragraphs per file."""

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


def generate_wiki(
    config: JobConfig,
    ingested_files: list[VaultFile],
    on_chunk=None,
    debug_dir: str | None = None,
) -> list[VaultFile]:
    """Pass 1: generate wiki from interview answers + ingested content.

    Always splits files across MAX_PARALLEL_CHUNKS concurrent calls regardless
    of total content size. on_chunk(chunk_index, total_chunks, tokens) is called
    after each call completes.

    When debug_dir is set (or env var ENTROPY_WIKI_DEBUG_DIR), writes
    chunk_{i}.json per chunk containing the input, raw response, finish_reason,
    and parse diagnostics. Used by scripts/replay_wiki_parse.py to iterate on
    parser logic without re-spending model tokens.
    """
    api_key, url, model, max_tokens = _backend(config)
    interview_block = f"INTERVIEW ANSWERS:\n{json.dumps(config.interview_answers, indent=2)}\n\n"

    debug_dir = debug_dir or os.environ.get("ENTROPY_WIKI_DEBUG_DIR") or None
    debug_path: Path | None = None
    if debug_dir:
        debug_path = Path(debug_dir)
        debug_path.mkdir(parents=True, exist_ok=True)

    num_chunks = min(max(len(ingested_files), 1), MAX_PARALLEL_CHUNKS)

    # Distribute files round-robin across chunks so each gets a balanced mix
    groups: list[list[VaultFile]] = [[] for _ in range(num_chunks)]
    for i, f in enumerate(ingested_files):
        groups[i % num_chunks].append(f)

    chunks: list[tuple[str, list[str]]] = []  # (chunk_content, file_paths_in_chunk)
    for group in groups:
        content = interview_block
        for f in group:
            content += f"FILE: {f.path}\n{f.content[:2000]}\n\n"
        chunks.append((content, [f.path for f in group]))

    merged: dict[str, str] = {}
    lock = threading.Lock()
    completed = [0]

    def _process(i: int, chunk: str) -> tuple[int, str, int, str | None]:
        raw, tokens, finish_reason = _call_kimi(
            api_key, _PASS1_SYSTEM, chunk, url=url, model=model, max_tokens=max_tokens
        )
        return i, raw, tokens, finish_reason

    with ThreadPoolExecutor(max_workers=len(chunks)) as pool:
        futures = {pool.submit(_process, i, chunk): i for i, (chunk, _) in enumerate(chunks)}
        for future in as_completed(futures):
            i, raw, tokens, finish_reason = future.result()
            chunk_content, chunk_file_paths = chunks[i]
            files, parse_meta = _parse_wiki_response_with_meta(raw)

            logger.info(
                "[wiki] chunk %d/%d tokens=%d raw_chars=%d finish=%s parse=%s files=%d "
                "dropped_non_str=%d input_files=%d error=%s",
                i + 1, len(chunks), tokens, len(raw), finish_reason or "none",
                parse_meta["extraction_path"], len(files),
                parse_meta["values_dropped_non_str"], len(chunk_file_paths),
                parse_meta["error"] or "none",
            )

            if debug_path:
                artifact = {
                    "chunk_idx": i,
                    "total_chunks": len(chunks),
                    "input_chars": len(chunk_content),
                    "input_files": chunk_file_paths,
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
                (debug_path / f"chunk_{i:02d}.json").write_text(json.dumps(artifact, indent=2))

            with lock:
                completed[0] += 1
                if on_chunk:
                    on_chunk(completed[0], len(chunks), tokens)
                for vf in files:
                    if vf.path in merged and vf.path != "TRAVERSAL-INDEX.md":
                        merged[vf.path] += "\n\n" + vf.content
                    else:
                        merged[vf.path] = vf.content

    logger.info(
        "[wiki] merge complete: %d unique files from %d chunks", len(merged), len(chunks)
    )
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
