# PRD — Handoff Manifest & Migration Applier

**Author:** David Proctor
**Date:** 2026-05-20
**Status:** Draft for build
**Covers:** Architecture builds #1 (handoff manifest) and #2 (migration applier). See [ARCHITECTURE.md](ARCHITECTURE.md).
**Related:** [jay-sync/README.md](jay-sync/README.md), [jay-sync/handlers.md](jay-sync/handlers.md), [jay-sync/manifest-format.md](jay-sync/manifest-format.md)

---

## Why these two, why now

These are the two builds that make the "builder scaffolds → Cowork finishes → vault self-heals" model real instead of artisanal.

- **Handoff manifest** closes the *seam between the builder and Cowork.* Today the handoff is "open the vault in Cowork and let it figure out the rest." That is not reproducible. The manifest turns it into a scoped checklist with state.
- **Migration applier** closes the *update loop.* The sync bot already mirrors Jay's changes into the template (upstream half). The applier replays those same changes against a returning user's vault (downstream half). Without it, users drift the moment the template moves, and "share the framework" wins by default.

Both are additive. Neither requires touching the existing pipeline behavior.

---

## Current state (what already exists)

Verified in the repo as of this PRD:

- `pipeline/vault_builder.py::build_vault()` already emits, at the vault root:
  - `vault_version.json` → `{template_version, built_at, update_check_url}` where `update_check_url = https://entropy.elelem.expert/api/template/version`
  - `Portfolio Brain/CHANGELOG.md` (human-readable, from `TEMPLATE_VERSION.json.history`)
  - `gaps.json` → the gap items the status page already reads
- `entropy-template/TEMPLATE_VERSION.json` — canonical version + history (distribution SoT)
- `entropy-template/.jay-sync-manifest.json` — tracked paths, per-file hashes, ingested changes
- `scripts/sync_from_entropy.py` + `.github/workflows/sync-from-entropy.yml` — the upstream sync bot
- `docs/jay-sync/handlers.md` — handler contracts (v0: `rename`, `add_file`, `delete_file`, `structure_split`, `content_patch`), each already specifying **applier-side behavior** including local-edit conflict handling
- `pipeline/migrations/` — **does not exist yet** (this PRD)

**Naming reconciliation:** the vault's local version file is `vault_version.json` (key: `template_version`). The template's is `TEMPLATE_VERSION.json` (key: `version`). The applier and staleness check read the *vault's* `vault_version.json`. ARCHITECTURE.md's references to "the vault's `TEMPLATE_VERSION.json`" mean this file.

---

# Build 1 — Handoff Manifest (`_handoff/STATE.json`)

## Goal

The builder emits a machine-readable description of **what it did** and **what's left for Cowork**, so a Cowork session can resume deterministically rather than re-deriving scope every time.

## Non-goals

- Not a task runner. It describes work; it does not execute Layer-3 extraction.
- Not a replacement for `gaps.json` (which is content gaps the *builder* found). STATE.json is *handoff* state across the builder/Cowork boundary.

## Schema (`_handoff/STATE.json`, schema_version 1)

```json
{
  "schema_version": 1,
  "template_version": "1.1.0",
  "built_at": "2026-05-20",
  "role": "ic",
  "user_name": "David Proctor",
  "connectors": {
    "notion":     {"status": "pulled",  "records": 47},
    "gmail":      {"status": "pulled",  "stubs": 120},
    "readai":     {"status": "pulled",  "stubs": 33},
    "drive":      {"status": "skipped", "reason": "not granted in onboarding"},
    "salesforce": {"status": "needed",  "reason": "no API connector in pipeline; requires Cowork + Chrome"}
  },
  "extraction_waves": [
    {"id": "wave-1", "scope": "Tier-1 renewals in next 90d", "status": "pending"},
    {"id": "wave-2", "scope": "At-risk accounts",            "status": "pending"}
  ],
  "open_gaps": [
    {"category": "data", "description": "No transcripts older than 90d", "blocking": false}
  ],
  "next_actions": [
    "Wire Salesforce via Chrome and pull opportunity/renewal fields",
    "Run extraction wave-1 against Tier-1 renewals"
  ]
}
```

### Field contract

| Field | Source | Notes |
|---|---|---|
| `schema_version` | constant `1` | bump on breaking schema change |
| `template_version` | `TEMPLATE_VERSION.json.version` (falls back to `null`) | same value stamped into `vault_version.json` |
| `built_at` | `date.today().isoformat()` | ISO date |
| `role` | `config.user_role` | `ic` / `manager` / `external` |
| `user_name` | `config.user_name` | |
| `connectors.*.status` | derived | `pulled` / `skipped` / `needed` / `error` |
| `connectors.notion.records` | `len(customers)` | |
| `connectors.gmail.stubs` / `readai.stubs` | from `connector_stats` (optional param) | if not provided, status `unknown` |
| `connectors.salesforce` | always `needed` for now | Layer-3 connector, Cowork-only |
| `extraction_waves` | role → wave map | sales/ic get renewal+at-risk waves; external gets none |
| `open_gaps` | projected from `gap_items` (category `data`/`moc`) | `blocking` defaults `false` |
| `next_actions` | derived from `needed` connectors + `pending` waves | human-readable, ordered |

## Implementation (builder side)

Additive and backward-compatible:

1. Add `_generate_handoff_state(config, customers, gap_items, connector_stats=None) -> dict` to `vault_builder.py`.
2. Add an **optional** `connector_stats: dict | None = None` parameter to `build_vault(...)` (defaults to `None`, so existing callers in `run.py`/`jobs.py` keep working unchanged).
3. Emit `zf.writestr("_handoff/STATE.json", json.dumps(_generate_handoff_state(...), indent=2))` inside the existing `with zipfile.ZipFile(...)` block, next to the `vault_version.json` write.
4. (Optional, later) thread real `connector_stats` from `run.py`/`jobs.py` where the email/transcript counts are known (`email_stubs`, `transcript_stubs`) so the counts are exact instead of `unknown`.

The scaffold for steps 1–3 ships with this PRD (see `vault_builder.py`). Step 4 is a follow-up to avoid touching the job orchestration in the same change.

## Cowork-side consumption (separate, not in this build)

A Cowork session-start skill reads `_handoff/STATE.json`, presents `next_actions`, and on completion of each wave/connector writes status back (`pending` → `done`) and re-saves the file. Spec lives with the staleness skill (Architecture build #4).

## Acceptance criteria

- `_generate_handoff_state` returns a dict that round-trips through `json.dumps`/`json.loads`.
- With `connector_stats=None`: notion shows real `records`; gmail/readai show `status: unknown`; salesforce shows `needed`.
- With `connector_stats={"gmail": 120, "readai": 33}`: those counts appear.
- `role="external"` produces zero extraction waves.
- Existing `build_vault` callers run unchanged (param is optional).

---

# Build 2 — Migration Applier (`pipeline/migrations/`)

## Goal

Given a user's vault that is behind the current template, fetch the intervening `CHANGES/vX.Y.Z.md` files and replay each handler against the *vault directory*, honoring local-edit conflicts, so the vault converges to the current template version.

## Inputs

- The vault's local version: `vault_version.json.template_version`.
- The published version + migration payloads (consumption SoT). Per the existing `update_check_url`:
  - **Version signal:** `GET https://entropy.elelem.expert/api/template/version` → `{version, ...}` (public).
  - **Migration payload:** `GET https://entropy.elelem.expert/api/migrations/{version}` → the `CHANGES/vX.Y.Z.md` frontmatter + file bodies (auth-gated; may contain `Company-Rules.md`). *Endpoint to be added; see Open Questions.*

## Handler parity with the sync bot

The applier replays the **same v0 handlers** the bot validates, but targets the user's vault instead of `entropy-template/`. `handlers.md` already specifies applier-side behavior for each — implement to that spec:

| Handler | Applier behavior (per handlers.md) |
|---|---|
| `rename` | `git mv` (or fs move) in vault; rewrite `[[from/...]]` → `[[to/...]]` wikilinks across all `.md` |
| `add_file` | write file at path; if user already has one, **preserve theirs**, report conflict |
| `delete_file` | if local hash == last-known → delete; if diverged → **keep local**, report |
| `structure_split` | create destinations; run classifier (`participant_domain_majority` / `frontmatter_field_match` / `filename_regex` / `manual`); move files; per-file report |
| `content_patch` | if local hash == last-known source hash → overwrite; if diverged → write `<path>.new`, **keep local**, report conflict |

**Conflict principle (non-negotiable):** never silently overwrite user edits. Diverged files are preserved; the applier reports and (for `content_patch`) drops a `.new` sidecar.

## Flow

```
applier.apply(vault_dir):
  local   = read vault_dir/vault_version.json.template_version
  latest  = GET /api/template/version
  if latest <= local: report "current"; stop
  versions = ordered (local, latest]            # apply in semver order
  for v in versions:
     changes = GET /api/migrations/v             # auth-gated
     validate frontmatter vs handlers schema
     for entry in changes.changes:
        run handler(entry) against vault_dir     # collect actions + conflicts
  write vault_dir/vault_version.json.template_version = latest
  emit migration report (applied, skipped, conflicts) to outputs/
```

## Module layout

```
pipeline/migrations/
├── __init__.py
├── applier.py        # orchestration: version diff, ordered apply, report
├── handlers.py       # one function per handler type; shared with bot where possible
├── classifiers.py    # participant_domain_majority, frontmatter_field_match, filename_regex, manual
├── client.py         # fetch version signal + migration payloads (auth-gated)
└── report.py         # migration report writer (outputs/)
```

Where logic overlaps the sync bot (`scripts/sync_from_entropy.py`), factor the shared handler/classifier core into `pipeline/migrations/` and have the bot import it, so bot and applier can never diverge in handler semantics. This is the single most important design constraint: **one handler implementation, two call sites (template vs. vault).**

## Acceptance criteria

- Replays a multi-version gap in semver order and lands `vault_version.json` at the latest.
- Each handler matches the documented applier behavior in `handlers.md`.
- Local-edit conflicts are preserved (never overwritten); `content_patch` writes `.new`.
- Produces a migration report under the vault's `outputs/`.
- Handler/classifier core is shared with the sync bot (no duplicate implementation).
- Dry-run mode (`--dry-run`) prints the plan without touching files.

---

## Risks & open questions

- **Migration payload endpoint.** `GET /api/migrations/{version}` does not exist yet; only the version signal does. Build it on the webapp (has OAuth + S3 already) and gate it to the user's account. Until then, the applier can read migrations from a local checkout for testing.
- **Sensitive content.** Migration payloads can carry `Company-Rules.md` (pricing/contracts). The version signal stays public; the payload must be auth-gated. Do not log payload bodies.
- **Auth model for the applier.** The applier runs on the user's machine (or in their Cowork session). It needs the same token the user used to build the vault. Decide: reuse the builder session token, or issue a long-lived per-vault read token at build time and store it in `.env`.
- **Version composition under core + role-pack split.** Once multiple upstreams each version independently, `template_version` becomes a composed value. Resolve the composition scheme before that split ships (flagged in ARCHITECTURE.md).
- **Wikilink rewrite blast radius.** `rename` rewrites links across the whole vault. Use a word-boundary-guarded regex and include the rewrite count in the report so the user can sanity-check.
