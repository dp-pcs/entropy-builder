# Portfolio Brain Skill: Post-Meeting Debrief

Turns a meeting transcript into a full intelligence update in one pass. Use after any customer meeting — when a Read.ai transcript lands, when Jay says "debrief [Customer]", "process the [Customer] meeting", or "what came out of the call with [Customer]".

**Design principle:** Extract everything actionable from the transcript, update the intelligence file, and assess whether the current strategy still holds — all in a single operation. This is Tier 2+ processing with strategic overlay.

## What to Load

1. The transcript file (full read — this is the primary input)
2. `_intelligence_summary.md` for this customer (full read — you'll be updating it)
3. Active playbook if one exists (most recent `*_Playbook.md`) — read Recommended Approach + Success Metrics sections only
4. `_skills/health.md` — for cancellation-intent scoring weights and contact field definitions

Do NOT load: Company-Rules, Prediction Ledger, vault MOCs, other customers, pattern reports. Those are for playbook generation, not debriefing.

## Debrief Process (8 Steps)

### Step 1: Participant Classification

Classify every participant using the role classification rules:

| Domain Pattern | Classification |
|---------------|---------------|
| Customer's known domain | **Customer** |
| @trilogy.com, @aurea.com, @skyvera.com | **Internal** |
| @shi.com, @carahsoft.com, @tekservinc.com, @softwareone.com, @penril.net, @bechtle.com | **Reseller** |
| Any other domain | **External** |

For each customer participant, check against the `## Key Contacts` table:
- **Known contact** → Note their current Role, Stance, Influence for context.
- **New contact** → Flag for addition. Estimate Role from title/context, set Stance: Unknown, estimate Influence from title.

### Step 2: Decision Extraction

Scan the transcript for commitment language. Look for:
- "agreed to", "will send", "committed to", "by [date]", "action item", "next step", "follow up with", "let's plan to", "I'll make sure", "we need to", "can you", "I'll have [someone]"

For each decision found, classify:

| Field | How to Determine |
|-------|-----------------|
| **Decision** | The specific commitment in plain language |
| **Owner** | Jay, Customer, Internal (name), or Mutual — based on who made the commitment |
| **Due Date** | Explicit date if stated, otherwise estimate from context ("next week" = +7d, "end of month", etc.), or "TBD" |
| **Status** | Open |
| **Source** | Link to this transcript file |

### Step 3: Sentiment & Intent Scoring

Assess the overall tone and score for cancellation intent using the weights from `_skills/health.md`:

| Category | Weight | Look For |
|----------|--------|---------|
| Explicit cancellation | 1.0 | "cancel", "terminate", "end the contract" |
| Competitor evaluation | 0.8 | Alternative vendors mentioned, comparison language |
| Budget/value challenge | 0.7 | Cost concerns, ROI questioning, budget pressure |
| Escalation language | 0.6 | "unacceptable", frustration, threats to escalate |
| Disengagement signals | 0.5 | Low usage admission, deprioritization language |
| Frustration accumulation | 0.4 | Repeated complaints, unresolved issue references |

Also scan for **positive signals**:
- Expansion language: team growth, new use cases, feature requests, integration interest
- Satisfaction markers: praise, success stories, referral willingness, future planning language
- Deepening engagement: requesting more training, asking about advanced features, introducing new stakeholders

### Step 4: Contact Intelligence Update

For each customer participant, determine if any Key Contacts fields should change:

- **Stance shift**: Did their language reveal advocacy, neutrality, frustration, or blocking behavior? Only update if evidence is clear — a single mildly negative comment isn't a stance shift.
- **Influence reassessment**: Did they demonstrate decision-making authority, budget control, or deference to someone else?
- **Last Engaged**: Update to the meeting date.
- **New relationship dynamics**: Did contacts reference each other in ways that reveal reporting lines, alliances, or tensions?

### Step 5: Framework Surfacing

Based on what the transcript revealed, check whether a vault framework applies to the customer's current situation. This turns the debrief from "here's what happened" into "here's what happened and here's a lens for what to do next."

Load `Khalife Second Brain/MOCs/Customer-Intelligence-MOC.md` ONLY when a trigger matches — not on every debrief.

| Signal From Transcript | Framework to Surface |
|-----------------------|---------------------|
| Customer expressed frustration with support quality | [[Crucial Conversations]] — STATE method to rebuild trust |
| Customer mentioned evaluating competitors or received an RFP | [[MEDDICC Framework]] — identify Champion and Economic Buyer immediately |
| Customer pushed back on pricing or questioned ROI | [[Diagnostic-Funnel]] — diagnose why they perceive low value before defending the price |
| Customer described a support failure that was well-recovered | [[Service-Recovery-Paradox]] — this is a loyalty-building moment, lean into it |
| New executive joined the call or was referenced | [[Essential Account Planning]] — map the power structure shift |
| Customer's tone was adversarial or escalatory | [[Tactical Empathy]] — label the emotion before addressing the substance |
| Customer raised expansion topics unprompted | [[The Expansion Sale]] — they opened the door, now use "Why Stay" / "Why Grow" framing |
| Low engagement admitted by customer | [[Flip the Funnel]] → [[Behavior-Design]] — reactivation before retention |

**Output format:** Add to the debrief output after PLAYBOOK STATUS:

```
FRAMEWORK:
[[Framework Name]] — [One sentence: what this framework says about the situation revealed in this meeting.]
```

If no trigger matches, omit the section. If multiple match, surface the most strategically important one (max 2).

### Step 7: Playbook Alignment Check

If an active playbook exists, compare what happened in the meeting against the playbook's expectations:

- **On track**: The conversation followed the playbook's predicted path. The recommended approach is working. Note which success metrics were met.
- **Deviation — positive**: Something better than expected happened (e.g., customer brought up expansion unprompted, new champion emerged). Note the upside and whether the playbook should be updated to capitalize.
- **Deviation — negative**: Something the playbook didn't anticipate (e.g., new blocker emerged, budget was cut, champion was less supportive than expected). Check if any exit criteria have been triggered.
- **No playbook**: Skip this step. If the meeting reveals concerning signals, recommend generating one.

### Step 8: Intelligence Summary Update

Apply all findings to the customer's `_intelligence_summary.md`:

1. **Key Contacts table** — Update `Last Engaged` dates, add new contacts, update Stance/Influence if evidence supports it.
2. **Decisions table** — Append all extracted decisions.
3. **Cancellation Intent section** — Add entry if score ≥ 0.5.
4. **Expansion Signals section** — Add entry if positive signals detected.
5. **Health History** — Recalculate and append a row if the score changed. Trigger: "Debrief [date]".
6. **Graph Connections** — Update if sentiment nodes or pain point nodes should change.

## Debrief Output Template

After updating the intelligence summary, respond to Jay with this structure:

```
DEBRIEF: [Customer Name] — [Meeting Date]
Attendees: [names + roles]

KEY TAKEAWAYS:
[3-5 bullet points capturing the most important things that happened. Lead with what matters most — decisions, risks, opportunities. Not a transcript summary.]

DECISIONS LOGGED:
[Table of decisions extracted, or "No explicit commitments made."]
| Decision | Owner | Due Date |

SENTIMENT READ:
[1-2 sentences on overall tone. Include cancellation-intent score if ≥ 0.3, even below the alert threshold — Jay should know early.]

CONTACT UPDATES:
[Any stance shifts, new contacts added, or relationship dynamics observed. "No changes" if nothing shifted.]

PLAYBOOK STATUS:
[On track / Positive deviation / Negative deviation / No playbook exists]
[1-2 sentences explaining why, referencing specific playbook phases or success metrics.]

RECOMMENDED NEXT STEPS:
[2-3 specific actions Jay should take based on this meeting, with suggested timelines. These should be concrete — "Send the pricing proposal by Friday" not "Follow up soon."]
```

## Transcript File Creation

If the transcript doesn't already have an .md file in the customer's `Transcripts/` folder, create one:

**Filename:** `YYYY-MM-DD_Meeting_Title.md`

**YAML frontmatter:**
```yaml
---
type: transcript
customer: "Exact Customer Name"
product: Tivian | Influitive | Lyris | QuickSilver
date: YYYY-MM-DD
participants: [Name1, Name2, Name3]
source: Read.ai
---
```

**Body:** Include a `## Summary` section with the key takeaways, a `## Decisions` section mirroring what was logged in the intelligence summary, and a `## Raw Notes` section with relevant excerpts (not the full transcript — keep it to the substantive portions).

## Edge Cases

- **Multiple customers on the same call** → Debrief each customer separately. Create/update intelligence summaries for each. Decisions may be shared but log them in both.
- **Internal-only meeting discussing a customer** → Still debrief. Classify as internal intelligence. Update the intelligence summary but don't update contact `Last Engaged` dates (the customer wasn't present).
- **Meeting with no clear decisions** → That's a signal in itself. Note "No commitments made" and flag if this is part of a pattern of unproductive engagement.
- **Transcript is low quality or incomplete** → Note the data quality issue. Extract what you can. Don't fabricate details to fill gaps.
