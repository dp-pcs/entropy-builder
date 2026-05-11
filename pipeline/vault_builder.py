import io
import json
import posixpath
import zipfile
from datetime import date
from pathlib import Path
from .models import JobConfig, CustomerRecord, VaultFile, GapItem

_SKILLS_TO_COPY = [
    "triage.md", "debrief.md", "playbook.md", "health.md", "ingestion.md",
    "dashboard.md", "alerting.md", "enrichment.md", "commitment-extraction.md",
    "lint.md", "renewal-countdown.md", "churn-autopsy.md", "email-draft.md",
    "segmentation.md", "competitive-intel.md", "pressure-test.md",
]
_ANALYTICS_TO_COPY = ["metrics.md", "queries.md", "schemas.md"]


def _safe_zip_path(path: str) -> str:
    normalized = posixpath.normpath(path.replace("\\", "/")).lstrip("/")
    if normalized.startswith(".."):
        raise ValueError(f"Unsafe VaultFile path rejected: {path!r}")
    return normalized


def build_vault(
    config: JobConfig,
    wiki_files: list[VaultFile],
    customers: list[CustomerRecord],
    customer_files: list[VaultFile],
    hub_nodes: list[VaultFile],
    gap_items: list[GapItem],
) -> bytes:
    """Assemble all pipeline outputs into a ZIP and return bytes."""
    buf = io.BytesIO()
    brain_name = f"{config.user_name}'s Second Brain"
    template = Path(config.entropy_template_path)

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Root files
        zf.writestr("CLAUDE.md", generate_claude_md(config))
        zf.writestr(".env", _generate_env(config))

        # 2nd brain wiki files (rename root prefix to user's brain name)
        for vf in wiki_files:
            dest = f"{brain_name}/{_safe_zip_path(vf.path)}"
            zf.writestr(dest, vf.content)

        # Empty folders for 2nd brain
        for folder in ["raw", "Contradictions", "Applications", "outputs"]:
            zf.writestr(f"{brain_name}/{folder}/.gitkeep", "")

        # Customer files (intelligence summaries, emails, transcripts)
        for vf in customer_files:
            zf.writestr(_safe_zip_path(vf.path), vf.content)

        # Hub nodes
        for vf in hub_nodes:
            zf.writestr(_safe_zip_path(vf.path), vf.content)

        # Hot cache
        zf.writestr("Entropy/_hot_cache.md", generate_hot_cache(config, customers))
        zf.writestr("Entropy/_Portfolio_Dashboard.md", _portfolio_dashboard_stub(config))
        zf.writestr("Entropy/_Action_Tracker.md", "# Action Tracker\n\n_Run ingestion skill to populate._\n")

        # Entropy INDEX
        zf.writestr("Entropy/INDEX.md", _entropy_index(config))

        # Gaps JSON (read by status page for inline prompts)
        zf.writestr("gaps.json", json.dumps(
            [{"category": g.category, "description": g.description,
              "prompt": g.prompt, "upload_accepted": g.upload_accepted}
             for g in gap_items], indent=2
        ))

        # Skills (copied from entropy template)
        skills_dir = template / "Entropy" / "_skills"
        for skill_name in _SKILLS_TO_COPY:
            src = skills_dir / skill_name
            if src.exists():
                zf.writestr(f"Entropy/_skills/{skill_name}", src.read_text())

        # Analytics (copied from entropy template)
        analytics_dir = template / "Entropy" / "_analytics"
        for fname in _ANALYTICS_TO_COPY:
            src = analytics_dir / fname
            if src.exists():
                zf.writestr(f"Entropy/_analytics/{fname}", src.read_text())

        # Company rules (copied verbatim)
        company_rules = template / "Entropy" / "Company-Rules.md"
        if company_rules.exists():
            zf.writestr("Entropy/Company-Rules.md", company_rules.read_text())

    return buf.getvalue()


def generate_claude_md(config: JobConfig) -> str:
    role_desc = {
        "ic": "Individual Contributor — manages their own customer portfolio",
        "manager": "Manager — oversees team portfolio",
        "external": "External user",
    }.get(config.user_role, config.user_role)

    products = ", ".join(config.product_lines) if config.product_lines else "All"
    filter_rule = (
        f"Account Manager == '{config.account_manager_name}'"
        if config.user_role != "manager"
        else f"Account Manager IN [{', '.join(repr(m) for m in config.team_members)}]"
    )

    return f"""# {config.user_name} — Entropy Intelligence System

**User:** {config.user_name}
**Role:** {role_desc}
**Product Lines:** {products}
**Notion Filter:** {filter_rule}
**Notion Database ID:** {config.notion_database_id}
**2nd Brain:** [[{config.user_name}'s Second Brain/TRAVERSAL-INDEX|TRAVERSAL-INDEX]]
**Entropy Entry:** [[Entropy/INDEX|INDEX]]

---

## Session Start Protocol

1. Read `Entropy/_hot_cache.md` — active fires, decisions, portfolio snapshot
2. Determine session type (daily scan / weekly sweep / on-demand query)
3. Load only the required skills from `Entropy/_skills/`

## Skill Routing

| Task | Load |
|------|------|
| Daily scan | `_skills/ingestion.md` |
| Weekly sweep | `_skills/ingestion.md` + `_skills/dashboard.md` + `_skills/alerting.md` |
| Customer triage | `_skills/triage.md` |
| Post-meeting | `_skills/debrief.md` |
| Renewal playbook | `_skills/playbook.md` + `_skills/renewal-countdown.md` |
| Health score | `_skills/health.md` |
| At-risk analysis | `_skills/alerting.md` + `_skills/segmentation.md` |

## Portfolio Scope

Direct portfolio: {products}
Notion DB: `{config.notion_database_id}`
Filter: `{filter_rule}`

Do NOT process customer folders outside the above products.

## 2nd Brain Navigation

1. Start with `{config.user_name}'s Second Brain/TRAVERSAL-INDEX.md`
2. Follow wikilinks in prose — links carry meaning
3. Use MOCs for topic clusters
4. Check Contradictions when advice conflicts
"""


def generate_hot_cache(config: JobConfig, customers: list[CustomerRecord]) -> str:
    today = date.today().isoformat()
    arr_total = sum(c.arr for c in customers)
    hvo_count = sum(1 for c in customers if "HVO" in c.status_tags)
    at_risk = [c for c in customers if "At Risk" in c.status_tags]

    at_risk_lines = "\n".join(
        f"- [[{c.name}]] ({c.product}) — ARR ${c.arr:,.0f}"
        for c in at_risk[:5]
    )

    shown = customers[:50]
    roster_note = (
        f"\n> Showing {len(shown)} of {len(customers)} customers — run daily scan for full roster.\n"
        if len(customers) > 50 else ""
    )

    roster_lines = "\n".join(
        f"| [[{c.name}]] | {c.product} | ${c.arr:,.0f} | {c.renewal_date} | {', '.join(c.status_tags)} |"
        for c in shown
    )

    return f"""# Hot Cache — {config.user_name}

_Last updated: {today}_

---

## Active Fires

_None identified at initial import. Run daily scan to populate._

## Portfolio Snapshot

| Metric | Value |
|--------|-------|
| Total Customers | {len(customers)} |
| Total ARR | ${arr_total:,.0f} |
| HVO Accounts | {hvo_count} |
| At Risk | {len(at_risk)} |

## At Risk Accounts

{at_risk_lines or "_None identified at initial import._"}

## Customer Roster

| Customer | Product | ARR | Renewal | Tags |
|----------|---------|-----|---------|------|
{roster_lines}{roster_note}

## Decisions Made

_Session log starts here._

## Session Log

### {today} — Initial Import

Vault generated via entropy.elelem.expert onboarding wizard.
{len(customers)} customers imported from Notion.
Run daily scan to populate email and transcript history.
"""


def _generate_env(config: JobConfig) -> str:
    google = config.google_credentials or {}
    return f"""# Entropy environment — KEEP PRIVATE, do not commit to git or share
NOTION_TOKEN={config.notion_token}
NOTION_DATABASE_ID={config.notion_database_id}
READAI_API_KEY={config.readai_api_key}
GOOGLE_ACCESS_TOKEN={google.get('access_token', '')}
GOOGLE_REFRESH_TOKEN={google.get('refresh_token', '')}
GOOGLE_CLIENT_ID={google.get('client_id', '')}
GOOGLE_CLIENT_SECRET={google.get('client_secret', '')}
"""


def _portfolio_dashboard_stub(config: JobConfig) -> str:
    return f"""# Portfolio Dashboard — {config.user_name}

_Run weekly sweep (Monday 8:05am) to generate._

Load `_skills/dashboard.md` and execute.
"""


def _entropy_index(config: JobConfig) -> str:
    products = ", ".join(config.product_lines) if config.product_lines else "all products"
    return f"""# Entropy — {config.user_name}'s Customer Intelligence System

**Portfolio:** {products}
**Entry point for all customer intelligence operations.**

## Navigation

- [[_hot_cache|Hot Cache]] — start every session here
- [[_Portfolio_Dashboard|Portfolio Dashboard]] — weekly overview
- [[_Action_Tracker|Action Tracker]] — open commitments
- [[CLAUDE.md|System Config]] — skill routing and portfolio scope

## Skills

Load from `_skills/` directory. See [[CLAUDE.md]] for routing table.

## Analytics

- [[_analytics/metrics|Metrics]] — health score formula, risk bands
- [[_analytics/schemas|Schemas]] — canonical frontmatter for all file types
- [[_analytics/queries|Queries]] — MCP query patterns
"""
