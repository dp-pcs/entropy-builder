# Portfolio Brain Skill: Pressure Test

Load this file before any high-stakes customer outreach on accounts with ARR > $50K. Also useful for win-back attempts, difficult renewals, and any account where the outcome is uncertain and the contact has a known behavioral profile.

## Purpose

Simulate the customer's most likely pushback before Jay engages. The goal is to surface objections he hasn't prepared for, test his positioning under pressure, and identify where his approach is weakest — before the real conversation.

## When to Use

- **Pre-playbook execution**: After a playbook is generated but before the first outreach
- **Pre-call preparation**: Before any renewal, win-back, or escalation call
- **Email stress-testing**: Before sending high-stakes emails (save offers, pricing discussions, re-engagement)
- **Win-back triage**: To simulate which Active+Cancelled accounts are most saveable

## Pre-Read Checklist

1. The customer's `_intelligence_summary.md` — full context
2. `## Contact Personas` section (if populated) — behavioral profile of the contact you're engaging
3. Any relevant playbook — the approach being tested
4. `Portfolio Brain/Company-Rules.md` — what you can and can't offer
5. Recent emails/transcripts — the customer's actual words and tone

## Simulation Protocol

### Step 1: Build the Persona

Construct the contact's simulation profile from available data:

```
PERSONA BRIEF
─────────────
Name: [Contact name]
Role: [Title + organizational authority]
Account: [Customer] | ARR: [$X] | Status: [Active/Cancelled/etc.]

Behavioral Profile:
- Decision Style: [analytical | consensus | authority | relationship-driven]
- Risk Tolerance: [low | medium | high]
- Price Sensitivity: [low | medium | high]
- Communication Style: [formal | direct | technical | collaborative]
- Engagement Velocity: [fast | moderate | slow]
- Primary Motivators: [what drives their decisions]
- Known Objection Patterns: [from prior interactions]

Current State:
- Last engaged: [date]
- Current sentiment: [from intelligence summary]
- Known pain points: [from transcripts/emails]
- Open commitments: [from action tracker]
- Churn drivers: [if applicable]
```

If the `## Contact Personas` section exists in the intelligence summary, pull behavioral dimensions from there. If not, infer from available transcripts, emails, and engagement patterns — but flag inferences as low-confidence.

### Step 2: Run the Simulation

Adopt the persona and respond to Jay's proposed approach as the customer would. Follow these rules:

1. **Use the customer's actual language patterns** from transcripts and emails where available
2. **Lead with their known concerns** — don't invent objections, surface ones grounded in evidence
3. **Escalate realistically** — if the customer has a history of escalating to finance/legal, simulate that
4. **Test pricing reactions** — if Jay is proposing a price, react based on the customer's price sensitivity and prior pricing history
5. **Surface hidden blockers** — stakeholders who aren't in the room but hold veto power (finance, legal, procurement)
6. **Model organizational dynamics** — if multiple contacts exist, simulate how the proposal flows through the org

### Step 3: Debrief Output

After simulation, produce a structured debrief:

```markdown
## Red-Team Debrief: [Customer Name]

### Simulation Summary
**Contact simulated:** [Name]
**Approach tested:** [1-sentence description of Jay's proposed approach]
**Persona confidence:** [High/Medium/Low] — based on available behavioral data

### Anticipated Objections (ranked by likelihood)

| # | Objection | Likelihood | Evidence | Suggested Counter |
|---|-----------|-----------|----------|-------------------|
| 1 | [Objection] | High/Med/Low | [What data supports this] | [How to handle it] |

### Hidden Risks
- [Risks not obvious from the playbook — org dynamics, timing, competitor pressure, etc.]

### Approach Vulnerabilities
- [Where Jay's positioning is weakest]
- [What assumption, if wrong, breaks the whole strategy]

### Recommended Adjustments
- [Specific changes to the approach based on simulation findings]

### Pre-Call Prep Notes
- **Open with:** [Recommended opening based on persona]
- **Avoid:** [Topics/framings that will trigger resistance]
- **Listen for:** [Signals that indicate which way the conversation is going]
- **Pivot if:** [Trigger → alternative approach]
```

## Multi-Stakeholder Simulation

For accounts with 3+ contacts, simulate the internal dynamics:

1. **Map the influence chain**: Who talks to whom? Who has veto power?
2. **Simulate the handoff**: If Jay convinces Contact A, how does A present it to Contact B?
3. **Identify the blocker path**: Which stakeholder is most likely to kill the deal, and through what mechanism?
4. **Test the champion**: If there's an internal advocate, how strong is their political capital? Will they spend it on this?

## Integration with Playbooks

When a playbook exists, the pressure-test simulation should:
1. Test each scenario against the persona (not just the recommended one)
2. Identify which scenario the customer is most likely to accept
3. Flag scenarios that will trigger immediate resistance
4. Suggest scenario sequencing (which to propose first, which to hold in reserve)

## Quality Gates

- **Never simulate without evidence.** If there's no transcript, no email history, and no engagement data — say so. A simulation built on nothing is worse than no simulation.
- **Flag inference vs. observation.** Behavioral dimensions extracted from transcripts are observations. Dimensions inferred from role/title alone are guesses. Label them differently.
- **Don't over-rotate on simulation results.** This is preparation, not prediction. The real conversation will diverge. The value is in forcing Jay to think through objections he hasn't considered.
