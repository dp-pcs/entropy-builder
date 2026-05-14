# QA — Dangling Wikilink Audit

**Run audited:** `thursday_vault.zip`  |  **Date:** 2026-05-14  |  **Method:** every `[[target]]` in all 138 `.md` files, resolved against note basenames, vault-relative paths, and frontmatter aliases.

## Summary

| Metric | Value |
|---|---|
| Distinct wikilink targets | 259 |
| Flagged dangling (strict) | 111 |
| Likely false positives (resolve in Obsidian via suffix/extension match) | 6 |
| **Genuine broken links** | **105** |
| Effective link integrity | ~59% |

- **C1 — Template placeholders leaked into prose** — 19
- **C3 — Missing core / spine notes** — 31
- **C4 — Missing MOC hubs** — 8
- **C5 — Missing `knowledge/` BrainLift folder** — 20
- **C6 — Missing sales/persuasion frameworks (cross-component break)** — 23
- **C7 — Portfolio Brain internal refs** — 4

> Note: counts are by distinct *target*. A single missing note like `AI-Federation-Architecture-Framework` is one row but breaks 36 source files — see `ref_file_count`. Machine-readable version: `_QA_dangling-links_2026-05-14.csv`.

## C1 — Template placeholders leaked into prose  (19)

Skill/schema example tokens emitted as live `[[wikilinks]]`. Pure generation bug — these should never be links. Fix: strip or escape placeholder tokens in skill/schema templates before render.

| Dangling target | # files | Example referencing file |
|---|---|---|
| `CustomerName` | 3 | `Portfolio Brain/_skills/competitive-intel.md` |
| `Framework Name` | 2 | `Portfolio Brain/_skills/debrief.md` |
| `Non-HVO` | 2 | `Portfolio Brain/Playbooks/Test Customer 1/_intelligence_summary.md` |
| `...` | 1 | `Portfolio Brain/_skills/lint.md` |
| `Customer` | 1 | `Portfolio Brain/_skills/commitment-extraction.md` |
| `Customer A` | 1 | `Portfolio Brain/_skills/commitment-extraction.md` |
| `CustomerName1` | 1 | `Portfolio Brain/_analytics/schemas.md` |
| `CustomerName2` | 1 | `Portfolio Brain/_analytics/schemas.md` |
| `Entropy/...` | 1 | `Portfolio Brain/CHANGELOG.md` |
| `filename` | 1 | `Portfolio Brain/_skills/lint.md` |
| `new playbook` | 1 | `Portfolio Brain/_skills/playbook.md` |
| `Platinum` | 1 | `Portfolio Brain/Playbooks/Test Customer 2/_intelligence_summary.md` |
| `Portfolio Brain/...` | 1 | `Portfolio Brain/CHANGELOG.md` |
| `Related Node 1` | 1 | `Portfolio Brain/_analytics/schemas.md` |
| `Related Node 2` | 1 | `Portfolio Brain/_analytics/schemas.md` |
| `Standard` | 1 | `Portfolio Brain/Playbooks/Test Customer 1/_intelligence_summary.md` |
| `Target` | 1 | `Portfolio Brain/_skills/lint.md` |
| `YYYY-MM-DD_Meeting_Title` | 1 | `Portfolio Brain/_skills/commitment-extraction.md` |
| `YYYY-MM-DD_Renewal_Playbook` | 1 | `Portfolio Brain/_skills/playbook.md` |

## C3 — Missing core / spine notes  (31)

The content references hub notes that were never generated. These are the highest-impact misses — `AI-Federation-Architecture-Framework`, `OGP-Protocol-Reference`, `David-Proctor-Profile`, `Decision-Making-Framework` are each linked from 30+ files. Fix: linker must create a stub for any target it emits, or generation must run a closure pass.

| Dangling target | # files | Example referencing file |
|---|---|---|
| `AI-Federation-Architecture-Framework` | 36 | `David Proctor's Second Brain/Books/Pillars of the Earth.md` |
| `Decision-Making-Framework` | 34 | `David Proctor's Second Brain/Books/The Art of War.md` |
| `David-Proctor-Profile` | 30 | `David Proctor's Second Brain/Books/Pillars of the Earth.md` |
| `OGP-Protocol-Reference` | 30 | `David Proctor's Second Brain/Books/Pillars of the Earth.md` |
| `AI-CoE-Enablement-Framework` | 27 | `David Proctor's Second Brain/Books/Pillars of the Earth.md` |
| `GEPA-Tutor-Refinery` | 22 | `David Proctor's Second Brain/Books/The Cat in the Hat.md` |
| `Learning-System` | 22 | `David Proctor's Second Brain/Books/The Cat in the Hat.md` |
| `Communication-Framework` | 18 | `David Proctor's Second Brain/Books/The Art of War.md` |
| `Prompt-Engineering-Principles` | 17 | `David Proctor's Second Brain/Books/The Cat in the Hat.md` |
| `Agentic-Framework-Evaluation` | 16 | `David Proctor's Second Brain/Concepts/AI-Infrastructure-Dependency-Stack.md` |
| `Agent-and-Repo-Guardrails` | 13 | `David Proctor's Second Brain/Concepts/AI-Agent-Isolation.md` |
| `AI-Infrastructure-Reliability` | 13 | `David Proctor's Second Brain/Concepts/AI-Infrastructure-Dependency-Stack.md` |
| `Crossover-Operations-Leadership` | 13 | `David Proctor's Second Brain/Books/Pillars of the Earth.md` |
| `Expertise-Inflation-Research` | 10 | `David Proctor's Second Brain/Concepts/Expertise-Inflation-Measurement.md` |
| `Karpathy-LLM-Wiki-Methodology` | 10 | `David Proctor's Second Brain/Concepts/Friction-Forced-Learning.md` |
| `Hermes-vs-OpenClaw` | 8 | `David Proctor's Second Brain/Concepts/AI-Agent-Isolation.md` |
| `Asynchronous-Coding-Agents` | 7 | `David Proctor's Second Brain/Concepts/Agentic-AI-Maturity.md` |
| `MCP-and-Tool-Discovery` | 5 | `David Proctor's Second Brain/Concepts/Intent-Based-Messaging.md` |
| `AI-CoE-Portal-Pattern` | 4 | `David Proctor's Second Brain/Concepts/AI-CoE-as-Internal-Product.md` |
| `Reading-Library` | 4 | `David Proctor's Second Brain/Concepts/Audiobook-Series-Tracking.md` |
| `AICOE-Expert-Network` | 2 | `David Proctor's Second Brain/MOCs/AI-Agent-Federation-MOC.md` |
| `ESW Paper` | 2 | `Portfolio Brain/Playbooks/Test Customer 1/_intelligence_summary.md` |
| `How-To Change Control at Ludicrous Speed` | 2 | `David Proctor's Second Brain/Mental Models/Governance Without Friction.md` |
| `OpenClaw-and-Personal-AI-Gateways` | 2 | `David Proctor's Second Brain/MOCs/AI-Agent-Federation-MOC.md` |
| `AI-Vision-and-UI-Testing` | 1 | `David Proctor's Second Brain/MOCs/AI-Strategy-MOC.md` |
| `axoviq-ai/synthadoc` | 1 | `David Proctor's Second Brain/Concepts/LLM-Maintained-Wiki.md` |
| `David-Profile` | 1 | `Portfolio Brain/_skills/playbook.md` |
| `How-To Why Most Architecture Review Boards Suck` | 1 | `David Proctor's Second Brain/Frameworks/TOGAF.md` |
| `Jay-Profile` | 1 | `Portfolio Brain/Company-Rules.md` |
| `Systems Thinking` | 1 | `David Proctor's Second Brain/Mental Models/Second-Order Thinking.md` |
| `The Algorithm that Stopped Counting` | 1 | `David Proctor's Second Brain/Concepts/Algorithmic-Misclassification.md` |

## C4 — Missing MOC hubs  (8)

17 MOC targets are referenced; only 6 MOCs exist. Note `MOCs/Security-and-Cryptography-MOC` — gaps.json independently flagged this same hole. Fix: generate MOCs from the link graph after notes exist, not before.

| Dangling target | # files | Example referencing file |
|---|---|---|
| `Customer-Intelligence-MOC` | 2 | `Portfolio Brain/Company-Rules.md` |
| `GitHub-Repos-MOC` | 2 | `David Proctor's Second Brain/Frameworks/Archimate.md` |
| `Communication-Mastery-MOC` | 1 | `Portfolio Brain/_skills/playbook.md` |
| `Decision-Making-Toolkit-MOC` | 1 | `Portfolio Brain/_skills/playbook.md` |
| `Leadership-and-Management-MOC` | 1 | `Portfolio Brain/_skills/playbook.md` |
| `MOCs/Security-and-Cryptography-MOC` | 1 | `David Proctor's Second Brain/MOCs/AI-Agent-Federation-MOC.md` |
| `Sales-Playbook-MOC` | 1 | `Portfolio Brain/_skills/playbook.md` |
| `Strategy-and-Power-MOC` | 1 | `Portfolio Brain/_skills/playbook.md` |

## C5 — Missing `knowledge/` BrainLift folder  (20)

An entire `knowledge/` directory of BrainLift source articles is referenced but absent from the vault. Either ingestion of your BrainLift/Substack corpus was expected and skipped, or these point outside the vault. Fix: confirm whether `knowledge/` is an input the run should copy in.

| Dangling target | # files | Example referencing file |
|---|---|---|
| `knowledge/How-To Why Most Architecture Review Boards Suck.md` | 2 | `David Proctor's Second Brain/Quotes/David-Proctor-Quotes.md` |
| `BrainLift-AI Vision and UI Testing` | 1 | `David Proctor's Second Brain/Principles/AI Ethics Is a Human Problem Not an AI Problem.md` |
| `BrainLift-AI-Augmented CICD Right-Sized Pipelines for Fast Safe Shipping` | 1 | `David Proctor's Second Brain/Mental Models/Governance Without Friction.md` |
| `BrainLift-GEPA` | 1 | `David Proctor's Second Brain/People/Omar-Khattab.md` |
| `BrainLift-Open Gateway Protocol OGP - AI Agent Federation` | 1 | `David Proctor's Second Brain/Mental Models/Decentralization vs Centralization Tradeoffs.md` |
| `BrainLift-When AI Misclassifies` | 1 | `David Proctor's Second Brain/Principles/AI Ethics Is a Human Problem Not an AI Problem.md` |
| `knowledge/BrainLift-Agentic AI.md` | 1 | `David Proctor's Second Brain/Quotes/David-Proctor-Quotes.md` |
| `knowledge/BrainLift-AI Browsers.md` | 1 | `David Proctor's Second Brain/Quotes/David-Proctor-Quotes.md` |
| `knowledge/BrainLift-AI-Augmented CICD Right-Sized Pipelines for Fast Safe Shipping.md` | 1 | `David Proctor's Second Brain/Quotes/David-Proctor-Quotes.md` |
| `knowledge/BrainLift-Asynchronous Coding Agents Jules.md` | 1 | `David Proctor's Second Brain/Quotes/Andrej-Karpathy-Quotes.md` |
| `knowledge/BrainLift-Drafts - Spiky POV.md` | 1 | `David Proctor's Second Brain/Quotes/David-Proctor-Quotes.md` |
| `knowledge/BrainLift-Open Gateway Protocol OGP - AI Agent Federation.md` | 1 | `David Proctor's Second Brain/Quotes/David-Proctor-Quotes.md` |
| `knowledge/BrainLift-When AI Misclassifies.md` | 1 | `David Proctor's Second Brain/Quotes/David-Proctor-Quotes.md` |
| `knowledge/Framework Five Layers of No How OGPΓÇÖs Doorman Actually Works` | 1 | `David Proctor's Second Brain/Mental Models/Inversion.md` |
| `knowledge/How-To Fast, Not Fragile with AI.md` | 1 | `David Proctor's Second Brain/Quotes/David-Proctor-Quotes.md` |
| `knowledge/OGP, A2A, and MCP Three Lanes, Same Highway.md` | 1 | `David Proctor's Second Brain/Quotes/David-Proctor-Quotes.md` |
| `knowledge/Postmortem When Your AI Tools (OpenClaw) Keep Crashing.md` | 1 | `David Proctor's Second Brain/Quotes/World-Without-End-Quotes.md` |
| `knowledge/The 15.7 Tbps DDoS That Should Scare AI Teams More Than Model Benchmarks.md` | 1 | `David Proctor's Second Brain/Quotes/David-Proctor-Quotes.md` |
| `knowledge/The Algorithm that Stopped Counting.md` | 1 | `David Proctor's Second Brain/Quotes/David-Proctor-Quotes.md` |
| `knowledge/Your Agent, My Agent.md` | 1 | `David Proctor's Second Brain/Quotes/David-Proctor-Quotes.md` |

## C6 — Missing sales/persuasion frameworks (cross-component break)  (23)

The Portfolio Brain skills were enriched to depend on a sales-framework library (`Tactical Empathy`, `MEDDICC Framework`, `QBS Ladder`...). The Second Brain generator — correctly reading you as VP of AI CoE — deleted exactly these. The two halves ran on different identity models. Fix: both generators must consume one shared profile; decide whether sales frameworks belong in this vault at all.

| Dangling target | # files | Example referencing file |
|---|---|---|
| `Service-Recovery-Paradox` | 4 | `Portfolio Brain/_skills/debrief.md` |
| `Accusation-Audit` | 3 | `Portfolio Brain/_skills/email-draft.md` |
| `Crucial Conversations` | 3 | `Portfolio Brain/_skills/debrief.md` |
| `The Expansion Sale` | 3 | `Portfolio Brain/_skills/debrief.md` |
| `Ethos-Logos-Pathos` | 2 | `Portfolio Brain/_skills/email-draft.md` |
| `Framing-Effect` | 2 | `Portfolio Brain/_skills/email-draft.md` |
| `MEDDICC Framework` | 2 | `Portfolio Brain/_skills/debrief.md` |
| `Tactical Empathy` | 2 | `Portfolio Brain/_skills/debrief.md` |
| `Anchoring` | 1 | `Portfolio Brain/_skills/email-draft.md` |
| `Behavior-Design` | 1 | `Portfolio Brain/_skills/debrief.md` |
| `Compounding` | 1 | `Portfolio Brain/_skills/triage.md` |
| `Contract & Renewal Friction` | 1 | `Portfolio Brain/_skills/competitive-intel.md` |
| `Diagnostic-Funnel` | 1 | `Portfolio Brain/_skills/debrief.md` |
| `Diminishing-Returns` | 1 | `Portfolio Brain/_skills/triage.md` |
| `Endowment-Effect` | 1 | `Portfolio Brain/_skills/email-draft.md` |
| `Essential Account Planning` | 1 | `Portfolio Brain/_skills/debrief.md` |
| `Flip the Funnel` | 1 | `Portfolio Brain/_skills/debrief.md` |
| `Loss-Aversion` | 1 | `Portfolio Brain/_skills/email-draft.md` |
| `Pre-Mortems` | 1 | `Portfolio Brain/_skills/triage.md` |
| `Product Sentiment - Negative` | 1 | `Portfolio Brain/_skills/competitive-intel.md` |
| `QBS Ladder` | 1 | `Portfolio Brain/_skills/triage.md` |
| `Tactical-Empathy` | 1 | `Portfolio Brain/_skills/email-draft.md` |
| `Three Pillars of Charisma` | 1 | `Portfolio Brain/_skills/email-draft.md` |

## C7 — Portfolio Brain internal refs  (4)

Genuine broken internal links inside the Portfolio Brain tree.

| Dangling target | # files | Example referencing file |
|---|---|---|
| `Portfolio Brain/CLAUDE` | 1 | `Portfolio Brain/Company-Rules.md` |
| `Test Customer 1` | 1 | `Portfolio Brain/_hot_cache.md` |
| `Test Customer 2` | 1 | `Portfolio Brain/_hot_cache.md` |
| `Tivian` | 1 | `Portfolio Brain/_skills/competitive-intel.md` |

## Likely false positives (verify in Obsidian, do not action)

These were flagged by strict path-matching but resolve in Obsidian via partial-path suffix matching or `.md`-extension handling. Listed for completeness.

| Target | Why it likely resolves |
|---|---|
| `CLAUDE.md` | `[[CLAUDE.md]]` — Obsidian strips the `.md`; `CLAUDE.md` exists at vault root |
| `_analytics/metrics` | suffix-matches `Portfolio Brain/_analytics/metrics.md` |
| `_analytics/queries` | suffix-matches `Portfolio Brain/_analytics/queries.md` |
| `_analytics/schemas` | suffix-matches `Portfolio Brain/_analytics/schemas.md` |
| `Test Customer 1/_intelligence_summary` | suffix-matches `Portfolio Brain/Playbooks/Test Customer 1/_intelligence_summary.md` |
| `Test Customer 2/_intelligence_summary` | suffix-matches `Portfolio Brain/Playbooks/Test Customer 2/_intelligence_summary.md` |

## Recommended fix order

1. **C1** — trivial, pure bug. Stop emitting placeholder tokens as links.
2. **C3 + C4** — add a graph-closure pass: any emitted link target must have a note (stub at minimum); generate MOCs *after* notes exist.
3. **C6** — unify the identity model feeding both vault halves. This is the architectural fix, not a linting fix.
4. **C5** — confirm whether `knowledge/` is a missing ingestion input.
5. **C7** — minor; fix internal Portfolio Brain links.
