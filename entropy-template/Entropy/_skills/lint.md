---
type: skill
title: "Vault Lint"
triggers:
  - "lint the vault"
  - "vault health check"
  - "find orphans"
  - "check dead links"
  - "graph integrity"
  - monthly enrichment (co-loaded with enrichment.md)
---

# Vault Lint Skill

Checks Entropy's structural integrity across 8 categories. Run monthly alongside enrichment, or on-demand when the vault feels messy.

---

## When This Skill Loads

| Context | What To Do |
|---------|-----------|
| Monthly enrichment | Run full 8-category lint after enrichment updates |
| "Lint the vault" / "health check" | Run full lint, output report |
| "Find orphans" / "check dead links" | Run only the requested category |
| After bulk ingestion (10+ files) | Quick lint on the ingested files' connections |

---

## 8-Category Health Check

### 1. Orphan Files

**What:** Files with zero incoming wikilinks — nothing points to them.

**How to check:**
1. List all `.md` files in Entropy/
2. For each file, search the entire vault for `[[filename]]` (without extension)
3. If no other file links to it, it's an orphan

**Exceptions (not orphans):**
- `INDEX.md`, `CLAUDE.md`, `Company-Rules.md`, `_hot_cache.md`, `_Daily_View.md` — root-level files don't need incoming links
- Files in `_skills/` — loaded by routing, not wikilinked
- Files in `_nodes/` — these ARE the hub; they don't need incoming links (but should have outgoing links to customers)

**Fix:** Add the orphan to its customer's `_intelligence_summary.md` Graph Connections section, or to a relevant hub node.

**Severity:** LOW per file, but HIGH in aggregate. >50 orphans means the graph is fragmenting.

---

### 2. Dead Wikilinks

**What:** `[[Target]]` links where `Target.md` doesn't exist anywhere in the vault.

**How to check:**
1. Scan all `.md` files for `[[...]]` patterns
2. For each wikilink target, check if a matching file exists (account for aliases in frontmatter)
3. Dead link = target file not found

**Common causes:**
- Customer renamed in Notion but not in Entropy
- Typo in wikilink
- Hub node referenced but never created
- File deleted but links to it remain

**Fix:** Either create the missing file or update the link to point to the correct target.

**Severity:** MEDIUM. Dead links break graph navigation and make the vault feel unreliable.

---

### 3. Missing Graph Connections

**What:** `_intelligence_summary.md` files that lack the required `## Graph Connections` section.

**How to check:**
1. Find all `_intelligence_summary.md` files
2. Check each for `## Graph Connections` section
3. If missing, flag it

**Also check for incomplete Graph Connections:**
- Missing `**Product:**` line (every customer has a product)
- Missing `**Status:**` line (every customer has HVO/Non-HVO status)
- Missing `**Contract:**` line (every customer is ESW or Non-ESW)

**Fix:** Add the Graph Connections section using the template from CLAUDE.md.

**Severity:** HIGH. Missing graph connections = invisible customer in the graph view. The node exists but isn't connected to the topology.

---

### 4. Stale Frontmatter

**What:** YAML frontmatter with outdated data — especially renewal dates in the past and health scores that haven't been recalculated.

**How to check:**
1. Find all `_intelligence_summary.md` files
2. Check `renewal_date` — if it's before today and the customer is still Active, the date is stale
3. Check `date` — if last updated >90 days ago, the summary may be stale
4. Check `arr` — cross-reference with Notion if possible (ARR changes at renewal)
5. Check `health_score` — if present and the customer's situation has materially changed (new transcripts, sentiment shifts), the score needs recalculation
6. Check `last_verified` — context freshness scoring (see CLAUDE.md freshness table):
   - **Missing:** Treat as stale. Add field with today's date on next substantive update
   - **Aging (31-60 days):** Flag for review in weekly sweep
   - **Stale (60+ days):** Flag in Portfolio Dashboard, prioritize for enrichment
   - Note: `last_verified` should only be updated on substantive reviews (debriefs, playbooks, manual review, monthly enrichment) — NOT on routine Tier 1 metadata-only updates

**Fix:** Update stale fields. For renewal dates, check Fionn/Notion for the actual current renewal date. For `last_verified`, either perform a substantive review or flag for the next enrichment cycle.

**Severity:** HIGH for renewal dates (you'll miss renewal windows), HIGH for `last_verified` stale/missing on HVO accounts, MEDIUM for other fields.

---

### 5. Hub Node Integrity

**What:** Hub nodes in `_nodes/` that have incorrect `customer_count` values or list customers that no longer exist.

**How to check:**
1. For each hub node, count the actual customer links in "Connected Customers"
2. Compare to the `customer_count` in YAML frontmatter
3. Also check: does each linked customer actually have a folder in the vault?
4. Check: are there customers that SHOULD be linked (based on their frontmatter) but aren't?

**Fix:** Update the customer count and add/remove customer links.

**Severity:** MEDIUM. Inaccurate counts erode trust in the data. Missing links mean the graph view is incomplete.

---

### 6. Empty Customer Folders

**What:** Customer folders that exist but contain only `_intelligence_summary.md` with no emails, transcripts, or playbooks.

**How to check:**
1. List all customer folders across Tivian/, Influitive/, Lyris/, QuickSilver/
2. For each, count the total files
3. Flag folders with only 1 file (just the summary) or 0 files

**Why this matters:** An empty folder means no intelligence has been captured. For HVO accounts, this is a gap. For Non-HVO accounts below a certain ARR threshold, it may be acceptable.

**Fix:** Check if there are emails/transcripts/Jira tickets that should have been ingested. If the customer is genuinely low-touch, note it in the summary.

**Severity:** LOW for non-HVO, HIGH for HVO accounts with empty folders.

---

### 7. Duplicate/Conflicting Data

**What:** Multiple files covering the same event, or frontmatter that contradicts across files.

**How to check:**
1. Look for multiple transcript files on the same date for the same customer (like CEA-CAPA's Apr 2 and Apr 3 transcripts that cover the same meeting)
2. Check for intelligence summaries with conflicting sentiment vs. what transcripts show
3. Check for playbooks that reference different ARR values than the intelligence summary

**Fix:** Merge duplicates (keep the richer one), resolve conflicts by checking the source of truth (Notion for ARR, transcripts for sentiment).

**Severity:** MEDIUM. Duplicates waste processing time and can cause conflicting recommendations.

---

### 8. Action Tracker Drift

**What:** Commitments that exist in transcripts/playbooks but were never extracted into `_Action_Tracker.md`, or tracker items that have been completed but not updated.

**How to check:**
1. Scan recent transcripts (last 30 days) for `### Action Items` sections
2. For each action item, check if it appears in `_Action_Tracker.md`
3. Flag any that are missing from the tracker
4. Also check: are there tracker items marked as open that have evidence of completion in subsequent transcripts/emails?

**Fix:** Run the commitment-extraction skill to sync the tracker.

**Severity:** HIGH. The whole point of the tracker is to catch slipping commitments. If the tracker itself drifts, it defeats the purpose.

---

## Output Format

After running lint, output a health report:

```
🏥 Vault Health Report — YYYY-MM-DD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall: 🟢 HEALTHY | 🟡 NEEDS ATTENTION | 🔴 DEGRADED

| Category | Status | Count | Severity |
|----------|--------|-------|----------|
| Orphan files | 🟢/🟡/🔴 | X files | LOW/MED/HIGH |
| Dead wikilinks | 🟢/🟡/🔴 | X links | LOW/MED/HIGH |
| Missing graph connections | 🟢/🟡/🔴 | X summaries | HIGH |
| Stale frontmatter | 🟢/🟡/🔴 | X files | HIGH |
| Hub node integrity | 🟢/🟡/🔴 | X nodes off | MEDIUM |
| Empty customer folders | 🟢/🟡/🔴 | X folders | VARIES |
| Duplicate/conflicting data | 🟢/🟡/🔴 | X items | MEDIUM |
| Action tracker drift | 🟢/🟡/🔴 | X missed | HIGH |

Top 5 fixes (highest impact):
1. [specific fix]
2. [specific fix]
3. [specific fix]
4. [specific fix]
5. [specific fix]
```

**Thresholds:**
- 🟢 = 0 issues in category
- 🟡 = 1-5 issues
- 🔴 = 6+ issues

**Overall:**
- 🟢 = no 🔴 categories and ≤2 🟡 categories
- 🟡 = 1 🔴 category or 3+ 🟡 categories
- 🔴 = 2+ 🔴 categories

---

## Integration Points

### With `enrichment.md`
Run lint after monthly enrichment. Enrichment updates firmographic data; lint catches any structural issues the updates introduced (new dead links, stale counts).

### With `commitment-extraction.md`
Category 8 (Action Tracker Drift) is essentially a cross-check against the commitment extraction pipeline. If drift is detected, re-run commitment-extraction.

### With `dashboard.md`
Lint results feed into the Daily View — if vault health is 🔴, it shows as a system alert in the morning dashboard.

---

## Scheduling

| Frequency | Scope |
|-----------|-------|
| Monthly | Full 8-category lint |
| Weekly (during Monday sweep) | Categories 4 (stale frontmatter) and 8 (tracker drift) only — quick pass |
| On-demand | Any category, any time |
| After bulk operations | Categories 1, 2, 3 on affected files only |
