"""End-to-end pipeline test using mocked external APIs and fixture data."""
import io
import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from pipeline.ingest import ingest
from pipeline.notion_pull import parse_notion_rows, build_intelligence_summary, build_customer_domains, build_hub_nodes
from pipeline.vault_builder import build_vault
from pipeline.models import JobConfig, VaultFile, GapItem

FIXTURES = Path(__file__).parent / "fixtures"


def _make_config(tmp_path):
    (tmp_path / "Entropy" / "_skills").mkdir(parents=True)
    (tmp_path / "Entropy" / "_analytics").mkdir(parents=True)
    for skill in ["triage.md", "ingestion.md", "dashboard.md"]:
        (tmp_path / "Entropy" / "_skills" / skill).write_text(f"# {skill}")
    for analytics in ["metrics.md", "queries.md", "schemas.md"]:
        (tmp_path / "Entropy" / "_analytics" / analytics).write_text(f"# {analytics}")
    (tmp_path / "Entropy" / "Company-Rules.md").write_text("# Company Rules")
    return JobConfig(
        user_name="Jane Smith", user_role="ic", account_manager_name="Jane Smith",
        team_members=[], notion_token="tok", notion_database_id="db123",
        google_credentials={}, readai_api_key="ra", fireworks_api_key="fw",
        interview_answers={"role": "AE", "books": ["Never Split the Difference"]},
        entropy_template_path=str(tmp_path), product_lines=["Influitive"],
    )


def test_full_pipeline_produces_valid_vault(tmp_path, mocker):
    # Mock Kimi to return predictable wiki files
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"choices": [{"message": {"content": json.dumps({
        "User-Profile.md": "---\ntype: profile\ndescription: Jane's profile\ntags: []\naliases: []\n---\n# Jane Smith\n\nHigh D, High C. Analytical, systematic.",
        "Books/Never Split the Difference.md": "---\ntype: book\ndescription: Negotiation\ntags: [negotiation]\naliases: []\n---\n# Never Split the Difference\n\nBy Chris Voss.",
        "TRAVERSAL-INDEX.md": "- [[User-Profile]] — Jane's profile\n- [[Books/Never Split the Difference]] — Negotiation",
    })}}]}
    mock_resp.raise_for_status = MagicMock()
    mocker.patch("pipeline.kimi.requests.post", return_value=mock_resp)

    # Ingest a sample file
    md_source = {"type": "file", "content": b"# My Notes\nSome ideas.", "filename": "notes.md"}
    ingested = ingest([md_source])
    assert len(ingested) == 1

    # Generate wiki
    from pipeline.kimi import generate_wiki, analyze_gaps
    cfg = _make_config(tmp_path)
    wiki_files = generate_wiki(cfg, ingested)
    assert any("User-Profile" in f.path for f in wiki_files)

    # Mock gap analysis to return no gaps
    mock_resp2 = MagicMock()
    mock_resp2.json.return_value = {"choices": [{"message": {"content": "[]"}}]}
    mock_resp2.raise_for_status = MagicMock()
    mocker.patch("pipeline.kimi.requests.post", return_value=mock_resp2)
    gaps = analyze_gaps(cfg, wiki_files)
    assert gaps == []

    # Build customer data from fixture
    notion_rows = json.loads((FIXTURES / "sample_notion_rows.json").read_text())
    notion_rows[0]["Account Manager"] = "Jane Smith"
    customers = parse_notion_rows(notion_rows)
    customer_files = [build_intelligence_summary(c) for c in customers]
    domains_vf = build_customer_domains(customers)
    hub_nodes = build_hub_nodes(customers)
    all_customer_files = customer_files + [domains_vf]

    # Build vault ZIP
    zip_bytes = build_vault(cfg, wiki_files, customers, all_customer_files, hub_nodes, gaps)
    assert isinstance(zip_bytes, bytes)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert any("User-Profile" in n for n in names)
        assert any("Never Split the Difference" in n for n in names)
        assert any("_intelligence_summary" in n for n in names)
        assert any("customer_domains" in n for n in names)
        assert any("CLAUDE.md" in n for n in names)
        assert any("triage.md" in n for n in names)
        assert any("_hot_cache" in n for n in names)
        assert any("Company-Rules" in n for n in names)

        # Verify intelligence summary has correct frontmatter
        summary_name = next(n for n in names if "_intelligence_summary" in n)
        summary_content = zf.read(summary_name).decode()
        assert "type: intelligence-summary" in summary_content
        assert "arr: 63818.76" in summary_content

        # Verify CLAUDE.md is personalized
        claude_content = zf.read("CLAUDE.md").decode()
        assert "Jane Smith" in claude_content
