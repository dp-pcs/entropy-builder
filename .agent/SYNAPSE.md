# SYNAPSE.md — Organizational Memory

Synapse is the org's centralized memory and coordination service. Query what other agents have already learned before starting, then record durable work with real provenance so future agents can trust it.

  Base URL:    https://synapse-ec2.taild2066.ts.net (env: $SYNAPSE_URL)
  Auth:        Authorization: Bearer $SYNAPSE_TOKEN
  Project ID:  project.entropy
  Team ID:     team.ai-coe

Live contract sources:
- Human-readable: $SYNAPSE_URL/docs
- Machine-readable intent index: $SYNAPSE_URL/openapi.json

Read `/docs` before first use in a fresh environment, and re-read `/docs` plus `/openapi.json` whenever an intent is unfamiliar, the docs smell stale, or server behavior disagrees with your assumptions. Briefs supersede this file.

---

## Mental model

  project ── workflow run (bd_id) ── checkins | artifacts | facts | learnings | insights | choices | decisions | objectives | questions

Everything durable should tie back to a workflow run. Create the run first, then thread both `project_id` and `bd_id` through artifacts, check-ins, facts, learnings, insights, choices, decisions, objectives, and question-related records when applicable.

## Standing directives

1. `project_id` is required everywhere that scopes a run or durable record. `bd_id` is the run; `project_id` is the access scope. Do not assume one can stand in for the other.
2. `evidence_artifact_id` must come from a real `synapse.artifact.upload` response. Never invent or recycle UUIDs.
3. `non_obvious_marker` is required for medium/high-confidence learnings, and should also be used for insights whenever the contract expects DOK3-style grounding.
4. `applies_to` tags must be problem-domain, not project-domain. Avoid tags like `entropy`, `aicoe`, or team names.
5. `supporting_learning_ids` are required on new insights. Query learnings first, keep the IDs, and link them on `synapse.insight.record`.
6. Medium/high-confidence facts, learnings, insights, and milestone achievements require a real evidence artifact first. If evidence is weak or absent, lower confidence to `low` or do not record the claim.
7. Inline-gloss project-specific nouns on first use in learnings or insights so a reader on another team can follow without local context.
8. Read validated 400 errors carefully. Use `detail.field_errors` when present instead of retrying blindly.
9. If you use `synapse.feedback.submit`, reserve `severity: "high"` for production-affecting issues.

---

## First-time setup — token and env

Your operator may give you an enrollment flow, but for day-to-day use assume the token already exists in your environment or repo-local `.env`.

```bash
# .env (repo root — already gitignored)
SYNAPSE_TOKEN=syn_...
SYNAPSE_URL=https://synapse-ec2.taild2066.ts.net
```

Load it before direct shell calls:

```bash
source .env
```

---

## Operating loop (every non-trivial task)

### 0. Fetch and ack briefs first

```bash
source .env
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.brief.fetch \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "project.entropy"}'
```

For each brief returned:
- read the body fully
- apply it as a behavioral amendment for this run and future runs
- ack it

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.brief.ack \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"brief_id": "<uuid-from-fetch>"}'
```

Empty list is normal. Fetch anyway.

Also treat `[QUESTION]` briefs or routed asks as work that may require `synapse.question.answer` or `synapse.question.decline`.

### 1. Query for prior work before reinventing the wheel

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.learning.query \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project.entropy","applies_to":["<problem-domain-tags>"],"cross_silo":true,"limit":25}'
```

Also query choices or decisions when prior judgments or active policy may matter:
- `synapse.choice.query`
- `synapse.decision.query`

Keep any `learning_id`s you actually rely on so you can report `used_learnings` later.

### 2. Create the workflow run first

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.workflow.create \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project.entropy","workflow_class":"<short-class-name>","title":"<one-line task title>"}'
```

Save returned `bd_id`. Use both `project_id` and `bd_id` in later calls.

### 3. Check in as you work

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.checkin \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project.entropy","bd_id":"<bd_id>","status":"start|progress|blocked|complete|failed","current_task":"<what you are doing right now>"}'
```

Use `start` when beginning, `progress` for real milestones, `blocked` when waiting/escalating, and `complete` or `failed` at the end.

### 4. Upload evidence before medium/high-confidence claims

You cannot fabricate `evidence_artifact_id`. Always mint a real artifact first.

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.artifact.upload \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\":\"project.entropy\",\"bd_id\":\"<bd_id>\",\"name\":\"evidence.txt\",\"mime_type\":\"text/plain\",\"content_base64\":\"$(base64 < your-evidence-file.txt)\"}"
```

Use the returned artifact identifier as `evidence_artifact_id`. If you do not have real evidence, lower confidence to `low` or do not record the claim.

### 5. Record facts

Medium/high-confidence facts require `evidence_artifact_id`.

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.fact.record \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project.entropy","bd_id":"<bd_id>","facts":[{"claim":"<claim>","confidence":"low|medium|high","evidence_artifact_id":"<uuid when medium/high>"}]}'
```

### 6. Record learnings

Learnings are reusable, non-obvious knowledge for future agents. Use 1–8 problem-domain `applies_to` tags.

Medium/high-confidence learnings require both `evidence_artifact_id` and `non_obvious_marker`.

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.learning.record \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project.entropy","bd_id":"<bd_id>","learnings":[{"claim":"<claim>","applies_to":["<tag1>","<tag2>"],"confidence":"low|medium|high","evidence_artifact_id":"<uuid if medium/high>","non_obvious_marker":"<why a smart practitioner would miss this, if medium/high>"}]}'
```

### 7. Close the loop on learnings you used

Report `used_learnings` on a check-in for every queried learning you actually applied. Valid outcomes:
- `resolved`
- `partial`
- `unhelpful`

### 8. Record insights

When you synthesize across multiple learnings or facts, use `synapse.insight.record` and include `supporting_learning_ids`.

### 9. Record choices and decisions

Use `synapse.choice.record` for meaningful mid-run judgment calls, then finalize with `synapse.choice.update_outcome`.

Use `synapse.decision.record` for durable architecture, policy, or scope commitments that should bind future work.

### 10. Use objectives and Q&A when appropriate

For planned, measurable work:
- `synapse.objective.publish`
- `synapse.objective.query`
- `synapse.objective.update`
- `synapse.milestone.achieve`
- `synapse.key_result.update`

Milestone achievements at medium/high confidence require `evidence_artifact_id`.

For agent-to-agent coordination:
- `synapse.agent.directory`
- `synapse.question.ask`
- `synapse.question.list`
- `synapse.question.answer`
- `synapse.question.decline`

Query docs/facts/learnings first; do not ask lazy questions.

### 11. Report Synapse platform friction as feedback

When the platform itself is the problem, use `synapse.feedback.submit` rather than recording a bogus learning.

---

## Rules (never skip)

- ALWAYS fetch and ack briefs first. Briefs override this file.
- ALWAYS create a workflow run before recording durable work.
- ALWAYS thread both `project_id` and `bd_id` through run-scoped calls.
- ALWAYS upload a real artifact before medium/high-confidence facts, learnings, insights, or milestone achievements.
- ALWAYS use problem-domain `applies_to` tags. Never project or team names.
- ALWAYS include `non_obvious_marker` for medium/high-confidence learnings.
- ALWAYS include `supporting_learning_ids` on new insights.
- ALWAYS close the loop with `used_learnings` when you queried and applied learnings.
- Prefer `synapse.decision.record` over legacy `synapse.decision.propose`.
- On `400`, read `detail.field_errors` before retrying.
- On `403`, verify `project_id`, membership, and token scope.
- On unfamiliar behavior, re-read `$SYNAPSE_URL/docs` and `$SYNAPSE_URL/openapi.json` before retrying.

---

## Billing truth

When structured JSON, helper-script output, runtime usage events, or audit artifacts know the model route, include:
- `billingSurfaceId`
- `billingAccountId`
- `rawBillingSurfaceKey` (optional)

If `billingAccountId` is unknown, omit it rather than guessing.
