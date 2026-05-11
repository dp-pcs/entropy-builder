---
type: skill
title: "Email Drafting"
triggers:
  - "draft email for [Customer]"
  - "help me write the [action item] email"
  - "write the follow-up to [Customer]"
  - "email [Customer] about [topic]"
  - Action Tracker follow-up (co-loaded with commitment-extraction.md)
  - playbook action step requiring outbound email
---

# Entropy Skill: Email Drafting

Generates ready-to-send email drafts from Action Tracker commitments, customer intelligence, and vault frameworks — calibrated to Jay's communication style and the recipient's expectations. Use when Jay says "draft email for [Customer]", "help me write the [action item] email", "write the follow-up to [Customer]", or when a playbook action step calls for outbound email.

**Design principle:** Every email Jay sends either builds trust or erodes it. Drafts must reflect what the intelligence file says about this relationship — not generic business email. Match the customer's formality, reference real history, and never promise what Company-Rules doesn't allow.

## Pre-Draft Checklist

Read these before writing a single word. Order matters.

| # | File | Why | What to Extract |
|---|------|-----|----------------|
| 1 | Customer's `_intelligence_summary.md` | Relationship context | Tone, communication style, recent activity, pain points, health score, key contacts (name + role + stance), sentiment, last engaged date |
| 2 | Relevant prior emails in `Emails/` | Thread continuity | Reply style, formality level, how the customer signs off, any open threads on this topic, what was last said and by whom |
| 3 | `_Action_Tracker.md` (grep for customer) | Commitment context | What was committed, to whom, when it was due, whether it's overdue, source of the commitment |
| 4 | `Company-Rules.md` | Compliance | **Only if** the email involves pricing, terms, discounts, contract changes, or any commercial commitment. Skip for routine follow-ups. |
| 5 | Active playbook (most recent `*_Playbook.md`) | Strategic alignment | **Only if** this email is a playbook action step. Read the Recommended Approach + current phase to ensure the email aligns with the strategy. |

**Contact validation:** Check the recipient's `Last Engaged` date in the Key Contacts table. If >180 days, flag it:
> "Heads up: [Contact Name] hasn't been engaged in [N] days. Email address may be stale. Verify before sending."

## Email Structure Framework

### Subject Line

- **Continuing a thread:** Match the existing subject. Don't rename threads mid-conversation.
- **New thread:** Short + specific. Lead with the customer's interest or the deliverable. No filler words.
  - Good: "Survey deployment timeline for Q3"
  - Bad: "Quick follow-up" / "Touching base" / "Checking in"
- **Overdue commitment:** Name the thing. "API documentation — delayed, new ETA Friday"

### Opening

No "I hope this finds you well." No "I hope you're having a great week." Never.

Match the customer's formality level from prior emails:

| Customer Style | Opening Approach |
|---------------|-----------------|
| Formal / corporate | Direct but professional. "Following up on our April 15th discussion regarding..." |
| Casual / first-name basis | Conversational. "Wanted to get back to you on the migration timeline." |
| Terse / busy executive | Skip the opening entirely. Lead with the point. |

If following up on a commitment: lead with what you promised and what you're delivering. Don't bury the lede.

### Body

- **One topic per email.** If there are multiple topics, send multiple emails or use clearly separated bullets with bold headers.
- **Lead with the customer's interest, not ours.** Frame everything from their perspective. Not "We'd like to schedule a review" but "To make sure you're getting full value from the platform, here's what I'd suggest."
- **If delivering something:** Attach or link it immediately after the first sentence. Don't make them read three paragraphs to find the deliverable.
- **If requesting something:** Be specific about what you need, in what format, and by when.
- **Keep it short.** If the body exceeds 150 words, cut it. Executives don't read walls of text.

### Call to Action

One clear next step. Not two. Not "let me know your thoughts." Make it easy to say yes.

| Scenario | CTA Pattern |
|---------|-------------|
| Scheduling | "Does Thursday at 2pm ET work? If not, here are two other slots: [X], [Y]." |
| Decision needed | "If this looks good, I'll go ahead and [next action]. Just confirm and I'll get it moving." |
| Information needed | "Could you send me [specific thing] by [date]? That'll let me [what it unblocks]." |
| FYI / no action needed | "No action needed on your end — just wanted to keep you in the loop." (Say it explicitly.) |

Always include a specific date or timeframe. "Soon" and "when you get a chance" are not deadlines.

### Closing

Match the customer's sign-off style from prior emails. If no prior emails exist, default based on region and formality:

| Context | Sign-off |
|---------|----------|
| North American, casual | "Thanks," or "Talk soon," |
| North American, formal | "Best regards," |
| European | "Kind regards," |
| Executive / terse | "Best," or just the name |
| After delivering bad news | "Appreciate your patience," |

## Tone Calibration by Scenario

### Follow-up on overdue commitment (we're late)

Own it directly. No hedging, no passive voice, no burying it in paragraph three.

```
Pattern:
"I owe you [X] and it's overdue. Here's where it stands: [status].
You'll have it by [new date]. [One sentence on what caused the delay — optional, only if it adds trust, not as an excuse.]"
```

Do NOT say: "I wanted to circle back on..." / "Just checking if you received..." / "Apologies for the delay, we've been busy..."

### Re-engagement after silence

Use the Accusation Audit approach from the Khalife Second Brain ([[Tactical-Empathy]], [[Accusation-Audit]]). Acknowledge the gap. Don't pretend everything is fine. Don't open with a sales pitch.

```
Pattern:
"I realize it's been [timeframe] since we last connected, and I wouldn't blame you if [reasonable negative assumption — e.g., 'this fell off your radar' / 'you assumed we dropped the ball'].
[One sentence of value or relevance to re-earn attention.]
[Low-pressure CTA — no hard ask on the first touch.]"
```

### Good news delivery

Lead with the result. Not the backstory, not the process, not who was involved. Result first, context second if needed.

```
Pattern:
"[The good news in one sentence.]
[One sentence of context if needed.]
[CTA or 'No action needed.']"
```

Keep the whole email under 75 words. Good news doesn't need a novel.

### Bad news / escalation

Facts first, then what we're doing about it. No passive voice. No "unfortunately" more than once. Take ownership.

```
Pattern:
"[What happened — plain language, no jargon.]
[Impact on the customer — be honest about what this means for them.]
[What we're doing about it — specific actions, not 'we're looking into it.']
[New timeline or next step.]"
```

If the issue is serious, offer a call: "I'd rather walk through this live if you have 15 minutes — [proposed time]."

### Pricing / renewal discussion

**Always read `Company-Rules.md` first.** Non-negotiable.

Rules:
- Never put specific discount percentages in writing unless Company-Rules explicitly allows it.
- Never reference floor pricing, redline terms, or CEO-approval pathways in customer-facing email.
- Frame pricing around value delivered, not cost. Use the renewal as a checkpoint, not a negotiation.
- If the customer raises price objections, acknowledge the concern but redirect to a call. Pricing discussions happen live, not over email.

```
Pattern:
"Your renewal is coming up on [date]. I'd like to set up time to walk through what's ahead and make sure we're aligned.
[If value evidence exists: 'Over the past year, [specific usage/outcome data].']
Are you available [proposed time] for a 30-minute review?"
```

### Win-back attempt

**Only draft if approved** — check the hot cache and intelligence summary for prior decisions. If no win-back has been authorized, flag it and stop.

Frame around value the customer lost by leaving, not around discounts. Reference specific outcomes from when they were active, if available.

```
Pattern:
"[Reference to their previous usage/success — concrete, not generic.]
[What's changed since they left — new feature, new team, resolved issue — something relevant to their reason for churning.]
[Low-pressure CTA: 'Would it be worth a 20-minute conversation to see if the math works again?']"
```

Never lead with price. Never mention discounts in the first outreach.

## Output Format

Every draft must follow this structure:

```
**TO:** [name] <[email]>
**SUBJECT:** [subject line]
**THREAD:** [wikilink to prior email in Emails/ if this is a reply, or "New thread"]

---

[email body]

---

*Sources: [wikilink to intelligence summary, playbook, prior emails, or Action Tracker entries referenced during drafting]*
```

## Rules

1. **Never hallucinate prior conversations.** Only reference emails that exist in the customer's `Emails/` folder. If you're unsure whether a prior thread exists, say so — don't fabricate one.
2. **Never include pricing or discount amounts** without first reading and confirming compliance with `Company-Rules.md`. If the email touches pricing and you haven't loaded Company-Rules, stop and load it.
3. **Always flag stale contacts.** If the recipient's `Last Engaged` date in the Key Contacts table is >180 days ago, warn Jay before outputting the draft.
4. **Output is conversational only.** Do NOT save the draft as a file in the vault. Jay copies from the conversation and pastes into his email client. No files created.
5. **One draft per request.** If Jay asks for emails to multiple customers, draft them one at a time. Confirm each before moving to the next.
6. **Respect playbook strategy.** If an active playbook exists and the email contradicts the recommended approach (e.g., playbook says "go silent for 2 weeks" but Jay asks to send a follow-up now), flag the conflict. Don't refuse — Jay overrides strategy when he wants to — but make him aware.
7. **Never CC or suggest CC'ing** internal stakeholders unless Jay explicitly asks. Internal visibility decisions are Jay's call.
8. **Match thread tone.** If prior emails in the thread were casual, don't suddenly go formal. If they were formal, don't drop to casual. Consistency builds trust.

## Integration Points

### With `commitment-extraction.md`
When drafting a follow-up email for an Action Tracker item, mark the commitment as "In Progress" or note that outreach was made. Jay still manually marks items as complete after sending.

### With `playbook.md`
Playbook action steps often require outbound emails. When a playbook says "send value reinforcement email" or "schedule renewal review," this skill handles the drafting. Read the playbook's current phase and recommended approach to ensure alignment.

### With `debrief.md`
Post-meeting debriefs often generate commitments that need follow-up emails. The debrief output's "Recommended Next Steps" section feeds directly into this skill. Check the Decisions table for what was promised and to whom.

### With `triage.md`
A triage read might surface "gone silent 30+ days" or "overdue commitment." Both are triggers for this skill. The triage recommendation tells you what kind of email to draft (re-engagement vs. follow-up vs. escalation).

## Edge Cases

- **No prior emails exist for this customer.** Draft as a first-touch email. Use a slightly more formal tone until the customer's style is established. Note in sources: "No prior email history in vault."
- **Multiple contacts at the same customer.** Ask Jay who the email is going to. Don't guess. Different contacts may require different tones and different levels of detail.
- **Customer's primary contact has left the company.** Flag it. Suggest Jay verify the new point of contact before sending. If the intelligence summary shows a Champion Risk alert, reference it.
- **Email is responding to an inbound from the customer.** Read the inbound email first. Match urgency — if they wrote with urgency, don't draft a casual reply. Mirror their energy level.
- **Jay asks to draft something that violates Company-Rules.** Do not draft it. Explain which rule it violates and suggest a compliant alternative. Jay can override, but he needs to know.
