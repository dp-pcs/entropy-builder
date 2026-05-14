# Portfolio Brain Skill: Competitive Intelligence

Load this file when a competitor is mentioned in an email, transcript, or Jira ticket; when a renewal has competitive pressure; when doing win/loss analysis; or during quarterly landscape reviews as part of monthly enrichment.

## Known Competitors by Product

| Product | Primary Competitors | Secondary Competitors |
|---------|-------------------|---------------------|
| Tivian (DXI/CXI) | Qualtrics, Medallia, SurveyMonkey/Momentive | Forsta, Confirmit, InMoment, Typeform |
| Influitive | Gainsight, Totango, Pendo Feedback | Advocately, Referral Rock, Ambassador |
| Lyris | Mailchimp, Constant Contact, Salesforce Marketing Cloud | SendGrid, Brevo (Sendinblue), Campaign Monitor |
| QuickSilver | Arena Solutions, Aras Innovator | OpenText, Windchill (PTC), Teamcenter (Siemens) |

Use these names for signal detection during ingestion. If a new competitor appears that is not on this table, log it in the Competitive Signals table and add it here during the next monthly enrichment.

## Signal Detection (During Ingestion)

Integrated into the Tier 1 / Tier 2 processing model from `_skills/ingestion.md`. **Scope clarification:** Tier 1 detects competitor mentions via keyword scan and escalates to Tier 2 for content extraction (see below). This skill file itself is loaded for **Tier 3 deep analysis only** — competitive landscape reviews, win/loss analysis, and playbook generation with competitive pressure. Tier 2 extraction uses the templates below but does not require loading this full skill.

### Tier 1 Trigger Words

Scan email subjects, Jira summaries, and meeting titles for:
- Any competitor name from the table above (case-insensitive)
- "alternative", "evaluating options", "RFP", "demo with", "shortlist", "compared to", "considering other", "vendor evaluation", "competitive bid"

**When detected:** Escalate to Tier 2 content scan automatically. This follows the same escalation pattern as cancellation-intent keywords in `_skills/ingestion.md`.

### Tier 2 Competitive Extraction

When a Tier 1 trigger fires, read the full content and extract:

| Field | What to Capture |
|-------|----------------|
| **Competitor** | Exact name from the table (or new entrant) |
| **Context** | One of: `evaluation`, `comparison`, `switch-threat`, `feature-gap`, `pricing-pressure`, `lost-deal`, `won-deal` |
| **Who mentioned it** | Contact name and role (customer, internal, reseller) |
| **Date** | Date of the source document |
| **Verbatim quote** | The exact sentence(s) where the competitor was mentioned, if available |

## Competitive Intelligence Log

When a competitive signal is detected, add it to the customer's `_intelligence_summary.md` under a dedicated section. Create the section if it does not exist.

### Template

```markdown
## Competitive Signals

| Date | Competitor | Context | Source | Risk Level |
|------|-----------|---------|--------|-----------|
| 2026-05-01 | Qualtrics | Customer requested feature comparison | Email 2026-04-28 | Medium |
| 2026-04-15 | Medallia | Mentioned attending Medallia webinar | Transcript 2026-04-15 | Low |
```

### Risk Level Assignment

| Risk Level | Criteria |
|-----------|----------|
| **Low** | Passing mention, no evaluation language, general awareness |
| **Medium** | Direct comparison, feature gap discussion, pricing question referencing competitor |
| **High** | Active RFP, explicit evaluation, shortlist, demo scheduled with competitor, "considering switching" |

## Competitive Playbook Triggers

Escalation tiers determine what action to take when competitive signals appear.

| Signal Pattern | Action |
|---------------|--------|
| Single competitor mention, no evaluation language | Log in Competitive Signals table. No further action. |
| Competitor + evaluation language ("evaluating", "comparing", "RFP") | Log in Competitive Signals table + flag in weekly sweep as competitive threat. |
| Competitor + explicit comparison, RFP, or shortlist | Alert. Load `_skills/playbook.md`. Recommend generating a competitive positioning playbook. |
| Customer names a specific competitor feature they want | Log as BOTH a product feedback item (in intelligence summary) AND a competitive signal. |

When escalating to playbook generation, include the full Competitive Signals history for that customer so the playbook can address the specific competitive angle.

## Competitor Hub Nodes

Competitive intelligence is stored per-account in intelligence summaries (the `## Competitive Signals` table). But cross-portfolio competitive patterns require an aggregated view. Competitor hub nodes in `_nodes/Competitors/` provide this — just like Pain Point nodes aggregate customer issues across the portfolio.

### Node Structure

Each competitor with 2+ mentions across the portfolio gets a hub node at `_nodes/Competitors/[Competitor Name].md`:

```yaml
---
type: node
node_type: competitor
title: "Qualtrics"
customer_count: 0
signal_count: 0
wins: 0
losses: 0
last_signal: "2026-05-11"
---
```

```markdown
# [Competitor Name]

[One paragraph: what this competitor offers, which of Jay's products they threaten, and why customers evaluate them.]

## Products Threatened

- [[Tivian]] — [why customers compare, what the feature gap or value gap is]

## Connected Customers

Accounts where this competitor has been mentioned, sorted by risk level:

### Active Evaluations (High Risk)
- [[CustomerName]] — [date, context, risk level, current status]

### Past Mentions (Medium/Low Risk)
- [[CustomerName]] — [date, context, resolution if any]

## Positioning That Works

What has successfully defended against this competitor in past encounters:
- [Approach] — [which customer, what happened, outcome]

## Positioning That Failed

- [Approach] — [which customer, what happened, why it didn't work]

## Related Dimensions

- [[Product Sentiment - Negative]] — customers unhappy with the product are more likely to evaluate
- [[Contract & Renewal Friction]] — pricing disputes often trigger competitive evaluation
- [Other relevant pain point or sentiment nodes]
```

### When to Create / Update Nodes

| Event | Action |
|-------|--------|
| **Tier 2 competitive signal detected** | Check if a node exists for this competitor. If yes, add the customer to Connected Customers. If no and this is the 2nd+ mention across the portfolio, create the node. |
| **Outcome recorded (churn or renewal)** | If the Competitive Signals table had an entry for this account, update the competitor node: increment wins/losses, add to Positioning That Works or Failed. |
| **Monthly enrichment** | Refresh `customer_count`, `signal_count`, `wins`, `losses` from actuals. Update `last_signal` date. |
| **Quarterly landscape review** | Review all competitor nodes. Archive nodes with no signals in 6+ months (move to `_nodes/Competitors/_archive/`). |

### Cross-Portfolio Queries Enabled

With competitor nodes in the graph, these queries become trivial:

- "Which customers are currently evaluating Qualtrics?" → Read `_nodes/Competitors/Qualtrics.md` → Active Evaluations section
- "What positioning worked against Medallia?" → Read `_nodes/Competitors/Medallia.md` → Positioning That Works section
- "Is competitive pressure increasing for Tivian?" → Scan all competitor nodes with `[[Tivian]]` in Products Threatened, compare signal_count trends
- "When I generate a playbook for a customer evaluating [Competitor], what's worked before?" → The playbook skill can read the competitor node for empirical positioning data

## Quarterly Landscape Summary

Generated as a section within the monthly `Portfolio_Pattern_Report.md` (not a standalone file). Run during monthly enrichment alongside the pattern report from `_skills/enrichment.md`.

### What to Aggregate

1. **Mention count by competitor** — How many times each competitor appeared across the portfolio this quarter.
2. **Mention count by product** — Which of Jay's 4 products is seeing the most competitive pressure.
3. **Win/loss by competitor** — Cross-reference with `_Prediction_Ledger.md` outcomes. When a renewal was lost or a customer churned, check if a competitor was involved.
4. **Biggest threat per product** — The competitor with the highest combined signal count + lost deals for each product.
5. **Trend direction** — Is competitive pressure increasing, stable, or decreasing compared to last quarter.

### Template (Section in Pattern Report)

```markdown
## Competitive Landscape

### Signal Volume
| Competitor | Tivian | Influitive | Lyris | QuickSilver | Total |
|-----------|--------|-----------|-------|-------------|-------|
| [Name] | [N] | [N] | [N] | [N] | [N] |

### Win/Loss vs. Competitors
| Competitor | Wins (Retained) | Losses (Churned) | Pending |
|-----------|----------------|-----------------|---------|
| [Name] | [N] | [N] | [N] |

### Top Threat by Product
| Product | Primary Threat | Signals | Losses | Trend |
|---------|---------------|---------|--------|-------|
| Tivian | [Name] | [N] | [N] | [direction] |

### Recommendations
[Portfolio-level competitive positioning adjustments]
```

## Rules

1. **Never trash-talk competitors** in email drafts, playbooks, or any customer-facing content. Focus on Tivian/Influitive/Lyris/QuickSilver value, not competitor weaknesses.
2. **No custom pricing to match competitors** unless the account is >$100K ARR and CEO-approved. Check [[Company-Rules]] before recommending any pricing response to competitive pressure.
3. **Scope is Jay's 4 products only** — Tivian, Influitive, Lyris, QuickSilver. Do not track competitive intelligence for team portfolio products (ACRM, Artemis, Bonzai, etc.).
4. **No standalone competitive report files** — competitive data lives in customer intelligence summaries (per-account signals) and the monthly pattern report (portfolio-level landscape). This follows the same "no loose files at Portfolio Brain root" principle from `CLAUDE.md`.
5. **New competitor names** not in the Known Competitors table should be logged exactly as mentioned, then added to the table during the next monthly enrichment after verification.
6. **Historical signals are never deleted** — they form the competitive timeline for the account. Old signals with resolved context can be moved to a `### Resolved Competitive Signals` sub-section if the table grows beyond 15 rows.
