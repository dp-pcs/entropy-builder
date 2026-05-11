# Entropy Skill: Proactive Alerting & Expansion Intelligence

Load this file when running alert scans (weekly sweep step 3), evaluating expansion signals, or triaging accounts for attention.

## Alert Conditions

Alerts are detected during the weekly sweep and surfaced in the Portfolio Dashboard. An alert means "this account needs human attention."

| Alert Type | Trigger | Severity |
|-----------|---------|----------|
| **Gone Silent** | No email, meeting, or Jira in 30+ days | 🔴 High (HVO/At-Risk) / 🟡 Medium (others) |
| **Ticket Spike** | Ticket volume 2x+ the 90-day average this week | 🟡 Medium |
| **Sentiment Shift** | Any change in `product_sentiment`, `support_sentiment`, or `renewals_sentiment` from Positive/Neutral to Negative between scans | 🔴 High |
| **Renewal Without Playbook** | Renewal within 180 days, no playbook in folder | 🔴 High (HVO) / 🟡 Medium (others) |
| **Escalation Detected** | VP+ contacts not previously involved, or escalation language ("unacceptable", "executive review", "considering alternatives") | 🔴 High |
| **Payment Issue** | Fionn: overdue balance or payment failure | 🟡 Medium |
| **Champion Risk** | Primary contact email bouncing, or LinkedIn shows role/company change | 🔴 High |

## Severity Logic

- **🔴 High**: Top of "Attention Required". Jay acts this week.
- **🟡 Medium**: Below high-severity. Jay plans action within 2 weeks.
- HVO and At-Risk accounts → automatically elevated one severity level.
- Cancellation-intent score ≥ 0.7 → always 🔴 High regardless of account type.

## Alert Resolution

Cleared when:
- New engagement occurs (email, meeting, Jira activity), OR
- Jay manually acknowledges ("I'm aware, no action needed").

Cleared alerts don't carry forward to the next dashboard.

## Expansion Intelligence

Track signals indicating readiness for upsell, cross-sell, or deeper engagement. Detected during weekly sweep, logged in `_intelligence_summary.md`.

### Usage Growth Signals

Detect in emails, transcripts, Jira:
- Asks about features/modules they don't have
- Mentions growing team, adding users, expanding to new departments/regions
- Ticket volume increasing alongside positive sentiment (deeper adoption, not frustration)
- References use cases beyond current product scope
- Asks about API access, integrations, or automation they haven't used

### Contract Timing Signals

Detect from Notion/Fionn data + Company-Rules:
- On Standard, could benefit from Platinum (high tickets, complex use cases)
- On 1-year, approaching 180-day window for multi-year lock-in
- ARR approaching threshold where PS/training become relevant
- Multiple portfolio products — cross-sell for unused ones

### Logging Format

```markdown
## Expansion Signals

| Date | Signal Type | Detail | Source |
|------|------------|--------|--------|
| 2026-04-10 | Feature inquiry | Asked about API access for automated survey deployment | Email 2026-04-08 |
| 2026-03-15 | Team growth | Expanding research team from 5 to 12 | Transcript 2026-03-15 |
```

Signals also surface in the Dashboard's "Expansion Opportunities" section. When enough signals accumulate → recommend generating an Expansion Playbook (`YYYY-MM-DD_Expansion_Playbook.md`).
