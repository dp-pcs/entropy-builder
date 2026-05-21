# Dev Handoff — Builder→Cowork Handoff & Update Loop

**For:** the next engineer/agent (e.g. Claude Code) picking this up.
**Date:** 2026-05-20
**Read first:** [ARCHITECTURE.md](ARCHITECTURE.md) (the three-layer model + source-of-truth), then [prd-handoff-manifest-and-migration-applier.md](prd-handoff-manifest-and-migration-applier.md) (the spec for the two builds). For **how a vault is shaped per user/role** (and what's still hardcoded to sales), see [BUILD-MODEL.md](BUILD-MODEL.md).

## 30-second orientation

Entropy is three layers: **(1)** generalizable skills/protocol distributed by this builder, **(2)** per-user scaffolding + initial connector pull the builder generates, **(3)** deep extraction (Salesforce, renewal emails, transcript waves) that can't be pre-baked and is finished interactively in Claude Cowork.

The work in this handoff makes the **seam between layer 2 and layer 3 reproducible** (a machine-readable handoff manifest the builder emits and a Cowork skill that consumes it), and lays the groundwork for the **update loop** (how a user's vault learns it's out of date and self-heals). Without these, the builder→Cowork handoff is artisanal and users drift the moment the upstream template changes.

## What's done (this session)

| Change | File(s) | What it does |
|---|---|---|
| Handoff manifest emit | `pipeline/vault_builder.py` (`_generate_handoff_state`, emit in `build_vault`) | Every vault now ships `_handoff/STATE.json`: connectors pulled/needed, role-derived extraction waves, open gaps, ordered `next_actions` |
| Real connector counts | `pipeline/run.py`, `webapp/jobs.py` | Pass `connector_stats={gmail,readai[,drive]}` into `build_vault` so STATE.json shows real numbers, not `unknown` |
| Session-start skill | `entropy-template/_handoff/SKILL.md` + emit in `build_vault` (inline fallback `_HANDOFF_SKILL_FALLBACK`) | Builder-owned "core pack" skill (NOT synced from Jay). Tells a Cowork session to read STATE.json, surface what's left, execute, write status back, and check for template updates |
| CLAUDE.md wiring | `pipeline/vault_builder.py` (`generate_claude_md`) | Generated vault `CLAUDE.md` now lists running `_handoff/SKILL.md` as **step 1** of the Session Start Protocol |
| Docs | `docs/ARCHITECTURE.md`, `docs/prd-handoff-manifest-and-migration-applier.md` | The model + the build spec |

Backward-compatible: `connector_stats` is an optional last param on `build_vault`. Verified: **8/8 pipeline tests pass** (`test_vault_builder.py` + `test_integration.py`), and the existing tests call `build_vault` positionally without the new param.

## What's NOT done (next builds, in priority order)

1. **Migration applier** — `pipeline/migrations/` (does not exist yet). Replays the same handlers the sync bot uses (`docs/jay-sync/handlers.md`: `rename`/`add_file`/`delete_file`/`structure_split`/`content_patch`) against a *returning user's vault*, honoring local-edit conflicts (never silently overwrite). **This is what makes the staleness check in `_handoff/SKILL.md` actually do something.** Spec: PRD "Build 2." Critical constraint: factor the handler/classifier core so `scripts/sync_from_entropy.py` (bot) and the applier share one implementation and can't drift.
2. **`GET /api/migrations/{version}` endpoint** — `webapp/` (only the version signal `GET /api/template/version` exists today). Auth-gated, because payloads can carry `Company-Rules.md` (pricing). Webapp already has OAuth + S3.
3. **`connector_stats` "skipped" nuance** — `run.py` doesn't pull Drive, so Drive shows `unknown`; it should arguably be `skipped`. Minor. Decide whether to pass an explicit skipped signal.
4. **Open question — version composition** — once skills split into core + role packs (each versioned independently), `template_version` becomes a composed value. Resolve before that split ships. (ARCHITECTURE.md "core + role-pack split.")

## Why (the reasoning, briefly)

- **Handoff manifest** turns "throw the vault into Cowork and let it figure it out" into a scoped checklist with state. It's the single highest-leverage fix because it's the seam everything else depends on.
- **Session-start skill** is the consumer — without it, STATE.json is a file nobody reads.
- **Migration applier** closes the update loop. The upstream half (Jay's repo → this builder's template, via the sync bot) is already built; the applier is the downstream half (template → existing user vaults). Until it exists, "share the framework" wins by default because users can't stay current.

## How to test it in the real world

### A. Run the automated tests
```bash
# Sandbox/dev only — these deps are normally provided by requirements.txt:
pip install pytest pytest-mock notion-client --break-system-packages
python3 -m pytest tests/pipeline/test_vault_builder.py tests/pipeline/test_integration.py -q
# Webapp tests additionally need starlette etc.:  pip install -r requirements.txt
python3 -m pytest tests/webapp/test_jobs.py -q
```

### B. Build a real vault and inspect the handoff artifacts
```bash
# Full pipeline (needs real creds in config.json: Notion/Google/read.ai/Fireworks)
python -m pipeline.run --config config.json --output vault.zip

unzip -o vault.zip -d vault/
cat vault/_handoff/STATE.json        # connectors show real counts; salesforce=needed; waves pending
cat vault/_handoff/SKILL.md          # the session-start skill
sed -n '1,25p' vault/CLAUDE.md       # confirm step 1 of Session Start Protocol = _handoff/SKILL.md
cat vault/vault_version.json         # template_version + update_check_url
```
Expect: `_handoff/STATE.json` and `_handoff/SKILL.md` present; `connectors.gmail/readai` show `pulled` with counts; `connectors.salesforce.status == "needed"`; `extraction_waves` present for ic/manager (empty for external).

### C. Exercise the Cowork/Claude Code consumption
```bash
cd vault && claude     # open the built vault in Claude Code
```
Confirm the agent, at session start: reads `_handoff/STATE.json` first, surfaces `next_actions` (e.g. "Wire salesforce…", "Run extraction wave-1…"), and checks `vault_version.json` against the update URL. Pick one action; confirm it then writes status back into `STATE.json` (`pending`→`done`, prune `next_actions`).

### D. Exercise the update path (upstream → builder), end-to-end
1. In Jay's repo, edit a tracked file (`Portfolio Brain/_skills/...`) and add `CHANGES/vX.Y.Z.md` per `docs/jay-sync/changelog-discipline-skill.md`. Commit both together.
2. The sync bot (`.github/workflows/sync-from-entropy.yml`, ~15 min) opens PR `sync/jay-vX.Y.Z` in this repo. Review + merge.
3. Confirm `entropy-template/TEMPLATE_VERSION.json` bumped.
4. Rebuild a vault (step B) → confirm `STATE.json.template_version` and `vault_version.json` reflect the new version.

**Known gap:** step D proves the *new-build* path. An **existing** vault can't auto-upgrade until the migration applier (Build 2) exists — that's exactly the gap to close next.

## Guardrails when working in here

- `_handoff/SKILL.md` is **builder-owned** ("core pack"). Do **not** add a `CHANGES/` entry for it and do **not** let the sync bot track it — it's not Jay's. Keep `entropy-template/_handoff/SKILL.md` and the `_HANDOFF_SKILL_FALLBACK` constant in `vault_builder.py` in sync.
- `ENTROPY_TEMPLATE_PATH` = `/app/entropy-template` in the Docker image; the build reads skills, analytics, `Company-Rules.md`, and `TEMPLATE_VERSION.json` from there. The `run.py` docstring example pointing at Jay's repo is stale — ignore it.
- The vault's local version file is `vault_version.json` (key `template_version`); the template's is `TEMPLATE_VERSION.json` (key `version`). The applier reads the vault's.
- Migration payloads can contain sensitive content (`Company-Rules.md`). Keep the version *signal* public, the *payload* auth-gated. Don't log payload bodies.
