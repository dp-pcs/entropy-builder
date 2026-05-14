# Portfolio Brain Skill: Portfolio Segmentation

Load this file when running portfolio reviews, resource planning, answering "which accounts need attention?", or during monthly enrichment. Goes beyond health score to cluster all 300 customers by behavior pattern for actionable resource allocation.

**Design principle:** Segments answer "what kind of account is this?" while health scores answer "how healthy is it?" A Silent Renewer at 45 health is a completely different situation from a Drifting Away at 45 health — same score, opposite actions.

## Segment Definitions

Six mutually exclusive segments. Every customer gets exactly one.

### Silent Renewers

Low engagement, auto-renew pattern, no open issues. These accounts just work — don't fix what isn't broken.

**Criteria (ALL must be true):**
- `health_score` 40–69
- `data_confidence` low or medium
- No emails or transcripts in 90+ days
- No open Jira tickets
- `renewal_date` > 90 days out

**Action:** Monitor only. Don't chase. If they stop renewing, run churn autopsy via `_skills/playbook.md`. Silence here is not a signal — it's a pattern.

### High-Touch Engagers

Regular meetings, feature requests, expansion signals. These are the accounts worth Jay's personal time.

**Criteria (ALL must be true):**
- Transcripts exist within the last 60 days
- 3+ contacts in Key Contacts table
- Engagement dimension score > 60 (from health formula)

**Action:** Invest. Schedule QBRs. Track expansion signals via `_skills/alerting.md`. Prioritize for upsell and cross-sell conversations. These accounts convert effort into revenue.

### Price Shoppers

Renewal friction, discount history, competitor mentions. They're evaluating whether to stay.

**Criteria (ANY one is sufficient):**
- `renewals_sentiment` is Negative
- Prior discount recorded in Notion
- Competitor mentions detected in emails or transcripts (last 180 days)

**Action:** Defend. Prepare value narrative early — don't wait for the renewal call. Read `Company-Rules.md` for pricing flexibility before engaging. Load `_skills/playbook.md` for renewal strategy if renewal < 180 days.

### Drifting Away

Declining engagement, stale contacts, no recent meetings. The relationship is cooling and nobody's addressing it.

**Criteria (ANY two must be true):**
- Health score shows declining trend (check Health History for negative trajectory: latest score 10+ points below score from 8 weeks ago)
- Last Engaged > 60 days on primary contact in Key Contacts
- No transcript in 120+ days

**Action:** Intervene. Send re-engagement email. Validate contacts are still at the company (check LinkedIn during monthly enrichment). If 2+ criteria are met and renewal < 180 days, generate a playbook immediately.

### Active Crisis

Open escalation, critical Jira tickets, cancellation intent. This account needs attention now, not next week.

**Criteria (ANY one is sufficient):**
- `cancellation_intent` >= 0.5
- Active fire documented in `_hot_cache.md`
- CRITICAL overdue commitments in `_Action_Tracker.md`

**Action:** Immediate. Load `_skills/triage.md` for situational snapshot, then `_skills/playbook.md` for strategy. These accounts jump the queue on everything.

### Managed Decline

Floor price, end-of-engineering product, no growth path. The math doesn't support investment.

**Criteria (ANY one is sufficient):**
- Status contains "Floor Price" (check Graph Connections or hub nodes)
- Product is designated End of Engineering (EoE)
- ARR < $10K AND product sentiment is Negative

**Action:** Harvest. Keep interactions clean and professional but don't invest time in expansion, QBRs, or deep relationship-building. Accept churn if it comes. Don't generate playbooks unless explicitly asked.

## Segmentation Process

### Step 1: Collect Frontmatter

Read YAML frontmatter of all `_intelligence_summary.md` files across the 4 products (Tivian, Influitive, Lyris, QuickSilver). **Frontmatter only — do not read full files.** This keeps context lean across 300 accounts.

Collect per customer: `health_score`, `data_confidence`, `renewal_date`, `arr`, `cancellation_intent`, `product`, `status`, and any `segment` field already present.

### Step 2: Deep-Check Where Needed

For customers where frontmatter alone is insufficient to classify (e.g., need to check Health History trend, Key Contacts count, or last transcript date), open the full intelligence summary only for those accounts.

### Step 3: Classify

Assign each customer to exactly one segment. When a customer matches multiple segment criteria, apply the priority tiebreaker:

```
Active Crisis > Drifting Away > Price Shoppers > High-Touch Engagers > Silent Renewers > Managed Decline
```

Rationale: Urgency wins. An account that is both a Price Shopper and Drifting Away is "Drifting Away" because the engagement decay is the more dangerous signal.

### Step 4: Output

Produce a segment summary table:

```markdown
## Portfolio Segmentation — [Month Year]

| Segment | Count | Total ARR | % of Portfolio ARR | Top 5 Accounts (by ARR) |
|---------|-------|-----------|-------------------|------------------------|
| Active Crisis | N | $X | X% | Account1, Account2, ... |
| Drifting Away | N | $X | X% | Account1, Account2, ... |
| Price Shoppers | N | $X | X% | Account1, Account2, ... |
| High-Touch Engagers | N | $X | X% | Account1, Account2, ... |
| Silent Renewers | N | $X | X% | Account1, Account2, ... |
| Managed Decline | N | $X | X% | Account1, Account2, ... |
| **Total** | **300** | **$X** | **100%** | |
```

Table is ordered by action priority (crisis first, decline last) — not alphabetically.

## Integration

### Monthly Enrichment

Segmentation runs during monthly enrichment alongside the pattern report (`_skills/enrichment.md`). Sequence:

1. Enrichment updates health scores and firmographic data
2. Segmentation classifies accounts using updated data
3. Pattern report references segment distribution for trend analysis

### Frontmatter Storage

After classification, update each customer's `_intelligence_summary.md` YAML frontmatter:

```yaml
segment: silent-renewer | high-touch | price-shopper | drifting | active-crisis | managed-decline
```

Use the hyphenated slug values exactly as shown. This enables vault-wide queries like "show all drifting accounts for Lyris."

### Portfolio Dashboard

`_Portfolio_Dashboard.md` should include a segment distribution section when refreshed after segmentation runs. Reference the segment summary table from the most recent run.

### Scope

Only process Jay's 4 products: **Tivian, Influitive, Lyris, QuickSilver.** Never include team portfolio products (ACRM, Artemis, Aurea Platform, Bonzai, Jigsaw Platform, Messageone, Onyx, Pivotal, Saratoga, Stratifyd).

## Rules

1. **Monthly cadence.** Segments are re-evaluated monthly, not daily or weekly. Running segmentation on 300 accounts is expensive in context — don't do it ad hoc unless Jay explicitly asks.

2. **Multi-step jumps trigger alerts.** If a customer's segment changes by more than one position in the priority order (e.g., Silent Renewer to Active Crisis, or High-Touch Engager to Managed Decline), flag it as an alert in the dashboard. These jumps indicate a rapid shift that warrants investigation.

3. **Segment is a lens, not a verdict.** Don't over-index on the segment label. Always check the intelligence summary before acting on any account. A "Drifting Away" account might have a perfectly good reason for low engagement (seasonal business, contact on leave, etc.).

4. **Segment does not override health score.** Both exist and serve different purposes. Health score = quantitative pulse. Segment = behavioral pattern. Use both together for triage.

5. **New customers default to Silent Renewer** until enough data exists to classify them accurately (minimum 60 days of data or 2+ interactions).

6. **Churned customers are not segmented.** Only active accounts receive segments. If an account churns, remove the `segment` field from frontmatter during the next monthly run.
