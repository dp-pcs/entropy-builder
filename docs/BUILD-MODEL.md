# Build Model — How a Vault Is Shaped Per User & Role

**For:** anyone (e.g. Claude Code) working on how Entropy generalizes across users.
**Date:** 2026-05-20
**Companion to:** [ARCHITECTURE.md](ARCHITECTURE.md) (three-layer model), [DEV-HANDOFF.md](DEV-HANDOFF.md) (handoff/update loop).

This doc covers the part the handoff/update docs don't: **how the builder produces a different vault for a different user/role**, what actually varies today, and what's still hardcoded to the sales use case. That last gap is the crux of the "can this generalize to other user types?" question.

---

## Two build surfaces (don't conflate them)

| Surface | Where | Mode | Produces |
|---|---|---|---|
| **Web builder** | `webapp/` + `pipeline/` | Hosted, automated, connector-driven | `vault.zip` from a wizard + OAuth pulls (Notion/Gmail/Drive/read.ai) |
| **Onboard skill** | `.agent/skills/onboard/SKILL.md` | Interactive, in Claude Code | Initial vault structure via a starting-point-aware interview |

The web builder is the "go to the site, get a scaffold" path. The onboard skill is the "open the repo in Claude Code, answer ~9 questions" path. They overlap in intent but are independent code paths. The rest of this doc is mostly about the **web builder** (the automated build), since that's the one that ships `vault.zip`.

---

## The per-user build pipeline (web)

Entry: `POST /api/wizard/submit` (`webapp/main.py`) → `jobs.run_job` (`webapp/jobs.py`) → `vault_builder.build_vault`.

The wizard collects (`WizardSubmit` in `webapp/main.py`):

- `user_role` — `ic` | `manager` | `external`
- `user_name`, `account_manager_name`, `team_members`
- OAuth tokens (Google, read.ai; Notion is a shared service token)
- `s3_keys` — uploaded files
- `interview_answers` — a free-form dict (e.g. `{"role": "...", "books": [...]}`)

Pipeline steps and where personalization enters:

1. **Wiki generation** (`pipeline/kimi.py`, Pass 1) — builds the **2nd Brain** (Books / Concepts / Frameworks / Mental Models / Principles / MOCs / User-Profile). Input is `interview_answers` + uploaded file text only (`_build_input_block`). **This is genuinely general-purpose** — topics follow whatever source material the user gives (sales, productivity, philosophy, research…). Note: `user_role` is **not** injected into the wiki prompt; only `interview_answers` is.
2. **Gap analysis** (Pass 2) — checks the wiki against a generic "good 2nd brain" bar (≥3 books, ≥5 frameworks, etc.).
3. **Org data pull** (`pipeline/notion_pull.py`) — pulls **customers** from a Notion DB. Role gates the filter: IC → own name; manager → `team_members`.
4. **Gmail / Drive / read.ai** (`webapp/jobs.py`) — role gates strategy: `external` → general emails + Drive docs; otherwise → customer-domain emails. read.ai for all.
5. **Assembly** (`vault_builder.build_vault`) — writes the 2nd Brain + Portfolio Brain + skills + handoff manifest into the zip.

---

## What varies per user/role TODAY

| Input | Shapes | Generalizes? |
|---|---|---|
| `interview_answers` + uploaded files | The entire 2nd-Brain wiki content (Kimi Pass 1) | **Yes** — source-driven, domain-agnostic |
| `user_role` | Notion filter, email strategy, Drive inclusion, `CLAUDE.md` role line + filter rule, extraction waves (`_EXTRACTION_WAVES_BY_ROLE`) | Partly — branches behavior, not the domain model |
| `account_manager_name` / `team_members` | Which customers are pulled | Sales-specific (assumes a customer book) |
| `product_lines` (derived from Notion) | Portfolio scope in `CLAUDE.md`/hot cache | Sales-specific |

---

## What's HARDCODED to sales (copied for every build, any role)

This is the honest gap. Regardless of role, **every** vault gets the sales-shaped **Portfolio Brain**:

- **Customer-intelligence domain model** — `pipeline/notion_pull.py` pulls ARR, renewal dates, HVO/At-Risk tags, success level, churn signals; builds customer hub nodes, domains, and a portfolio snapshot in `_hot_cache.md`. There is no non-customer alternative.
- **Fixed skill set** — `_SKILLS_TO_COPY` in `vault_builder.py` is an unconditional list of **18 sales skills** (`renewal-countdown`, `churn-autopsy`, `competitive-intel`, `playbook`, …). Every user gets all of them; role does **not** gate the list.
- **`Company-Rules.md` + `_analytics/`** — copied verbatim for all (`_ANALYTICS_TO_COPY`).
- **`Role-Specific-Brain-Baselines.md`** (in `input/`) exists as a reference doc but is **not wired into the automated pipeline** — nothing reads it.

**Net:** the 2nd-Brain half generalizes (it's source-driven); the Portfolio-Brain half is sales-shaped and identical for everyone. `user_role` tweaks *connectors and filters*, not the *domain model or skill set*. `external` is the only non-customer-facing path, and even it inherits the Portfolio Brain scaffolding.

```
            ┌───────────────────────────┐
            │  2nd Brain (Kimi wiki)     │  ← GENERAL: driven by interview
            │  Books/Concepts/Frameworks │     answers + uploaded files
            └───────────────────────────┘
            ┌───────────────────────────┐
            │  Portfolio Brain           │  ← SALES-SHAPED: Notion customers,
            │  customers/renewals/skills │     18 fixed skills, Company-Rules —
            └───────────────────────────┘     copied for every role
```

---

## Target model: core + role packs (the real generalization)

The fix (see ARCHITECTURE.md "core + role-pack split"): make the **domain model and skill set selectable by role**, composed at build time, instead of hardcoding the sales frame.

- **Core pack** (role-agnostic, builder-owned): the 2nd-Brain wiki generation, ingestion/lint/dashboard/debrief skills, the `_handoff/` machinery, the `CLAUDE.md` operating contract.
- **Role packs** (per role): the domain model + skills + connector strategy.
  - *Sales*: customer model (Notion → ARR/renewals), `renewal-countdown`/`churn-autopsy`/`competitive-intel`, customer-domain email pull.
  - *Internal-engagements (David's case)*: engagement/stakeholder model, internal-commitment extraction, internal-team email/transcript pull — **no customer book**.
  - *External / generic IC*: lighter still.

Onboarding selects the role → builder composes **core + chosen role pack(s)** → each pack versioned independently (the version-composition open question in ARCHITECTURE.md).

### Concrete code touch-points to get there

1. **`_SKILLS_TO_COPY`** (`vault_builder.py`) → replace the fixed list with a role→skill-set map (mirror the pattern already used by `_EXTRACTION_WAVES_BY_ROLE`).
2. **Portfolio Brain assembly** (`notion_pull.py` + the Portfolio Brain writes in `build_vault`) → gate behind a role/domain selector; introduce a non-customer domain model for non-sales roles.
3. **`Company-Rules.md` / `_analytics/`** → move into the sales role pack, not the unconditional copy.
4. **`interview_answers`** → already general; feed a role into the Kimi system prompt if role-specific wiki emphasis is wanted.
5. **Template layout** → split `entropy-template/` into `core/` + `roles/<role>/` so packs sync from distinct upstreams (the `_handoff/` skill is already the first builder-owned core-pack member).

---

## How to test "a different user type" today

You can't fully — that's the point — but you can see exactly where it breaks:

1. Build with `user_role="external"` and non-sales `interview_answers` (e.g. a researcher's books/notes).
2. Inspect the zip:
   - The **2nd Brain** content correctly reflects the non-sales source material ✅ (generalizes).
   - The **Portfolio Brain** still appears with all 18 sales skills, `Company-Rules.md`, and a customer-shaped `_hot_cache.md` ❌ (hardcoded).
3. That delta is the role-pack work scoped above.

(See DEV-HANDOFF.md §"How to test it in the real world" for the build/inspect commands.)
