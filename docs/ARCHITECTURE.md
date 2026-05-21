# Entropy Architecture — Builder, Cowork Handoff, and Distribution

**Author:** David Proctor
**Date:** 2026-05-20
**Status:** Design doc / decision record. Some components built (see Status table), some proposed.
**Audience:** Anyone deciding how Entropy is generalized, distributed, and kept current across users and roles.

---

## TL;DR

Entropy is **three layers**, not one. Most disagreement about "can the builder generalize?" comes from people defending different layers and calling them the same thing.

1. **Protocol / skills layer** — generalizable, versioned, distributed by the builder. *Already built.*
2. **Scaffolding + initial-push layer** — generated per-user by the builder from an onboarding config. *Already built.*
3. **Deep-extraction layer** — irreducibly per-user (Salesforce, renewal emails, transcript waves), driven interactively in Claude Cowork. *Cannot be pre-baked — and shouldn't be.*

The builder's job is **not** to do 100% of the work. It is to (a) distribute a consistent, versioned structure, (b) do the initial connector pull, and (c) hand Cowork a **machine-readable manifest** that converts the remaining deep-extraction work from open-ended to scoped.

Updates flow one direction: **authoring repo → builder (distribution) → published surface → user vault.** Users check staleness against a **published version signal**, never against a private repo.

---

## The problem this resolves

Two real positions, both partly correct, talking past each other:

- **"Just share the framework."** Correct that the deep extraction is manual and team-specific. Wrong as a *distribution* strategy — it has no versioning, no role adaptation, and no update path. It collapses the moment the upstream skills change. "Share the framework" is the null distribution strategy: it's what you do when you haven't built a channel.
- **"Builder scaffolds, Cowork finishes, and a check-in keeps it current."** Correct about the generalizable layers and the need for an update channel. The risk is the **handoff seam**: "throw the vault into Cowork and let it figure out the rest" is not a contract, it's a vibe, and it's why the continuation feels artisanal every time.

Naming the three layers dissolves the conflict. The "different settings per team" objection is an argument *for* a structured onboarding config (which the pipeline already collects as `JobConfig`), not against generalization.

---

## The three layers

| Layer | Generalizable? | Owner | Mechanism | Status |
|---|---|---|---|---|
| **1. Protocol / skills** — skills, analytics schemas, ingestion rules, the operating `CLAUDE.md` contract | Yes, fully | Authoring repo → builder + sync bot | Versioned template, distributed via published surface | **Built** (sync bot, manifest, `TEMPLATE_VERSION.json`) |
| **2. Scaffolding + initial push** — role frameworks, vault structure, first connector pulls | Shape yes, content no | Builder, per-user | Onboarding interview → `JobConfig` → vault.zip | **Built** (pipeline + webapp) |
| **3. Deep extraction** — Salesforce-via-Chrome, renewal-email reading, transcript waves | No — per-user, interactive | Claude Cowork | Scoped task manifest emitted by the builder | **Proposed** (handoff manifest) |

The connectors in the pipeline today (Notion, Gmail, Drive, read.ai) are Layer 2. The things that are *not* in the pipeline — Salesforce, deep CRM/email reasoning — are Layer 3 by nature, and that's correct: they belong in Cowork where a human is in the loop.

---

## Source of truth — three roles, one direction

There are three distinct "sources of truth" and conflating them is the most common mental-model error.

```
  AUTHORING SoT                DISTRIBUTION SoT               CONSUMPTION SoT
  ─────────────                ────────────────               ───────────────
  Jay's entropy repo     →     entropy_builder/         →     published surface
  (sales role pack)            entropy-template/ +            (latest.json +
  + future role packs          TEMPLATE_VERSION.json          migration payloads)
  [PRIVATE]                    [PRIVATE]                      [PUBLIC signal /
                                                               AUTH-GATED payload]
                                                                      │
                                                                      ▼
                                                               user vaults read
                                                               only THIS surface
```

- **Authoring SoT** — where skill *content* is written. Today that's Jay's repo for the sales role pack. With the core/role-pack split (below), it becomes *one upstream among several*. Private.
- **Distribution SoT** — the compiled, versioned, multi-role artifact that actually ships. `entropy-template/` + `TEMPLATE_VERSION.json`. The canonical answer to "what version exists." Private.
- **Consumption SoT** — the thin published surface user vaults read to answer "am I current?" and "what changed?" Public version signal; auth-gated payloads.

**Rule:** the session-start staleness skill reads the **Consumption SoT only**. It never needs read access to Jay's repo or the builder repo.

---

## Update flow (corrected)

```
   ┌──────────────────────────────────────────────┐
   │ Authoring repo (e.g. jaykhalife/entropy)       │
   │ Jay edits a tracked path AND writes            │
   │ CHANGES/vX.Y.Z.md (changelog-discipline skill) │
   └───────────────────────┬────────────────────────┘
                           │ commit (change + CHANGES in same commit)
                           ▼
   ┌──────────────────────────────────────────────┐
   │ Sync bot (GH Action, ~15 min)                  │
   │ - validates CHANGES frontmatter vs handler schema
   │ - applies handler to entropy-template/         │
   │ - stamps TEMPLATE_VERSION.json + manifest      │
   │ - opens PR sync/jay-vX.Y.Z                     │
   └───────────────────────┬────────────────────────┘
                           │ human (David) reviews & merges
                           ▼
   ┌──────────────────────────────────────────────┐
   │ DISTRIBUTION SoT is now current.               │
   │ Builder publishes latest.json + migration files│
   │ to the CONSUMPTION SoT (public/gated surface). │
   └───────────────────────┬────────────────────────┘
              ┌────────────┴─────────────┐
              ▼                           ▼
   ┌────────────────────┐      ┌────────────────────────┐
   │ New builds pick up  │      │ Returning users:        │
   │ the change          │      │ session-start skill     │
   │ automatically       │      │ detects version gap,    │
   │                     │      │ runs migration applier  │
   └────────────────────┘      └────────────────────────┘
```

### What flows automatically vs. what doesn't

| Upstream change | Auto-flows? | Why |
|---|---|---|
| Edit a file under a tracked path + `content_patch` entry | Yes | Handler exists |
| Add a skill under a tracked path + `add_file` entry | Yes | Handler exists |
| Rename a tracked file/folder + `rename` entry | Yes | Handler exists |
| Split a tracked folder + `structure_split` entry | Yes | Handler exists (with classifier) |
| Change with **no** `CHANGES` entry | **No** | Surfaced as a *drift* flag in the PR for human review — never applied |
| New top-level folder/format **outside** `tracked_paths` | **No** | Needs deliberate `tracked_paths` expansion + possibly a new handler (cross-cutting change: schema + bot validator + applier + test) |

**Versions** originate as the semver Jay assigns in the `CHANGES/vX.Y.Z.md` filename (MAJOR = breaking restructure, MINOR = additive/rename, PATCH = in-place edit), and become canonical when the bot stamps `TEMPLATE_VERSION.json`. Users compare against the builder's stamped version, not Jay's filename.

---

## The published surface (solving "repos may be private")

The builder is the **only** component that needs read access to private authoring repos (deploy key / PAT in the GH Action). Everything users touch is published, decoupled from the private repos.

Split the surface by sensitivity:

| Artifact | Visibility | Contents | Delivery |
|---|---|---|---|
| **Version signal** (`latest.json`) | Public | `{version, date, summary[]}` — numbers and one-line summaries only | Static (S3/CloudFront or a public `GET /api/version/latest`) |
| **Migration payload** (`CHANGES/vX.Y.Z.md` + file bodies) | Auth-gated | Actual skill text, and possibly `Company-Rules.md` (pricing/contract constraints) | Through the builder's existing OAuth (`GET /api/migrations/vX.Y.Z`, scoped to the user's account) |

This gives a clean boundary: **staleness detection is anonymous and cheap; update *content* is gated** behind the same auth the user already used to build their vault. No customer data ever transits the public surface.

> Implementation note: the webapp already has S3 (`webapp/s3.py`) and OAuth (`webapp/oauth.py`). The version signal is a static JSON write on merge; the gated payload is one authenticated endpoint. Lowest-friction path — no new infra.

---

## The handoff manifest (Builder → Cowork contract)

This is the missing piece that makes the tag-team reproducible. The builder emits not just a vault but a **state contract** describing what's done and what remains.

Proposed: `_handoff/STATE.json` at the vault root.

```json
{
  "schema_version": 1,
  "template_version": "1.1.0",
  "built_at": "2026-05-20T14:00:00Z",
  "role": "ic | sales | ...",
  "connectors": {
    "notion":  {"status": "pulled", "records": 47},
    "gmail":   {"status": "pulled", "stubs": 120},
    "readai":  {"status": "pulled", "stubs": 33},
    "salesforce": {"status": "needed", "reason": "no API connector in pipeline; Cowork + Chrome required"}
  },
  "extraction_waves": [
    {"id": "wave-1", "scope": "Tier-1 renewals next 90d", "status": "pending"},
    {"id": "wave-2", "scope": "At-risk accounts", "status": "pending"}
  ],
  "open_gaps": [
    {"category": "data", "description": "No transcripts older than 90d", "blocking": false}
  ]
}
```

Cowork reads this on first session, executes the `needed`/`pending` items as scoped tasks, writes results back into the vault, and updates the manifest. The handoff stops being "figure it out" and becomes a checklist with state.

---

## Session-start staleness skill

A skill that ships **inside the vault** and runs at the top of every Cowork/Claude Code session — the same passive pattern this vault already uses for `_hot_cache.md`.

```
on session start:
  local  = read ./TEMPLATE_VERSION.json   # stamped at build time
  latest = GET <published>/latest.json     # public version signal
  if latest.version > local.version:
     fetch CHANGES/<each missing version>.md   # auth-gated payload
     run migration applier (handlers: rename | add_file | delete_file
                            | structure_split | content_patch)
     report what changed; on content_patch conflict, write <path>.new and flag
  else:
     proceed normally
```

Why a session-start skill beats a website "check-in":

- No re-uploading the vault or re-granting filesystem access to a web service.
- The service never needs to *see* the vault to answer "are you current?" — it's a one-line version diff.
- Self-healing: users converge to current without funneling through Jay or manual redistribution.

The **migration applier** is the one piece `docs/jay-sync/README.md` already flags as *"Not built — next session."* It replays the *same* handlers the sync bot uses against the user's vault (vs. against the template). The handler contracts in `docs/jay-sync/handlers.md` already specify the applier-side behavior, including local-edit conflict handling — so this is completion, not new design.

---

## Core + role-pack skill split

The concrete answer to "how do you adapt to different users" — and the refutation of "it's too specific to generalize."

- **Core pack** (role-agnostic): `ingestion`, `lint`, `dashboard`, `debrief`, plus the operating `CLAUDE.md` contract and analytics schemas. One upstream, synced to everyone.
- **Role packs** (role-specific): e.g. sales gets `renewal-countdown`, `churn-autopsy`, `competitive-intel`, `email-draft`; an internal-engagements role gets its own equivalents (engagement health, stakeholder maps, internal-commitment extraction).

Distribution model becomes: **core synced from a core repo; each role pack synced from its role-owner repo.** Jay's repo stops being a single point of distribution and becomes one role-pack upstream. Onboarding selects the role → builder composes core + the chosen role pack(s) → versioned per pack.

This is what makes "every team has different settings" tractable: settings are captured as a typed onboarding config (`JobConfig` already has role, internal/reseller domains, Notion DB id, team members), and *behavior* differences are captured as role packs. Neither requires hand-editing a shared framework.

---

## Status

| Component | Status | Location |
|---|---|---|
| Skills/analytics template | Built | `entropy-template/Portfolio Brain/` |
| `TEMPLATE_VERSION.json` | Built | `entropy-template/TEMPLATE_VERSION.json` |
| Sync manifest | Built | `entropy-template/.jay-sync-manifest.json` |
| Sync bot + GH Action | Built | `scripts/sync_from_entropy.py`, `.github/workflows/sync-from-entropy.yml` |
| Changelog-discipline skill (the contract for Jay) | Built | `docs/jay-sync/changelog-discipline-skill.md` |
| Handler contracts | Built (v0: rename, add_file, delete_file, structure_split, content_patch) | `docs/jay-sync/handlers.md` |
| Onboarding + pipeline + connectors (Notion/Gmail/Drive/read.ai) | Built | `pipeline/`, `webapp/` |
| **Migration applier (user-side upgrade)** | **Not built** | `pipeline/migrations/` (planned) |
| **Published surface (latest.json + gated payload endpoint)** | **Not built** | `webapp/` (proposed endpoints) |
| **Handoff manifest (`_handoff/STATE.json`)** | **Not built** | `pipeline/vault_builder.py` (proposed emit) |
| **Session-start staleness skill** | **Not built** | ships in vault template (proposed) |
| **Core + role-pack split** | **Not built** | template reorg + multi-upstream sync (proposed) |

---

## Recommended build order

1. **Handoff manifest** — highest leverage; fixes the seam that makes the tag-team feel artisanal. Pure additive emit from `vault_builder.py`.
2. **Migration applier** — completes the half-built sync system; unlocks the staleness skill.
3. **Published surface** — the public `latest.json` + auth-gated payload endpoint. Small, uses existing S3/OAuth.
4. **Session-start staleness skill** — depends on 2 + 3.
5. **Core + role-pack split** — the generalization story; do once the single-role loop is proven end-to-end.

---

## Risks and open questions

- **The handoff seam is the make-or-break.** Without `_handoff/STATE.json`, "builder + Cowork" really is artisanal every time, and the skeptics are right by default. Build it first.
- **Sensitive content on the wire.** `Company-Rules.md` carries pricing/contract constraints. The public/gated split must hold — never let migration payloads leak to the public version signal.
- **Local edits vs. upstream patches.** `content_patch` and `delete_file` can collide with user edits. Handlers already specify conflict behavior (preserve local, write `.new`, flag) — the applier must honor it, and the staleness skill must surface conflicts rather than silently overwrite.
- **Structural changes outside tracked paths.** Genuinely novel folders/formats are *not* automatic. Decide deliberately whether to expand `tracked_paths` + add a handler, or keep them out of the synced surface.
- **Version authority.** Jay assigns semver in the `CHANGES` filename, but the builder stamps the canonical version. If multiple role-pack upstreams each assign versions, the published surface needs a composition scheme (per-pack versions + a composed vault version). Resolve before the core/role-pack split ships.
- **Who owns the core pack?** With the split, the core pack needs an owner/repo distinct from any single role. Likely entropy_builder itself, or a dedicated `entropy-core` repo.
