# Entropy Skill: Playbook Generation

Load this file before generating any customer playbook, win-back strategy, expansion plan, or renewal scenario. Also load when recording prediction outcomes.

## Pre-Read Checklist (mandatory before generating)

1. `Entropy/Company-Rules.md` — pricing, contract terms, compliance checklist
2. `Entropy/_Prediction_Ledger.md` — calibrate scenario probabilities from historical patterns
3. `Khalife Second Brain/MOCs/Customer-Intelligence-MOC.md` — map vault frameworks to this customer's situation (lives outside Entropy)
4. `Khalife Second Brain/Jay-Profile.md` — calibrate coaching notes to Jay's psychological profile (lives outside Entropy)
5. The customer's `_intelligence_summary.md` — current state, contacts, health, graph connections

**Sequence:** Company-Rules → Prediction Ledger → Customer Data → Playbook Generation.

## Playbook Versioning

Every playbook is timestamped and **never overwritten**. Old playbooks are preserved as historical records.

**Naming:** `YYYY-MM-DD_Renewal_Playbook.md` (or `_Winback_Playbook.md`, `_Expansion_Playbook.md`)

**Location:** Inside the customer's folder, alongside `_intelligence_summary.md`. NEVER save copies to `Khalife Second Brain/outputs/` or the vault root.

```
CustomerName/
├── _intelligence_summary.md           ← always links to the latest playbook
├── 2026-04-09_Renewal_Playbook.md     ← v1 (historical)
├── 2026-06-15_Renewal_Playbook.md     ← v2 (current)
├── 2026-06-15_Outcome.md              ← feedback on v1's predictions
```

**Rules:**
- When a customer already has a playbook, create a NEW file with today's date.
- Update `_intelligence_summary.md` → `## Current Playbook` section to link to the latest.
- Previous playbook remains untouched.

### Plan File Storage

Every playbook gets a companion plan file that preserves the strategic reasoning, data sources consulted, frameworks considered, and why certain approaches were chosen or rejected. This is the thinking behind the playbook — not just the output.

**Naming:** `YYYY-MM-DD_Renewal_Playbook_Plan.md` (same date prefix as the playbook)

**Why this matters:** When a similar account profile appears later (same ARR range, same risk signals, same industry), the plan file lets you start at 80% instead of zero. The playbook tells you *what to do*; the plan tells you *why this approach was chosen over alternatives*.

**What to include:**
1. **Data Sources Consulted** — Which files were read, which MCP tools were called, what data was available vs missing.
2. **Frameworks Considered** — Which vault frameworks were evaluated and why each was selected or rejected for this situation.
3. **Scenario Reasoning** — Why each scenario was modeled, what assumptions drove the probability estimates, what would change the calculus.
4. **Rejected Approaches** — Strategies that were considered but not recommended, and why. These are valuable for similar-but-different future accounts.
5. **Confidence Notes** — Where the analysis feels solid vs. where it's built on thin data or assumptions.

**YAML frontmatter:** See `_analytics/schemas.md` for the playbook-plan schema.

Do NOT summarize plan files — future sessions should be able to build on them in their entirety.

## Playbook Template

Only include sections when real data supports them. Never shoehorn components for completeness. **If there's no data to populate a section, don't include it.**

### Always Included (Core Sections)

1. **Situation Assessment** — What the data says, and the real problem underneath. Draws from emails, transcripts, Jira, and intelligence summary.

2. **Key Contacts** — Names, roles, last engagement date. If sufficient interaction data exists, upgrade to a **Stakeholder Power Map** showing budget authority, influence lines, advocate/neutral/blocker stance. If the data isn't there, just list contacts — don't guess.

3. **Strategic Frame** — Why standard approaches will fail for this customer, and what the right frame is. Apply vault frameworks (Chris Voss, MEDDICC, Crucial Conversations, Expansion Sale "Why Stay" / "Why Forgive") where they genuinely add strategic value.

4. **Scenario Simulations** — 2-3 scenarios, each with:
   - Framework(s) applied
   - Phased execution plan
   - Probability of success (calibrated against Prediction Ledger patterns)
   - Expected pricing outcome (per Company-Rules)
   - Expected contract term
   - Expected value calculation
   - Risk/upside assessment
   - Company-Rules compliance confirmation

5. **Recommended Approach** — Which scenario (or hybrid) to execute, with phase-by-phase tactical timeline and specific action items.

6. **Financial Modeling** — Side-by-side scenario comparison:
   | Scenario | Probability | Year 1 ARR | Contract Term | Total Expected Value | Notes |
   Includes: annual renewal compounding, multi-year lock-in savings, churn + win-back expected value.

7. **Success Metrics & Exit Criteria** — Per phase:
   - What measurable outcome signals the phase is working
   - What triggers switching to an alternative scenario
   - What timeline constitutes "too late"

8. **Risk Register** — Table: Risk | Probability | Impact | Mitigation.

9. **Jay-Specific Coaching Notes** — Calibrated through [[Jay-Profile]]. Where Jay's instincts serve him, where his growth edges are, and what to resist.

10. **Sources** — Vault frameworks, models, books, customer data files, Company-Rules compliance notes.

### Included Only When Data Supports It

- **Customer Health Scorecard** — Engagement frequency, ticket volume/trend, usage indicators, payment history, NPS/CSAT. Only when data can be pulled from real sources. Do not fabricate.
- **Stakeholder Power Map** — Budget authority, influence lines, stance, relationships. Only when multiple emails/meetings/transcripts support mapping these dynamics.
- **Post-Renewal Plan** — First 90 days after closing. Include for HVO accounts and accounts where post-renewal relationship is critical.
- **Black Swan Hunt** — Hidden factors that could redefine the engagement. Include when genuine unknowns exist (post-acquisition, stakeholder shifts, competitive threats). Skip for straightforward situations.
- **MEDDICC Qualification** — Full scoring table. Include for complex, multi-stakeholder, or unqualified deals. Skip for straightforward renewals.

## Prediction Feedback Loop

### Outcome Files

When Jay provides feedback on a playbook's execution, create an Outcome file.

**Filename:** `YYYY-MM-DD_Outcome.md` (dated to when outcome is recorded).

**YAML frontmatter:**
```yaml
---
type: outcome
customer: "Exact Customer Name"
product: Tivian | Influitive | Lyris | QuickSilver
playbook_ref: "YYYY-MM-DD_Renewal_Playbook.md"
scenario_selected: "Scenario N: Name"
date_resolved: YYYY-MM-DD
result: renewed | churned | downgraded | expanded | pending
---
```

**Body structure:**
```markdown
# Outcome: [Customer Name]

## What Was Predicted
[Pull from the selected scenario: probability, expected pricing, term, expected value, timeline]

## What Actually Happened
[Jay's feedback: real outcome, actual pricing, actual term, what worked, what didn't]

## Delta Analysis
- Was probability over/under-estimated? By how much?
- Did a Black Swan materialize? Was it identified or missed?
- Did the stakeholder landscape shift as anticipated?
- Did the chosen framework/approach work as expected?
- What would the agent do differently next time?

## Pattern Tags
- scenario_type: accusation_audit | executive_reset | multi_year_lockin | value_reinforcement | etc.
- customer_profile: hvo | non_hvo | at_risk | floor_price
- outcome_accuracy: hit | partial_hit | miss
- key_factor: [what most influenced the outcome]
```

### Prediction Ledger

**File:** `Entropy/_Prediction_Ledger.md` — aggregates all prediction-vs-outcome records.

**Structure:**
```markdown
# Prediction Ledger

## Summary Statistics
- Total predictions tracked: N
- Hit rate: X%
- Partial hit rate: X%
- Miss rate: X%
- Average probability calibration error: ±X%

## Outcome Log
| Date | Customer | Product | Scenario Type | Predicted % | Actual Result | Accuracy | Key Learning |

## Pattern Library
### Scenario Patterns
[e.g., "Accusation Audit works best when: silence < 60 days, historical relationship exists"]

### Calibration Adjustments
[e.g., "For at-risk HVOs with 25%+ price increases, reduce base renewal probability by 10%"]

### Black Swan Frequency
[Track which Black Swans materialized vs. identified]
```

**Feedback loop in practice:**
1. Playbook generated with scenario probabilities.
2. Jay selects and executes a scenario.
3. Jay reports what happened.
4. Agent creates Outcome file in customer folder.
5. Agent updates Prediction Ledger.
6. Future playbooks MUST read the Ledger first and cite specific patterns when they influence predictions.

## Second Brain Integration

**Bridge file:** [[Customer-Intelligence-MOC]]
**Jay's profile:** [[Jay-Profile]]
**Key MOCs:**
- [[Sales-Playbook-MOC]] — renewals, pricing, champion building
- [[Leadership-and-Management-MOC]] — team dynamics, executive engagement
- [[Communication-Mastery-MOC]] — customer communication, escalation handling
- [[Decision-Making-Toolkit-MOC]] — portfolio prioritization, risk assessment
- [[Strategy-and-Power-MOC]] — competitive positioning, long-term strategy

When analyzing a customer situation, always check if a vault framework or mental model applies. Customer data = *what's happening*; vault = *what to do about it*.

## Company Rules Quick Reference

- **Pricing:** 25% (Standard) / 45% (Platinum) — non-negotiable
- **Terms:** 1-year, 3-year, or 5-year only
- **Revenue opportunities:** PS, license upsells, Standard→Platinum, multi-year extension
- **180-day rule:** Multi-year extensions only available >180 days from renewal
- **Redline rules:** Only reactive, only for >$100K ARR, never proactively disclosed
- **Win-back rules:** Flat renewals and free Platinum require CEO approval
- **Margin targets:** 80% software, 65% services
- **Compliance:** Every playbook must pass the 10-point compliance checklist in Section 8 of [[Company-Rules]]. Flag violations with `⚠️ NON-COMPLIANT`.
