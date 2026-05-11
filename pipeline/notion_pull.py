import json
import re
import requests
from datetime import date
from notion_client import Client
from .models import JobConfig, CustomerRecord, VaultFile

_NOTION_API = "https://api.notion.com/v1"


def _query_database(token: str, database_id: str, filter_body: dict, cursor: str | None = None) -> dict:
    """POST /databases/{id}/query directly — notion-client SDK dropped this method."""
    body: dict = {"filter": filter_body, "page_size": 100}
    if cursor:
        body["start_cursor"] = cursor
    resp = requests.post(
        f"{_NOTION_API}/databases/{database_id}/query",
        headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"},
        json=body,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def pull_customers(config: JobConfig) -> list[CustomerRecord]:
    """Query the shared Notion DB filtered by account manager name(s)."""
    names = (config.team_members if config.user_role == "manager"
             else [config.account_manager_name])

    all_rows = []
    for name in names:
        cursor = None
        while True:
            resp = _query_database(
                config.notion_token,
                config.notion_database_id,
                {"property": "Account Manager", "rich_text": {"equals": name}},
                cursor,
            )
            for page in resp.get("results", []):
                all_rows.append(_page_to_row(page))
            cursor = resp.get("next_cursor")
            if not resp.get("has_more") or not cursor:
                break

    return parse_notion_rows(all_rows)


def _page_to_row(page: dict) -> dict:
    """Flatten Notion page properties to a flat dict matching the CSV structure."""
    props = page.get("properties", {})

    def text(key):
        p = props.get(key, {})
        if p.get("type") == "rich_text":
            return "".join(r["plain_text"] for r in p.get("rich_text", []))
        if p.get("type") == "title":
            return "".join(r["plain_text"] for r in p.get("title", []))
        if p.get("type") == "select":
            sel = p.get("select")
            return sel["name"] if sel else ""
        if p.get("type") == "people":
            return ", ".join(u.get("name", "") for u in p.get("people", []))
        if p.get("type") == "email":
            return p.get("email") or ""
        if p.get("type") == "url":
            return p.get("url") or ""
        return ""

    def number(key):
        p = props.get(key, {})
        if p.get("type") == "number":
            return str(p.get("number") or "")
        return text(key)

    def checkbox(key):
        p = props.get(key, {})
        if p.get("type") == "checkbox":
            return "Yes" if p.get("checkbox") else "No"
        return text(key)

    def date_prop(key):
        p = props.get(key, {})
        if p.get("type") == "date":
            d = p.get("date")
            return d["start"] if d else ""
        return text(key)

    return {
        "Account Manager": text("Account Manager"),
        "Customers": text("Customers"),
        "Product": text("Product"),
        "SubProduct": text("SubProduct"),
        "ARR": number("ARR"),
        "Renewal Date": date_prop("Renewal Date"),
        "Countdown": number("Countdown"),
        "Status": text("Status"),
        "Success Level": text("Success Level"),
        "Contract Term": number("Contract Term"),
        "ESW Paper": checkbox("ESW Paper"),
        "Primary Contact": text("Primary Contact"),
        "Email": text("Email"),
        "Additional Contacts": text("Additional Contacts"),
        "Champion": text("Champion"),
        "Detractor": text("Detractor"),
        "Decision Maker": text("Decision Maker"),
        "Influencer": text("Influencer"),
        "Product Sentiment": text("Product Sentiment"),
        "Support Sentiment": text("Support Sentiment"),
        "Renewals Sentiment": text("Renewals Sentiment"),
        "Product Feedback": text("Product Feedback"),
        "Account Notes": text("Account Notes"),
        "Actual Usage": number("Actual Usage"),
        "Usage Limit": number("Usage Limit"),
        "Eligible for Extension": text("Eligible for Extension"),
        "EOS: Extended": text("EOS: Extended"),
        "Ext Next Steps": text("Ext Next Steps"),
    }


def parse_notion_rows(rows: list[dict]) -> list[CustomerRecord]:
    """Parse flat row dicts (from CSV export or _page_to_row) into CustomerRecord objects."""
    records = []
    for row in rows:
        arr_str = re.sub(r"[,$]", "", row.get("ARR", "0") or "0")
        try:
            arr = float(arr_str)
        except ValueError:
            arr = 0.0

        renewal_raw = row.get("Renewal Date", "")
        renewal_date = _parse_date(renewal_raw)

        status_raw = row.get("Status", "")
        status_tags = [s.strip() for s in status_raw.split(",") if s.strip()]

        contract_raw = row.get("Contract Term", "0") or "0"
        try:
            contract_term = int(float(contract_raw))
        except ValueError:
            contract_term = 12

        usage_actual = _optional_int(row.get("Actual Usage"))
        usage_limit = _optional_int(row.get("Usage Limit"))

        records.append(CustomerRecord(
            name=row.get("Customers", "").strip().replace("/", "-"),
            product=row.get("Product", "").strip(),
            sub_product=row.get("SubProduct", "").strip(),
            arr=arr,
            renewal_date=renewal_date,
            status_tags=status_tags,
            success_level=row.get("Success Level", "Standard").strip(),
            contract_term=contract_term,
            esw_paper=(row.get("ESW Paper", "No").strip().lower() == "yes"),
            primary_contact=row.get("Primary Contact", "").strip(),
            primary_email=row.get("Email", "").strip(),
            additional_contacts=row.get("Additional Contacts", "").strip(),
            champion=row.get("Champion", "").strip(),
            detractor=row.get("Detractor", "").strip(),
            decision_maker=row.get("Decision Maker", "").strip(),
            influencer=row.get("Influencer", "").strip(),
            product_sentiment=row.get("Product Sentiment", "").strip() or "Unknown",
            support_sentiment=row.get("Support Sentiment", "").strip() or "Unknown",
            renewals_sentiment=row.get("Renewals Sentiment", "").strip() or "Unknown",
            product_feedback=row.get("Product Feedback", "").strip(),
            account_notes=row.get("Account Notes", "").strip(),
            actual_usage=usage_actual,
            usage_limit=usage_limit,
            eligible_for_extension=row.get("Eligible for Extension", "").strip(),
            eos_extended=row.get("EOS: Extended", "").strip(),
            ext_next_steps=row.get("Ext Next Steps", "").strip(),
        ))
    return [r for r in records if r.name]


def build_intelligence_summary(record: CustomerRecord) -> VaultFile:
    """Generate _intelligence_summary.md for one customer from Notion data."""
    today = date.today().isoformat()
    status_str = ", ".join(record.status_tags)

    # Graph connections — wikilinks to hub nodes
    graph_lines = [f"**Product:** [[{record.product}]]"]
    if record.sub_product:
        graph_lines.append(f"**Sub-Product:** [[{record.sub_product}]]")

    hvo_status = "[[HVO]]" if "HVO" in record.status_tags else "[[Non-HVO]]"
    graph_lines.append(f"**Status:** {hvo_status}")
    if "At Risk" in record.status_tags:
        graph_lines.append("**Risk:** [[At Risk]]")

    graph_lines.append(f"**Success Level:** [[{record.success_level}]]")
    esw = "[[ESW Paper]]" if record.esw_paper else "[[Non-ESW Paper]]"
    graph_lines.append(f"**Contract:** {esw}")

    for sentiment_type, val in [
        ("Product Sentiment", record.product_sentiment),
        ("Support Sentiment", record.support_sentiment),
        ("Renewal Sentiment", record.renewals_sentiment),
    ]:
        if val and val not in ("Unknown", ""):
            graph_lines.append(f"**{sentiment_type}:** [[{sentiment_type} - {val}]]")

    # Stakeholders table
    stakeholder_rows = []
    if record.primary_contact:
        email = record.primary_email or ""
        stakeholder_rows.append(f"| {record.primary_contact} | {email} | Primary Contact |")
    for role, name in [("Champion", record.champion), ("Detractor", record.detractor),
                        ("Decision Maker", record.decision_maker), ("Influencer", record.influencer)]:
        if name:
            stakeholder_rows.append(f"| {name} | | {role} |")

    stakeholder_table = (
        "| Name | Email | Role |\n|------|-------|------|\n" + "\n".join(stakeholder_rows)
        if stakeholder_rows else "_No contacts recorded._"
    )

    content = f"""---
type: intelligence-summary
customer: "{record.name}"
product: "{record.product}"
arr: {record.arr}
renewal_date: "{record.renewal_date}"
status: "{status_str}"
health_score: 50
data_confidence: medium
primary_contact: "{record.primary_contact}"
segment: drifting
product_sentiment: "{record.product_sentiment}"
support_sentiment: "{record.support_sentiment}"
renewals_sentiment: "{record.renewals_sentiment}"
last_updated: {today}
last_verified: {today}
notion_synced: "{today}"
sub_product: "{record.sub_product}"
contract_term: {record.contract_term}
eos_customer_success: "{record.eos_extended}"
primary_contact_email: "{record.primary_email}"
---

# {record.name}

## Customer Profile

{record.account_notes or "_No account notes available._"}

## Key Stakeholders

{stakeholder_table}

## Product Feedback

{record.product_feedback or "_No product feedback recorded._"}

## Health History

| Date | Score | Band | Trigger |
|------|-------|------|---------|
| {today} | 50 | At Risk | Initial import |

## Graph Connections

{chr(10).join(graph_lines)}
"""
    path = f"Entropy/{record.product}/{record.name}/_intelligence_summary.md"
    return VaultFile(path=path, content=content)


def build_customer_domains(records: list[CustomerRecord]) -> VaultFile:
    """Build customer_domains.json from Notion email field.

    Returns a VaultFile whose content is a flat JSON mapping of domain -> {customer, product}.
    """
    domains: dict[str, dict] = {}
    reseller_domains = {"shi.com", "carahsoft.com", "bechtle.com", "softwareone.com",
                        "penril.net", "tekservinc.com"}
    for record in records:
        if not record.primary_email or "@" not in record.primary_email:
            continue
        domain = record.primary_email.split("@")[1].lower()
        if domain in reseller_domains:
            continue
        domains[domain] = {"customer": record.name, "product": record.product}

    data = {
        "version": "1.0",
        "generated": date.today().isoformat(),
        "domains": domains,
    }
    return VaultFile(
        path="Entropy/_data/customer_domains.json",
        content=json.dumps(data, indent=2),
    )


def build_hub_nodes(records: list[CustomerRecord]) -> list[VaultFile]:
    """Generate hub node files from portfolio data."""
    from collections import defaultdict
    product_customers: dict[str, list[str]] = defaultdict(list)
    status_customers: dict[str, list[str]] = defaultdict(list)

    for r in records:
        product_customers[r.product].append(r.name)
        for tag in r.status_tags:
            if tag in ("HVO", "Non-HVO", "At Risk", "Floor Price"):
                status_customers[tag].append(r.name)

    nodes = []
    for product, customers in product_customers.items():
        links = "\n".join(f"- [[{c}/_intelligence_summary|{c}]]" for c in sorted(customers))
        content = f"""---
type: node
node_type: product
title: {product}
customer_count: {len(customers)}
---

# {product}

## Connected Customers

{links}
"""
        nodes.append(VaultFile(path=f"Entropy/_nodes/{product}.md", content=content))

    for status, customers in status_customers.items():
        links = "\n".join(f"- [[{c}/_intelligence_summary|{c}]]" for c in sorted(customers))
        safe = status.replace(" ", "-")
        content = f"""---
type: node
node_type: status
title: {status}
customer_count: {len(customers)}
---

# {status}

## Connected Customers

{links}
"""
        nodes.append(VaultFile(path=f"Entropy/_nodes/{safe}.md", content=content))

    return nodes


def _parse_date(raw: str) -> str:
    """Convert MM/DD/YYYY or ISO to ISO date string."""
    if not raw:
        return ""
    raw = raw.strip()
    if re.match(r"\d{4}-\d{2}-\d{2}", raw):
        return raw[:10]
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw)
    if m:
        month, day, year = m.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return raw


def _optional_int(val) -> int | None:
    if val is None or val == "":
        return None
    try:
        return int(float(str(val)))
    except (ValueError, TypeError):
        return None
