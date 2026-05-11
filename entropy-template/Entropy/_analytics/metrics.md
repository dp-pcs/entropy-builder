# Entropy Metrics Reference

Canonical definitions for every metric used across the Entropy system. When a skill needs to know how a metric is calculated or what a score means, reference this file instead of re-deriving from skill instructions.

## Health Score

`health_score = (Engagement × 0.40) + (Relationship × 0.25) + (Cadence × 0.20) + (Product × 0.15)`

### Dimension Scoring (0-100 each)

| Dimension | Weight | Score 80-100 | Score 40-79 | Score 0-39 |
|-----------|--------|-------------|-------------|------------|
| Engagement | 0.40 | Monthly+ emails, meetings, Jira activity | Quarterly contact, some activity | No contact 60+ days |
| Relationship | 0.25 | Multi-threaded, exec sponsor, advocate contacts | Single thread, neutral contacts | Single thread or no contacts classified |
| Cadence | 0.20 | Regular rhythm, customer initiates | Irregular but responsive | Goes silent, only responds when pushed |
| Product | 0.15 | Positive feedback, feature requests, expanding usage | Neutral, no complaints | Negative sentiment, complaints, low usage |

### Health Bands

| Band | Range | Action | Dashboard Color |
|------|-------|--------|----------------|
| Good | 70-100 | Monitor | 🟢 |
| At Risk | 40-69 | Proactive outreach | 🟡 |
| Critical | 0-39 | Immediate attention | 🔴 |

### Alert Triggers

| Alert | Condition |
|-------|-----------|
| Health Drift | Score change ≥ 10 points between calculations |
| Stale Health | Score not recalculated in 14+ days |
| Missing Dimension | Any dimension at 0 (not 25 — true zero) |

### Data Confidence

| Level | Meaning |
|-------|---------|
| high | 3+ data sources, recent activity, classified contacts |
| medium | 1-2 data sources, some gaps |
| low | Minimal data, mostly inferred |

Only act on high/medium confidence scores. Low confidence → flag for enrichment before making strategic decisions.

---

## Cancellation Intent Score

Weighted signal detection from customer communications. Range: 0.0 to 1.0.

| Signal | Weight | Examples |
|--------|--------|---------|
| Explicit cancellation language | 1.0 | "cancel", "terminate", "end the contract" |
| Competitor evaluation | 0.8 | Alternative vendors mentioned, comparison requests |
| Budget/value challenge | 0.7 | Cost concerns, ROI questioning, "justify the spend" |
| Escalation language | 0.6 | "unacceptable", threats to escalate, executive complaints |
| Disengagement signals | 0.5 | Low usage admission, deprioritization, "not a priority" |
| Frustration accumulation | 0.4 | Repeated complaints, unresolved issue callbacks |

**Alert threshold:** ≥ 0.5 → log in intelligence summary. ≥ 0.7 for HVO → recommend Tier 3 analysis.

---

## Customer Segments

Behavioral segments assigned during health scoring. Drives prioritization and playbook strategy.

| Segment | Definition | Typical Action |
|---------|-----------|----------------|
| active | Engaged, healthy, no concerns | Monitor, look for expansion |
| drifting | Was active, engagement declining | Re-engage before it becomes a problem |
| price-shopper | Primarily motivated by cost, compares alternatives | Value reinforcement, lock-in incentives |
| managed-decline | Low ARR, minimal engagement, not worth heavy investment | Maintain, don't over-invest |
| active-crisis | Actively expressing churn signals or frustration | Immediate playbook, executive engagement |
| expansion-ready | Positive signals, growing usage, requesting features | Expansion playbook, upsell approach |

---

## Sentiment Scales

Three sentiment dimensions tracked per customer:

| Dimension | What It Measures | Sources |
|-----------|-----------------|---------|
| product_sentiment | How the customer feels about the product itself | Feedback, tickets, usage patterns |
| support_sentiment | How the customer feels about support quality | Ticket resolution, CSAT, direct quotes |
| renewals_sentiment | How the customer feels about renewing | Renewal discussions, pricing reactions, contract language |

Values: `Positive`, `Negative`, `Neutral`, `Unknown`

**Unknown** means no data — not neutral. Unknown should be resolved during enrichment.

---

## Risk Bands (from Fionn)

| AI Signal | Meaning |
|-----------|---------|
| RED | High churn risk — immediate attention |
| YELLOW | Moderate concern — monitor closely |
| GREEN | Healthy — standard cadence |
| GRAY | Insufficient data for signal |

Fionn's AI signal is independent of Entropy's health score. When they disagree (e.g., Fionn RED but Entropy health 72), investigate — one system may have data the other doesn't.

---

## Portfolio Classification

| Classification | Definition |
|---------------|-----------|
| HVO | High Value Opportunity — strategic accounts, typically high ARR |
| Non-HVO | Standard accounts |
| Floor Price | At or near minimum pricing — limited pricing leverage |
| At Risk | Active churn signals or declining engagement |
| Cancelled | Customer has churned — preserved for analysis |
| Active | Currently paying and engaged |

Status field in frontmatter may combine: e.g., `"Active, HVO"` or `"Floor Price, Active, Non-HVO"`.
