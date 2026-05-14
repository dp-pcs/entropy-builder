import json
import pytest
from unittest.mock import patch, MagicMock
from pipeline.kimi import generate_wiki, analyze_gaps, _parse_wiki_response
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


def _sse_lines(content: str) -> list[bytes]:
    """Build minimal SSE stream wrapping `content` as a single delta chunk."""
    delta = json.dumps({"choices": [{"delta": {"content": content}}]})
    return [f"data: {delta}".encode(), b"data: [DONE]"]


def _mock_sse_response(content: str) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.iter_lines.return_value = iter(_sse_lines(content))
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
