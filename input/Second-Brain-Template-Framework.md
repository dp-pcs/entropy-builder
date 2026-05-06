# Second Brain Template Framework
**Organizational Standard for Building Personal Knowledge Systems**

**Version 1.0** | Created: April 2026 | Based on Entropy System Beta

---

## Overview

This document establishes the **baseline requirements** and **optional enhancements** for building individual Second Brains across the organization. The Second Brain is a personal knowledge system that serves three purposes:

1. **Individual Augmentation**: Enhance your decision-making with your own curated knowledge
2. **Organizational Intelligence**: Contribute to a federated network of collective intelligence
3. **AI-Powered Workflows**: Enable AI agents to operate within a knowledge-bounded context specific to your role and expertise

The template is role-agnostic and follows **Andrej Karpathy's knowledge graph methodology**, enhanced with visual connections, semantic tagging, and operational guardrails.

---

## Core Principles

### 1. Knowledge Organization
- **Nodes**: Individual files representing concepts, frameworks, people, or resources
- **Edges**: Wikilinks connecting related nodes (create semantic relationships)
- **MOCs (Maps of Content)**: Curated navigation hubs for clusters of related topics
- **Frontmatter**: YAML metadata on every file for parsing, filtering, and federation

### 2. Scalability
- **Individual autonomy**: Your brain works for you first
- **Federated sharing**: Selective contribution to organizational intelligence
- **Role-based variation**: Baseline is consistent; personalization aligns with your function
- **Frictionless updates**: Changes to your brain flow naturally into shared systems without manual sync

### 3. Quality Over Quantity
- **Intentional curation**: Not a dump of every document you've ever seen
- **Connections matter more than volume**: A well-linked 50-node brain beats a messy 500-node brain
- **Living system**: Iteratively refined, not static

---

## Part 1: Baseline (Must-Haves for All Roles)

Every Second Brain must include these foundational elements, regardless of function (Sales, Product, Marketing, etc.).

### 1.1 Identity & Operating Model

#### **Your Profile** (`[YourName]-Profile.md`)

Describes who you are as a professional and decision-maker. This is how AI agents understand *how* you think, not just *what* you know.

**Required fields:**
- **Full Name & Role**: Title and primary function
- **Psychological Profile**: Operating style, communication preferences, decision-making patterns
  - Example: "ENTJ, high risk tolerance, data-driven, direct communication, low patience for ambiguity"
  - This might come from: CliftonStrengths, Myers-Briggs, DiSC, internal psych evaluations, self-assessment
- **Spiky POVs (Points of View)**: 3–5 non-negotiable beliefs or areas of expertise that differentiate you
  - These are your leverage points for organizational decision-making
  - Example: "ARR is the only metric that matters for SaaS retention," "Customer empathy is non-negotiable," "Process automation before hiring"
- **Key Strengths** (2–3): What you bring to the table that's rare
- **Growth Edges**: 1–2 areas you're consciously developing
- **Working Style**: Remote/office preference, collaboration style, meeting preferences, timezone, response time expectations
- **Relevant History**: 2–3 sentence summary of career trajectory and why it's relevant now

**Why this matters**: When your agent queries the organizational brain, it doesn't just find answers—it finds answers that fit *how you operate*. This prevents tone mismatches, ensures recommendations align with your decision criteria, and allows for lateral peer consultation.

**Example (Sales):**
```markdown
---
type: profile
name: Jamie Sanchez
role: Account Executive
operating_style: "Relationship-driven, intuitive, high EQ, collaborative decision-making, oral communicator"
spiky_povs:
  - "Customer success is revenue success—align incentives early"
  - "Enterprise deals are won on strategic fit, not features"
  - "Personal relationships drive renewals; we underinvest in relationship depth"
psychological_profile: "ENFP, Adaptable-Confident, high empathy, moderate risk tolerance"
strengths:
  - "Strategic account planning with multi-threaded stakeholder engagement"
  - "Enterprise negotiation and executive-level presence"
growth_edges:
  - "Data-driven forecasting and pipeline discipline"
  - "Handling ambiguity in early-stage deals"
---
# Jamie Sanchez — Account Executive

**Role**: Enterprise Account Executive, Tivian  
**Background**: 8 years in B2B SaaS, 3 years in enterprise renewals, previously in mid-market expansion.

## Operating Style
...
```

---

#### **Company Rules & Guardrails** (`CLAUDE.md`)

A master reference file that governs how your brain behaves operationally. This is *your* version of organizational constraints—what you can and cannot do.

**Required sections:**
- **Pricing Boundaries**: What discounts can you offer? What requires approval?
  - Example: "Can offer 0–15% on renewals. 15–25% requires SVP approval. >25% requires CEO."
- **Engagement Constraints**: What can you promise customers? What's out of bounds?
  - Example: "Can promise 24-hour support response. Cannot promise dedicated engineer without PS approval."
- **Approval Matrix**: Who approves what at what dollar threshold?
- **Ethical Boundaries**: What should your agent never recommend?
  - Example: "Never recommend a customer be deprovisioned without 30-day notice and executive sign-off."
- **Data Sensitivity**: What parts of your brain are private? What can be federated?
  - Example: "Personal development notes: private. Customer win strategies: shareable. Salary information: private."

**Why this matters**: Your agent learns the rules *before* it acts. When it simulates a scenario, it stays within bounds. When you query it, it knows what it can and cannot recommend.

---

### 1.2 Role-Specific Expertise

#### **Knowledge Articles** (`knowledge/` folder)

Curated articles, documentation, or reference material relevant to your function. This is the equivalent of a personal wiki.

**Structure:**
```
knowledge/
├── [Product-Name] Product Documentation/
│   ├── [Product-Name] Features.md
│   ├── [Product-Name] Pricing.md
│   ├── [Product-Name] Roadmap.md (if relevant to your role)
│   └── [Product-Name] Known Issues.md
├── [Company Name] Policies/
│   ├── Discount Policy.md
│   ├── SLA Policy.md
│   └── Data Privacy Policy.md
└── Domain Knowledge/
    ├── [Industry] Market Trends.md
    └── [Competitor Name] Overview.md
```

**What to include:**
- Product documentation (user-facing and internal)
- Company policies and SLAs
- Competitive intelligence (if relevant)
- Industry standards and compliance docs
- Process documentation for your function

**Why organize this way:**
- Product agents can be queried: "What features solve X?"
- Policy agents can be queried: "Can I offer this discount?"
- Domain agents can be queried: "What's our competitive position?"

**Important**: These are **reference materials**, not analysis. Save raw materials here; your frameworks (next section) interpret them.

---

#### **Frameworks & Methodologies** (`frameworks/` folder)

Operating systems you use. Not generic frameworks from books—frameworks you *actually use* in your role.

**Examples by role:**

**Sales:**
- Sales process/methodology (MEDDIC, solution selling, consultative selling adapted for your company)
- Account planning framework
- Negotiation framework
- Renewal playbook
- Pipeline management framework

**Product:**
- Feature prioritization framework (MoSCoW, RICE, impact vs. effort)
- User research synthesis template
- Roadmap planning framework
- Technical debt assessment framework

**Marketing:**
- Campaign planning framework
- Buyer persona definition
- Content strategy framework
- Metrics & attribution model

**Any Role:**
- Decision-making framework (how you actually decide, not theory)
- Problem-solving process
- Communication strategy (how you structure arguments, what resonates with your audience)

**Format** (use this template for consistency):
```markdown
---
type: framework
name: "Framework Name"
role: "Sales" (or applicable role)
description: "One-line summary of what this framework does"
when_to_use: "The specific situations where you apply this"
source: "Where you learned it (book, mentor, experience)"
tags: ["tag1", "tag2"]
---

# Framework Name

## Why This Works
[2–3 sentences on the underlying logic]

## The Steps
1. [Step 1 with real example from your work]
2. [Step 2 with real example]
...

## Common Mistakes
- Mistake 1 (and how you've learned to avoid it)
- Mistake 2

## When It Breaks
[Acknowledge limitations—no framework is universal]

## Related Frameworks
- [[Framework B]] (when to use instead)
- [[Framework C]] (use together with this one)
```

**Why this matters**: Frameworks are where your *operational expertise* lives. When your agent needs to decide how to handle a situation, it reads your framework, not a generic textbook version.

---

### 1.3 Knowledge Sources

#### **Curated References** (`sources/` folder)

The 5–10 **most influential** sources that shaped your thinking. Not 100 books—the ones that actually changed how you operate.

**Format:**
```markdown
---
type: source
name: "Source Name"
author: "Author(s)"
source_type: "book" | "podcast" | "research" | "internal_document" | "course"
url: "[Link if applicable]"
date_read: "YYYY-MM"
relevance: "How this shaped your thinking in 2–3 sentences"
tags: ["topic1", "topic2"]
---

# Source Name

## Key Ideas
- Idea 1 and why it matters to you
- Idea 2 and how you applied it

## Quotes That Stuck
> Relevant quote with page number

## How You Use This
[Concrete example of applying this source]
```

**What counts as a source:**
- Books
- Research papers
- Courses or certifications
- Industry reports
- Podcasts or interviews
- Internal training materials
- Mentorship insights (attribute the mentor)

**Why not 100 sources?**
- More sources = noise, not signal
- 5–10 deeply understood sources > 100 titles
- AI agents query your sources for decision-making; 10 trustworthy inputs beat 100 generic ones

---

#### **Key People & Mentors** (`people/` folder)

Thought leaders, mentors, or colleagues who've influenced your approach. This is about intellectual lineage.

**Format:**
```markdown
---
type: person
name: "Person Name"
role: "Their role/expertise"
relationship: "mentor" | "peer" | "thought_leader" | "colleague"
how_they_influence_you: "2–3 sentence summary"
relevant_insights: ["insight1", "insight2"]
tags: ["topic1", "topic2"]
---

# Person Name

## Their Core Philosophy
[What they believe/teach]

## How They've Shaped Your Thinking
[Specific ways they've influenced you]

## Recommended if You Want to Learn About
[Topics they excel in]
```

---

### 1.4 Organization & Navigation

#### **TRAVERSAL-INDEX.md**

A master file listing every node in your brain with one-line descriptions. This is your brain's table of contents.

**Format:**
```markdown
# [YourName]'s Second Brain — Traversal Index

**Last Updated**: April 2026  
**Total Nodes**: 47  
**Knowledge Debt**: 3 (outdated nodes listed below)

## Structure Overview
```
├── Core Identity
│   ├── [YourName]-Profile.md — Psychological profile, operating style, spiky POVs
│   └── CLAUDE.md — Company rules, approval matrices, ethical boundaries
├── Knowledge Base
│   ├── Tivian Product Documentation/
│   ├── Company Policies/
│   └── Industry Intelligence/
├── Frameworks (17 files)
│   ├── Sales Process Framework
│   ├── Account Planning Framework
│   └── [...]
├── Sources (8 curated)
│   ├── Never Split the Difference
│   └── [...]
├── People (5 key influences)
├── Maps of Content (MOCs)
│   ├── Enterprise Sales MOC
│   ├── Renewal Strategy MOC
│   └── [...]
└── Working Notes (raw intake, will be processed)
```

## Files at a Glance

**Identity**
| File | Type | Description |
|------|------|-------------|
| [YourName]-Profile.md | profile | ENTJ, high EQ, data-driven negotiator; expert in multi-threaded enterprise deals |
| CLAUDE.md | rules | Pricing: 0–15% autonomy. 15–25% SVP approval. >25% CEO. |

**Knowledge Base**
| File | Type | Description |
|------|------|-------------|
| Tivian Features.md | documentation | Full feature list, use cases, competitive differentiation |
| Tivian Pricing.md | documentation | Pricing tiers, packaging, discount policy |
| SLA Policy.md | policy | 24-hour response, 99.5% uptime commitment |

**Frameworks**
| File | Type | Description |
|------|------|-------------|
| Enterprise Sales Process.md | framework | MEDDIC adapted; maps to 5 renewal stages |
| Account Planning Framework.md | framework | Stakeholder mapping, expansion scoring, risk assessment |
| Negotiation Framework.md | framework | Anchoring, creative structuring, walkaway points |

**Sources**
| File | Type | Description |
|------|------|-------------|
| Never Split the Difference.md | source | Tactical empathy, calibrated questions, value-building |
| The Expansion Sale.md | source | Land-expand-consume; how to move from renewals to growth |

**People**
| File | Type | Description |
|------|------|-------------|
| Shannon Ramsey.md | mentor | Strategic thinking, agentic systems, organizational design |

---

#### **Maps of Content (MOCs)** (`mocs/` folder)

High-level navigation hubs. Each MOC clusters related nodes around a theme.

**Common MOCs for all roles:**
- **Decision-Making MOC**: Links to your decision frameworks, case studies, and decision post-mortems
- **Learning MOC**: Links to sources, mentors, and concepts you're currently developing
- **Operational MOC**: Links to company rules, approval matrices, and process documentation

**Role-specific MOCs:**
- **Sales**: Enterprise Sales MOC, Renewal Strategy MOC, Account Intelligence MOC, Competitive Intelligence MOC
- **Product**: Roadmap Planning MOC, Technical Debt MOC, User Research MOC, Feature Prioritization MOC
- **Marketing**: Campaign Planning MOC, Buyer Intelligence MOC, Content Strategy MOC, Attribution MOC

**Format:**
```markdown
---
type: moc
name: "MOC Name"
description: "What this cluster covers and why it matters"
tags: ["topic1", "topic2"]
---

# [Enterprise Sales MOC]

## Purpose
Navigate the strategic, tactical, and operational aspects of enterprise account management.

## Clusters

### Strategic
- [[Account Planning Framework]] — How to approach a new enterprise account
- [[Competitive Intelligence MOC]] — Competitive positioning and win strategies
- [[Shannon Ramsey]] — Mentorship on enterprise strategy

### Tactical
- [[Enterprise Sales Process]] — Step-by-step process adapted from MEDDIC
- [[Negotiation Framework]] — Structuring deals, anchoring, creative solutions
- [[Tivian Product Documentation]] — Features to lead with in enterprise contexts

### Operational
- [[SLA Policy]] — Service level agreements; what we promise
- [[Discount Policy]] — Approval matrices for pricing flexibility
- [[Case Studies]] — Real examples of closed deals (if applicable)

## Recent Updates
- Updated Competitive Intelligence after new pricing launch (Apr 2026)
- Added negotiation case study from Acme Corp renewal (Apr 2026)

## Open Threads
- [ ] Research 3 new competitors entering the market
- [ ] Document lessons from the last 5 lost deals
```

---

### 1.5 Metadata & Federability

#### **Frontmatter Standard**

Every file must have YAML frontmatter for parsing, filtering, and organizational intelligence:

```yaml
---
type: "profile" | "rule" | "documentation" | "framework" | "source" | "person" | "moc" | "concept"
name: "Human-readable name"
description: "One-line summary (used for scanning TRAVERSAL-INDEX)"
role: "Sales" | "Product" | "Marketing" | optional_if_universal
tags: ["tag1", "tag2", "tag3"]  # for filtering and federation
is_shareable: true | false  # can this be federated to organizational hub?
last_updated: "YYYY-MM-DD"
aliases: ["Alt name 1", "Alt name 2"]  # so both "MEDDIC" and "Meddic Sales Process" resolve
---
```

**Example:**
```yaml
---
type: framework
name: Enterprise Sales Process
description: MEDDIC-based 5-stage enterprise sales and renewal process
role: Sales
tags: ["sales", "process", "enterprise", "meddic"]
is_shareable: true
last_updated: 2026-04-23
aliases: ["Enterprise Sales", "MEDDIC Process"]
---
```

---

## Part 2: Optional Enhancements (Role & Personality-Driven)

Once baseline is in place, personalize based on your role and how you work.

### 2.1 Sales-Specific Enhancements

**If you manage enterprise accounts or complex renewals, add:**

- **Customer Intelligence Templates** (`customers/` folder)
  - Stakeholder maps, win/loss analysis, account health scoring
  - Not shareable (private to you) or shareable at your discretion

- **Deal Playbooks** (`playbooks/` folder)
  - Specific playbooks for your most common deal types
  - Example: "How to handle a competitive threat in renewal," "Land-expand-consume playbook for [product]"

- **Psychological Profiles of Common Customer Personas** (`personas/` folder)
  - How do procurement personas differ from end-user personas?
  - How do you adjust your communication for each?
  - *Optional*: Incorporate psychographic data (if available) about decision-makers

- **Market & Competitive Intelligence** (`intelligence/` folder)
  - What competitors are winning? How?
  - Market trends relevant to your accounts
  - Emerging threats

### 2.2 Product-Specific Enhancements

**If you drive product strategy, add:**

- **Roadmap Planning Artifacts** (`roadmap/` folder)
  - Current roadmap, prioritization framework, user research synthesis
  - Competitive feature gaps

- **Technical Architecture Documentation** (`architecture/` folder)
  - System design, scalability constraints, debt items
  - *Optional*: Link to actual codebase docs

- **User Research Synthesis** (`research/` folder)
  - Customer interviews, feedback themes, feature requests
  - Trend analysis

- **Metrics & KPI Dashboard** (`metrics/` folder)
  - Current product health, adoption rates, retention cohorts
  - Linked to your decision frameworks (how do you use these metrics?)

### 2.3 Marketing-Specific Enhancements

**If you drive campaigns or brand, add:**

- **Campaign Playbooks** (`campaigns/` folder)
  - Proven campaign templates with results, what worked, what didn't

- **Content Inventory & Performance** (`content/` folder)
  - What content exists? What's performing? What's gaps?
  - Link to your content strategy framework

- **Attribution & Funnel Data** (`funnel/` folder)
  - How you track buyer journey, conversion rates by stage
  - Feedback loops from Sales about what drives deals

- **Brand Voice & Guidelines** (`brand/` folder)
  - How you communicate, tone, visual identity
  - Regional or audience-specific variations if applicable

### 2.4 Cross-Role Enhancements (Any Role Can Add)

- **Case Studies & War Stories** (`cases/` folder)
  - Real examples from your work: wins, losses, pivots
  - Anonymized if necessary
  - Link to underlying frameworks and decision-making

- **Decision Post-Mortems** (`decisions/` folder)
  - When you make a big decision, document it:
    - What did you decide?
    - Why (which framework did you use)?
    - What happened?
    - What would you do differently?
  - This becomes organizational learning over time

- **Contradictions & Tensions** (`contradictions/` folder)
  - Where do you disagree with company policy or your mentor's approach?
  - Both perspectives, with your synthesis
  - *Example*: "Tactical Empathy vs. Hard Negotiation: When to use each"

- **Personal Development Notes** (`development/` folder - **PRIVATE**)
  - Coaching feedback, 360 reviews, growth areas
  - *Never* federated—this is for you and your manager

---

## Part 3: Creating Your Second Brain — Quick Start

### Phase 1: Identity & Rules (1–2 hours)

1. **Create `[YourName]-Profile.md`**
   - Answer: Who are you? How do you think? What makes you different?
   - Pull from: psych evals if available, self-reflection, feedback from peers/manager

2. **Create `CLAUDE.md`**
   - Copy from organizational templates or ask your manager
   - Add role-specific constraints (discounts, approvals, engagement limits)
   - Mark sensitive sections as non-shareable

3. **Create `TRAVERSAL-INDEX.md`**
   - Start empty; you'll populate it as you build

### Phase 2: Baseline Knowledge (2–4 hours)

4. **Create `knowledge/` folder**
   - Copy/export product documentation
   - Add company policies and SLAs
   - Add 2–3 pieces of domain knowledge relevant to your role

5. **Create 3–5 `frameworks/` files**
   - Start with frameworks you *already use*
   - Don't invent new ones; document your existing operating system
   - Use the template above; keep it under 500 words each initially

6. **Create `sources/` folder**
   - List your 5–10 most influential sources
   - Add 1–2 sentence on why each matters to you

7. **Create `people/` folder**
   - 3–5 key mentors or thought leaders who've shaped your thinking

### Phase 3: Navigation & Connections (1–2 hours)

8. **Create MOC files** for your main topic clusters
   - Start with 2–3 MOCs
   - Example for Sales: "Enterprise Sales MOC", "Renewal Strategy MOC"
   - Link to existing files using `[[Filename]]`

9. **Update `TRAVERSAL-INDEX.md`** with all files created so far

10. **Start using Wikilinks**
    - In frameworks, link to sources: `[[Never Split the Difference]]`
    - In MOCs, link to frameworks: `[[Account Planning Framework]]`
    - Each link becomes a navigable path through your brain

### Phase 4: Iterate & Personalize (Ongoing)

11. **Add role-specific enhancements** (see Part 2)
    - Pick 2–3 that align with your function
    - Build incrementally, not all at once

12. **Link frameworks to case studies**
    - When you close a deal, win a project, or learn from failure, document it
    - Link it back to the framework you used

13. **Maintain & Update**
    - Review TRAVERSAL-INDEX monthly
    - Mark files as outdated if they need refresh
    - Every 3 months, synthesize what you've learned into new nodes or updated frameworks

---

## Part 4: Federation & Sharing

Once your brain is functional, parts of it feed into the organizational intelligence system.

### What Gets Shared?

**Shareable (opt-in contribution to organizational hub):**
- Frameworks (your operating systems)
- Sources (curated knowledge)
- Case studies (wins, losses, learnings)
- Decision post-mortems (organizational learning)
- Anonymous or aggregated customer intelligence

**Private (stays local):**
- Personal profile (except role and spiky POVs, which are shareable)
- Personal development notes
- Specific customer contracts or sensitive negotiation details
- Health metrics tied to performance reviews

### Marking Files for Sharing

In frontmatter, set `is_shareable: true` to flag files for potential federation:

```yaml
---
type: framework
is_shareable: true  # Can contribute to organizational hub
---
```

The organizational hub will have a **central process** for:
1. Aggregating shareable frameworks across all roles
2. Detecting contradictions and creating synthesis nodes (e.g., "When Sales Framework A conflicts with Product Framework B")
3. Creating a federated index so anyone can query: "How do we handle X?" and get multiple perspectives
4. Managing versioning so changes to your brain don't break shared systems

---

## Part 5: Visual Knowledge Graph Structure

### Recommended Folder Structure

```
[YourName]-Second-Brain/
├── CLAUDE.md                          ← Rules, guardrails, approval matrices
├── TRAVERSAL-INDEX.md                 ← Master file index with descriptions
├── [YourName]-Profile.md              ← Identity, operating style, spiky POVs
│
├── knowledge/                         ← Reference materials
│   ├── [Product-Name]/
│   │   ├── Features.md
│   │   ├── Pricing.md
│   │   └── Known Issues.md
│   ├── Company Policies/
│   │   ├── Discount Policy.md
│   │   ├── SLA Policy.md
│   │   └── Data Privacy.md
│   └── Industry Intelligence/
│       ├── Market Trends.md
│       └── Competitive Landscape.md
│
├── frameworks/                        ← Operating systems (your methodologies)
│   ├── Enterprise Sales Process.md
│   ├── Account Planning Framework.md
│   ├── Negotiation Framework.md
│   ├── Decision-Making Framework.md
│   └── [...]
│
├── sources/                           ← Curated references (5–10)
│   ├── Never Split the Difference.md
│   ├── The Expansion Sale.md
│   ├── [Research Paper].md
│   └── [Mentor Insights].md
│
├── people/                            ← Key influences
│   ├── Shannon Ramsey.md
│   ├── [Mentor Name].md
│   └── [Thought Leader].md
│
├── mocs/                              ← Maps of Content (navigation hubs)
│   ├── Enterprise Sales MOC.md
│   ├── Renewal Strategy MOC.md
│   ├── Decision-Making MOC.md
│   ├── Learning MOC.md
│   └── [...]
│
├── cases/                             ← [Optional] Real examples & war stories
│   ├── Acme Corp Renewal.md
│   ├── Competitive Loss Analysis.md
│   └── [...]
│
├── decisions/                         ← [Optional] Decision post-mortems
│   ├── Should We Lower Price?.md
│   └── [...]
│
├── customers/                         ← [Optional, Sales] Account intelligence
│   ├── [Customer Name] Account Plan.md
│   └── [...]
│
├── personas/                          ← [Optional] Buyer/user psychology
│   ├── Procurement Persona.md
│   └── [...]
│
├── development/                       ← [Optional, Private] Personal growth
│   ├── Coaching Feedback.md
│   └── [...]
│
└── raw/                               ← Unprocessed intake
    ├── Article Clippings/
    ├── Meeting Notes/
    └── processed/                     ← Files you've already integrated
```

---

## Part 6: Using Your Second Brain

### With AI Agents

**Query your brain:**
```
Based on my frameworks and experience, should I offer a 20% discount to this customer?
```
The agent:
1. Reads your `CLAUDE.md` (approval matrix)
2. Reads your `[YourName]-Profile.md` (your decision criteria)
3. Reads your `Negotiation Framework` (how you structure offers)
4. Reads relevant case studies (what worked before)
5. Returns a recommendation within your guardrails

**Simulate scenarios:**
```
If this customer churns, run a simulation: what would I have done differently?
```
The agent:
1. Creates a hypothetical chain of decisions using your frameworks
2. Compares it to similar case studies
3. Suggests adjustments to prevent recurrence

### With Peers

**Share selectively:**
- "Check out my Enterprise Sales MOC for navigating this type of deal"
- "I've documented 3 frameworks we could use for this project"

**Get lateral insights:**
```
Jamie, can I query your renewal playbook for this situation?
(Jamie's agent consults her brain, responds with her perspective)
```

### Individually

**Learning loop:**
1. Apply a framework to a decision
2. Document the outcome
3. Refine the framework based on results
4. Next time, the refined version is available

**Development tracking:**
- Review your growth edges monthly
- Document progress in `development/` folder
- Show evolution of thinking over time

---

## Part 7: Governance & Maintenance

### Quarterly Checkpoints

| Month | Task | Time |
|-------|------|------|
| Every month | Review TRAVERSAL-INDEX; mark outdated files | 15 min |
| Q1, Q2, Q3, Q4 | Full brain audit: remove dupes, prune stale knowledge | 1 hour |
| Q2 | Update profile with new spiky POVs or growth edges | 30 min |
| Q4 | Year-end synthesis: what changed in how you operate? | 1 hour |

### Quality Indicators

Your brain is healthy if:
- ✅ Every file has clear frontmatter
- ✅ Files are linked (not isolated islands)
- ✅ You reference your own frameworks in your work (not external sources)
- ✅ Your MOCs are navigable (you can find related concepts)
- ✅ You update at least one file per week
- ✅ Peers ask to see your frameworks or case studies

Your brain needs attention if:
- ❌ Files are 6+ months old without updates
- ❌ No wikilinks between files (isolated knowledge)
- ❌ Frontmatter is incomplete or inconsistent
- ❌ You default to Google searching instead of querying your brain
- ❌ You can't summarize the structure in 2 minutes

---

## Part 8: Role-Specific Baselines

### Sales

**Baseline + Must-Add:**
- [ ] [YourName]-Profile.md (psychological operating style is critical)
- [ ] Enterprise Sales Process (or your actual sales methodology)
- [ ] Account Planning Framework
- [ ] Negotiation Framework
- [ ] Tivian/[Product] Features & Pricing
- [ ] SLA & Discount Policy (from CLAUDE.md)
- [ ] Enterprise Sales MOC, Renewal Strategy MOC
- [ ] 2–3 case studies (wins and losses)
- [ ] Competitive Intelligence (if you track it)

**Optional Enhancements:**
- Customer intelligence templates for top 5 accounts
- Persona profiles (procurement vs. end-user vs. exec)
- Psychographic research on common customer types
- Market trends and emerging threats

---

### Product

**Baseline + Must-Add:**
- [ ] [YourName]-Profile.md (technical background + decision style matters)
- [ ] Feature Prioritization Framework (how do *you* decide what ships?)
- [ ] Technical Roadmap (current + next 2 quarters)
- [ ] Product Metrics Dashboard (usage, retention, satisfaction)
- [ ] User Research Synthesis (who are your users? what do they need?)
- [ ] Technical Debt Assessment Framework
- [ ] Roadmap Planning MOC, User Research MOC

**Optional Enhancements:**
- Architecture diagrams and design docs
- Competitive feature analysis
- Case studies of feature launches (what worked, what didn't)
- User personas and psychographics
- Technical constraints and scaling roadmap

---

### Marketing

**Baseline + Must-Add:**
- [ ] [YourName]-Profile.md (communication style is your tool)
- [ ] Campaign Planning Framework (how do *you* structure a campaign?)
- [ ] Content Strategy Framework
- [ ] Buyer Persona Definitions (who are we trying to reach?)
- [ ] Attribution & Funnel Model (how do you measure success?)
- [ ] Current Content Inventory (what exists? what's gaps?)
- [ ] Campaign Planning MOC, Buyer Intelligence MOC

**Optional Enhancements:**
- Campaign case studies with performance data
- Brand voice guidelines (tone, visual identity)
- Competitor creative analysis
- Content performance dashboard
- Market segmentation strategy

---

## Part 9: Common Mistakes & How to Avoid Them

| Mistake | Why It Happens | How to Avoid |
|---------|----------------|----|
| **Brain bloat** (500+ nodes, mostly junk) | Saving everything instead of curating | Ask: "Will I consult this again in the next 6 months?" If no, don't add. |
| **No connections** (isolated notes) | Treating brain as a filing cabinet | After adding a file, add 2–3 wikilinks to related concepts. If nothing connects, the file is probably irrelevant. |
| **Outdated frameworks** (built in 2024, never touched) | "Set it and forget it" mentality | Review your frameworks quarterly. If you've changed how you work, update the framework. |
| **Unclear frontmatter** (inconsistent types, tags) | Rushing through setup | Use the templates in this document. Consistency matters for federation. |
| **Too much personal opinion** (not useful to peers) | Confusing personal notes with operational knowledge | Mark personal development notes as private. Share frameworks and synthesized insights, not raw opinions. |
| **Not using your brain** (it exists but you don't consult it) | Habit of Googling instead | Make a conscious choice: next decision you face, consult your framework first. Then notice: faster? Better decision? More aligned? |

---

## Part 10: Scaling to Organization

Once 3–5 people have functioning Second Brains, the federation layer enables:

1. **Central Hub** (hub-and-spoke topology)
   - Aggregates shareable frameworks from everyone
   - Detects contradictions ("When Sales says X but Product says Y")
   - Creates synthesis nodes
   - Provides a searchable central index

2. **Cross-functional Queries**
   - Sales queries the central hub: "What does Product think about discounting?"
   - Product queries Sales: "What's the customer churn reason we're hearing?"
   - Gets multiple perspectives, not single answers

3. **Organizational Learning**
   - Every decision post-mortem becomes organizational learning
   - New hires can access collective frameworks instead of learning from scratch
   - Framework evolution is visible and traceable

4. **Agentic Workflows**
   - Individual agents augment individual contributors
   - Hub agents make org-level decisions (routing, resource allocation)
   - Hierarchy of agents reflects organizational hierarchy

---

## Conclusion

Your Second Brain is:
- **For you first**: It makes you smarter, faster, more consistent
- **For the organization second**: It contributes to collective intelligence when you choose to share
- **Living, not static**: It evolves as you evolve
- **Federated, not centralized**: You maintain autonomy; sharing is opt-in

**Start small.** Baseline takes 2–4 hours. Build quality, not volume. One well-crafted 20-node brain beats a chaotic 500-node dump.

**Iterate constantly.** Your brain should reflect how you actually work, not how you think you work.

**Share intentionally.** Frameworks and learnings have organizational value; personal notes stay private.

The goal is not a perfect brain—it's a *useful* brain that makes you better at your job, helps your peers learn, and scales your organization's intelligence as it grows.

---

## Appendix: File Templates

### Template: Profile.md
```markdown
---
type: profile
name: "[Your Name]"
role: "[Your Role]"
operating_style: "[MBTI/DiSC/etc], [key traits]"
spiky_povs: ["POV 1", "POV 2", "POV 3"]
last_updated: 2026-04-23
---

# [Your Name] — [Your Role]

## Psychological Profile
[Operating style, decision-making approach, communication preferences]

## Spiky POVs
1. [Non-negotiable belief 1]
2. [Non-negotiable belief 2]
3. [Non-negotiable belief 3]

## Strengths
- [Strength 1]
- [Strength 2]

## Growth Edges
- [Edge 1]
- [Edge 2]

## Working Style
[Remote/office, collaboration preferences, timezone, response time]
```

### Template: Framework.md
```markdown
---
type: framework
name: "[Framework Name]"
role: "[Sales|Product|Marketing|etc]"
description: "[One-liner]"
when_to_use: "[Specific situations]"
tags: ["tag1", "tag2"]
is_shareable: true
last_updated: 2026-04-23
---

# [Framework Name]

## Why This Works
[2–3 sentences on underlying logic]

## The Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Real Example
[Concrete example from your work]

## Common Mistakes
- [Mistake 1]
- [Mistake 2]

## When It Breaks
[Limitations and exceptions]

## Related Frameworks
- [[Framework B]]
- [[Framework C]]
```

### Template: MOC.md
```markdown
---
type: moc
name: "[MOC Name]"
description: "[What this clusters and why it matters]"
tags: ["topic1", "topic2"]
last_updated: 2026-04-23
---

# [MOC Name]

## Purpose
[Why this MOC exists]

## Clusters

### [Cluster 1]
- [[File 1]]
- [[File 2]]

### [Cluster 2]
- [[File 3]]
- [[File 4]]

## Open Threads
- [ ] Task 1
- [ ] Task 2
```

---

**Document Version**: 1.0  
**Last Updated**: April 2026  
**Created by**: Entropy System Beta Team  
**Feedback or Questions?** Contact your manager or the Entropy governance team.
