import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pipeline.kimi import (
    generate_wiki,
    analyze_gaps,
    _parse_wiki_response,
    _parse_wiki_response_with_meta,
)
from pipeline.models import JobConfig, VaultFile, GapItem


def _make_config(fireworks_api_key="fw-test"):
    return JobConfig(
        user_name="Test", user_role="ic", account_manager_name="Test",
        team_members=[], notion_token="", notion_database_id="",
        google_credentials={}, readai_access_token="", fireworks_api_key=fireworks_api_key,
        interview_answers={"role": "AE", "books": ["Atomic Habits"]},
        entropy_template_path="/tmp",
    )


def test_parse_wiki_response_valid_json():
    raw = json.dumps({
        "Books/Atomic Habits.md": "---\ntype: book\n---\n# Atomic Habits",
        "TRAVERSAL-INDEX.md": "- [[Books/Atomic Habits]] — habit formation"
    })
    files = _parse_wiki_response(raw)
    assert len(files) == 2
    assert any(f.path == "Books/Atomic Habits.md" for f in files)


def test_parse_wiki_response_strips_code_fence():
    raw = "```json\n" + json.dumps({"User-Profile.md": "# Profile"}) + "\n```"
    files = _parse_wiki_response(raw)
    assert len(files) == 1
    assert files[0].path == "User-Profile.md"


def test_parse_wiki_response_invalid_json_returns_empty():
    files = _parse_wiki_response("not json at all")
    assert files == []


def _sse_lines(content: str, finish_reason: str | None = None) -> list[bytes]:
    """Build minimal SSE stream wrapping `content` as a single delta chunk."""
    delta = json.dumps({"choices": [{"delta": {"content": content}}]})
    lines = [f"data: {delta}".encode()]
    if finish_reason:
        final = json.dumps({"choices": [{"delta": {}, "finish_reason": finish_reason}]})
        lines.append(f"data: {final}".encode())
    lines.append(b"data: [DONE]")
    return lines


def _mock_sse_response(content: str, finish_reason: str | None = None) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.iter_lines.return_value = iter(_sse_lines(content, finish_reason))
    return resp


def test_generate_wiki_calls_fireworks(mocker):
    body = json.dumps({
        "User-Profile.md": "---\ntype: profile\n---\n# Profile",
        "TRAVERSAL-INDEX.md": "- [[User-Profile]] — profile",
    })
    mocker.patch("pipeline.kimi.requests.post", return_value=_mock_sse_response(body))

    cfg = _make_config()
    files = generate_wiki(cfg, [VaultFile("note.md", "# My Note")])
    assert any(f.path == "User-Profile.md" for f in files)


def test_analyze_gaps_returns_gap_items(mocker):
    body = json.dumps([
        {"category": "psych_profile", "description": "No profile",
         "prompt": "Do you have a DiSC result?", "upload_accepted": True}
    ])
    mocker.patch("pipeline.kimi.requests.post", return_value=_mock_sse_response(body))

    cfg = _make_config()
    gaps = analyze_gaps(cfg, [VaultFile("Books/Atomic Habits.md", "# AH")])
    assert len(gaps) == 1
    assert gaps[0].category == "psych_profile"
    assert gaps[0].upload_accepted is True


def test_analyze_gaps_returns_empty_on_no_gaps(mocker):
    mocker.patch("pipeline.kimi.requests.post", return_value=_mock_sse_response("[]"))

    cfg = _make_config()
    gaps = analyze_gaps(cfg, [VaultFile("User-Profile.md", "# P")])
    assert gaps == []


def test_parse_wiki_response_handles_nested_fences():
    inner = json.dumps({"file.md": "# Title\n```python\ncode here\n```\n"})
    raw = f"```json\n{inner}\n```"
    files = _parse_wiki_response(raw)
    assert len(files) == 1
    assert "```python" in files[0].content


def test_parse_with_meta_reports_failure():
    files, meta = _parse_wiki_response_with_meta("totally not json")
    assert files == []
    assert meta["extraction_path"] == "failed"
    assert meta["error"] is not None


def test_parse_with_meta_reports_success_path():
    raw = json.dumps({"User-Profile.md": "# Profile"})
    files, meta = _parse_wiki_response_with_meta(raw)
    assert len(files) == 1
    # Legacy single-object format → envelope fallback path
    assert meta["extraction_path"] == "envelope_direct"
    assert meta["error"] is None
    assert meta["values_dropped_non_str"] == 0


def test_parse_with_meta_counts_dropped_non_string_values():
    raw = json.dumps({
        "good.md": "# ok",
        "bad.md": {"content": "# nope", "tags": []},   # non-string value silently dropped today
    })
    files, meta = _parse_wiki_response_with_meta(raw)
    assert len(files) == 1
    assert meta["values_dropped_non_str"] == 1


def test_generate_wiki_writes_one_debug_artifact_per_topic(mocker, tmp_path):
    """Topic-based chunking: each of the 8 output topics writes its own
    artifact so we can audit per-topic generation independently."""
    body = (
        '{"path": "User-Profile.md", "content": "---\\ntype: profile\\n---\\n# Profile"}\n'
    )
    mocker.patch("pipeline.kimi.requests.post",
                 return_value=_mock_sse_response(body, finish_reason="stop"))

    cfg = _make_config()
    debug_dir = tmp_path / "wiki_debug"
    generate_wiki(cfg, [VaultFile("note.md", "# My Note")], debug_dir=str(debug_dir))

    artifacts = sorted(debug_dir.glob("chunk_*.json"))
    from pipeline.kimi import TOPIC_CHUNKS
    assert len(artifacts) == len(TOPIC_CHUNKS)
    # Artifact filenames include the topic name for easy inspection
    topic_names = {name for name, _ in TOPIC_CHUNKS}
    for art_path in artifacts:
        assert any(t in art_path.name for t in topic_names), art_path.name
    # All artifacts share the same input
    art = json.loads(artifacts[0].read_text())
    assert art["finish_reason"] == "stop"
    assert art["parse"]["extraction_path"] == "ndjson"
    assert art["input_files"] == ["note.md"]


def test_generate_wiki_keeps_longest_on_path_collision(mocker):
    """When two chunks emit the same path, the longer version wins — never
    concatenated. This is the property that kills the old 8x bloat."""
    call_count = [0]

    def fake_post(*args, **kwargs):
        # First chunk emits a short User-Profile; subsequent emit longer ones
        idx = call_count[0]
        call_count[0] += 1
        if idx == 0:
            body = '{"path": "User-Profile.md", "content": "short"}\n'
        else:
            body = '{"path": "User-Profile.md", "content": "this is a much longer profile body"}\n'
        return _mock_sse_response(body, finish_reason="stop")

    mocker.patch("pipeline.kimi.requests.post", side_effect=fake_post)

    cfg = _make_config()
    files = generate_wiki(cfg, [VaultFile("note.md", "# Note")])
    profile = next(f for f in files if f.path == "User-Profile.md")
    assert profile.content == "this is a much longer profile body"
    # Crucially: NOT concatenated
    assert "short" not in profile.content


def test_traversal_index_is_auto_generated(mocker):
    """TRAVERSAL-INDEX.md is deterministic — assembled from merged frontmatter,
    not invented by the model. Guarantees it's complete and accurate."""
    body = (
        '{"path": "Books/X.md", "content": "---\\ntype: book\\ndescription: A book about X\\n---\\n# X"}\n'
        '{"path": "Concepts/Y.md", "content": "---\\ntype: concept\\ndescription: The concept of Y\\n---\\n# Y"}\n'
    )
    mocker.patch("pipeline.kimi.requests.post",
                 return_value=_mock_sse_response(body, finish_reason="stop"))

    cfg = _make_config()
    files = generate_wiki(cfg, [VaultFile("note.md", "# Note")])
    index = next(f for f in files if f.path == "TRAVERSAL-INDEX.md").content
    assert "[[Books/X]]" in index
    assert "A book about X" in index
    assert "[[Concepts/Y]]" in index
    assert "The concept of Y" in index


def test_generate_wiki_handles_empty_input(mocker):
    """No ingested files → skip wiki generation entirely, no model calls."""
    post_mock = mocker.patch("pipeline.kimi.requests.post")
    cfg = _make_config()
    files = generate_wiki(cfg, [])
    assert files == []
    post_mock.assert_not_called()


def test_dangling_wikilinks_are_stripped(mocker):
    """Links to files that no chunk produced get replaced with bold text so
    Obsidian doesn't show a graph full of dead links."""
    body = (
        '{"path": "Books/Atomic-Habits.md", "content": "Connects to '
        '[[Concepts/Compound-Growth]] and [[Concepts/Missing-Topic]] and '
        '[[Books/Atomic-Habits]] itself."}\n'
        '{"path": "Concepts/Compound-Growth.md", "content": "see [[Books/Atomic-Habits]]"}\n'
    )
    mocker.patch("pipeline.kimi.requests.post",
                 return_value=_mock_sse_response(body, finish_reason="stop"))

    cfg = _make_config()
    files = generate_wiki(cfg, [VaultFile("note.md", "# Note")])
    book = next(f for f in files if f.path == "Books/Atomic-Habits.md")
    # Existing targets preserved
    assert "[[Concepts/Compound-Growth]]" in book.content
    assert "[[Books/Atomic-Habits]]" in book.content
    # Missing target rewritten to bold so the graph stays clean
    assert "[[Concepts/Missing-Topic]]" not in book.content
    assert "**Missing-Topic**" in book.content


def test_dangling_wikilink_uses_alias_when_present():
    """When a dangling link has a |alias, the visible alias becomes the bold text."""
    from pipeline.kimi import _strip_dangling_wikilinks
    merged = {"Books/Real.md": "see [[Concepts/Fake|the fake one]] and [[Books/Real]]"}
    _strip_dangling_wikilinks(merged)
    assert "**the fake one**" in merged["Books/Real.md"]
    assert "[[Books/Real]]" in merged["Books/Real.md"]


def test_generate_wiki_captures_truncated_response(mocker, tmp_path):
    """If the model emits the legacy JSON envelope AND truncates mid-content,
    the envelope parser fails and we record it as a parse failure per topic."""
    truncated = '{"Books/X.md": "---\\ntype: book\\n---\\n# X"  '  # never closed
    mocker.patch("pipeline.kimi.requests.post",
                 return_value=_mock_sse_response(truncated, finish_reason="length"))

    cfg = _make_config()
    debug_dir = tmp_path / "wiki_debug"
    files = generate_wiki(cfg, [VaultFile("note.md", "# Note")], debug_dir=str(debug_dir))

    artifacts = sorted(debug_dir.glob("chunk_*.json"))
    assert artifacts, "expected per-topic debug artifacts"
    art = json.loads(artifacts[0].read_text())
    assert art["finish_reason"] == "length"
    assert art["parse"]["extraction_path"] == "failed"
    # Wiki output is just the auto-generated TRAVERSAL-INDEX (built from an
    # empty merged set when every chunk parse-fails)
    assert {f.path for f in files} == {"TRAVERSAL-INDEX.md"}


def test_parse_ndjson_basic():
    raw = (
        '{"path": "User-Profile.md", "content": "---\\ntype: profile\\n---\\n# P"}\n'
        '{"path": "Books/Atomic Habits.md", "content": "---\\ntype: book\\n---\\n# AH"}\n'
    )
    files, meta = _parse_wiki_response_with_meta(raw)
    assert len(files) == 2
    assert meta["extraction_path"] == "ndjson"
    assert meta["line_count"] == 2
    assert meta["lines_failed"] == 0


def test_parse_ndjson_recovers_when_last_line_truncated():
    """Critical case: the model hits max_tokens mid-content on the final file.
    Earlier files must still be recovered."""
    raw = (
        '{"path": "User-Profile.md", "content": "# Complete profile"}\n'
        '{"path": "Books/X.md", "content": "# Complete book"}\n'
        '{"path": "Books/Y.md", "content": "# Partial book that gets cut off here'
    )
    files, meta = _parse_wiki_response_with_meta(raw)
    assert len(files) == 2
    assert {f.path for f in files} == {"User-Profile.md", "Books/X.md"}
    assert meta["lines_failed"] == 1


def test_parse_ndjson_strips_unclosed_code_fence():
    """Truncated response retains the opening ```ndjson but loses the closing
    fence. Parser must still extract complete lines."""
    raw = '```ndjson\n{"path": "a.md", "content": "# A"}\n{"path": "b.md", "content": "# B partial'
    files, _ = _parse_wiki_response_with_meta(raw)
    assert len(files) == 1
    assert files[0].path == "a.md"


def test_parse_ndjson_falls_back_to_json_envelope():
    """If the model regresses to emitting the legacy single-object format,
    the parser should still work."""
    raw = json.dumps({
        "User-Profile.md": "# Profile",
        "Books/X.md": "# Book",
    })
    files, meta = _parse_wiki_response_with_meta(raw)
    assert len(files) == 2
    assert meta["extraction_path"].startswith("envelope")


def test_parse_ndjson_ignores_preamble():
    """If Sonnet ignores the 'no preamble' rule and adds prose before the JSON,
    the parser should skip non-JSON lines."""
    raw = (
        'Here are the files:\n'
        '\n'
        '{"path": "a.md", "content": "# A"}\n'
        '{"path": "b.md", "content": "# B"}\n'
    )
    files, _ = _parse_wiki_response_with_meta(raw)
    assert len(files) == 2
