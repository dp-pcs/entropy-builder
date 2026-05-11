# Entropy Skill: Portfolio Dashboard, Action Tracker & Decision Logging

Load this file when generating the weekly Portfolio Dashboard, refreshing the Action Tracker, or processing decisions from transcripts/emails.

## Portfolio Dashboard

**File:** `Entropy/_Portfolio_Dashboard.md`
**Generated:** Every Monday (weekly sweep).
**Purpose:** Single-page triage view. Answers "where should Jay focus this week?"

Overwritten each week (not versioned — always reflects current state).

### Template

```markdown
# Portfolio Dashboard
**Generated:** YYYY-MM-DD | **Next refresh:** Monday

## 🔴 Attention Required
[Accounts with alert conditions this week]
| Customer | Product | ARR | Alert Type | Days Since Last Contact | Renewal Date | Action Needed |

## 📅 Upcoming Renewals (Next 90 Days)
| Customer | Product | ARR | Renewal Date | Days Left | Playbook Status | Sentiment |

## ⚡ Expansion Opportunities
| Customer | Product | ARR | Signal Type | Detail | Suggested Action |

## 📊 Portfolio Health Summary
- Total active customers: N
- HVO accounts: N (list any with alerts)
- At-risk accounts: N (list any without playbooks)
- No engagement 30+ days: N
- No playbook + renewal < 180 days: N
- Stale intelligence summaries (60+ days): N

## 🎯 Playbook Tracker
| Customer | Product | Playbook Date | Phase | Next Milestone | On Track? |

## 📈 Prediction Ledger Summary
- Predictions tracked: N
- Current hit rate: X%
- Latest outcome: [Customer] — [result]

## 🩺 Data Quality & Freshness
- No activity 60+ days: N (list top 5 by ARR)
- Summaries not updated 60+ days: N
- **Stale context (last_verified 60+ days):** N (list top 5 by ARR)
- **Aging context (last_verified 31-60 days):** N
- **Unverified (last_verified missing):** N
- No classified contacts: N
- Health score missing/stale (>14d): N
- HVO/At-Risk without current playbook (90d): N
- Orphan files (no wikilinks): N
- Contacts "⚠️ Silent 90d+": N (list by customer)
- **Unprocessed meetings (debrief gate):** N (list all)
```

### Rules
- Only include sections with data. Omit empty sections.
- "Attention Required" sorted by ARR descending — highest-value first.
- Flag any account renewing within 90 days without a current playbook.
- Link customer names to `[[_intelligence_summary]]`.

## Action Tracker

**File:** `Entropy/_Action_Tracker.md`
**Refreshed:** Every Monday (weekly sweep).
**Purpose:** Every open commitment Jay has made. Answers "what did I promise, and is any overdue?"

Overwritten each week. Pulls from:
1. **Playbook actions** — Recommended Approach timelines with deadlines.
2. **Meeting/email decisions** — `## Decisions` section in intelligence summaries.

### Template

```markdown
# Action Tracker
**Generated:** YYYY-MM-DD | **Next refresh:** Monday

## 🔴 Overdue
| Customer | Product | Action | Source | Due Date | Days Overdue |

## 📅 Due This Week
| Customer | Product | Action | Source | Due Date |

## 📋 Upcoming (Next 30 Days)
| Customer | Product | Action | Source | Due Date |

## ✅ Completed This Week
| Customer | Product | Action | Source | Completed |
```

### Rules
- Overdue sorted by days overdue descending.
- Source column links to originating playbook or intelligence summary.
- Actions extracted from: (a) active playbook timelines, (b) `## Decisions` tables.
- Completed when: Jay confirms, or daily/weekly scan detects evidence.
- Cancelled when: playbook superseded or Jay explicitly cancels.
- Link customer names to `[[_intelligence_summary]]`.
- Tracker does NOT replace playbooks. Playbooks = strategy. Tracker = execution checklist.

### Debrief Gate

No customer call should end without the repo being updated. During the weekly Action Tracker refresh, check for unprocessed meetings:

1. Pull recent meetings from Read.ai (`list_meetings`, last 7 days).
2. For each meeting with a customer participant, check if a corresponding transcript file exists in `CustomerName/Transcripts/`.
3. If a meeting occurred but no debrief was processed, add a **Debrief Overdue** entry to the Action Tracker:

```
| Customer | Product | Debrief: [Meeting Title] [Date] | Read.ai | [Meeting Date] | [Days Overdue] |
```

This ensures Jay always knows when a meeting's intelligence hasn't been captured. Unprocessed meetings older than 7 days are flagged as overdue. The debrief gate compounds context quality — every meeting that goes unprocessed is a context rot source.

## Decision Logging

Intelligence summaries may include `## Decisions` for commitments from customer interactions. Populated during Tier 2 processing.

### What Counts as a Decision

Explicit commitments, agreements, or action items:
- "We agreed to extend the POC by 2 weeks"
- "Jay committed to sending pricing by Friday"
- "Customer requested a call with product team — Jay to schedule"
- "Both sides agreed to revisit after Q2 results"

NOT decisions: general sentiment, internal observations, status updates without commitments.

### Template

```markdown
## Decisions

| Date | Decision | Owner | Due Date | Status | Source |
|------|----------|-------|----------|--------|--------|
| 2026-04-18 | Send revised pricing proposal | Jay | 2026-04-22 | Open | Transcript 2026-04-18 |
```

### Field Definitions

| Field | Values | Notes |
|-------|--------|-------|
| **Owner** | Jay, Customer, Internal (name), Mutual | Who is responsible |
| **Due Date** | YYYY-MM-DD or "TBD" | When it should be done |
| **Status** | Open, Done, Overdue, Cancelled | Updated during scans or by Jay |
| **Source** | Link to transcript or email | For context retrieval |

### Rules
- Extracted during **Tier 2 processing**. Scan for: "agreed to", "will send", "committed to", "by [date]", "action item", "next step", "follow up with".
- Track BOTH Jay's and customer's commitments. Customer promises that go overdue by 7+ days → follow-up recommendation.
- Owner: Jay + Due Date → feeds into `_Action_Tracker.md` during weekly sweep.
- Completion → note date in Source: "Done 2026-04-16".
- **Append-only.** Never delete. Cancelled → "Cancelled" with explanation.
