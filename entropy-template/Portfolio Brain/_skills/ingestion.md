# Portfolio Brain Skill: Data Ingestion & Tiered Processing

Load this file before running daily inbox scans, weekly sweeps, or monthly enrichment. Contains the tiered processing model, cadence definitions, and checkpoint patterns.

## Tiered Processing Model

All data processing follows three tiers. The tier determines analysis depth, balancing thoroughness against usage cost.

### Tier 1 — Metadata Only (80% of daily activity)

**What:** Grab metadata (sender domain, subject, date, ticket key/priority) without reading full content. Match to customer via domain mapping. Log the event.

**When:** Routine emails, standard Jira tickets, regular meetings. Any communication where metadata doesn't contain escalation signals.

**Actions:**
- Create stub .md file with YAML frontmatter + one-line summary from subject. No full body read.
- Update `last_updated` and `Last Engaged` dates.
- Increment engagement counter for health score.
- Update contact `Last Engaged` if sender is in Key Contacts.

**Cost:** ~2 tool calls per item. Minimal context.

### Tier 2 — Content Scan (triggered by signals)

**What:** Read full content. Analyze for cancellation intent, expansion signals, sentiment shifts, new contacts.

**Triggers (automatic escalation from Tier 1):**
- Subject contains: "cancel", "terminate", "alternative", "unacceptable", "executive review", "considering options", "competitor", "budget cut", "not renewing"
- Jira priority: Critical or Blocker
- Meeting participants include VP+ titles not previously seen
- Sender is new contact for HVO or At-Risk account
- Customer has cancellation-intent score ≥ 0.5 from prior scan

**Actions:**
- Read full email/ticket/transcript.
- Score cancellation intent (load `_skills/health.md` for weights).
- Check for expansion signals.
- Classify new contacts (Role, Stance: Unknown, Influence from title).
- Update intelligence summary with detailed notes.
- Append Health History row if score changes significantly.

**Cost:** ~5-8 tool calls per item. Moderate context.

### Tier 3 — Full Analysis (on-demand only)

**What:** Deep vault traversal, framework application, playbook generation, stakeholder mapping.

**Triggers (never automatic — requires Jay's confirmation):**
- Jay explicitly requests a playbook or analysis.
- Health score drops to 🔴 Critical for HVO (agent recommends, Jay confirms).
- Cancellation-intent score ≥ 0.7 for HVO (agent recommends, Jay confirms).
- Renewal within 90 days for HVO without current playbook.

**Actions:**
- Load `_skills/playbook.md` for full playbook generation.
- Read Company-Rules, Prediction Ledger, Customer Intelligence MOC, vault frameworks.
- Generate full playbook per template.

**Cost:** High context. Dedicated session, not part of a sweep.

## Role Classification

When processing emails or meeting transcripts, classify participants:

| Domain Pattern | Classification |
|---------------|---------------|
| Customer's known domain | **Customer** |
| @trilogy.com, @aurea.com, @skyvera.com | **Internal** |
| @shi.com, @carahsoft.com, @tekservinc.com, @softwareone.com, @penril.net, @bechtle.com | **Reseller** |
| Any other domain | **External** |

## Daily Inbox Scan (Weekdays 8am)

Tier 1 default, Tier 2 when triggered. Lightweight triage-and-route. Does NOT sync with Notion.

**Sources:**
1. **Gmail**: `newer_than:1d`. Extract sender domain + subject + date. Match via domain mapping. Create stub. If subject has Tier 2 keywords → read full body.
2. **Jira**: `updated >= -1d`. Extract ticket key, priority, reporter domain, summary. Create stub. Critical/Blocker → Tier 2.
3. **Read.ai**: `list_meetings` past 24h. Extract participants + title. Create stub. VP+ contacts → Tier 2.

**Post-routing (all customers with new data):**
4. Update `Last Engaged` dates. Add new senders as Unknown contacts.
5. Update engagement + cadence scores. Append Health History only if score changed. Trigger: "Daily scan".
6. Lightweight alert check: health drift (≥10 pts), cancellation intent (from Tier 2), new escalation contacts.

**Output:** Brief summary: items ingested by source, customers updated, Tier 2 escalations, alerts triggered. Output this as conversational text only — **do NOT create a standalone scan report file.** Scan results are persisted via intelligence summary updates, `_hot_cache.md`, and dashboard/alert updates. No `*_Daily_Scan_*`, `*_Scan_Report*`, or similar files should ever be written to the Portfolio Brain root or any other location.

### Checkpoint Pattern (for daily scans)
After processing every 50 items (or every source transition), output a progress checkpoint:
```
CHECKPOINT: [source] complete. [N] items processed, [M] Tier 2 escalations. Continuing to [next source].
```
This keeps context lean over large batches.

## Weekly Sweep (Mondays 8:05am)

Optimized to avoid re-doing daily work. Uses frontmatter-only reads and file existence checks.

1. **Weekend sweep**: 2-day lookback (`newer_than:2d`) for Sat/Sun only. Same triage logic.
2. **Tier 2 batch**: Process items flagged Tier 2 during the week that weren't fully analyzed. Skip already-processed items.
3. **Portfolio alert scan (frontmatter only)**: Read ONLY YAML (~20 lines) of each intelligence summary. Check: Gone Silent (30d+), Renewal Without Playbook (file existence check), Stale Health (14d+), Cancellation Intent Persistence, **Context Freshness** (`last_verified` aging/stale/missing — see CLAUDE.md freshness table).
4. **Targeted health recalc**: Only for (a) customers with new data this week, (b) customers with stale scores (14d+). Skip all others.
5. **Action Tracker + Debrief Gate**: Read only active playbooks (dated within 90d, ~10-20 files). Scan Decisions for Tier 2 customers only. Also run the debrief gate: check Read.ai meetings from the past 7 days against existing transcript files — flag any unprocessed meetings as overdue in the Action Tracker (see `_skills/dashboard.md` for debrief gate rules). Generate `_Action_Tracker.md`.
6. **Lightweight data quality**: Frontmatter + metadata only. Check: stale summaries (60d+), empty folders, HVO without playbooks. Skip full contact audit (monthly task).
7. **Portfolio Dashboard**: Generate from data already collected in steps 3-6. No additional reads.
8. **Weekly report**: Alerts, health changes, action tracker, data quality, top 5 accounts needing attention. Under 800 words. Conversational output only — do NOT save as a standalone file. All persistent data lives in `_Portfolio_Dashboard.md`, `_Action_Tracker.md`, `_hot_cache.md`, and individual intelligence summaries.

### Checkpoint Pattern (for weekly sweeps)
After each step, output:
```
CHECKPOINT: Step [N]/8 complete — [step name]. [key stats]. Proceeding to step [N+1].
```

## Monthly Enrichment (1st of month, 9am)

Runs alongside the monthly pattern report. Adds external context. Load `_skills/enrichment.md` for full details on external intelligence gathering.

1. **Notion sync**: Pull ARR, renewal_date, status, contacts, success_level. Update summaries. This is the ONLY Notion sync — not daily, not weekly.
2. **Company news scan (HVO + At-Risk only)**: Web search for M&A, layoffs, funding, leadership changes, competitor wins, public reviews.
3. **Firmographic enrichment**: For customers missing data — size, industry, HQ, tech stack.
4. **Enrichment summary**: Log findings in `## External Intelligence`.
5. **Pattern report**: Generate `Portfolio Brain/YYYY-MM_Portfolio_Pattern_Report.md`.
6. **Health check**: 10-point monthly check (load `_skills/enrichment.md` for checklist).

7. **System Improvement Review (Flywheel)**: The automation-to-learning flywheel — each automation frees time to improve the system, which enables more automation. Review:
   - What manual steps did Jay repeat most this month? Could any become a skill or automation?
   - Which skills triggered correctly? Which were under-triggered or never used?
   - Were there recurring data gaps or query failures? Should a new MCP be connected?
   - Are any existing skills producing low-quality output that needs iteration?
   - Did any new patterns emerge that could inform a new skill (e.g., a new customer segment, a common email type)?
   Output a brief "System Improvement" section in the monthly report with 2-3 concrete recommendations ranked by leverage (time saved × frequency). Track improvements made in `_hot_cache.md` under a `## System Improvements` section so future sessions can see what changed and when.

### Checkpoint Pattern (for monthly enrichment)
After each step, output:
```
CHECKPOINT: Step [N]/7 complete — [step name]. [key findings]. Proceeding to step [N+1].
```

## Folder Scoping

**Jay's portfolio is exactly 4 products:** `Tivian/`, `Influitive/`, `Lyris/`, `QuickSilver/`. All other product folders at the Portfolio Brain root (`ACRM`, `Artemis`, `Aurea Platform`, `Bonzai`, `Jigsaw Platform`, `Messageone`, `Onyx`, `Pivotal`, `Saratoga`, `Stratifyd`) belong to the wider team and must be excluded from all scans, sweeps, and enrichment.

When a task targets a specific customer, scope file access:
- **Single customer query** → Only mount `Portfolio Brain/[Product]/[CustomerName]/` + the intelligence summary. Don't scan the whole portfolio.
- **Portfolio-wide task** → Use frontmatter-only reads first. Only open full files when triggered. Only traverse the 4 portfolio products.
- **Cross-customer comparison** → Load only the specific customers being compared, not all 300.

## Customer Domain Mapping

**File:** `Portfolio Brain/_data/customer_domains.json` — maps 446 email domains to customer names and products. Use for matching emails and meeting participants. Reseller domains (shi.com, carahsoft.com, etc.) map to multiple customers — use subject/body for disambiguation.

## Data Sources

| Source | Tool | What It Provides |
|--------|------|------------------|
| Notion | Notion MCP (`28485e927d3181c89d6cdd6fd57ea07d`) | Master customer database, structured fields |
| Read.ai | list_meetings, get_meeting_by_id | Meeting transcripts, summaries, action items |
| Gmail | gmail_search_messages, gmail_read_thread | Customer email threads |
| Jira | searchJiraIssuesUsingJql, getJiraIssue | Support tickets, project work |
| Knowledge Base | Direct file read | Product docs, KB articles, release notes |
