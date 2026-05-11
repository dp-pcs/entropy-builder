# entropy_builder/pipeline/kimi.py
import json
import re
import time
import requests
from .models import JobConfig, VaultFile, GapItem

_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*)```", re.DOTALL)

FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
MODEL = "accounts/fireworks/models/kimi-k2p6"
CHUNK_SIZE = 80_000  # chars — stay under Kimi's context limit per call

_PASS1_SYSTEM = """You are building a personal knowledge wiki ("Second Brain") for a professional.

Given their interview answers and uploaded notes, generate structured Obsidian markdown files.

Return ONLY a JSON object where keys are relative file paths and values are complete file contents.

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


def _call_kimi(api_key: str, system: str, user_content: str) -> str:
    payload = {
        "model": MODEL,
        "max_tokens": 32768,
        "temperature": 0.6,
        "top_p": 1,
        "top_k": 40,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    last_exc = None
    for attempt in range(3):
        if attempt > 0:
            time.sleep(2 ** attempt)  # 2s, 4s
        try:
            resp = requests.post(FIREWORKS_URL, headers=headers, json=payload, timeout=300)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code < 500 and e.response.status_code != 429:
                raise  # don't retry 4xx except 429
            last_exc = e
        except requests.RequestException as e:
            last_exc = e
    raise last_exc


def _parse_wiki_response(raw: str) -> list[VaultFile]:
    try:
        text = raw.strip()
        if text.startswith("```"):
            m = _CODE_FENCE_RE.search(text)
            if m:
                text = m.group(1).strip()
        data = json.loads(text)
        return [VaultFile(path=k, content=v) for k, v in data.items() if isinstance(v, str)]
    except (json.JSONDecodeError, AttributeError):
        return []


def generate_wiki(config: JobConfig, ingested_files: list[VaultFile]) -> list[VaultFile]:
    """Pass 1: generate wiki from interview answers + ingested content."""
    user_content = f"INTERVIEW ANSWERS:\n{json.dumps(config.interview_answers, indent=2)}\n\n"
    for f in ingested_files:
        user_content += f"FILE: {f.path}\n{f.content[:3000]}\n\n"

    if len(user_content) <= CHUNK_SIZE:
        raw = _call_kimi(config.fireworks_api_key, _PASS1_SYSTEM, user_content)
        return _parse_wiki_response(raw)

    return _generate_wiki_chunked(config, ingested_files)


def _generate_wiki_chunked(config: JobConfig, ingested_files: list[VaultFile]) -> list[VaultFile]:
    interview_block = f"INTERVIEW ANSWERS:\n{json.dumps(config.interview_answers, indent=2)}\n\n"
    chunks = [interview_block]
    for f in ingested_files:
        addition = f"FILE: {f.path}\n{f.content[:3000]}\n\n"
        if len(chunks[-1]) + len(addition) > CHUNK_SIZE:
            chunks.append(addition)
        else:
            chunks[-1] += addition

    merged: dict[str, str] = {}
    for i, chunk in enumerate(chunks):
        prefix = "CONTINUE and EXTEND the wiki with additional content. Merge with prior output.\n\n" if i > 0 else ""
        raw = _call_kimi(config.fireworks_api_key, _PASS1_SYSTEM, prefix + chunk)
        for vf in _parse_wiki_response(raw):
            if vf.path in merged and vf.path != "TRAVERSAL-INDEX.md":
                merged[vf.path] += "\n\n" + vf.content
            else:
                merged[vf.path] = vf.content

    return [VaultFile(path=k, content=v) for k, v in merged.items()]


def analyze_gaps(config: JobConfig, wiki_files: list[VaultFile]) -> list[GapItem]:
    """Pass 2: identify gaps in the generated wiki."""
    file_list = "\n".join(f"- {f.path}" for f in wiki_files)
    raw = _call_kimi(
        config.fireworks_api_key,
        _PASS2_SYSTEM,
        f"GENERATED FILES:\n{file_list}",
    )
    try:
        data = json.loads(raw.strip())
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
