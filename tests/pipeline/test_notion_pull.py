import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from pipeline.notion_pull import (
    parse_notion_rows, build_intelligence_summary,
    build_customer_domains, build_hub_nodes, pull_customers
)
from pipeline.models import JobConfig, CustomerRecord


FIXTURES = Path(__file__).parent / "fixtures"


def _load_rows():
    return json.loads((FIXTURES / "sample_notion_rows.json").read_text())


def _make_config():
    return JobConfig(
        user_name="Test User", user_role="ic", account_manager_name="Test User",
        team_members=[], notion_token="tok", notion_database_id="db123",
        google_credentials={}, readai_api_key="", fireworks_api_key="",
        interview_answers={}, entropy_template_path="/tmp",
    )


def test_parse_notion_rows_returns_customer_records():
    rows = _load_rows()
    records = parse_notion_rows(rows)
    assert len(records) == 1
    r = records[0]
    assert r.name == "Blackbaud"
    assert r.product == "Influitive"
    assert r.arr == 63818.76
    assert r.renewal_date == "2026-09-15"
    assert "Active" in r.status_tags
    assert "Non-HVO" in r.status_tags
    assert r.esw_paper is True
    assert r.primary_email == "christine.newman@blackbaud.com"


def test_parse_notion_rows_parses_arr_currency():
    rows = [{"Account Manager": "A", "Customers": "X", "Product": "Tivian",
             "SubProduct": "", "ARR": "$1,234,567.89", "Renewal Date": "01/01/2027",
             "Countdown": "200", "Status": "Active, HVO", "Success Level": "Platinum",
             "Contract Term": "36", "ESW Paper": "Yes", "Primary Contact": "",
             "Email": "", "Additional Contacts": "", "Champion": "", "Detractor": "",
             "Decision Maker": "", "Influencer": "", "Product Sentiment": "",
             "Support Sentiment": "", "Renewals Sentiment": "", "Product Feedback": "",
             "Account Notes": "", "Actual Usage": "", "Usage Limit": "",
             "Eligible for Extension": "", "EOS: Extended": "", "Ext Next Steps": ""}]
    records = parse_notion_rows(rows)
    assert records[0].arr == 1234567.89
    assert "HVO" in records[0].status_tags


def test_build_intelligence_summary_valid_frontmatter():
    rows = _load_rows()
    record = parse_notion_rows(rows)[0]
    vf = build_intelligence_summary(record)
    assert vf.path == "Entropy/Influitive/Blackbaud/_intelligence_summary.md"
    assert "type: intelligence-summary" in vf.content
    assert "arr: 63818.76" in vf.content
    assert 'renewal_date: "2026-09-15"' in vf.content
    assert "Negative" in vf.content
    assert "Christine Newman" in vf.content
    assert "[[Influitive]]" in vf.content


def test_build_customer_domains():
    rows = _load_rows()
    records = parse_notion_rows(rows)
    domains_vf = build_customer_domains(records)
    data = json.loads(domains_vf.content)
    assert "domains" in data
    assert "blackbaud.com" in data["domains"]
    assert data["domains"]["blackbaud.com"]["customer"] == "Blackbaud"


def test_build_hub_nodes_creates_product_node():
    rows = _load_rows()
    records = parse_notion_rows(rows)
    nodes = build_hub_nodes(records)
    paths = [n.path for n in nodes]
    assert any("Influitive" in p for p in paths)


def test_pull_customers_filters_by_account_manager(mocker):
    # pull_customers calls notion SDK — mock the query
    mock_notion = MagicMock()
    mock_notion.databases.query.return_value = {
        "results": [],
        "has_more": False
    }
    mocker.patch("pipeline.notion_pull.Client", return_value=mock_notion)
    cfg = _make_config()
    records = pull_customers(cfg)
    # Verify filter was applied
    call_kwargs = mock_notion.databases.query.call_args[1]
    assert call_kwargs["filter"]["property"] == "Account Manager"
    assert records == []
