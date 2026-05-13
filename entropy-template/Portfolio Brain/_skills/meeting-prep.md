---
type: skill
title: "Meeting Prep"
triggers:
  - "prep me for [Customer] call"
  - "meeting prep for [Customer]"
  - "I have a call with [Customer]"
  - "brief me before [Customer] meeting"
  - "what do I need to know for [Customer]?"
---

# Portfolio Brain Skill: Meeting Prep

Generates a structured pre-call brief when Jay has an upcoming meeting with a customer. Use when Jay says "prep me for [Customer]", "I have a call with [Customer]", or "brief me before the [Customer] meeting."

**Design principle:** By the time Jay joins a call, he should know: who's in the room, what was said last time, what he owes them, what they owe him, what's changed since the last touchpoint, and what he should steer the conversation toward. This brief takes 60 seconds to read and replaces 15 minutes of file-hopping.

**This is NOT pressure-test.** Pressure-test simulates objections for high-stakes situations. Meeting prep aggregates context for ANY meeting — routine check-ins, renewal discussions, escalation calls, onboarding sessions.

## Pre-Brief Data Collection

Read these in order. Stop early if the meeting is a routine check-in and lower sections aren't relevant.

| # | Source | What to Extract |
|---|--------|----------------|
| 1 | Customer's `_intelligence_summary.md` | Health score, band, trajectory, segment, ARR, renewal date, status, all sentiments, key contacts (names, roles, stances, last engaged dates), pain points, expansion signals |
| 2 | Last 3 files in `Emails/` + `Transcripts/` (by date, most recent first) | What was discussed, what was promised, what tone was used, any unresolved threads |
| 3 | `_Action_Tracker.md` (grep for customer) | Open commitments — split into: what Jay owes them, what they owe Jay, what team members owe them |
| 4 | Active playbook (most recent `*_Playbook.md`) | Current phase, selected scenario, exit criteria, what the strategy says to do next. **Only if a playbook exists.** |
| 5 | `## Contact Personas` in intelligence summary | Behavioral profiles for each known attendee — decision style, communication style, risk tolerance, motivators |
| 6 | `## Playbook Execution` in intelligence summary | Phase status, whether deadlines are approaching or passed. **Only if execution tracking is active.** |
| 7 | Competitor hub nodes (if customer appears in any `_nodes/Competitors/*.md`) | Which competitors have been mentioned, what positioning worked or failed |

**If Jay names specific attendees:** Match them against the Key Contacts table. If an attendee isn't in the table, flag it — this is either a new stakeholder (opportunity to build the relationship map) or someone from a department Jay hasn't engaged before.

## Brief Output Format

```
PRE-CALL BRIEF: [Customer Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Product: [Product] | ARR: $[X] | Status: [status tags]
Health: [score] [band emoji] [trajectory direction] | Confidence: [high/med/low]
Renewal: [date] ([N] days away)
Segment: [segment]

WHO'S IN THE ROOM
─────────────────
[For each known attendee:]
• [Name] — [Title] | [Stance: Champion/Neutral/Detractor/Unknown]
  Style: [communication style] | Decides by: [decision style]
  Last engaged: [date] ([N] days ago)
  [One line: what they care about most, from persona or prior interactions]

[If attendee not in Key Contacts:]
• [Name] — ⚠️ NEW CONTACT — not in Key Contacts table. Opportunity to map.

WHAT HAPPENED LAST TIME
───────────────────────
[Date] — [Type: Call/Email] — [1-2 sentence summary]
[Date] — [Type] — [1-2 sentence summary]
[Date] — [Type] — [1-2 sentence summary]

OPEN COMMITMENTS
────────────────
You owe them:
• [Action] — due [date] [OVERDUE X days / due in X days]
• [Action] — due [date]

They owe you:
• [Contact]: [Action] — waiting [N] days

Team owes them:
• [Owner]: [Action] — [status]

[If no commitments: "Clean slate — no open items."]

STRATEGIC CONTEXT
─────────────────
Sentiments: Product [P] | Support [S] | Renewal [R]
Pain Points: [from intelligence summary, if any]
Expansion Signals: [if any logged]
Competitive Pressure: [competitor name + context, or "None detected"]
Playbook: [Active — Phase X: description / No active playbook / Stale — last updated N days ago]

TALKING POINTS (Raise These)
────────────────────────────
1. [Based on open commitments: deliver on promises first]
2. [Based on last interaction: follow up on unresolved topics]
3. [Based on playbook phase: what the strategy says to advance]
4. [Based on expansion signals or health trajectory: proactive topic]

LANDMINES (Avoid These)
────────────────────────
• [Topics that will trigger resistance, based on sentiment/persona/history]
• [Promises you can't keep — check Company-Rules if pricing-adjacent]
• [Overdue commitments from other team members that the customer might raise]

LISTEN FOR
──────────
• [Signals that health is improving/declining]
• [Competitor mentions or evaluation language]
• [Stakeholder changes or org restructuring hints]
• [Budget/procurement timing signals if renewal is approaching]
```

## Scenario-Specific Adjustments

### Routine Check-In (biweekly/monthly cadence)

Keep the brief short. Focus on: last interaction summary, open commitments, and one proactive talking point. Skip strategic context unless something has changed. The goal is a 30-second scan, not a deep dive.

### Renewal Discussion

**Load `Company-Rules.md` before generating.** Add a section:

```
RENEWAL CONTEXT
───────────────
Current term: [months] | Current ARR: $[X]
Floor price: [if applicable — DO NOT include in customer-facing notes]
Multi-year eligible: [Yes/No — check 180-day rule]
Price sensitivity: [from persona or prior interactions]
Pricing approach: [value-led / hold-the-line / concession-ready — from playbook]
```

Never include internal pricing thresholds, floor prices, or CEO-approval pathways in the brief if there's any chance the screen is shared.

### Escalation Call

Lead with: what went wrong, what the customer's emotional state is, what they've been promised so far, and what you can actually deliver. Add:

```
ESCALATION CONTEXT
──────────────────
Trigger: [what caused the escalation]
Customer's stated position: [from their last email/call]
Promises already made: [careful — don't re-promise what someone already committed]
What you CAN offer: [within Company-Rules bounds]
What you CANNOT offer: [flag anything the customer might ask for that's off-limits]
```

### First Meeting / New Relationship

If no prior interactions exist in the vault, the brief is lighter:

```
FIRST MEETING BRIEF: [Customer Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Product: [Product] | ARR: $[X] | Status: [status tags]
Health: [score] [band] | Confidence: [likely low]
Renewal: [date]

WHAT WE KNOW
─────────────
[From intelligence summary: Notion data, any firmographic info]
[From Fionn: financial history, discovery status]

WHAT WE DON'T KNOW
───────────────────
[List gaps: no transcripts, no email history, no contact personas]
[Recommend: take notes on communication style, decision patterns, motivators]

SUGGESTED APPROACH
──────────────────
[Based on product, ARR, status — generic but grounded in Company-Rules and product knowledge]
```

## Framework Surfacing

Check if the meeting context matches a framework trigger (same patterns as triage.md and debrief.md):

| Meeting Context | Framework | How It Shapes Prep |
|----------------|-----------|-------------------|
| Re-engagement after 30d+ silence | [[Accusation-Audit]] | Prep an opening that acknowledges the gap |
| Customer raised competitor in last interaction | [[Framing-Effect]] | Prep value framing before they anchor on competitor pricing |
| Escalation call after support failure | [[Service-Recovery-Paradox]] | Prep an over-delivery response |
| Renewal discussion with analytical contact | [[Ethos-Logos-Pathos]] | Prep data-first positioning |
| Multiple stakeholders with conflicting stances | [[Crucial Conversations]] | Prep STATE method, identify the shared goal |

Only load Customer-Intelligence-MOC when a trigger matches. Note the framework in the brief under `TALKING POINTS` as a lens, not a script.

## Post-Meeting Handoff

After the meeting, the debrief skill takes over. Meeting prep feeds forward into debrief in two ways:

1. **Talking points not raised:** If the brief recommended raising a topic and it didn't come up, the debrief should flag it as "still unaddressed — carry forward."
2. **New contacts discovered:** If an attendee was flagged as "NEW CONTACT" and Jay learned their role/style in the meeting, the debrief should populate the Key Contacts table.

## Rules

1. **Output is conversational only.** Do not save the brief as a file. Jay reads it, joins the call, and the debrief skill captures what happened afterward.
2. **One brief per meeting.** If Jay has back-to-back calls with different customers, generate separate briefs.
3. **Never fabricate interaction history.** If there are no prior emails or transcripts, say so. Don't invent "last time you discussed X."
4. **Respect the 60-second rule.** The brief should be scannable in under a minute. If it's too long, cut the Strategic Context and Landmines sections for routine check-ins.
5. **Flag stale data.** If `last_verified` is 60+ days old, note it at the top: "Intelligence data is [N] days stale — verify key assumptions in the call."
6. **If a playbook exists, align talking points with the current phase.** Don't recommend actions that contradict the playbook strategy. If Jay wants to deviate, that's his call — but the brief should reflect the strategy, not freelance.

## Integration Points

### With `triage.md`
Triage gives a quick status snapshot. Meeting prep builds on triage but adds: attendee profiles, interaction history, commitment status, and tactical recommendations. If Jay asks "what's going on with [Customer]?" — that's triage. If Jay asks "prep me for [Customer] call" — that's this skill.

### With `pressure-test.md`
For high-stakes meetings (ARR > $50K, renewal within 90 days, or active escalation), recommend running pressure-test AFTER the meeting prep brief. Meeting prep tells Jay what to expect; pressure-test stress-tests his approach against the contact's likely pushback.

### With `debrief.md`
Meeting prep → meeting → debrief is the full meeting lifecycle. The brief sets expectations; the debrief captures what actually happened. Together they create a feedback loop on meeting preparation quality.

### With `email-draft.md`
If the brief surfaces overdue commitments that should be delivered before the meeting (e.g., "you promised to send X last week"), recommend drafting and sending that email BEFORE the call. Walking into a meeting with an unfulfilled promise is worse than sending it 30 minutes before.
