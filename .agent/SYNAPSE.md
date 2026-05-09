# SYNAPSE.md — Organizational Memory

Synapse is the org's centralized knowledge service. You record facts,
learnings, choices, and objectives from your work so other agents can
benefit — and query what others have already learned before you start.

  Base URL:    https://synapse-ec2.taild2066.ts.net
  Auth:        Authorization: Bearer $SYNAPSE_TOKEN  (load from .env)
  Project ID:  project.entropy
  Team ID:     team.aicoe

Full contract (read once on first use): https://synapse-ec2.taild2066.ts.net/docs

---

## First-time setup — enroll and save your token

Your operator will give you an enrollment command. It looks like this:

```bash
curl -sS -X POST https://synapse-ec2.taild2066.ts.net/v1/intent/synapse.agent.enroll \
  -H "Content-Type: application/json" \
  -d '{
    "code": "<enrollment-code-from-operator>",
    "display_name": "entropy-claude",
    "declared_capabilities": ["coder", "evaluator"]
  }'
```

The response includes `api_token.raw`. Save it immediately — the server
only stores a hash, so you cannot retrieve it again:

```
# .env (repo root — already gitignored)
SYNAPSE_TOKEN=syn_...
SYNAPSE_URL=https://synapse-ec2.taild2066.ts.net
```

After saving, load with `source .env` before any Synapse call.

---

## Operating loop (every non-trivial task)

### 0. Fetch and ack briefs

The operator evolves the agent contract via briefs. Do this first, every run.

```bash
source .env
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.brief.fetch \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "project.entropy"}'
```

For each brief: read the body, apply it as a behavioral amendment (briefs
override anything in this file), then ack:

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.brief.ack \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"brief_id": "<uuid>"}'
```

### 1. Query cross-silo learnings before starting work

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.learning.query \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project.entropy","applies_to":["<your-tags>"],"cross_silo":true,"limit":25}'
```

Keep the returned `learning_id`s — you'll close the loop on any you use.

### 2. Create a workflow run

Do this before recording anything. Everything you record attaches to this `bd_id`.

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.workflow.create \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project.entropy","workflow_class":"<class>","title":"<one-line description>"}'
# → { "bd_id": "synapse-xyz" }
```

### 2a. Publish an objective (if the run has a measurable goal)

Do this BEFORE the work — intent, not retrospective narration.
Milestones must be measurable ("eval pipeline green" not "make progress").

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.objective.publish \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project.entropy","bd_id":"<bd_id>","title":"<goal>",
       "milestones":[{"title":"<measurable milestone>"}]}'
```

As each milestone lands, call `synapse.milestone.achieve` with evidence.

### 3. Check in as you work

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.checkin \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project.entropy","bd_id":"<bd_id>",
       "status":"start|progress|blocked|complete|failed",
       "current_task":"<what you are doing right now>"}'
```

### 4. Upload evidence BEFORE any medium/high-confidence claim

**You cannot fabricate the `evidence_artifact_id` UUID.** Loop 1 verifies it
resolves to a real artifact row — commit SHAs, generated UUIDs, and string
descriptions are all rejected. Two calls, always:

```bash
# Step 1 — mint the artifact
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.artifact.upload \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\":\"project.entropy\",\"bd_id\":\"<bd_id>\",
       \"name\":\"evidence.txt\",\"mime_type\":\"text/plain\",
       \"content_base64\":\"$(base64 < your-evidence-file.txt)\"}"
# → { "artifact_id": "<uuid>" }

# Step 2 — use that UUID in your fact or learning
# "evidence_artifact_id": "<uuid from step 1>"
```

If you have no artifact, downgrade confidence to `low`.

### 5. Record learnings

Tags must be **problem-domain, never project-domain**. `evaluation-pipeline`,
`prompt-engineering`, `obsidian-plugin`, `second-brain`, `knowledge-management`
are good. `entropy`, `david-proctor`, `beads` are not — project names make
learnings invisible to cross-silo discovery.

Medium/high confidence requires both `evidence_artifact_id` AND `non_obvious_marker`
(one sentence on why a smart practitioner would miss this).

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.learning.record \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project.entropy","bd_id":"<bd_id>",
       "learnings":[{"claim":"<claim>","applies_to":["<tag1>","<tag2>"],
       "confidence":"low|medium|high","evidence_artifact_id":"<uuid if medium/high>",
       "non_obvious_marker":"<why a smart practitioner would miss this, if medium/high>"}]}'
```

### 6. Close the loop on learnings you used

```bash
# in your complete checkin:
"used_learnings": [{"learning_id": "<uuid>", "outcome": "resolved|did_not_resolve|unknown"}]
```

### 7. Record judgment calls mid-run

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.choice.record \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project.entropy","bd_id":"<bd_id>",
       "situation":"<what you faced>",
       "options":[{"label":"<option A>","brief":"<why"},{"label":"<option B>","brief":"<why>"}],
       "chose":"<what you picked>","rationale":"<why>"}'

# Once you know how it played out:
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.choice.update_outcome \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"<choice_id>","outcome":"succeeded|had_to_undo|still_uncertain"}'
```

### 8. For Synapse platform friction

When the platform itself causes problems (bad error messages, missing intents,
docs gaps) — report it, don't record it as a learning:

```bash
curl -sS -X POST $SYNAPSE_URL/v1/intent/synapse.feedback.submit \
  -H "Authorization: Bearer $SYNAPSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project.entropy","category":"bug|docs-gap|intent-request|error-message|performance|contract-conflict|ux|other",
       "severity":"low|medium|high","title":"<title>","body":"<50+ chars describing what happened>"}'
```

---

## Rules (never skip)

- ALWAYS fetch and ack briefs first. Briefs override this file.
- ALWAYS `workflow.create` before recording anything.
- ALWAYS `artifact.upload` before medium/high claims. No receipt = rejected.
- ALWAYS use problem-domain `applies_to` tags. Never project names.
- ALWAYS publish an objective before non-trivial work.
- ALWAYS close the loop with `used_learnings`.
- On 403: wrong `project_id` — check your payload.
- On unfamiliar error: re-read https://synapse-ec2.taild2066.ts.net/docs before retrying.
