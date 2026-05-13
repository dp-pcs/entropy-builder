---
type: skill
title: "Commitment Extraction"
triggers:
  - "update action tracker"
  - "check overdue commitments"
  - "what commitments are overdue"
  - "extract commitments"
  - post-meeting debrief (co-loaded with debrief.md)
  - weekly sweep (co-loaded with ingestion.md + dashboard.md + alerting.md)
---

# Commitment Extraction Skill

Extracts actionable commitments from transcripts, playbooks, emails, and intelligence summaries. Writes them to `_Action_Tracker.md` (portfolio-wide view) and each customer's `_intelligence_summary.md` (local view).

---

## When This Skill Loads

| Context | What To Do |
|---------|-----------|
| Post-meeting debrief | Extract action items from the transcript just processed. Update tracker + customer intelligence summary. |
| Weekly sweep (Monday) | Scan all files modified in the past 7 days. Extract new commitments, age existing ones, recalculate overdue. |
| Direct request ("what's overdue?") | Read `_Action_Tracker.md` and report. If tracker looks stale (last_updated >7 days ago), run a quick extraction first. |
| Playbook generation | Check existing open commitments for this customer before writing new ones. Flag if there are already overdue items. |

---

## Extraction Rules

### From Transcripts

Look for the `### Action Items` section (present in all properly formatted transcripts).

For each bullet:
1. **Parse owner** from "[Name] to..." prefix. If no prefix, owner = Jay.
2. **Parse action** = remainder of the bullet after the owner prefix.
3. **Parse due date** from "by [date/timeframe]" suffix. Defaults:
   - "by end of week" → Friday of the transcript's week
   - "by [day name]" → next occurrence of that day
   - "by [month day]" → that date
   - No date mentioned → `transcript_date + 7 days`
4. **Determine type:**
   - Owner is Jay or Trilogy team member → `internal`
   - Owner is customer contact → `customer`
   - Both parties mentioned → `joint`
5. **Source** = wikilink to transcript file: `[[YYYY-MM-DD_Meeting_Title]]`

### From Playbooks

Look for tables under headers matching: `Open Commitments`, `Commitments`, `Action Items`, `Open Items`.

Map columns:
- `Commitment` or `Action` → **Action**
- `Owner` → **Owner**
- `Status` → **Status** (preserve exact text)
- `Due Date` → **Due Date**
- `Days Overdue` → calculate due date as `playbook_date - days_overdue`

**Source** = wikilink to playbook file.

### From Intelligence Summaries

Look for numbered/bulleted items under `## Next Steps`, `## Decisions`, `## Open Commitments`.

Parse priority from bold prefixes:
- `**IMMEDIATE**:` → due date = today
- `**Before [date]**:` → due date = that date
- `**This week**:` → due date = Friday of current week
- `**Strategic**:` → due date = today + 30 days
- No prefix → due date = today + 14 days

### From Emails (Opportunistic Only)

Only extract when explicit first-person commitment language appears:
- "I'll send you..." / "I will follow up..."
- "We'll have this to you by..."
- "Let me check on..." / "I'll confirm..."
- "We'll reconnect in..." / "I'll circle back..."

Parse the promise and any date reference. Default due date = `email_date + 7 days`.

**Do NOT extract** vague language like "let's stay in touch" or "happy to help if needed."

---

## Deduplication

Before adding any commitment to the tracker:

1. Check existing rows for same customer
2. Fuzzy-match action text (>80% similarity)
3. If duplicate found:
   - Keep the version with more metadata (explicit due date > inferred, named owner > default)
   - Merge source links (one row can reference multiple sources)
   - Update status if the new source has fresher information
4. If no duplicate: add as new row

---

## Completion Detection

A commitment moves to ✅ Completed when:

1. **Explicit mention in a later transcript or email:**
   - "we delivered X", "X is now available", "I sent the Y", "the Z is done"
   - "they confirmed X", "Alex said he completed Y"
2. **Playbook outcome file** references it as resolved
3. **Jay manually marks it** during a sweep or debrief
4. **Customer confirms** in an email thread

When completing:
- Move from current table to ✅ Completed This Week
- Record the completion date and resolution source
- Update the customer's `_intelligence_summary.md` (move from Open to Resolved)

---

## Tracker Update Procedure

After extraction and deduplication:

1. **Sort Overdue** by Days Overdue descending (worst first)
2. **Calculate Risk** for each overdue item:
   - `CRITICAL` = >30 days overdue AND account is HVO
   - `HIGH` = >14 days overdue, OR any overdue on an at-risk/negative-sentiment account
   - `MEDIUM` = 7-14 days overdue
   - `LOW` = 1-7 days overdue
3. **Sort Due This Week** by Due Date ascending
4. **Sort Upcoming** by Due Date ascending
5. **Move items between tables** as dates pass:
   - Upcoming → Due This Week (when due date enters current week)
   - Due This Week → Overdue (when due date passes)
6. **Update YAML frontmatter:**
   - `last_updated: YYYY-MM-DD`
   - `total_open: [count of all non-completed items]`
   - `total_overdue: [count of overdue items]`
   - `customers_with_overdue: [list of customer names with overdue items]`
7. **Recalculate Commitment Velocity** (rolling 30 days):
   - Count opened, closed, net change
   - Average days to close
   - Identify oldest open item

---

## Output Format

After running extraction (whether post-debrief or weekly sweep), output a summary:

```
📋 Action Tracker refreshed (YYYY-MM-DD)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 Overdue: X (Y critical, Z high)
📅 Due this week: X
📋 Upcoming (30d): X
⏳ Awaiting customer: X
✅ Completed this week: X

New commitments extracted: N
  - From transcripts: A
  - From playbooks: B
  - From emails: C

⚠️ Critical overdue:
  - [Customer] — [Action] (X days overdue)
  - [Customer] — [Action] (X days overdue)

🔗 Accounts also flagged in Dashboard:
  - [[Customer A]] — overdue + renewal in 90 days
```

---

## Integration Points

### With `debrief.md`
After the debrief skill processes a transcript, this skill runs to extract action items. The debrief skill should NOT duplicate commitment tracking — it focuses on intelligence extraction (sentiment, themes, relationship signals). This skill handles the commitment layer.

### With `dashboard.md`
The weekly dashboard generation should read `_Action_Tracker.md` YAML frontmatter and include:
- Count of overdue commitments in the portfolio health summary
- List of customers with critical overdue items in "Attention Required"

### With `alerting.md`
Overdue commitments (especially CRITICAL and HIGH) are alert triggers. The alerting skill should check the tracker during evaluation and generate alerts for:
- Any commitment overdue >14 days
- Any HVO account with any overdue commitment
- Any account where a commitment has been overdue for >30 days (relationship erosion signal)

### With `playbook.md`
Before generating a new playbook, load this skill to check:
- Are there existing open commitments for this customer?
- If yes, the playbook should acknowledge them (either as "still pending" or "now resolved")
- New playbooks should NOT create commitments that duplicate existing open ones

---

## Edge Cases

- **Commitment with no clear owner:** Default to Jay. It's better to over-assign to yourself than to lose track.
- **Commitment with no clear due date:** Use the context-appropriate default (7 days for transcripts/emails, 14 days for intelligence summaries, 30 days for strategic items).
- **Customer-owned commitment that customer never acknowledged:** Still track it in ⏳ Awaiting Customer. Jay needs to know what he's waiting for even if the customer didn't formally agree.
- **Commitment from a very old transcript (>90 days):** During backfill, mark these as `STALE` rather than `CRITICAL`. They need manual triage — some may have been completed without documentation, others may be genuinely forgotten.
- **Duplicate commitment across multiple customers** (e.g., "Jay to check with Tiago on feature X" for two different accounts): Track as separate rows per customer. The action is the same but the customer context differs.
