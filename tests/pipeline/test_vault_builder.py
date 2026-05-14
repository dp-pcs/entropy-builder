import io
import zipfile
import json
from pathlib import Path
from unittest.mock import MagicMock
from pipeline.vault_builder import build_vault, generate_claude_md, generate_hot_cache
from pipeline.models import JobConfig, CustomerRecord, VaultFile, GapItem


def _make_config(tmp_path):
    # Create minimal template structure. build_vault reads from "Portfolio Brain/"
    # under entropy_template_path (renamed from "Entropy/" in commit de8b773).
    template_root = tmp_path / "Portfolio Brain"
    (template_root / "_skills").mkdir(parents=True)
    (template_root / "_analytics").mkdir(parents=True)
    (template_root / "_skills" / "triage.md").write_text("# Triage Skill")
    (template_root / "_analytics" / "metrics.md").write_text("# Metrics")
    (template_root / "Company-Rules.md").write_text("# Company Rules")

    return JobConfig(
        user_name="Jane Smith", user_role="ic", account_manager_name="Jane Smith",
        team_members=[], notion_token="", notion_database_id="",
        google_credentials={}, readai_access_token="", fireworks_api_key="",
        interview_answers={"role": "AE"}, entropy_template_path=str(tmp_path),
        product_lines=["Influitive"],
    )


def _make_customer():
    return CustomerRecord(
        name="Blackbaud", product="Influitive", sub_product="AdvocateHub",
        arr=63818.76, renewal_date="2026-09-15", status_tags=["Active", "Non-HVO"],
        success_level="Standard", contract_term=12, esw_paper=True,
        primary_contact="Christine Newman", primary_email="christine.newman@blackbaud.com",
        additional_contacts="", champion="", detractor="", decision_maker="",
        influencer="", product_sentiment="Negative", support_sentiment="Negative",
        renewals_sentiment="Negative", product_feedback="", account_notes="",
    )


def test_generate_claude_md_contains_user_name():
    cfg_mock = MagicMock()
    cfg_mock.user_name = "Jane Smith"
    cfg_mock.user_role = "ic"
    cfg_mock.product_lines = ["Influitive"]
    cfg_mock.account_manager_name = "Jane Smith"
    cfg_mock.notion_database_id = "db123"
    md = generate_claude_md(cfg_mock)
    assert "Jane Smith" in md
    assert "Influitive" in md
    assert "ic" in md.lower() or "Individual" in md


def test_generate_hot_cache_contains_portfolio():
    cfg_mock = MagicMock()
    cfg_mock.user_name = "Jane Smith"
    cfg_mock.product_lines = ["Influitive"]
    customers = [_make_customer()]
    md = generate_hot_cache(cfg_mock, customers)
    assert "Blackbaud" in md
    assert "Influitive" in md


def test_build_vault_returns_zip_bytes(tmp_path):
    cfg = _make_config(tmp_path)
    wiki_files = [VaultFile("Books/Atomic Habits.md", "---\ntype: book\n---\n# AH")]
    customers = [_make_customer()]
    customer_files = [VaultFile(
        "Entropy/Influitive/Blackbaud/_intelligence_summary.md", "---\ntype: intelligence-summary\n---"
    )]
    gap_items = [GapItem("psych_profile", "No profile", "Do you have DiSC?", True)]
    hub_nodes = []

    zip_bytes = build_vault(cfg, wiki_files, customers, customer_files, hub_nodes, gap_items)

    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 100

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert any("CLAUDE.md" in n for n in names)
        assert any("Company-Rules.md" in n for n in names)
        assert any("triage.md" in n for n in names)
        assert any("Atomic Habits" in n for n in names)
        assert any("_intelligence_summary" in n for n in names)
        assert any("gaps.json" in n for n in names)


def test_build_vault_second_brain_renamed(tmp_path):
    cfg = _make_config(tmp_path)
    wiki_files = [VaultFile("User-Profile.md", "# Profile")]
    zip_bytes = build_vault(cfg, wiki_files, [], [], [], [])
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert any("Jane Smith's Second Brain" in n for n in names)


def test_rewrite_placeholder_wikilinks_strips_known_tokens():
    """Skill templates use [[CustomerName]], [[YYYY-MM-DD]] etc. as runtime
    placeholders. Rewrite them to angle-bracket syntax so Obsidian doesn't
    render them as dangling wikilinks in the graph."""
    from pipeline.vault_builder import _rewrite_placeholder_wikilinks
    text = (
        "Run debrief for [[CustomerName]] on [[YYYY-MM-DD]] and save to "
        "[[filename]]. See also [[Books/Atomic-Habits]] for context."
    )
    out = _rewrite_placeholder_wikilinks(text)
    assert "<CustomerName>" in out
    assert "<YYYY-MM-DD>" in out
    assert "<filename>" in out
    # Real wikilinks must survive
    assert "[[Books/Atomic-Habits]]" in out


def test_rewrite_placeholder_wikilinks_catches_allcaps_placeholders():
    """ALL-CAPS short tokens like [[TARGET]] are treated as placeholders by
    convention even if not in the explicit token list."""
    from pipeline.vault_builder import _rewrite_placeholder_wikilinks
    out = _rewrite_placeholder_wikilinks("Apply to [[TARGET]] this week.")
    assert "<TARGET>" in out
    assert "[[TARGET]]" not in out


def test_patch_skill_content_rewrites_placeholders_end_to_end(tmp_path):
    """End-to-end: a copied skill file with placeholder wikilinks gets cleaned
    up by _patch_skill_content."""
    from pipeline.vault_builder import _patch_skill_content
    cfg = _make_config(tmp_path)
    raw = (
        "# Debrief skill\n\n"
        "Open the customer file [[CustomerName]] and the meeting note "
        "[[YYYY-MM-DD_Meeting_Title]]. Save to [[filename]]."
    )
    patched = _patch_skill_content(raw, cfg)
    assert "[[CustomerName]]" not in patched
    assert "<CustomerName>" in patched
    assert "<YYYY-MM-DD_Meeting_Title>" in patched
    assert "<filename>" in patched
