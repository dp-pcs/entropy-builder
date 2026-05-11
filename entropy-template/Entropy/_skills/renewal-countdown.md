# Entropy Skill: Renewal Countdown

Load this file when running weekly sweeps (to check renewal proximity), reviewing the renewal pipeline, or when Jay asks about upcoming renewals. This skill ensures readiness BEFORE a playbook is needed — it is the early warning system that triggers preparation, not the preparation itself.

**Design principle:** Proactive preparation over reactive scrambling. By the time a renewal is 30 days out, every data gap should already be closed, every contact validated, and every playbook generated. No surprises at the finish line.

## Scope

Only process Jay's 4 direct products: **Tivian, Influitive, Lyris, QuickSilver**. Never touch team portfolio folders (ACRM, Artemis, Aurea Platform, Bonzai, Jigsaw Platform, Messageone, Onyx, Pivotal, Saratoga, Stratifyd).

## How It Runs

During every weekly sweep, scan `renewal_date` from YAML frontmatter across all intelligence summaries. Calculate days until renewal. If an account falls within a countdown tier, execute that tier's checklist. Accounts entering a NEW tier (crossing a threshold since last sweep) get flagged in `_Daily_View.md` under a `## Renewal Countdown` section.

**Tier entry is cumulative** — an account at 60 days should have already passed through the 120-day and 90-day tiers. If it hasn't (e.g., newly onboarded account or missed sweeps), run all prior tiers first.

## Countdown Tiers

### Tier 1 — 120 Days Out: Data Validation

**Goal:** Ensure the intelligence foundation is solid. No action planning yet — just confirm the data is trustworthy.

| Check | Action | Flag If |
|-------|--------|---------|
| **Contact validation** | Review Key Contacts table. Check `Last Engaged` dates. Any contact silent 90d+ gets a "Silent 90d+" warning. | Primary contact has no engagement in 90+ days |
| **Notion sync** | Check Notion for ARR changes, status changes, product changes since last update. Update frontmatter if stale. | ARR or status differs from intelligence summary |
| **Data confidence** | Review `data_confidence` in frontmatter. If `low`, flag for data enrichment. | `data_confidence: low` |
| **Intelligence summary currency** | Check `last_updated` date. If older than 60 days, flag as stale. | `last_updated` older than 60 days |
| **Missing dimensions** | Verify all 4 health dimensions have real data (not scored at 0 due to missing data). | 2+ dimensions scored at 0 |

**Output:** For each flagged account, add an entry to `_Daily_View.md`:
```
- [[CustomerName]] (Product) — 120d to renewal — [flags: stale summary, low confidence, silent primary contact, etc.]
```

### Tier 2 — 90 Days Out: Health & Strategy Check

**Goal:** Confirm account health is current and strategy gaps are identified. This is the trigger point for playbook generation.

| Check | Action | Flag If |
|-------|--------|---------|
| **Health recalculation** | Load `_skills/health.md` and recalculate health score. Append row to Health History. | Score dropped 10+ points since last calculation |
| **Playbook existence** | Check customer folder for any `*_Playbook.md` file. | No playbook exists AND account is HVO or ARR > $50K |
| **Interaction trajectory** | Read frontmatter + first 5 lines of last 3 files across Emails/Transcripts/Jira. Assess tone: improving, stable, or deteriorating. | Trajectory is deteriorating |
| **Open commitments** | Check `_Action_Tracker.md` for any open items tagged to this customer. | Any CRITICAL overdue commitments exist |
| **Cancellation intent** | Review `cancellation_intent` in intelligence summary if present. | Score >= 0.5 |

**Playbook trigger rule:** If no playbook exists and the account is HVO or ARR > $50K, surface this explicitly:
```
- [[CustomerName]] (Product, $ARR) — 90d to renewal — NEEDS PLAYBOOK. Load _skills/playbook.md to generate.
```

### Tier 3 — 60 Days Out: Pre-Renewal Brief

**Goal:** Generate a structured brief that gives Jay everything he needs to plan the renewal conversation. This is the last "preparation" checkpoint before the 30-day escalation window.

**Generate a Pre-Renewal Brief** (output conversationally, also append key findings to the intelligence summary under `## Renewal Prep`):

```
PRE-RENEWAL BRIEF: [Customer Name] — [Product] — $[ARR]
Renewal Date: [date] (60 days)

HEALTH TREND:
Current: [score] [band] | 30d ago: [score] | 90d ago: [score]
Direction: [improving / stable / declining]
Confidence: [high / medium / low]

ENGAGEMENT TREND:
Last contact: [date] ([N] days ago) — [who, channel]
Frequency (90d): [X touches/month]
Trajectory: [increasing / stable / decreasing]

LAST 3 INTERACTIONS:
1. [date] — [type] — [one-line summary]
2. [date] — [type] — [one-line summary]
3. [date] — [type] — [one-line summary]

OPEN COMMITMENTS:
[List from Action Tracker, or "None"]

COMPETITIVE SIGNALS:
[Any competitor mentions from emails/transcripts, or "None detected"]

STAKEHOLDER STATUS:
[Key contacts with current stance and last engaged date]

PLAYBOOK STATUS: [Active / Stale / Missing]

RECOMMENDATION:
[What Jay should do in the next 30 days to prepare]
```

**For HVO accounts without a playbook:** Recommend Tier 3 analysis via `_skills/playbook.md`. This is the last comfortable window to generate a full strategic playbook before the 30-day escalation zone.

### Tier 4 — 30 Days Out: Escalation & Readiness

**Goal:** Final gate check. If the account isn't ready, escalate loudly. No more "flag for later" — this is the last checkpoint.

**Escalation alerts (create alerts in `_Daily_View.md`):**

| Condition | Alert |
|-----------|-------|
| No playbook exists for HVO or ARR > $50K | RENEWAL ESCALATION: [[CustomerName]] — 30d out, NO PLAYBOOK. Generate immediately. |
| No contact in 60+ days | RENEWAL ESCALATION: [[CustomerName]] — 30d out, GONE SILENT (last contact [N]d ago). Break silence NOW. |
| Health score < 40 with high confidence | RENEWAL ESCALATION: [[CustomerName]] — 30d out, CRITICAL HEALTH ([score]). Immediate intervention required. |
| `data_confidence: low` still unresolved | RENEWAL ESCALATION: [[CustomerName]] — 30d out, DATA GAPS UNRESOLVED. Cannot assess renewal risk. |

**Generate Readiness Checklist** (append to intelligence summary under `## Renewal Readiness`):

```markdown
## Renewal Readiness — [Renewal Date]

- [ ] Intelligence summary updated within 30 days
- [ ] Primary contact validated (not departed, responded in last 90 days)
- [ ] Health score recalculated with high confidence
- [ ] Active playbook exists (required for HVO / >$50K ARR)
- [ ] No CRITICAL overdue commitments to this customer
- [ ] Sentiment captured (not all Unknown)
- [ ] Renewal pricing prepared ([[Company-Rules]] consulted)

**Status:** [READY / NOT READY — list gaps]
**Escalations:** [count] active
```

**Readiness determination:**
- All boxes checked → Status: READY
- Any unchecked → Status: NOT READY, list which items failed
- Any escalation alert active → always NOT READY regardless of checklist

## Integration Rules

### Weekly Sweep Integration

During every weekly sweep, after ingestion and before dashboard generation:
1. Scan all `renewal_date` values across intelligence summaries.
2. Calculate days to renewal for each account.
3. Run the appropriate tier checklist for any account within 120 days.
4. Surface new tier entries and escalations in `_Daily_View.md`.

### Relationship to Other Skills

| Skill | Relationship |
|-------|-------------|
| `health.md` | Renewal countdown triggers health recalculation at 90 days. Health scoring formula and rules live in health.md. |
| `playbook.md` | Renewal countdown identifies WHEN a playbook is needed. Playbook.md generates it. This skill never generates playbooks itself. |
| `alerting.md` | Renewal countdown creates escalation alerts at 30 days. These follow alerting.md severity conventions (all renewal escalations are High). |
| `ingestion.md` | Weekly sweep runs ingestion first, then renewal countdown checks. Countdown relies on up-to-date data from ingestion. |
| `dashboard.md` | Renewal countdown entries feed into `_Daily_View.md` and `_Portfolio_Dashboard.md`. |
| `commitment-extraction.md` | Countdown checks for open commitments at 90 and 30 days. Commitment data comes from the Action Tracker. |

### _Daily_View.md Format

When accounts enter a countdown tier or have active escalations, add to `_Daily_View.md`:

```markdown
## Renewal Countdown

### Escalations (30 days)
- [[CustomerName]] — $ARR — [escalation reason]

### Pre-Renewal Briefs Due (60 days)
- [[CustomerName]] — $ARR — brief generated / brief needed

### Strategy Check (90 days)
- [[CustomerName]] — $ARR — [playbook status, health status]

### Data Validation (120 days)
- [[CustomerName]] — $ARR — [flags if any, or "clean"]
```

## Decision Rules

- **Account has no `renewal_date` in frontmatter** → Flag as data gap during any sweep. Cannot run countdown without a renewal date.
- **Renewal date is in the past** → Skip countdown. Account may have already renewed or churned. Flag for Jay to update status.
- **Account enters multiple tiers at once** (e.g., first seen at 45 days) → Run all applicable tiers in sequence (120 → 90 → 60 → 30). Do not skip earlier tiers.
- **Playbook exists but is older than 90 days** → Treat as stale at the 60-day and 30-day tiers. Recommend refresh.
- **Health confidence is low** → Do not trigger health-based escalations. Instead, flag for data enrichment. Low-confidence scores reflect missing data, not actual risk (per health.md rules).
- **Account is not HVO and ARR <= $50K** → Playbook is recommended but not required. No escalation for missing playbook at 30 days, but still flag in Daily View.
