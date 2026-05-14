# Portfolio Brain File Schemas

Canonical YAML frontmatter schemas for every file type in Portfolio Brain. When creating or validating files, reference these schemas to ensure consistency across all 300+ customers.

## Intelligence Summary Schema

The most important schema — every customer has exactly one `_intelligence_summary.md`. These 16 fields are the **canonical set**. Any skill that creates or updates an intelligence summary must use these exact field names.

### Required Fields (must be present in every summary)

```yaml
---
type: intelligence-summary           # Always this exact value
customer: "Exact Customer Name"      # Must match Notion and folder name
product: Tivian                      # Tivian | Influitive | Lyris | QuickSilver
arr: 143554.68                       # Numeric, USD, no currency symbol
renewal_date: "2027-05-01"           # ISO date, quoted
status: "Active, HVO"               # Comma-separated: Active/Cancelled, HVO/Non-HVO, Floor Price, At Risk
health_score: 72                     # Integer 0-100
data_confidence: high                # high | medium | low
primary_contact: "Contact Name"     # Full name of primary contact
segment: active                      # active | drifting | price-shopper | managed-decline | active-crisis | expansion-ready
product_sentiment: Positive          # Positive | Negative | Neutral | Unknown
support_sentiment: Positive          # Positive | Negative | Neutral | Unknown
renewals_sentiment: Negative         # Positive | Negative | Neutral | Unknown
last_updated: 2026-05-07             # ISO date, updated every time the file changes
last_verified: 2026-05-07            # ISO date, updated when a human or deep analysis confirms accuracy
notion_synced: "2026-05-04"          # ISO date, last Notion sync
---
```

### Optional Fields (include when data is available)

```yaml
sub_product: DXI                     # Product variant (DXI, CXI, AdvocateHub, ListManager, etc.)
industry: "Financial Services"       # From web search or Notion
employee_count: 2500                 # Nearest 100 (<5K), nearest 1000 (>5K)
hq_location: "London, UK"           # City, Country
contract_term: 36                    # Months (12, 36, or 60)
eos_customer_success: "Yes"          # Whether CS program is active
primary_contact_email: "a@b.com"    # Primary contact's email
domain: "company.com"               # Customer's primary email domain
```

### Deprecated Fields (do not use in new files)

These appear in legacy summaries and should be migrated when the file is next updated:

| Legacy Field | Replace With |
|-------------|-------------|
| `customer_name` | `customer` |
| `customer_id` | Remove (not needed) |
| `arr_usd` | `arr` (always USD) |
| `date_generated` | `last_updated` |
| `date` | `last_updated` |
| `contact` | `primary_contact` |
| `email` | `primary_contact_email` |
| `success_level` | `eos_customer_success` |
| `rank` | Remove (computed, not stored) |
| `engagement_level` | Derived from `health_score` |
| `churn_risk` | Derived from `health_score` + `segment` |
| `expansion_propensity` | Derived from `segment` |
| `champion_strength` | Derived from contact analysis |
| `themes` | Remove (use body sections instead) |
| `related` | Remove (use Graph Connections section) |
| `source` | Remove (tracked in body) |
| `generated_by` | Remove |
| `account_notes` | Move to body content |
| `product_feedback` | Move to body content |

### Type Field Standardization

The `type` field must be exactly `intelligence-summary` (hyphenated). Legacy values to migrate:

- `intelligence_summary` → `intelligence-summary`
- `customer_summary` → `intelligence-summary`
- `customer_intelligence_summary` → `intelligence-summary`

---

## Playbook Schema

```yaml
---
type: playbook
customer: "Exact Customer Name"
product: Tivian
date: 2026-04-09
tags: [renewal, playbook, hvo, at-risk, simulation]
---
```

## Playbook Plan Schema

Saved alongside the playbook to preserve strategic reasoning for future reuse.

```yaml
---
type: playbook-plan
customer: "Exact Customer Name"
product: Tivian
date: 2026-04-09
playbook_ref: "2026-04-09_Renewal_Playbook.md"
---
```

---

## Outcome Schema

```yaml
---
type: outcome
customer: "Exact Customer Name"
product: Tivian
playbook_ref: "2026-04-09_Renewal_Playbook.md"
scenario_selected: "Scenario 2: Executive Reset"
date_resolved: 2026-06-15
result: renewed                      # renewed | churned | downgraded | expanded | pending
---
```

---

## Transcript Schema

```yaml
---
type: transcript
customer: "Exact Customer Name"
product: Tivian
date: 2026-04-18
participants: [Jay Khalife, Contact Name, Other Name]
source: Read.ai
---
```

---

## Email Schema

```yaml
---
type: email
customer: "Exact Customer Name"
product: Tivian
date: 2026-04-18
---
```

---

## Jira Ticket Schema

```yaml
---
type: jira-ticket
customer: "Exact Customer Name"
product: Tivian
date: 2026-04-18
---
```

---

## Hub Node Schema

```yaml
---
type: node
node_type: status | product | sub-product | sentiment | pain-point | contract | competitor
title: "Node Title"
customer_count: 45
---
```

### Hub Node Body Structure

Every hub node follows this body format:

```markdown
# [Node Title]

[One-paragraph description of what this node represents and why it matters]

## Connected Customers

- [[CustomerName1]] — [one-line context: ARR, product, key detail]
- [[CustomerName2]] — [one-line context]

## Related Dimensions

- [[Related Node 1]] — [why this relationship matters]
- [[Related Node 2]] — [why this relationship matters]
```

**Rules:** `customer_count` in YAML must match the actual count in Connected Customers. When customers are added/removed, update both. Related Dimensions cross-link to other hub nodes (e.g., a Pain Point node links to the Sentiment nodes that commonly co-occur).

---

## Transcript Body Structure

Beyond the YAML frontmatter, transcript files should follow this body format:

```markdown
# [Meeting Title] — [Date]

## Participants
- [Name] ([Role/Company])

## Summary
[2-3 sentence meeting overview from Read.ai or manual notes]

## Key Discussion Topics
[Narrative or bullets covering what was discussed]

## Action Items
- [ ] [Owner]: [Action] — by [date]

## Decisions
[Any commitments made — feeds into the Decisions table in _intelligence_summary.md]

## Sentiment & Intent Notes
[Observed tone, cancellation signals, expansion signals, relationship dynamics]
```

**Rules:** Not all sections will be present for every transcript. Include only sections with real data. The Decisions section feeds into `_skills/commitment-extraction.md` and ultimately into `_Action_Tracker.md`.

---

## Health History Table Structure

The `## Health History` table in intelligence summaries uses this format (see `_skills/health.md` for full rules):

```markdown
| Date | Health Score | Band | Engagement | Relationship | Cadence | Product | Trigger |
|------|-------------|------|------------|-------------|---------|---------|---------|
| 2026-04-14 | 72 | 🟢 Good | 80 | 65 | 70 | 60 | Weekly sweep |
```

**Rules:** Append-only. Never delete rows. Archive rows older than 12 months. `Trigger` tracks what caused the recalculation (daily scan, weekly sweep, manual update, debrief).

---

## Cross-Portfolio Query Patterns

With standardized frontmatter, these queries work by scanning YAML only (no full file reads):

| Query | Frontmatter Fields Used |
|-------|------------------------|
| Renewals within 120 days | `renewal_date` |
| At-risk HVO accounts | `status` contains "HVO" AND (`health_score` < 50 OR `segment` = "active-crisis") |
| Accounts without recent verification | `last_verified` older than 60 days |
| Financial Services customers declining | `industry` = "Financial Services" AND `health_score` < 50 |
| Stale summaries | `last_updated` older than 60 days |
| Negative renewal sentiment + high ARR | `renewals_sentiment` = "Negative" AND `arr` > 100000 |
| Accounts missing enrichment data | `industry` is absent OR `employee_count` is absent |
