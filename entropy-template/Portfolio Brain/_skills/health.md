# Portfolio Brain Skill: Health Scoring & Contact Intelligence

Load this file when recalculating health scores, updating contact tables, scoring cancellation intent, or investigating health drift.

## Health Score Formula

Every `_intelligence_summary.md` includes `health_score` (0–100) in YAML frontmatter. Deterministic, weighted composite:

| Dimension | Weight | What It Measures | Scoring |
|-----------|--------|-----------------|---------|
| **Engagement** | 40% | Email + meeting + Jira activity in last 90 days | 0 = no activity 90d; 50 = 1-2 touches/month; 100 = weekly+ |
| **Relationship Depth** | 25% | Classified contacts with recent engagement | 0 = no contacts; 50 = 1 contact; 100 = 3+ contacts active in 60d |
| **Cadence** | 20% | Regularity of engagement | 0 = last contact 60d+; 50 = 14-30d ago; 100 = <14d ago |
| **Product Activity** | 15% | Support ticket trend + Fionn usage signals | 0 = no data; 50 = stable; 100 = low tickets + active usage |

**Composite:** `health_score = (Engagement × 0.40) + (Relationship × 0.25) + (Cadence × 0.20) + (Product × 0.15)`

### Health Bands

| Band | Range | Meaning |
|------|-------|---------|
| 🟢 Good | 70–100 | Healthy. Monitor, don't intervene. |
| 🟡 At Risk | 40–69 | Drifting. Proactive outreach recommended. |
| 🔴 Critical | 0–39 | Silent or deteriorating. Immediate attention. |

### Rules
- Recalculated during every daily inbox scan and weekly sweep.
- Score change ≥10 points → **Health Drift** alert.
- Score is a triage tool, not a verdict. Always read the intelligence summary for context.
- Missing data for a dimension → score that dimension at **0** (not 25). The old 25/100 penalty inflated scores uniformly and made triage useless.
- Every intelligence summary also includes `data_confidence` in YAML frontmatter.

### Data Confidence Tiers

| Tier | Dimensions with Real Data | Meaning |
|------|--------------------------|---------|
| **high** | 3–4 | Score is actionable. Use health bands to triage. |
| **medium** | 2 | Score is directional. Verify before acting. |
| **low** | 0–1 | Score is unreliable. Account needs data collection, not intervention. |

When confidence is **low**, the health score reflects missing data, not actual risk. Don't trigger alerts or playbooks based on low-confidence scores — instead, flag the account for data enrichment during the next sweep.

## Health History

Every intelligence summary includes an append-only `## Health History` table. **Never delete rows.**

```markdown
## Health History

| Date | Health Score | Band | Engagement | Relationship | Cadence | Product | Trigger |
|------|-------------|------|------------|-------------|---------|---------|---------|
| 2026-04-14 | 72 | 🟢 Good | 80 | 65 | 70 | 60 | Weekly sweep |
```

**Rules:**
- Append a new row every recalculation.
- `Trigger` column: what caused it (daily scan, weekly sweep, manual update).
- If table exceeds 52 rows (1 year), archive rows older than 12 months to `Health-Archive-YYYY.md` in the customer folder.

## Health Trajectory Analysis

The Health History table stores the data. This section defines how to extract trajectory — the direction, velocity, and acceleration of change.

### Computing Trajectory

When recalculating health or running a triage, compute these from the Health History table:

| Metric | Formula | What It Tells You |
|--------|---------|-------------------|
| **Direction** | Compare latest score to score 4 weeks ago | Improving, declining, or stable (±10 threshold) |
| **Velocity** | `(latest_score - score_8_weeks_ago) / weeks_elapsed` | Points gained or lost per week. A customer losing 3 pts/week is very different from one losing 0.5 pts/week |
| **Acceleration** | Compare velocity over last 4 weeks to velocity over the 4 weeks before that | Is the decline speeding up, slowing down, or steady? Accelerating decline is the most dangerous signal |
| **Projected Score** | `current_score + (velocity × weeks_to_renewal)` | Where this account lands if nothing changes. Compare to band thresholds (70 for Good, 40 for Critical) |

### Trajectory Alerts

These are distinct from the existing Health Drift alert (≥10 point single-event change). Trajectory alerts catch slow bleeds that never trigger a single-event drift.

| Alert | Condition | Severity |
|-------|-----------|----------|
| **Slow Bleed** | Velocity ≤ -1.5 pts/week sustained over 4+ weeks, even if no single drop ≥10 | 🟡 Medium |
| **Accelerating Decline** | Current velocity is ≥2× the velocity from the prior 4-week window | 🔴 High |
| **Trajectory to Critical** | Projected score at renewal date falls below 40 | 🔴 High (HVO) / 🟡 Medium (non-HVO) |
| **Recovery Stall** | Account was improving (velocity > 0) but velocity has dropped to ≤0 for 3+ weeks | 🟡 Medium |
| **Silent Plateau** | Score has been within ±3 points for 8+ weeks AND no engagement in 30+ days | 🟡 Medium — stability without engagement is disengagement in disguise |

### When to Compute

- **Triage:** Always compute Direction. Compute Velocity and Projected Score if Health History has ≥4 rows.
- **Weekly sweep:** Compute all metrics for every account with ≥4 history rows. Surface trajectory alerts in the Portfolio Dashboard.
- **Playbook generation:** Compute all metrics and include in the Situation Assessment. Projected Score at renewal is critical context for scenario modeling.
- **Monthly enrichment:** Flag accounts where Projected Score at renewal crosses a band threshold (Green→Yellow, Yellow→Red).

### Minimum Data Requirements

- Direction: 2+ rows spanning 2+ weeks
- Velocity: 3+ rows spanning 4+ weeks
- Acceleration: 6+ rows spanning 8+ weeks
- Projected Score: Velocity + known renewal_date

If insufficient data exists, say so. Don't compute from noise.

## Contact Intelligence

Every intelligence summary includes a `## Key Contacts` table:

```markdown
## Key Contacts

| Name | Role | Stance | Influence | Last Engaged | Email | Notes |
|------|------|--------|-----------|-------------|-------|-------|
| Fiona Smith | Decision Maker | Advocate | High | 2026-04-10 | fiona@customer.com | Budget holder |
```

### Field Definitions

| Field | Values | Update When |
|-------|--------|-------------|
| **Role** | Decision Maker, Executive Sponsor, Day-to-Day, Technical, Champion, Blocker | Role identified or changes |
| **Stance** | Advocate, Neutral, Blocker, At-Risk, Unknown | Sentiment evidence in emails/transcripts |
| **Influence** | High, Medium, Low | Based on title + observed decision involvement |
| **Last Engaged** | YYYY-MM-DD | New email/meeting/ticket involves contact |

### Rules
- Update `Last Engaged` every time a contact appears in newly ingested data.
- No engagement 90+ days → Notes: "⚠️ Silent 90d+".
- Champion's stance shifts to At-Risk or Blocker → 🔴 High severity alert.
- New contact appears → add with Stance: Unknown, flag for Jay's review.
- Never remove contacts. Departed → Notes: "Departed [date]", Stance: "N/A".

## Contact Personas (Behavioral Profiles)

When transcript or email data supports it, add a `## Contact Personas` section to the intelligence summary, below `## Key Contacts`. This provides the behavioral dimensions needed for pressure-test simulations and pre-call preparation.

```markdown
## Contact Personas

### [Contact Name]
**Source confidence:** High (multiple transcripts) | Medium (1 transcript + emails) | Low (emails only)

| Dimension | Value | Evidence |
|-----------|-------|----------|
| Decision Style | analytical / consensus / authority / relationship-driven | [brief citation] |
| Risk Tolerance | low / medium / high | [brief citation] |
| Price Sensitivity | low / medium / high | [brief citation] |
| Communication Style | formal / direct / technical / collaborative | [brief citation] |
| Engagement Velocity | fast (<48h) / moderate (3-7d) / slow (7d+) | [response pattern] |
| Motivators | ROI, compliance, innovation, risk-avoidance, relationship, efficiency | [brief citation] |

**Objection Patterns:** [Recurring themes from past conversations — what they push back on]
**Persuasion Levers:** [What has worked before — what moves them]
**Communication Preferences:** [Email vs. call, time-of-day patterns, formality level]
```

### Dimension Definitions

| Dimension | What It Captures | How to Score |
|-----------|-----------------|--------------|
| **Decision Style** | How they reach conclusions | `analytical` = data/ROI-driven, asks for metrics. `consensus` = needs buy-in from others, defers to group. `authority` = top-down, decisive, doesn't consult. `relationship-driven` = trust-based, values personal rapport. |
| **Risk Tolerance** | Appetite for change, new features, contract flexibility | `low` = prefers status quo, resists change, wants guarantees. `medium` = open to change with evidence. `high` = early adopter, comfortable with ambiguity. |
| **Price Sensitivity** | How much pricing dominates decisions | `low` = focuses on value, rarely pushes on price. `medium` = negotiates but reasonable. `high` = price is primary decision driver, compares alternatives. |
| **Communication Style** | How they prefer to interact | `formal` = structured, professional, agenda-driven. `direct` = blunt, wants bottom line fast. `technical` = detail-oriented, wants specs and data. `collaborative` = brainstorming, open-ended, wants partnership feel. |
| **Engagement Velocity** | How fast they respond and move | Based on observed response times across emails and meeting scheduling patterns. |
| **Motivators** | What drives their decisions | Observed from what they emphasize in conversations. Multiple values allowed. |

### Rules
- Only populate when real evidence exists (transcript quotes, email patterns, observed behavior).
- Tag each dimension with its evidence source so it can be validated.
- One persona per contact. Update after each new transcript ingestion.
- When a persona is populated, the pressure-test skill (`_skills/pressure-test.md`) can simulate that contact.
- Personas are living documents — update dimensions when new evidence contradicts old assessments.
- For accounts with no transcripts, do NOT guess personas from role/title alone. Leave the section absent.

## Cancellation-Intent Scoring

Score each communication for cancellation intent during processing.

### Category Weights

| Category | Weight | Examples |
|----------|--------|---------|
| Explicit cancellation | 1.0 | "We want to cancel", "termination notice" |
| Competitor evaluation | 0.8 | "Looking at alternatives", names a competitor |
| Budget/value challenge | 0.7 | "Can't justify the cost", "ROI isn't there" |
| Escalation language | 0.6 | "Unacceptable", "executive review" |
| Disengagement signals | 0.5 | "Not using it much", "low priority" |
| Frustration accumulation | 0.4 | Multiple negative emails in 30d, unresolved tickets |

### Scoring Rules
- Score = `max(category_weights_detected) + 0.1 × (additional_categories - 1)`
- Cap at 1.0.
- 3+ categories in one communication → +0.15 bonus.
- Same customer triggers intent in 2+ communications within 30d → +0.2 to latest score.
- Only flag when score ≥ 0.5. Below that, log but don't alert.
- **Threshold mapping:** ≥ 0.5 = Medium-or-higher risk (triggers Tier 2 escalation + alerts). ≥ 0.7 = High risk (triggers 🔴 High alert regardless of account type). This aligns with ingestion.md and alerting.md thresholds.

### When score ≥ 0.5

Add `## Cancellation Intent` section to intelligence summary:

```markdown
## Cancellation Intent

| Date | Score | Categories Detected | Source | Notes |
|------|-------|-------------------|--------|-------|
| 2026-04-15 | 0.85 | Explicit cancellation, Budget challenge | Email 2026-04-15 | CFO mentioned budget cuts |
```

### When score ≥ 0.7
Automatically trigger 🔴 High severity alert regardless of account type.
