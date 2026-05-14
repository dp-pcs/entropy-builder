import io
import json
import posixpath
import re
import zipfile
from datetime import date
from pathlib import Path
from .links import path_set_for_links, strip_dangling_wikilinks
from .models import JobConfig, CustomerRecord, VaultFile, GapItem

_SKILLS_TO_COPY = [
    "triage.md", "debrief.md", "playbook.md", "health.md", "ingestion.md",
    "dashboard.md", "alerting.md", "enrichment.md", "commitment-extraction.md",
    "lint.md", "renewal-countdown.md", "churn-autopsy.md", "email-draft.md",
    "segmentation.md", "competitive-intel.md", "pressure-test.md",
    "meeting-prep.md", "scenario-modeling.md",
]
_ANALYTICS_TO_COPY = ["metrics.md", "queries.md", "schemas.md"]


_TEMPLATE_PRODUCTS = ["Tivian", "Influitive", "Lyris", "QuickSilver"]
_TEMPLATE_NAME = "Jay"
_TEMPLATE_NOTION_DB = "28485e927d3181c89d6cdd6fd57ea07d"
_TEMPLATE_SECOND_BRAIN = "Khalife Second Brain"

# Wikilink targets used in skill templates that are RUNTIME PLACEHOLDERS, not
# real files. They pollute Obsidian's graph as dead links if left as [[…]].
# We rewrite them to angle-bracket syntax so the skill prose still reads as
# "replace <CustomerName> with the actual customer" but Obsidian no longer
# treats them as real wikilinks. Coverage extended from Claude Desktop's
# 2026-05-14 dangling-link audit (C1 category).
_PLACEHOLDER_WIKILINK_TOKENS = {
    # Customer placeholders
    "CustomerName", "Customer Name", "CustomerNames", "Customer",
    "Customer A", "Customer B", "Customer C", "Customer X",
    # Targets / filenames / generic
    "Target", "Targets", "filename", "Filename", "file_name",
    "new playbook", "the playbook",
    # Status / tag values that show up as [[Standard]] in skill examples
    "Standard", "Platinum", "Active", "At Risk", "Non-HVO", "HVO",
    # Date slugs
    "YYYY-MM-DD", "YYYY-MM-DD_Meeting_Title", "YYYY-MM-DD_Renewal_Playbook",
    "ISO-Date",
    # Graph-schema placeholders
    "Related Node 1", "Related Node 2", "Related Node N",
    "Related Note", "Related Notes",
    "Framework Name", "Topic Name", "Concept Name", "Person Name",
    "Topic", "TopicName",
    "ProductLine", "Product",
    "Source", "SourceName",
    "Quote",
}
# Regex patterns that catch placeholder families with variable suffixes
_PLACEHOLDER_PATTERNS = [
    re.compile(r"^CustomerName\d*$"),                  # CustomerName, CustomerName1, CustomerName2
    re.compile(r"^Customer\s+[A-Z][a-z]*$"),           # Customer A, Customer Bob
    re.compile(r"^YYYY-MM-DD"),                        # any YYYY-MM-DD_* slug
    re.compile(r"^[A-Z][a-z]+\s+Name$"),               # "Framework Name", "Topic Name"
]
_PLACEHOLDER_WIKILINK_RE = re.compile(r"\[\[([^\[\]\|\n]+?)(\|[^\[\]\n]+)?\]\]")


def _rewrite_placeholder_wikilinks(content: str) -> str:
    """Rewrite [[Placeholder]] tokens (CustomerName, YYYY-MM-DD_*, filename,
    Framework Name, etc.) to <Placeholder> so they don't appear as dangling
    wikilinks in Obsidian.

    Real wikilinks like [[Books/Atomic-Habits]] are left alone — only tokens
    matching the canonical placeholder vocabulary or known placeholder
    patterns are rewritten."""
    def _repair(match: re.Match) -> str:
        target = match.group(1).strip()
        if target in _PLACEHOLDER_WIKILINK_TOKENS:
            return f"<{target}>"
        for pat in _PLACEHOLDER_PATTERNS:
            if pat.match(target):
                return f"<{target}>"
        # ALL-CAPS short tokens — placeholder by convention ([[TARGET]] etc.)
        bare = target.split("/", 1)[-1]
        if bare and bare == bare.upper() and "_" not in bare and len(bare) <= 24:
            return f"<{bare}>"
        # Ellipsis-containing or path-ellipsis placeholders ([[Entropy/...]], [[...]])
        if "..." in target:
            return f"<{target}>"
        return match.group(0)
    return _PLACEHOLDER_WIKILINK_RE.sub(_repair, content)


def _patch_skill_content(content: str, config: JobConfig) -> str:
    """Substitute user-specific values into template skill files at vault build time."""
    first_name = config.user_name.split()[0] if config.user_name else "you"
    products = config.product_lines or []
    n = len(products)
    n_str = str(n) if products else "N"

    # --- Product list substitutions (order matters: longest/most specific first) ---
    old_backtick_slash = ", ".join(f"`{p}/`" for p in _TEMPLATE_PRODUCTS)
    new_backtick_slash = ", ".join(f"`{p}/`" for p in products) if products else "`[products]/`"
    content = content.replace(old_backtick_slash, new_backtick_slash)

    old_plain_slash = ", ".join(f"{p}/" for p in _TEMPLATE_PRODUCTS)
    new_plain_slash = ", ".join(f"{p}/" for p in products) if products else "[products]/"
    content = content.replace(old_plain_slash, new_plain_slash)

    old_pipe = " | ".join(_TEMPLATE_PRODUCTS)
    new_pipe = " | ".join(products) if products else "[product]"
    content = content.replace(old_pipe, new_pipe)

    old_plain = ", ".join(_TEMPLATE_PRODUCTS)
    new_plain = ", ".join(products) if products else "[products]"
    content = content.replace(old_plain, new_plain)

    # Remove hardcoded team-product exclusion lists (both backtick and plain variants)
    content = re.sub(
        r" \((?:`[^`]+`(?:, `[^`]+`)+|[A-Z][^)]+)\)"
        r"(?= belong to the wider team| — )",
        "",
        content,
    )

    # --- Count substitutions (before name swap so "Jay's 4" patterns still match) ---
    count_subs = [
        (f"exactly {len(_TEMPLATE_PRODUCTS)} products",
         f"exactly {n_str} product{'s' if n != 1 else ''}"),
        (f"{_TEMPLATE_NAME}'s {len(_TEMPLATE_PRODUCTS)} direct products",
         f"{first_name}'s {n_str} direct products"),
        (f"{_TEMPLATE_NAME}'s {len(_TEMPLATE_PRODUCTS)} products",
         f"{first_name}'s {n_str} products"),
        (f"across the {len(_TEMPLATE_PRODUCTS)} products",
         f"across the {n_str} products"),
        (f"the {len(_TEMPLATE_PRODUCTS)} portfolio products",
         f"the {n_str} portfolio products"),
        (f"Scope is {_TEMPLATE_NAME}'s {len(_TEMPLATE_PRODUCTS)} products only",
         f"Scope is {first_name}'s {n_str} products only"),
        (f"Which of {_TEMPLATE_NAME}'s {len(_TEMPLATE_PRODUCTS)} products",
         f"Which of {first_name}'s {n_str} products"),
    ]
    for old, new in count_subs:
        content = content.replace(old, new)

    # --- Name substitution (whole word, after product-count patterns) ---
    content = re.sub(r'\bJay\b', first_name, content)
    content = content.replace(_TEMPLATE_SECOND_BRAIN, f"{config.user_name}'s Second Brain")
    content = content.replace(f"{first_name}-Profile", f"{first_name}-Profile")  # already correct after Jay→first_name

    # --- Notion DB ID ---
    if config.notion_database_id:
        content = content.replace(_TEMPLATE_NOTION_DB, config.notion_database_id)

    # --- Folder name ---
    content = content.replace("Entropy/", "Portfolio Brain/")

    # --- Wikilink placeholder cleanup ---
    # Skill templates use [[CustomerName]], [[YYYY-MM-DD]], etc. as runtime
    # placeholders. Rewrite to <Placeholder> so Obsidian doesn't render them
    # as dangling wikilinks in the graph.
    content = _rewrite_placeholder_wikilinks(content)

    return content


def _generate_changelog(version_data: dict) -> str:
    current = version_data.get("version", "unknown")
    lines = [
        f"# Portfolio Brain — Changelog",
        f"",
        f"Current template version: **{current}**",
        f"",
        f"To check for updates: `GET https://entropy.elelem.expert/api/template/version`",
        f"",
        f"---",
        f"",
    ]
    for entry in version_data.get("history", []):
        lines.append(f"## v{entry['version']} — {entry.get('date', '')}")
        lines.append(f"")
        lines.append(entry.get("summary", ""))
        lines.append(f"")
        for change in entry.get("changes", []):
            lines.append(f"- **{change['type']}**: {change['description']}")
            if change.get("agent_instructions"):
                lines.append(f"  - _Agent action: {change['agent_instructions']}_")
        lines.append(f"")
    return "\n".join(lines)


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

    # Build the set of valid wikilink targets — every wiki file path, with and
    # without the Second-Brain root prefix Obsidian sees. Used to scrub
    # dangling references from copied skill content (C3/C6 in the audit).
    wiki_targets: set[str] = set()
    for vf in wiki_files:
        for variant in (vf.path, f"{brain_name}/{vf.path}"):
            wiki_targets.update(path_set_for_links([variant]))

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Root files
        zf.writestr("CLAUDE.md", generate_claude_md(config))
        zf.writestr(".env", _generate_env(config))
        zf.writestr("README.md", _generate_readme(config))

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
        zf.writestr("Portfolio Brain/_hot_cache.md", generate_hot_cache(config, customers))
        zf.writestr("Portfolio Brain/_Portfolio_Dashboard.md", _portfolio_dashboard_stub(config))
        zf.writestr("Portfolio Brain/_Action_Tracker.md", "# Action Tracker\n\n_Run ingestion skill to populate._\n")

        # Portfolio Brain INDEX
        zf.writestr("Portfolio Brain/INDEX.md", _portfolio_brain_index(config))

        # Template version + changelog (for future update checker)
        version_src = template / "TEMPLATE_VERSION.json"
        if version_src.exists():
            version_data = json.loads(version_src.read_text())
            zf.writestr("vault_version.json", json.dumps({
                "template_version": version_data.get("version"),
                "built_at": date.today().isoformat(),
                "update_check_url": "https://entropy.elelem.expert/api/template/version",
            }, indent=2))
            zf.writestr("Portfolio Brain/CHANGELOG.md", _generate_changelog(version_data))

        # Gaps JSON (read by status page for inline prompts)
        zf.writestr("gaps.json", json.dumps(
            [{"category": g.category, "description": g.description,
              "prompt": g.prompt, "upload_accepted": g.upload_accepted}
             for g in gap_items], indent=2
        ))

        # Skills (copied from entropy template, with placeholder rewriting and
        # a dangling-link sweep against the wiki target set so skill content
        # never links to a wiki file the generator didn't produce).
        skills_dir = template / "Portfolio Brain" / "_skills"
        for skill_name in _SKILLS_TO_COPY:
            src = skills_dir / skill_name
            if src.exists():
                patched = _patch_skill_content(src.read_text(), config)
                cleaned, _ = strip_dangling_wikilinks(patched, wiki_targets)
                zf.writestr(f"Portfolio Brain/_skills/{skill_name}", cleaned)

        # Analytics (copied from entropy template)
        analytics_dir = template / "Portfolio Brain" / "_analytics"
        for fname in _ANALYTICS_TO_COPY:
            src = analytics_dir / fname
            if src.exists():
                zf.writestr(f"Portfolio Brain/_analytics/{fname}", src.read_text())

        # Company rules (copied verbatim)
        company_rules = template / "Portfolio Brain" / "Company-Rules.md"
        if company_rules.exists():
            zf.writestr("Portfolio Brain/Company-Rules.md", company_rules.read_text())

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

    return f"""# {config.user_name} — Portfolio Brain Intelligence System

**User:** {config.user_name}
**Role:** {role_desc}
**Product Lines:** {products}
**Notion Filter:** {filter_rule}
**Notion Database ID:** {config.notion_database_id}
**2nd Brain:** [[{config.user_name}'s Second Brain/TRAVERSAL-INDEX|TRAVERSAL-INDEX]]
**Portfolio Brain:** [[Portfolio Brain/INDEX|INDEX]]

---

## Session Start Protocol

1. Read `Portfolio Brain/_hot_cache.md` — active fires, decisions, portfolio snapshot
2. Determine session type (daily scan / weekly sweep / on-demand query)
3. Load only the required skills from `Portfolio Brain/_skills/`

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


def _generate_readme(config: JobConfig) -> str:
    today = date.today().isoformat()
    return f"""# {config.user_name} — Portfolio Brain Intelligence System

Built: {today}

## What's in this vault

- **`Portfolio Brain/`** — your customer intelligence system. Portfolio data, customer folders, skills, analytics.
- **`{config.user_name}'s Second Brain/`** — your personal knowledge base. Books, frameworks, mental models, career history.
- **`CLAUDE.md`** — the operating instructions Claude reads automatically when you open this folder as a project.
- **`.env`** — your credentials for live data sync. Keep this private.

## Setup (one-time)

**Step 1 — Open in Obsidian**
Unzip this folder, then open it as an Obsidian vault: *Open folder as vault* → select the unzipped folder.

**Step 2 — Open as a Claude Code project**
In Claude Code, open the same folder as your project root. Claude will automatically read `CLAUDE.md` and know your full context.

Or in Claude Desktop: Settings → Projects → add this folder.

**Step 3 — Start**
Say one of these to get going:

| What you want | Say |
|---|---|
| Morning briefing | `daily scan` |
| Review your portfolio | `weekly sweep` |
| Process a customer meeting | `debrief [Customer Name]` |
| Triage a troubled account | `triage [Customer Name]` |
| Build a renewal playbook | `renewal playbook for [Customer Name]` |

## How the skills work

The `Portfolio Brain/_skills/` folder contains workflow specs that Claude loads on demand — no installation needed. When you say `debrief Acme Corp`, Claude reads `_skills/debrief.md` and runs the full 6-step process. Everything stays inside this vault.

## Keeping data fresh

Your vault was built with a snapshot of your Notion portfolio and recent emails. To refresh, rebuild your vault at entropy.elelem.expert — it takes about 15 minutes and replaces the customer data with the latest from Notion, Gmail, and Read.ai.
"""


def _generate_env(config: JobConfig) -> str:
    google = config.google_credentials or {}
    return f"""# Portfolio Brain environment — KEEP PRIVATE, do not commit to git or share
NOTION_TOKEN={config.notion_token}
NOTION_DATABASE_ID={config.notion_database_id}
READAI_API_KEY={config.readai_access_token}
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


def _portfolio_brain_index(config: JobConfig) -> str:
    products = ", ".join(config.product_lines) if config.product_lines else "all products"
    return f"""# Portfolio Brain — {config.user_name}'s Customer Intelligence System

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
