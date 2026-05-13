# Entropy Skill: Customer Triage

Fast situational snapshot for a single customer. Use when Jay asks "what's going on with [Customer]?", "give me a quick read on [Customer]", "status of [Customer]", or any question about a specific account that doesn't require a full playbook.

**Design principle:** Speed over depth. No vault traversal, no framework application, no playbook generation. Just the facts, the signals, and what needs attention — in under 200 words.

## What to Load

Only the customer's own folder. Do NOT scan the portfolio.

1. `_intelligence_summary.md` — full read (this is the single source of truth)
2. Last 5 files by date across `Emails/`, `Transcripts/`, `Jira/` — **frontmatter + first 5 lines only** (enough to get the gist without burning context)
3. Active playbook (most recent `*_Playbook.md`) — **frontmatter + Recommended Approach section only** (skip scenario simulations, financial modeling, etc.)
4. `_Action_Tracker.md` — grep for this customer's name only

Do NOT load: Company-Rules, Prediction Ledger, vault MOCs, other customers, skill files beyond this one.

## Triage Briefing Template

Respond in this structure. Keep the entire response under 200 words. Use plain language, not headers or tables.

```
[Customer Name] — [Product] — [ARR]
Health: [score] [band emoji] ([direction: stable / improving / declining] over last [N] entries)
Renewal: [date] ([N] days out) | Playbook: [exists/none/stale]
Last contact: [date] ([N] days ago) — [who, what channel]

WHAT'S HAPPENING:
[2-3 sentences synthesizing the current situation from the intelligence summary and recent interactions. What's the story right now?]

SIGNALS:
[Bullet any active flags — cancellation intent, expansion signals, champion risk, gone silent, sentiment shift. If none, say "No active signals."]

OPEN COMMITMENTS:
[Any overdue or upcoming actions from the Action Tracker or Decisions table for this customer. If none, say "No open items."]

RECOMMENDATION:
[One sentence: what Jay should do next, or "No action needed — monitor."]
```

## Decision Rules

- **Health declining + no playbook** → Recommendation: "Consider generating a playbook — health is trending down with no active strategy."
- **Health declining + active playbook** → Recommendation: "Review playbook — the current approach may not be landing. Check whether exit criteria have been triggered."
- **Gone silent 30d+** → Recommendation: "Break the silence — consider a low-pressure touchpoint (article share, check-in, product update)."
- **Cancellation intent ≥ 0.5** → Recommendation: "Escalation risk is real. Load `_skills/playbook.md` and consider generating a targeted playbook."
- **Expansion signals active** → Recommendation: "Expansion window is open. Evaluate timing for an upsell or cross-sell conversation."
- **Overdue actions exist** → Always surface these first in the recommendation, regardless of other signals. Broken promises erode trust faster than anything else.
- **Everything looks fine** → "No action needed — healthy engagement, no signals. Monitor."

## Health Direction Calculation

Read the `## Health History` table. Compare the most recent score to the score from 4 weeks ago (or the oldest available if fewer entries exist):
- Difference ≥ +10 → "improving"
- Difference ≤ -10 → "declining"
- Otherwise → "stable"

## When to Escalate Beyond Triage

If during the triage read you encounter any of these, tell Jay explicitly and suggest loading the appropriate skill:
- Cancellation-intent score ≥ 0.7 → suggest `_skills/playbook.md` for full analysis
- Renewal within 90 days + no playbook → suggest `_skills/playbook.md`
- New executive contact appeared in recent communications → suggest deeper Tier 2 analysis via `_skills/ingestion.md`
- Health dropped to 🔴 Critical for an HVO account → suggest full Tier 3 analysis

Don't auto-escalate. Surface the recommendation and let Jay decide.
