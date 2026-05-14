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
    assert meta["extraction_path"] == "direct"
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


def test_generate_wiki_writes_debug_artifacts(mocker, tmp_path):
    body = json.dumps({
        "User-Profile.md": "---\ntype: profile\n---\n# Profile",
        "TRAVERSAL-INDEX.md": "- [[User-Profile]] — profile",
    })
    mocker.patch("pipeline.kimi.requests.post",
                 return_value=_mock_sse_response(body, finish_reason="stop"))

    cfg = _make_config()
    debug_dir = tmp_path / "wiki_debug"
    generate_wiki(cfg, [VaultFile("note.md", "# My Note")], debug_dir=str(debug_dir))

    artifacts = sorted(debug_dir.glob("chunk_*.json"))
    assert len(artifacts) == 1
    art = json.loads(artifacts[0].read_text())
    assert art["chunk_idx"] == 0
    assert art["finish_reason"] == "stop"
    assert art["parse"]["extraction_path"] == "direct"
    assert art["parse"]["files_count"] == 2
    assert "User-Profile.md" in art["parse"]["files"]
    assert art["input_files"] == ["note.md"]


def test_generate_wiki_captures_truncated_response(mocker, tmp_path):
    """When the model hits max_tokens, finish_reason=length and parse fails silently
    today. Verify the artifact records this so we can spot it offline."""
    truncated = '{"Books/X.md": "---\\ntype: book\\n---\\n# X"  '  # never closed
    mocker.patch("pipeline.kimi.requests.post",
                 return_value=_mock_sse_response(truncated, finish_reason="length"))

    cfg = _make_config()
    debug_dir = tmp_path / "wiki_debug"
    files = generate_wiki(cfg, [VaultFile("note.md", "# Note")], debug_dir=str(debug_dir))

    art = json.loads((debug_dir / "chunk_00.json").read_text())
    assert art["finish_reason"] == "length"
    assert art["parse"]["extraction_path"] == "failed"
    assert art["parse"]["error"] is not None
    assert files == []  # confirms today's silent-drop behavior
