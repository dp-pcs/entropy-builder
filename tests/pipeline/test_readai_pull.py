from unittest.mock import MagicMock, patch
from pipeline.readai_pull import pull_transcripts, match_meeting_to_customer, build_transcript_stub
from pipeline.models import VaultFile

DOMAINS = {
    "domains": {
        "blackbaud.com": {"customer": "Blackbaud", "product": "Influitive"},
    }
}

SAMPLE_MEETING = {
    "id": "meet123",
    "title": "Quarterly Business Review",
    "start_time_ms": 1714999200000,  # 2026-05-06 14:00 UTC
    "participants": [
        {"email": "me@mycompany.com"},
        {"email": "christine.newman@blackbaud.com"},
    ],
    "summary": "Discussed renewal timeline and product feedback.",
}


def test_match_meeting_finds_customer():
    customer = match_meeting_to_customer(SAMPLE_MEETING, DOMAINS)
    assert customer is not None
    assert customer["customer"] == "Blackbaud"


def test_match_meeting_returns_none_no_match():
    meeting = {**SAMPLE_MEETING, "participants": [{"email": "unknown@xyz.com"}]}
    assert match_meeting_to_customer(meeting, DOMAINS) is None


def test_build_transcript_stub_valid_path():
    stub = build_transcript_stub(
        customer_name="Blackbaud",
        product="Influitive",
        title="Quarterly Business Review",
        date_str="2026-05-06",
        meeting_id="meet123",
        summary="Discussed renewal timeline.",
    )
    assert stub.path == "Portfolio Brain/Influitive/Blackbaud/Transcripts/2026-05-06_Quarterly-Business-Review.md"
    assert "meet123" in stub.content
    assert "Discussed renewal timeline." in stub.content


def test_pull_transcripts_calls_api(mocker):
    mock_get = mocker.patch("pipeline.readai_pull.requests.get")
    mock_get.return_value.json.return_value = {"data": [SAMPLE_MEETING], "has_more": False}
    mock_get.return_value.raise_for_status = MagicMock()

    from pipeline.models import JobConfig
    cfg = JobConfig(
        user_name="T", user_role="ic", account_manager_name="T", team_members=[],
        notion_token="", notion_database_id="", google_credentials={},
        readai_access_token="key123", fireworks_api_key="", interview_answers={},
        entropy_template_path="/tmp",
    )
    stubs = pull_transcripts(cfg, DOMAINS)
    assert len(stubs) == 1
    assert "Blackbaud" in stubs[0].path
    # Verify API key was sent in headers
    call_kwargs = mock_get.call_args
    assert "key123" in str(call_kwargs)


def test_match_meeting_with_string_participants():
    """read.ai may return participants as bare email strings, not objects."""
    meeting = {"participants": ["me@mycompany.com", "christine.newman@blackbaud.com"]}
    customer = match_meeting_to_customer(meeting, DOMAINS)
    assert customer is not None
    assert customer["customer"] == "Blackbaud"


def test_match_meeting_with_mixed_shape_participants():
    """Tolerate mixed-shape participants (some strings, some dicts, garbage)."""
    meeting = {"participants": ["me@mycompany.com", None, {"email": "buyer@blackbaud.com"}, 42]}
    customer = match_meeting_to_customer(meeting, DOMAINS)
    assert customer is not None
    assert customer["customer"] == "Blackbaud"


def test_build_transcript_stub_with_string_action_items():
    """read.ai may return action_items as plain strings."""
    stub = build_transcript_stub(
        customer_name="Blackbaud", product="Influitive", title="QBR",
        date_str="2026-05-06", meeting_id="m1", summary="",
        action_items=["Follow up with Christine", "Send proposal"],
    )
    assert "- Follow up with Christine" in stub.content
    assert "- Send proposal" in stub.content
