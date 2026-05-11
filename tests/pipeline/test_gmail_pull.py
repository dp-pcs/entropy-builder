import json
from unittest.mock import MagicMock, patch
from pipeline.gmail_pull import pull_emails, match_domain, flag_tier2, build_email_stub
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
    assert stub.path == "Entropy/Influitive/Blackbaud/Emails/2026-05-05_Renewal-Discussion.md"
    assert "tier2: true" in stub.content
    assert "Renewal Discussion" in stub.content
    assert "thread123" in stub.content
