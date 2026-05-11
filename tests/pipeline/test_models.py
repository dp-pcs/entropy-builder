# entropy_builder/tests/pipeline/test_models.py
from pipeline.models import JobConfig, CustomerRecord, VaultFile, GapItem


def test_job_config_fields():
    cfg = JobConfig(
        user_name="Test User",
        user_role="ic",
        account_manager_name="Test User",
        team_members=[],
        notion_token="tok",
        notion_database_id="db123",
        google_credentials={"access_token": "goog"},
        readai_api_key="readai",
        fireworks_api_key="fw",
        interview_answers={"role": "AE"},
        entropy_template_path="/tmp/entropy",
    )
    assert cfg.user_role == "ic"
    assert cfg.product_lines == []


def test_customer_record_status_tags():
    cr = CustomerRecord(
        name="Acme", product="Influitive", sub_product="AdvocateHub",
        arr=50000.0, renewal_date="2026-09-15", status_tags=["Active", "HVO"],
        success_level="Platinum", contract_term=12, esw_paper=True,
        primary_contact="Jane Doe", primary_email="jane@acme.com",
        additional_contacts="", champion="", detractor="", decision_maker="",
        influencer="", product_sentiment="Positive", support_sentiment="Neutral",
        renewals_sentiment="Positive", product_feedback="", account_notes="",
    )
    assert "HVO" in cr.status_tags


def test_vault_file():
    vf = VaultFile(path="Books/Atomic Habits.md", content="---\ntype: book\n---\n# Atomic Habits")
    assert vf.path.startswith("Books/")
    assert "type: book" in vf.content


def test_gap_item():
    gap = GapItem(
        category="psych_profile",
        description="No psychological profile found",
        prompt="Do you have a DiSC or StrengthsFinder result?",
        upload_accepted=True,
    )
    assert gap.upload_accepted is True
