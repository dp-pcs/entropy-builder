# Entropy Skill: External Enrichment, Pattern Reports & Monthly Health Check

Load this file when running the monthly enrichment (1st of month), generating pattern reports, enriching firmographic data, or running the monthly health check.

## External Intelligence

Intelligence summaries may include `## External Intelligence`, populated during monthly enrichment. Captures what internal data can't provide.

### Template

```markdown
## External Intelligence

| Date | Source | Finding | Impact |
|------|--------|---------|--------|
| 2026-04-01 | Web search | Company announced 15% workforce reduction | 🔴 High — budget cuts likely |
| 2026-03-01 | LinkedIn | Primary contact changed role to VP at competitor | 🔴 High — champion lost |
```

### What to Search For

| Signal | Why It Matters | Search Query |
|--------|---------------|-------------|
| Leadership changes | Champion departure = #1 churn predictor | "[Contact Name] LinkedIn" |
| M&A activity | Acquisitions trigger vendor consolidation | "[Company Name] acquisition OR merger" |
| Layoffs / restructuring | Budget cuts → cancellation risk | "[Company Name] layoffs OR restructuring" |
| Funding rounds | Growth → expansion opportunity | "[Company Name] funding OR series" |
| Competitor wins | Public case studies naming competitors | "[Company Name] [Competitor] OR alternative" |
| Public reviews | Unfiltered product sentiment | "[Product Name] review G2 OR Capterra" |

### Rules
- Gathered ONLY during monthly enrichment, ONLY for HVO and At-Risk accounts.
- Findings that change risk profile → immediately update Graph Connections.
- Champion departure → 🔴 High alert regardless of health score.
- M&A activity → 🟡 Medium alert + recommend new playbook.
- Never rely solely on external intelligence — always cross-reference internal data.

## Firmographic Data

YAML frontmatter fields for cross-portfolio analysis. Enriched during monthly sweep.

```yaml
industry: "Financial Services"
employee_count: 2500
hq_location: "London, UK"
tech_stack: [Salesforce, SAP, Azure]
```

### Rules
- Only populate when confirmed via web search or Notion.
- `employee_count`: round to nearest 100 (<5K), nearest 1,000 (>5K).
- `tech_stack`: from Jira integrations, email signatures, or public job postings. Don't guess.
- Enables queries like: "Financial Services customers with health_score < 50" or "churn rate by industry".

## Cross-Customer Pattern Report

**File:** `Entropy/YYYY-MM_Portfolio_Pattern_Report.md`
**Generated:** Monthly (1st of month).

### What It Analyzes

1. **Pain point clustering** — 3+ customers independently surfacing the same issue across a product → emerging pattern.
2. **Sentiment trends by product** — Aggregate per product. Is one product trending down?
3. **Churn pattern analysis** — Common factors preceding at-risk/churned accounts. Feed into Prediction Ledger.
4. **Renewal outcome trends** — Aggregate: % renewed at 25%, % multi-year, % churned, month-over-month comparison.
5. **Expansion conversion** — Flagged signals → converted to upsells/cross-sells → missed.

### Template

```markdown
# Portfolio Pattern Report — [Month Year]

## Emerging Pain Points
[Themes across 3+ customers, grouped by product]

## Sentiment Trends
[Product-level direction: improving / stable / declining]

## Churn & Risk Patterns
[Common precursors observed this month]

## Renewal Outcomes
[Aggregate stats: renewed, churned, multi-year, 1-year, average price increase]

## Expansion Conversion
[Signals flagged → converted → missed]

## Recommendations
[Portfolio-level strategic adjustments]
```

Feeds back into Prediction Ledger's Pattern Library.

## Hub Node Update Rules

- **Status changes in Notion** → update Status node + customer's graph connections.
- **New pain point from feedback** → add to existing node, or create new node if genuinely new theme.
- **New customer added** → create folder, generate `_intelligence_summary.md`, add wikilinks to all relevant nodes, add `[[CustomerName]]` to each node's Connected Customers.
- **Customer churns** → move to appropriate status. Do NOT delete files. Update graph connections.

## Automation-to-Learning Flywheel

The monthly enrichment includes a system improvement review (step 7 in `_skills/ingestion.md`). The enrichment skill's contribution to the flywheel is identifying data gaps and enrichment opportunities:

- Are there customers with `Unknown` sentiments that could be resolved with a targeted email or Fionn check?
- Are there industries or segments with thin firmographic data that a web search batch could fill?
- Did any external intelligence findings this month suggest a new signal type to track?

Feed improvement recommendations into the monthly report. The flywheel compounds: each improvement makes future enrichment faster and more accurate.

## Monthly Health Check (10-Point)

Run every month to maintain system integrity:

1. Verify all 300 customer folders exist and match Notion.
2. Check for orphan files (no wikilinks).
3. Verify every hub node's customer count matches reality.
4. Flag intelligence summaries not updated in 60+ days.
5. Check for contradictions between sentiment data and actual feedback.
6. Identify customers with zero emails, zero transcripts, zero Jira tickets — blind spots.
7. Verify Prediction Ledger is up to date — any playbooks with known outcomes not recorded?
8. Check expansion signals older than 90 days without action.
9. Verify all HVO and At-Risk accounts have current playbooks (within 90 days).
10. Generate the monthly Cross-Customer Pattern Report.

## Product Knowledge Base Reference

Canonical KB at `Obsidian Vault/Knowledge Base/` (2,325 articles):

| Folder | Product | Articles |
|--------|---------|----------|
| `Discover XI Support/` | Tivian (DXI/EFS) | 605 |
| `AEM Lyris LM/` | Lyris ListManager | 665 |
| `Influitive Support/` | Influitive | 795 |
| `Quicksilver Support/` | QuickSilver | 165 |
| `Communicate XI/` | Communicate XI (Lyris sub-product) | 95 |

**Structure:** Product → Category → Visibility Tier → Article.md
**Tiers:** PUBLIC (customer-facing), AUTHORIZED (authenticated), AGENTS (internal only)
