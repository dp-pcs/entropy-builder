# entropy_builder/pipeline/models.py
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobConfig:
    user_name: str
    user_role: str                   # "ic" | "manager" | "external"
    account_manager_name: str        # Notion filter value (IC: their name; manager: chosen team member)
    team_members: list[str]          # manager only — list of AM names to include
    notion_token: str                # Notion OAuth access token
    notion_database_id: str          # shared DB ID
    google_credentials: dict         # {"access_token": str, "refresh_token": str, "client_id": str, "client_secret": str, "token_uri": str}
    readai_access_token: str
    readai_refresh_token: str = ""
    readai_client_id: str = ""
    fireworks_api_key: str
    interview_answers: dict          # raw wizard answers {"role": str, "books": [...], ...}
    entropy_template_path: str       # abs path to Jay's vault for copying templates
    product_lines: list[str] = field(default_factory=list)  # populated after Notion pull


@dataclass
class CustomerRecord:
    name: str
    product: str
    sub_product: str
    arr: float
    renewal_date: str               # ISO date "YYYY-MM-DD"
    status_tags: list[str]          # parsed from comma-separated "Active, HVO, At Risk"
    success_level: str              # "Standard" | "Platinum"
    contract_term: int              # months
    esw_paper: bool
    primary_contact: str
    primary_email: str
    additional_contacts: str
    champion: str
    detractor: str
    decision_maker: str
    influencer: str
    product_sentiment: str          # "Positive" | "Negative" | "Neutral" | ""
    support_sentiment: str
    renewals_sentiment: str
    product_feedback: str
    account_notes: str
    actual_usage: Optional[int] = None
    usage_limit: Optional[int] = None
    eligible_for_extension: str = ""
    eos_extended: str = ""
    ext_next_steps: str = ""


@dataclass
class VaultFile:
    path: str     # relative path within vault root, e.g. "Books/Atomic Habits.md"
    content: str  # complete file content including YAML frontmatter


@dataclass
class GapItem:
    category: str       # "psych_profile" | "frameworks" | "books" | "concepts" | "moc" | "principles" | "people"
    description: str    # human-readable gap, e.g. "No psychological profile found"
    prompt: str         # specific question to show the user
    upload_accepted: bool  # whether a file upload is appropriate for this gap
