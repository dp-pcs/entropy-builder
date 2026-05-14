# Portfolio Brain Skill: Churn Autopsy

Structured post-mortem when a customer churns. Load this file when a customer's status changes to Churned, a cancellation is confirmed, or a loss is recorded. Extracts learnings from every churn event and feeds them into the Prediction Ledger to improve future forecasting.

**Design principle:** Blame the system, not the people. Every churn is a data point. The goal is to make the system smarter so the next one is caught earlier — or recognized as unpreventable sooner.

## When to Run

- Customer status changes to Churned in Notion
- Cancellation confirmation received (email, Jira ticket, or internal notification)
- Renewal outcome recorded as `churned` in an Outcome file
- Jay says "run autopsy on [Customer]", "what happened with [Customer]", or "why did we lose [Customer]"

**Timing rule:** Run within 7 days of churn confirmation. Evidence degrades fast — emails get buried, context fades, and the learning window closes.

## What to Load

1. The customer's `_intelligence_summary.md` — full read
2. All files in the customer's `Emails/`, `Transcripts/`, `Jira/` folders — frontmatter + first 10 lines each (enough to build the timeline)
3. Any existing playbooks in the customer folder — full read
4. Any existing Outcome files — full read
5. `_Prediction_Ledger.md` — full read (you'll be updating it)
6. `_skills/health.md` — cancellation-intent categories for signal analysis (Step 2)

Do NOT load: Company-Rules, vault MOCs, other customers, pattern reports. This is forensic, not strategic.

## Autopsy Process (6 Steps)

### Step 1 — Timeline Reconstruction

Walk back through all evidence and build a chronological timeline of signals. Read every email, transcript, and Jira ticket in the customer folder. For each, extract:

- **Date**
- **Event type** (email, meeting, ticket, health score change, playbook generated, decision logged)
- **Signal valence** (positive, neutral, negative, critical)
- **One-line summary**

Then answer these three questions:

1. **When was the first negative signal?** — The earliest evidence of trouble (disengagement, frustration, competitor mention, budget pressure). This is the "could have caught it" date.
2. **When did engagement drop?** — The point where communication frequency or depth declined. Compare against the Health History table.
3. **When was the last positive interaction?** — The final moment where the relationship felt intact. Everything after this was decline.

Present the timeline as a table:

```markdown
| Date | Event | Signal | Summary |
|------|-------|--------|---------|
| 2026-01-15 | Email | Positive | Thanked team for quick resolution on Jira ticket |
| 2026-02-20 | Health score | Negative | Dropped from 65 to 42 (At Risk) |
| 2026-03-10 | Email | Critical | "We're evaluating alternatives" |
| 2026-04-01 | — | Silent | No contact since March 10 |
| 2026-04-15 | Cancellation | Critical | Formal cancellation notice received |
```

### Step 2 — Signal Analysis

Map the signals found in Step 1 against the cancellation-intent categories from `_skills/health.md`:

| Category | Weight | Present? | Evidence |
|----------|--------|----------|----------|
| Explicit cancellation | 1.0 | | |
| Competitor evaluation | 0.8 | | |
| Budget/value challenge | 0.7 | | |
| Escalation language | 0.6 | | |
| Disengagement signals | 0.5 | | |
| Frustration accumulation | 0.4 | | |

For each category marked present, cite the specific evidence (date, source file, quote or paraphrase).

Also note any signals that were NOT in the standard categories — novel warning signs that the system doesn't currently track. These are candidates for adding to the alerting framework.

### Step 3 — System Failure Check

Evaluate whether Portfolio Brain's detection and response mechanisms worked. Answer each question:

| Check | Answer | Notes |
|-------|--------|-------|
| Was a health drift alert triggered? | Yes/No | If yes, when? If no, why not? |
| Was cancellation intent scored >= 0.5? | Yes/No | If yes, when? What was the score? |
| Was a playbook generated? | Yes/No | If yes, was the recommended scenario appropriate? |
| Were commitments from the playbook fulfilled? | Yes/No/N/A | Check Action Tracker and Decisions table |
| Was contact validated (no champion loss)? | Yes/No | Did the primary contact change without detection? |
| Was the account flagged in weekly sweeps? | Yes/No | Check Portfolio Dashboard history |

For every "No" answer, explain WHY the system missed it. Common failure modes:

- **Data gap**: No emails/meetings ingested during the critical period
- **Scoring gap**: Health score didn't reflect reality (missing dimensions scored at 0 but the account looked "fine")
- **Threshold gap**: Signals were present but below alerting thresholds
- **Response gap**: Alert was triggered but no action was taken
- **Timing gap**: By the time the system caught it, the decision was already made

### Step 4 — Counterfactual

Answer: **What would have needed to happen to prevent this churn?**

Construct the counterfactual scenario:

- **Trigger point**: The moment where intervention could have changed the trajectory (usually the first negative signal from Step 1)
- **Required action**: What specific action, by whom, by when
- **Probability of success**: Honest assessment — would it actually have worked?

Then classify:

- **Preventable** — A timely CSM intervention (outreach, escalation, pricing adjustment, executive engagement) could realistically have changed the outcome. The signals were there; the response was missing or late.
- **Partially preventable** — Intervention might have delayed or reduced the churn (e.g., could have negotiated a downgrade instead of full cancellation), but the underlying driver was strong.
- **Deterministic** — No CSM action would have changed this. The cause was outside Portfolio Brain's influence: EoE product, corporate M&A, org-wide vendor consolidation, hard budget elimination.

### Step 5 — Pattern Classification

Classify the churn into exactly one primary type:

| Churn Type | Definition | Typical Signals |
|-----------|-----------|-----------------|
| **Silent departure** | No warning, no escalation, just didn't renew | Low engagement, no negative signals, renewal passes quietly |
| **Slow fade** | Declining engagement over 6+ months | Gradual health score decline, decreasing email frequency, meetings cancelled |
| **Trigger event** | Single event caused departure | M&A announcement, leadership change, competitor RFP, sudden budget cut |
| **Product failure** | EoE, unresolved bugs, feature gaps | Repeated Jira tickets, product complaints, "not working" language |
| **Price rejection** | Cost couldn't be justified | Budget/value challenge language, ROI questioning, price comparison |
| **Corporate decision** | Org-wide vendor consolidation or policy change | "Corporate mandate", "standardizing on", "global policy" |

If the churn has elements of multiple types, pick the primary driver and note secondary factors.

### Step 6 — Prediction Ledger Update

Update `_Prediction_Ledger.md` with the churn outcome:

**1. Add a row to the Outcome Log:**

| Date | Customer | Product | Scenario Type | Predicted % | Predicted Value | Actual Result | Accuracy | Key Learning |
|------|----------|---------|--------------|-------------|-----------------|---------------|----------|-------------|
| [today] | [Customer] | [Product] | Renewal | [from playbook, or "---" if none] | [ARR] | Churned | [hit/miss/---] | [One-sentence key learning from this autopsy] |

**2. Update Summary Statistics:**
- Increment "Churn confirmed" count
- Recalculate hit rate if a playbook prediction existed

**3. Update Pattern Library:**
- If this churn confirms an existing pattern, add "(N=X, [customer list])" to strengthen it
- If this churn reveals a NEW pattern, add it with "(N=1, [customer])" and flag as low confidence
- If this churn contradicts an existing pattern, note the contradiction

**4. Update Signal Combination Registry:**
Build the account's signal profile at the time of churn using the 6 dimensions defined in the Prediction Ledger's "How to Build Signal Profiles" section (health trajectory, sentiment combination, status tags, engagement state, intervention state, financial profile). Check the Registry for a matching combination. If one exists, add this account and update the observed rate. If no match exists and the combination is meaningful, create a new entry.

## Autopsy Output

Save as `YYYY-MM-DD_Churn_Autopsy.md` in the customer's folder.

### Frontmatter

```yaml
---
type: outcome
customer: "Customer Name"
product: Tivian | Influitive | Lyris | QuickSilver
date: YYYY-MM-DD
result: churned
arr_lost: NNNNN
churn_type: silent-departure | slow-fade | trigger-event | product-failure | price-rejection | corporate-decision
preventable: yes | no | partial
---
```

### Body Structure

```markdown
# Churn Autopsy: [Customer Name]

**Product:** [Product]
**ARR Lost:** $[amount]
**Churn Type:** [classification]
**Preventable:** [Yes / No / Partial]
**Autopsy Date:** [date]
**Churn Confirmed:** [date confirmation was received]

## Timeline

[Table from Step 1]

## Signal Analysis

[Table from Step 2 with evidence citations]

## System Failure Check

[Table from Step 3 with explanations for each "No"]

## Counterfactual

[From Step 4 — what would have needed to happen, and the preventability assessment]

## Pattern Classification

**Primary type:** [type]
**Secondary factors:** [if any]
**Pattern match:** [Does this match or extend an existing Prediction Ledger pattern? Which one?]

## Key Learning

[One paragraph: the single most important thing Portfolio Brain should learn from this churn. What changes — in alerting thresholds, health scoring, playbook triggers, or engagement cadence — would help catch this pattern earlier next time?]

## Prediction Ledger Updates

- Outcome Log row added: [Yes/No]
- Pattern Library updated: [What was added or strengthened]
- Calibration adjustments: [Any new calibration rules, or "None"]
```

## Rules

1. **Run within 7 days of churn confirmation.** Evidence quality degrades rapidly.
2. **Always update the Prediction Ledger.** Every churn teaches something, even deterministic ones.
3. **Never blame individuals.** Focus on system gaps — what the detection, alerting, or response mechanisms missed. "Jay didn't call them" is not a finding. "The system didn't surface the account for attention during the critical window" is.
4. **Flag at-risk lookalikes.** If the churn reveals a pattern that could apply to other active accounts, list those accounts by name with a recommendation to review. Check for: same product, same churn type precursors, similar health trajectory, similar engagement pattern.
5. **Link back to the intelligence summary.** After creating the autopsy file, update the customer's `_intelligence_summary.md`:
   - Set `health_score: 0` and `health_band: Churned`
   - Add a final Health History row with Trigger: "Churn confirmed"
   - Add a `## Churn Autopsy` section linking to the autopsy file
   - Update Graph Connections to reflect churned status
6. **Preserve the customer folder.** Never delete a churned customer's folder. The data is the training set for future pattern recognition.

## Cross-Referencing Other Skills

- **health.md** — Cancellation-intent categories used in Step 2; health scoring used to validate Step 3
- **alerting.md** — If the autopsy reveals a gap in alert conditions, note it as a recommendation for updating alerting thresholds
- **playbook.md** — If a playbook existed, evaluate its scenario accuracy in Step 4; outcome feeds the Prediction Ledger per playbook.md's feedback loop
- **ingestion.md** — If the system failure was a data gap (Step 3), note whether ingestion cadence or coverage needs adjustment
