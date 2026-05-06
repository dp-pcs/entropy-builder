---
name: onboard
description: First-run onboarding for new Entropy users. Detects their starting point, interviews them with the minimum questions needed, then builds their initial Second Brain structure.
trigger: "onboard|first run|new user|setup brain|start here|build my brain"
version: 1.0.0
author: entropy
---

# onboard

New user entry point. Detects what they already have, routes them to the right path, interviews them with only the questions their existing content can't answer, then builds their vault.

---

## Before you start

Ask the user for their Obsidian vault path if not already known:

> "What's the full path to your Obsidian vault? (e.g. ~/Documents/My-Second-Brain or just tell me the folder name and I'll find it)"

Store this as `VAULT_PATH`. Run `setup-inbox.py` against it:

```bash
python3 .agent/skills/process-inbox/setup-inbox.py "$VAULT_PATH"
```

---

## Step 1 — Detect starting point

Present this exactly, formatted as shown:

---

**Welcome. Let's build your Second Brain.**

Before I ask you anything, tell me where you're starting from — this determines how much I need to ask you.

**Where do your notes currently live?** (type a number)

```
1. Nowhere organized — scattered across email, memory, Slack, random docs
2. Workflowy — I can export my notes or BrainLifts
3. Notion — I have pages I can export to markdown
4. Other markdown or text files — I have .md, .txt, or structured notes somewhere
5. A different Obsidian vault — I already use Obsidian, just not this structure
```

---

## Step 2 — Branch by starting point

### Path 1: Fresh start

Go straight to [Phase 0 Interview](#phase-0-interview). Run all questions.

---

### Path 2: Workflowy export

Say:

> "Export your Workflowy outline as markdown (File → Export → Markdown), drop the file into `[VAULT_PATH]/00-Inbox/`, and tell me the filename."

Once they confirm the file is there:

```bash
python3 .agent/skills/process-inbox/split-brainlifts.py \
  "$VAULT_PATH/00-Inbox/<filename>" \
  --output-dir "$VAULT_PATH/00-Inbox"

python3 .agent/skills/process-inbox/analyzer.py "$VAULT_PATH"
```

Read `$VAULT_PATH/proposals.md`. Note the topic clusters detected. Then go to [Gap Interview](#gap-interview) — skip any Phase 0 questions answerable from the content.

---

### Path 3: Notion export

Say:

> "In Notion: Settings → Export → Export format: Markdown & CSV. Drop the exported folder into `[VAULT_PATH]/00-Inbox/` and tell me when it's there."

Once confirmed:

```bash
python3 .agent/skills/process-inbox/analyzer.py "$VAULT_PATH"
```

Read `$VAULT_PATH/proposals.md`. Then go to [Gap Interview](#gap-interview).

---

### Path 4: Other markdown files

Say:

> "Drop your files into `[VAULT_PATH]/00-Inbox/` and tell me when they're in there. Doesn't have to be perfect — just get them in the folder."

Once confirmed:

```bash
python3 .agent/skills/process-inbox/analyzer.py "$VAULT_PATH"
```

Read `$VAULT_PATH/proposals.md`. Then go to [Gap Interview](#gap-interview).

---

### Path 5: Existing Obsidian vault

Ask:

> "What's the path to your existing vault?"

Then scan it:

```bash
find "$EXISTING_VAULT" -name "*.md" | wc -l
ls "$EXISTING_VAULT"
```

Note: file count, top-level folder structure, any existing frameworks or MOC files. Then go to [Gap Interview](#gap-interview), skipping questions answerable from what you found.

---

## Phase 0 Interview

Full interview for fresh-start users. Use **numbered options wherever possible**. User types a number or comma-separated numbers. Always allow "+ tell me more" after any pick.

Present questions one at a time. Wait for each answer before continuing.

---

**Q1 — Your role**

```
What's your role? (type a number or describe your own)

1. Account Executive (AE) — new business, closing
2. Account Manager (AM) — existing accounts, expansion
3. Customer Success Manager (CSM) — retention, health, renewal
4. Sales Manager / Team Lead — managing a sales team
5. VP / Director of Sales — leading the function
6. Something else — tell me

→
```

---

**Q2 — How you make decisions**

```
How do you make decisions? (pick 2–3 that fit)

1. Data-driven — I need numbers before I move
2. Intuitive — I read patterns and trust my gut
3. Collaborative — I talk it through with the team first
4. Decisive — I move fast and course-correct
5. Structured — I follow a process or framework
6. Risk-tolerant — I'll bet big if the upside is right

→
```

---

**Q3 — How others describe you**

```
How do colleagues typically describe you? (pick 1–2)

1. Direct — no-nonsense, tell it straight
2. Relationship-focused — warm, diplomatic, builds trust
3. Energetic — storyteller, engaging, owns the room
4. Thoughtful — measured, careful, doesn't rush
5. Data-heavy — facts first, numbers-driven
6. Strategic — big-picture, connects dots others miss

→
```

---

**Q4 — Top priorities right now**

```
What are your top 3 priorities over the next 90 days?
(free text — just type them out, one per line)

Priority 1:
Priority 2:
Priority 3:

→
```

---

**Q5 — Your spiky POVs**

```
What 2–3 things do you believe that your colleagues might push back on?
(These are your differentiators — what you'd go to the mat for)

Example: "Renewal is won 6 months before the renewal date, not at renewal"
Example: "We spend too much time on new logos and not enough on expansion"

POV 1:
POV 2:
POV 3 (optional):

→
```

---

**Q6 — What you're genuinely better at than most**

```
What 1–2 things are you rare at? Be specific.

Bad: "I'm a good communicator"
Good: "I can read an executive's real objection in the first 5 minutes"
Good: "I build multi-threaded relationships faster than anyone I've worked with"

Strength 1:
Strength 2 (optional):

→
```

---

**Q7 — Frameworks you actually use**

```
Which of these do you actually use in your daily work? (pick all that apply)

Sales methodology:
1. MEDDIC / MEDDPICC
2. Challenger Sale
3. SPIN Selling
4. Command of the Message / Force Management
5. Value Selling
6. Sandler
7. None of the above / I have my own approach

Account planning:
8. QBR / Executive Business Reviews
9. Account tiering (e.g. Tier 1/2/3)
10. Stakeholder mapping
11. Success plans / joint plans with customers

Other:
12. Something else — tell me

→
```

---

**Q8 — Your natural topic clusters**

```
What are the main "buckets" your work falls into?
(These become your Maps of Content — your navigation system)

Common ones for sales/account roles:
1. Pipeline & Deal Management
2. Account Planning & Expansion
3. Renewal & Retention
4. Competitive Intelligence
5. Negotiation & Deal Structuring
6. Executive Engagement & Relationships
7. Product Knowledge
8. Team & Coaching (if you manage)

Pick the ones that fit, add your own, or just describe your buckets:

→
```

---

**Q9 — Decision authority**

```
Quick housekeeping — what decisions do YOU own without needing approval?
(This goes into your CLAUDE.md as your operating boundary)

Examples:
- Discounts up to X%
- Contract term extensions up to X days
- Feature commitments (yes/no)
- Professional services scope

Just ballpark it — we'll refine later:

→
```

---

After Q9, say:

> "That's everything I need. Give me a minute to build your brain."

Then proceed to [Build Phase](#build-phase).

---

## Gap Interview

For users who came in with existing content (Paths 2–5). Only ask questions that the content analysis couldn't answer. At minimum always ask Q1 (role), Q4 (priorities), Q5 (POVs), and Q9 (decision authority) — these are personal and can't be inferred.

Skip Q7 (frameworks) if clear from content. Skip Q8 (clusters) if topic clusters were detected by analyzer.

Present the same numbered format. Introduce it like:

> "I've analyzed your existing notes. I can see [summary of what you found — e.g. 'you have a lot of content around enterprise account management and competitive positioning']. I only need to ask a few things I couldn't figure out from your content."

---

## Build Phase

After the interview, build the vault in this order:

### 1. Create the profile

Create `$VAULT_PATH/[FirstName]-[LastName]-Profile.md` using answers from the interview. Use the template in `input/Second-Brain-Onboarding-Checklist.md` (Task 1.1 section) as the format. Fill every field from their answers.

### 2. Create the vault CLAUDE.md

Create `$VAULT_PATH/CLAUDE.md` with:
- Their name and role at the top
- Decision authority from Q9
- A note that this is their personal operating boundary file
- Placeholder sections for constraints they can fill in later

### 3. Seed frameworks

Based on their role and Q7 answers, copy relevant templates from `input/Role-Specific-Brain-Baselines.md` into `$VAULT_PATH/frameworks/`. Rename files to match their actual use (e.g. `Enterprise-Account-Planning.md` not `Template-Account-Planning.md`).

Sales roles get at minimum:
- Enterprise Account Planning (or SMB Account Planning if their segment is SMB)
- Renewal & Retention Strategy
- One framework from their Q7 picks

### 4. Create initial MOCs

For each cluster from Q8 (or detected clusters), create a stub MOC in `$VAULT_PATH/mocs/[Topic]-MOC.md`:

```markdown
---
type: moc
topic: "[Topic]"
tags: []
last_updated: [today]
---

# [Topic] MOC

_Map of Content for [Topic]. Add links to frameworks, knowledge, and sources as they're created._

## Frameworks
<!-- wikilinks to relevant frameworks -->

## Knowledge
<!-- wikilinks to relevant knowledge articles -->

## Sources
<!-- wikilinks to source material -->
```

### 5. Create TRAVERSAL-INDEX.md

Create `$VAULT_PATH/TRAVERSAL-INDEX.md` as a skeleton with their MOCs listed and a note that it will fill in as content is added.

### 6. Confirm and hand off

Tell the user exactly what was built:

```
Built your Second Brain:

Profile:      [Name]-Profile.md ✓
CLAUDE.md:    decision authority + operating boundaries ✓
Frameworks:   [list what was created] ✓
MOCs:         [list what was created] ✓
Index:        TRAVERSAL-INDEX.md (skeleton) ✓

Next: Open Obsidian, enable the Entropy Inbox Processor plugin,
and start dropping things into your 00-Inbox folder.
The plugin will analyze them and propose where they belong.
```

---

## Anti-patterns

- **Don't ask all 9 questions if content analysis already answered them.** Gap interview only.
- **Don't create frameworks from scratch.** Use the templates in `input/Role-Specific-Brain-Baselines.md`.
- **Don't skip Q5 (POVs).** These are the most personal and the hardest to infer. Always ask.
- **Don't present all questions at once.** One at a time. Wait for the answer.
- **Don't accept vague answers on Q6.** Push once: "Can you make that more specific?"
