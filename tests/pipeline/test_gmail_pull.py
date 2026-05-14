import json
from unittest.mock import MagicMock, patch
from pipeline.gmail_pull import (
    pull_emails,
    match_domain,
    flag_tier2,
    build_email_stub,
    _process_thread,
)
from pipeline.models import VaultFile


DOMAINS = {
    "domains": {
        "blackbaud.com": {"customer": "Blackbaud", "product": "Influitive"},
        "acme.com": {"customer": "Acme Corp", "product": "Tivian"},
    }
}

SAMPLE_THREAD = {
    "id": "thread123",
    "messages": [{
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Renewal Discussion"},
                {"name": "From", "value": "Christine Newman <christine.newman@blackbaud.com>"},
                {"name": "Date", "value": "Mon, 5 May 2026 10:00:00 +0000"},
            ],
            "body": {"data": "V2Ugd2FudCB0byBjYW5jZWwgb3VyIHN1YnNjcmlwdGlvbg=="}  # "We want to cancel our subscription"
        }
    }]
}


def test_match_domain_finds_customer():
    customer = match_domain("christine.newman@blackbaud.com", DOMAINS)
    assert customer is not None
    assert customer["customer"] == "Blackbaud"


def test_match_domain_returns_none_for_unknown():
    assert match_domain("unknown@xyz.com", DOMAINS) is None


def test_flag_tier2_detects_cancel():
    assert flag_tier2("We want to cancel our subscription") is True


def test_flag_tier2_clean_email():
    assert flag_tier2("Looking forward to our next meeting") is False


def test_flag_tier2_detects_all_keywords():
    keywords = ["cancel", "terminate", "alternative", "competitor",
                "budget cut", "unacceptable", "executive review", "not renewing"]
    for kw in keywords:
        assert flag_tier2(f"We are considering {kw} options") is True


def test_build_email_stub_valid_file():
    stub = build_email_stub(
        customer_name="Blackbaud",
        product="Influitive",
        subject="Renewal Discussion",
        sender="Christine Newman <christine.newman@blackbaud.com>",
        date_str="2026-05-05",
        thread_id="thread123",
        is_tier2=True,
    )
    assert stub.path == "Portfolio Brain/Influitive/Blackbaud/Emails/2026-05-05_Renewal-Discussion.md"
    assert "tier2: true" in stub.content
    assert "Renewal Discussion" in stub.content
    assert "thread123" in stub.content


def _msg(from_addr: str, subject: str = "Hi", date: str = "Mon, 5 May 2026 10:00:00 +0000",
         body_b64: str = "") -> dict:
    return {
        "payload": {
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "From", "value": from_addr},
                {"name": "Date", "value": date},
            ],
            "body": {"data": body_b64},
        }
    }


def test_process_thread_matches_when_user_sent_first_message():
    """Regression: user-initiated threads must still match if a customer replies later."""
    thread = {
        "id": "t1",
        "messages": [
            _msg("Jaime Alvarez <jaime.alvarez@trilogy.com>", subject="Following up"),
            _msg("Christine <christine@blackbaud.com>"),
            _msg("Jaime Alvarez <jaime.alvarez@trilogy.com>"),
        ],
    }
    stubs = _process_thread(thread, DOMAINS)
    assert len(stubs) == 1
    assert "Blackbaud" in stubs[0].path
    assert "Following up" in stubs[0].content


def test_process_thread_drops_internal_only_threads():
    thread = {
        "id": "t2",
        "messages": [
            _msg("Jaime <jaime@trilogy.com>"),
            _msg("Other Internal <other@aurea.com>"),
        ],
    }
    assert _process_thread(thread, DOMAINS) == []


def test_process_thread_routes_reseller_threads_to_inbox():
    thread = {
        "id": "t3",
        "messages": [
            _msg("Jaime <jaime@trilogy.com>", subject="Quote request"),
            _msg("Rep <rep@shi.com>"),
        ],
    }
    stubs = _process_thread(thread, DOMAINS)
    assert len(stubs) == 1
    assert stubs[0].path.startswith("Portfolio Brain/_inbox/Resellers/shi.com/")
    assert "ambiguous: true" in stubs[0].content
    assert "reseller_domain: \"shi.com\"" in stubs[0].content


def test_process_thread_prefers_customer_match_over_reseller():
    thread = {
        "id": "t4",
        "messages": [
            _msg("Jaime <jaime@trilogy.com>"),
            _msg("Rep <rep@shi.com>"),
            _msg("Buyer <buyer@blackbaud.com>"),
        ],
    }
    stubs = _process_thread(thread, DOMAINS)
    assert len(stubs) == 1
    assert "Blackbaud" in stubs[0].path
    assert "ambiguous" not in stubs[0].content


def test_process_thread_unknown_external_returns_empty():
    thread = {
        "id": "t5",
        "messages": [
            _msg("Stranger <stranger@randomvendor.com>"),
        ],
    }
    assert _process_thread(thread, DOMAINS) == []


def test_tier2_detected_in_later_message_body():
    """Tier-2 keyword in a customer reply (not the first message) must still flag."""
    # base64("We are considering switching vendors next quarter.") with urlsafe alphabet
    import base64
    body_b64 = base64.urlsafe_b64encode(
        b"We are considering switching vendors next quarter."
    ).decode().rstrip("=")
    thread = {
        "id": "t6",
        "messages": [
            _msg("Jaime <jaime@trilogy.com>", subject="Q3 check-in"),
            _msg("Buyer <buyer@blackbaud.com>", subject="Re: Q3 check-in", body_b64=body_b64),
        ],
    }
    stubs = _process_thread(thread, DOMAINS)
    assert len(stubs) == 1
    assert "tier2: true" in stubs[0].content


def test_tier2_detected_via_snippet():
    """Even when bodies aren't fully fetched, snippet-level matches should fire."""
    thread = {
        "id": "t7",
        "messages": [
            _msg("Jaime <jaime@trilogy.com>", subject="Following up"),
            {
                "snippet": "Hi Jaime — we plan to cancel renewal this cycle.",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Re: Following up"},
                        {"name": "From", "value": "Buyer <buyer@blackbaud.com>"},
                        {"name": "Date", "value": "Mon, 5 May 2026 11:00:00 +0000"},
                    ],
                    "body": {"data": ""},
                },
            },
        ],
    }
    stubs = _process_thread(thread, DOMAINS)
    assert len(stubs) == 1
    assert "tier2: true" in stubs[0].content


def test_tier2_not_flagged_when_no_keywords_anywhere():
    thread = {
        "id": "t8",
        "messages": [
            _msg("Jaime <jaime@trilogy.com>", subject="Lunch next week"),
            _msg("Buyer <buyer@blackbaud.com>", subject="Re: Lunch next week"),
        ],
    }
    stubs = _process_thread(thread, DOMAINS)
    assert len(stubs) == 1
    assert "tier2: false" in stubs[0].content
