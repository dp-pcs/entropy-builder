# Second Brain Onboarding Checklist
**Rapid Implementation Guide for Individual and Team Rollout**

**Version 1.0** | April 2026 | Supports Sales-First Pilot + Multi-Function Scaling

---

## Quick Reference

| Phase | Duration | Outcome |
|-------|----------|---------|
| **Phase 0: Pre-Build Interview** | 30–45 min | Personalized brain scaffold based on your role & operating style |
| **Phase 1: Core Identity** | 1–2 hours | Profile, CLAUDE.md, TRAVERSAL-INDEX (skeleton) |
| **Phase 2: Baseline Knowledge** | 2–4 hours | Knowledge articles, 3–5 frameworks, curated sources |
| **Phase 3: Navigation & Links** | 1–2 hours | MOCs, wikilinks, full TRAVERSAL-INDEX |
| **Phase 4: Enhancement** | 2–6 hours | Role-specific additions (cases, playbooks, etc.) |
| **Total Time Investment** | 6–15 hours | Fully functional, shareable brain |

---

## Phase 0: Pre-Build Interview (30–45 min)

Before you build, answer these questions to scaffold your brain correctly. Do this with your manager or a peer who knows your work style.

### Identity Questions

**Q1: Operating Style**
```
How do you make decisions? (Pick 2–3 that resonate)
- [ ] Data-driven, analytical, need evidence
- [ ] Intuitive, pattern recognition, trust gut feel
- [ ] Collaborative, seek multiple perspectives
- [ ] Decisive, move fast, adjust on the fly
- [ ] Risk-averse, prefer structured approach
- [ ] High risk tolerance, bet big

Your actual answer:
_________________________________________
```

**Q2: Communication Style**
```
How do others typically describe you? (Pick 1–2)
- [ ] Direct, no-nonsense, tell it straight
- [ ] Diplomatic, relationship-focused, soft touch
- [ ] Energetic, storyteller, engaging
- [ ] Measured, thoughtful, careful with words
- [ ] Fact-based, data-heavy, numbers-driven
- [ ] Big-picture thinker, strategic

Your actual answer:
_________________________________________
```

**Q3: Spiky POVs (Non-Negotiable Beliefs)**
```
What 3 things do you believe that colleagues might disagree with?
(These are your differentiating points—what you'd "die on the hill" for)

POV 1: ______________________________________________
POV 2: ______________________________________________
POV 3: ______________________________________________
```

**Q4: Strengths (What You're Rare At)**
```
What are you better at than most colleagues?
(Not "I'm smart"—be specific: "I'm better at handling executive-level negotiations" or "I spot technical debt before it becomes a problem")

Strength 1: ______________________________________________
Strength 2: ______________________________________________
```

**Q5: Growth Edge (What You're Developing)**
```
What skill or mindset are you consciously working on?

Edge 1: ______________________________________________
Edge 2: ______________________________________________
```

### Role-Based Questions

**Q6: Role & Responsibilities**
```
Your title: ____________________________
Primary function: ____________________________
Top 3 things you're responsible for:
1. ______________________________________________
2. ______________________________________________
3. ______________________________________________
```

**Q7: Decision Authority**
```
What decisions do YOU own?
- [ ] Pricing/discounts up to: $______
- [ ] Customer scope/features: ____________________
- [ ] Hiring decisions: _____________________
- [ ] Process changes: _____________________
- [ ] Budget allocation: _____________________
- [ ] Other: _____________________
```

**Q8: Key Constraints**
```
What are the hard boundaries you operate within?
(Company policies, approval matrices, ethical limits)

Example: "Can't discount more than 20% without SVP approval"

Constraint 1: ______________________________________________
Constraint 2: ______________________________________________
Constraint 3: ______________________________________________
```

### Expertise Questions

**Q9: Frameworks You Actually Use**
```
What 3–5 frameworks or processes do you actually use in your daily work?
(Not theoretical—actual methodologies you follow)

Framework 1: ______________________________________________
Framework 2: ______________________________________________
Framework 3: ______________________________________________
Framework 4: ______________________________________________
Framework 5: ______________________________________________
```

**Q10: Knowledge Sources**
```
What 5 sources (books, courses, mentors, research) have most shaped how you work?

Source 1: ______________________________________________
Source 2: ______________________________________________
Source 3: ______________________________________________
Source 4: ______________________________________________
Source 5: ______________________________________________
```

**Q11: Key People / Mentors**
```
Who has most influenced your approach to work?
(Mentors, thought leaders, colleagues)

Person 1: __________ (and why): ______________
Person 2: __________ (and why): ______________
Person 3: __________ (and why): ______________
```

### Topic Clusters

**Q12: Natural Topic Clusters**
```
What are the natural "buckets" or themes in your work?
(Later, these become your MOCs)

Cluster 1: ______________________________________________
Cluster 2: ______________________________________________
Cluster 3: ______________________________________________
Cluster 4: ______________________________________________
```

**Example (Sales):**
- Enterprise Account Management
- Renewal & Retention Strategy
- Competitive Positioning
- Negotiation & Deal Structuring

**Example (Product):**
- Feature Prioritization
- Technical Roadmap
- User Research
- Metrics & Analytics

---

## Phase 1: Core Identity (1–2 hours)

### Task 1.1: Create [YourName]-Profile.md

Using answers from the interview above, create your profile file.

**Checklist:**
- [ ] YAML frontmatter complete (type, name, role, tags, is_shareable)
- [ ] Psychological profile (2–3 sentences on how you think)
- [ ] Spiky POVs (3, clearly stated)
- [ ] Key strengths (2–3)
- [ ] Growth edges (1–2)
- [ ] Working style (remote/office, collaboration, response time)
- [ ] Career summary (2–3 sentences, relevant to current role)

**Minimum viable version** (~200 words):
```markdown
---
type: profile
name: "Jamie Sanchez"
role: "Enterprise Account Executive"
operating_style: "Relationship-driven, intuitive, high EQ, collaborative"
spiky_povs: 
  - "Customer success is revenue success; align incentives early"
  - "Enterprise deals are won on strategic fit, not features"
  - "Personal relationships drive renewals"
psychological_profile: "ENFP, high empathy, moderate risk tolerance"
tags: ["sales", "enterprise", "relationships"]
is_shareable: true
last_updated: 2026-04-23
---

# Jamie Sanchez — Enterprise Account Executive

**Background**: 8 years B2B SaaS, 3 years enterprise renewals, previously mid-market expansion.

## Operating Style
Relationship-driven, intuitive reader of people. Prefer oral communication and collaborative decisions. Build trust through personal connection and deep stakeholder engagement.

## Spiky POVs
1. Customer success is revenue success—misalignment causes churn
2. Enterprise deals close on strategic fit, not feature lists
3. We underinvest in relationship depth; it's our biggest renewal lever

## Strengths
- Strategic account planning with multi-threaded engagement
- Enterprise-level negotiation and executive presence

## Growth Edges
- Data-driven forecasting (I trust intuition; need to trust numbers more)
- Handling ambiguity in early-stage deals
```

**Time:** 30–45 min

---

### Task 1.2: Create CLAUDE.md

Pull company rules, approval matrices, and constraints. Customize for your role.

**Checklist:**
- [ ] Approval matrix (pricing authority, engagement authority, budget authority)
- [ ] Company rules & policies (what can you offer? what requires approval?)
- [ ] Ethical boundaries (what should you never do?)
- [ ] Data sensitivity (what parts of your brain are private vs. shareable?)
- [ ] SLAs & service boundaries (what do you promise customers?)

**Minimum viable version** (~300 words):

```markdown
---
type: rule
name: "Company Rules & Boundaries"
description: "Approval matrices, pricing authority, ethical boundaries"
role: Sales
is_shareable: false
last_updated: 2026-04-23
---

# CLAUDE.md — Operating Boundaries

## Pricing Authority

**Renewal Discounts:**
- 0–15%: Your autonomous decision
- 15–25%: Requires SVP approval
- 25%+: Requires CEO approval

**Non-Standard Terms:**
- Can extend payment terms up to 90 days
- Cannot defer revenue recognition >90 days (requires Finance)

## Engagement Authority

**What You Can Promise:**
- 24-hour support response time
- Standard feature set per product
- Quarterly business reviews

**What Requires Approval:**
- Custom features or scope changes (>40 hours): Requires Product approval
- Dedicated resources or engineering time: Requires Director approval
- Discounted or free professional services: Requires Finance approval

## Ethical Boundaries

**Never Do Without Executive Sign-Off:**
- Decommission a customer without 30-day notice
- Override customer data privacy requests
- Make public statements about customer wins without approval
- Negotiate with multiple BU heads simultaneously (coordinate first)

## Data Sensitivity

**Private to You (Don't Share):**
- Personal development notes
- Salary/compensation discussions
- Specific customer contract terms
- Customer-provided internal data (org charts, financial performance)

**Shareable (Can Federate):**
- Deal playbooks and win strategies
- Negotiation frameworks
- Renewal playbooks
- Competitive intelligence
- Customer case studies (anonymized)
```

**Time:** 20–30 min

---

### Task 1.3: Create TRAVERSAL-INDEX.md (Skeleton)

Just the structure—you'll fill it in as you add files.

**Checklist:**
- [ ] Section headings in place
- [ ] Note total file count as you build (helps track brain growth)
- [ ] One-liner descriptions (will update as you create files)

**Skeleton version**:
```markdown
---
type: index
name: "Traversal Index"
description: "Master file listing and navigation guide"
last_updated: 2026-04-23
---

# [YourName]'s Second Brain — Traversal Index

**Last Updated**: April 2026  
**Total Nodes**: [will update as you build]

## Navigation Guide

### Core Identity
- [YourName]-Profile.md — [Operating style, spiky POVs]
- CLAUDE.md — [Rules, approval matrices, boundaries]

### Knowledge Base
- [Tivian | Influitive | Lyris] Product Documentation/
- Company Policies/
- [Industry] Intelligence/

### Frameworks
- [Framework 1]
- [Framework 2]
- [Framework 3]

### Sources (5–10 Curated)
- [Source 1]
- [Source 2]

### People (Key Influences)
- [Person 1]
- [Person 2]

### Maps of Content (MOCs)
- [MOC 1]
- [MOC 2]
- [MOC 3]

---

## Files at a Glance
[Will populate with table as you add files]
```

**Time:** 10–15 min

---

## Phase 2: Baseline Knowledge (2–4 hours)

### Task 2.1: Create knowledge/ Folder with Product Docs

What products does your role interface with? Export/document their core info.

**Checklist:**
- [ ] Product Features (use case, key features, competitive advantages)
- [ ] Pricing (tiers, packaging, standard discounts)
- [ ] Known Issues / Gaps (what doesn't work well?)
- [ ] Roadmap (if relevant to your role)

**File structure:**
```
knowledge/
├── Tivian/
│   ├── Tivian Features.md
│   ├── Tivian Pricing.md
│   └── Tivian Known Issues.md
├── Influitive/
│   └── [same as above]
├── Company Policies/
│   ├── Discount Policy.md
│   ├── SLA Policy.md
│   └── Data Privacy.md
└── Industry Intelligence/
    ├── Market Trends.md
    └── Competitive Landscape.md
```

**Example: Tivian Features.md**
```markdown
---
type: documentation
name: "Tivian Features"
description: "Core features, use cases, competitive advantages"
role: Sales
tags: ["tivian", "product"]
is_shareable: true
last_updated: 2026-04-23
---

# Tivian — Product Features

## Core Use Cases
1. [Use case 1 + which customers need it]
2. [Use case 2 + which customers need it]

## Key Features
- [Feature 1]: [Why it matters]
- [Feature 2]: [Why it matters]

## Competitive Advantages
- [Advantage 1 vs. Competitor X]
- [Advantage 2 vs. Competitor Y]

## Known Gaps / Limitations
- [Gap 1]: [Workaround or timeline]
- [Gap 2]: [Workaround or timeline]

## Related Framework
- [[Account Planning Framework]] (how to position features in an enterprise sale)
```

**Time:** 1–2 hours (depending on doc volume)

---

### Task 2.2: Create frameworks/ Files

Document 3–5 frameworks you actually use. Keep to ~300–500 words each; use the template.

**Checklist (per framework):**
- [ ] YAML frontmatter (type, name, role, when_to_use, tags, is_shareable)
- [ ] "Why This Works" section (underlying logic)
- [ ] The Steps (3–7 concrete steps with examples)
- [ ] Real example from your work
- [ ] Common mistakes you've made
- [ ] When it breaks / limitations
- [ ] Links to related frameworks or sources

**Frameworks by role (suggestions):**

**Sales:**
1. Enterprise Sales Process (your actual methodology)
2. Account Planning Framework
3. Negotiation Framework
4. Renewal Playbook

**Product:**
1. Feature Prioritization Framework
2. Technical Debt Assessment
3. Roadmap Planning Process
4. User Research Synthesis

**Marketing:**
1. Campaign Planning Framework
2. Content Strategy Framework
3. Attribution & Funnel Model
4. Buyer Persona Development

**Any Role:**
1. Decision-Making Framework (how you decide)
2. Problem-Solving Process
3. Communication Strategy

**Time:** 2–3 hours (30–45 min per framework)

---

### Task 2.3: Create sources/ Folder

List your 5–10 most influential sources. Use the template.

**Checklist:**
- [ ] YAML frontmatter (type, name, author, source_type, relevance)
- [ ] Why this source matters (2–3 sentences)
- [ ] Key ideas that changed how you work
- [ ] How you apply it in practice
- [ ] Relevant quotes (optional)

**Example:**
```markdown
---
type: source
name: "Never Split the Difference"
author: "Chris Voss"
source_type: book
url: "[Goodreads link]"
date_read: 2024-01
relevance: "Tactical empathy and calibrated questions transformed how I handle objections"
tags: ["negotiation", "sales", "communication"]
is_shareable: true
last_updated: 2026-04-23
---

# Never Split the Difference

## Key Idea: Tactical Empathy
Understanding the other party's perspective without agreeing with it. This doesn't require liking them or compromising your position.

## How I Use It
When a customer says "Your price is too high," instead of defending features, I ask: "Help me understand what budget constraints you're working with?" This shifts from argument to problem-solving.

## Relevant Quote
> "Empathy is not about agreement; it's about understanding." — Chris Voss

## Related Framework
- [[Negotiation Framework]] (applies tactical empathy to deal structuring)
```

**Time:** 45 min–1 hour (5–10 min per source)

---

### Task 2.4: Create people/ Folder

Key mentors, thought leaders, or colleagues who shaped your thinking.

**Checklist:**
- [ ] YAML frontmatter (type, name, role, relationship, how_they_influence_you)
- [ ] Their core philosophy (1 paragraph)
- [ ] How they've shaped your thinking (specific examples)
- [ ] What they're expert in

**Time:** 30 min (5 min per person, usually 3–5 people)

---

## Phase 3: Navigation & Links (1–2 hours)

### Task 3.1: Create MOC Files

Create 2–3 Maps of Content that organize your baseline knowledge into clusters.

**Standard MOCs (all roles):**
1. **Decision-Making MOC**: Links to your decision frameworks, case studies, sources
2. **Learning MOC**: Links to sources, mentors, concepts you're developing
3. **Operational MOC**: Links to company rules, policies, process documentation

**Role-specific MOCs:**

**Sales:**
- Enterprise Sales MOC (frameworks, negotiation, account planning)
- Renewal Strategy MOC (playbooks, sources, case studies)
- Competitive Intelligence MOC (competitive positioning, win/loss analysis)

**Product:**
- Roadmap Planning MOC (prioritization framework, roadmap, metrics)
- User Research MOC (research synthesis, user personas, feedback loops)

**Marketing:**
- Campaign Planning MOC (campaign framework, content, metrics)
- Buyer Intelligence MOC (personas, psychographics, engagement)

**Checklist per MOC:**
- [ ] YAML frontmatter (type, name, description, tags)
- [ ] Purpose section (why this cluster exists)
- [ ] 2–4 clusters with wikilinks to related files
- [ ] "Open Threads" section (what you're still building)

**Time:** 45 min–1 hour (15–20 min per MOC)

---

### Task 3.2: Add Wikilinks

Go back through your frameworks, sources, and knowledge docs. Add wikilinks to related files.

**Pattern:**
- Framework links to Sources: `[[Never Split the Difference]]`
- Framework links to other Frameworks: `[[Account Planning Framework]]`
- MOC links to Framework: `[[Enterprise Sales Process]]`
- Framework links to MOC: `[[Enterprise Sales MOC]]`

**Rule of thumb:** Each file should have 2–5 outbound links (to avoid over-linking).

**Time:** 30 min

---

### Task 3.3: Update TRAVERSAL-INDEX.md

Populate with all files you've created, organized by section.

**Checklist:**
- [ ] Total node count (updated)
- [ ] All files listed with one-line descriptions
- [ ] Organized by section (Identity, Knowledge, Frameworks, Sources, MOCs, etc.)
- [ ] File structure diagram at top
- [ ] "Files at a Glance" table (optional but helpful)

**Time:** 20 min

---

## Phase 4: Enhancements (2–6 hours, Optional)

Add role-specific or personality-driven extras as time permits.

### Sales-Specific Enhancements

**Option 1: Customer Intelligence (2 hours)**
- [ ] Create `customers/` folder
- [ ] Build account plan template for top 3 accounts
- [ ] Document stakeholder maps, risks, expansion opportunities
- [ ] Link to relevant frameworks (Account Planning, Negotiation)

**Option 2: Deal Playbooks (1.5 hours)**
- [ ] Create `playbooks/` folder
- [ ] Document 2–3 common deal types you face
- [ ] Include: trigger, key steps, common objections, how to counter
- [ ] Example: "Handling Competitive Threats in Renewal" playbook

**Option 3: Competitive Intelligence (1.5 hours)**
- [ ] Create `intelligence/` folder
- [ ] Competitor overviews (pricing, features, positioning)
- [ ] Win/loss analysis (past 5 deals)
- [ ] Market trends relevant to your accounts

**Option 4: Personas (1 hour)**
- [ ] Create `personas/` folder
- [ ] Document 3 buyer personas (procurement, end-user, executive)
- [ ] For each: decision criteria, communication preferences, pain points

---

### Product-Specific Enhancements

**Option 1: Roadmap Artifacts (2 hours)**
- [ ] Current roadmap with justifications
- [ ] Feature request backlog (link to user research)
- [ ] Prioritization rationale for top 10 items

**Option 2: Architecture & Constraints (2 hours)**
- [ ] System design overview
- [ ] Scaling constraints
- [ ] Technical debt register (linked to roadmap decisions)

**Option 3: User Research Synthesis (1.5 hours)**
- [ ] Recent user interviews or feedback (aggregated, anonymized)
- [ ] Themes and patterns
- [ ] Feature requests tied to research

**Option 4: Metrics Dashboard (1 hour)**
- [ ] Current KPIs (adoption, retention, satisfaction)
- [ ] How each metric ties to your decision frameworks
- [ ] Link to roadmap priorities

---

### Marketing-Specific Enhancements

**Option 1: Campaign Case Studies (2 hours)**
- [ ] Document 2–3 successful campaigns
- [ ] What worked? Why? What metrics matter?
- [ ] Templates for future campaigns

**Option 2: Content Inventory (1.5 hours)**
- [ ] What content exists (blog, case studies, whitepapers)?
- [ ] What's performing? What's not?
- [ ] Content gaps tied to buyer journey

**Option 3: Funnel & Attribution (1 hour)**
- [ ] How you track buyer movement
- [ ] Conversion rates by stage
- [ ] Which content/campaigns drive which outcomes?

**Option 4: Brand Voice (45 min)**
- [ ] How you communicate (tone, visual identity, messaging framework)
- [ ] Examples of on-brand vs. off-brand content
- [ ] Regional or audience-specific variations

---

### Cross-Role Enhancements (Any Role)

**Option 1: Case Studies & War Stories (2 hours)**
- [ ] Document a recent win (how did you land it? which frameworks?)
- [ ] Document a recent loss (what would you do differently?)
- [ ] Anonymize if necessary
- [ ] Link to frameworks and decision logic

**Option 2: Decision Post-Mortems (1.5 hours)**
- [ ] Pick a recent significant decision
- [ ] Document: what did you decide? why? what happened? what would you do differently?
- [ ] This becomes organizational learning over time

**Option 3: Contradictions & Tensions (1 hour)**
- [ ] Where do you disagree with company policy or your mentor?
- [ ] Document both perspectives + your synthesis
- [ ] Example: "Tactical Empathy vs. Hard Negotiation: When to use each"

---

## Getting Started: 7-Day Kickoff

Can't do 6–15 hours all at once? Here's a 7-day plan:

| Day | Task | Time | Outcome |
|-----|------|------|---------|
| **Day 1** | Phase 0 Interview + Task 1.1 (Profile) + Task 1.2 (CLAUDE.md) | 2 hours | Identity established |
| **Day 2** | Task 1.3 (TRAVERSAL-INDEX skeleton) + Task 2.1 (Product docs) | 2–3 hours | Knowledge base started |
| **Day 3** | Task 2.2 (Frameworks) | 2–3 hours | Operational expertise documented |
| **Day 4** | Task 2.3 (Sources) + Task 2.4 (People) | 1.5 hours | Influences documented |
| **Day 5** | Task 3.1 (MOCs) | 1 hour | Navigation structure in place |
| **Day 6** | Task 3.2 (Wikilinks) + Task 3.3 (Update TRAVERSAL-INDEX) | 1 hour | Brain is navigable |
| **Day 7** | Phase 4 enhancements (pick 1–2) | 2–4 hours | Personalization complete |
| **Total** | | 12–15 hours | Functional, shareable brain |

---

## Validation Checklist

Before you consider your brain "done," verify:

- [ ] **Completeness**: Profile, CLAUDE.md, TRAVERSAL-INDEX, 3+ frameworks, 5+ sources exist
- [ ] **Consistency**: All files have YAML frontmatter with type, description, tags, is_shareable
- [ ] **Connectivity**: 80%+ of files have 2+ wikilinks to related concepts
- [ ] **Usability**: You can answer a work question by querying your brain (not Googling)
- [ ] **Clarity**: Any colleague can read TRAVERSAL-INDEX and understand your brain's structure in <5 min
- [ ] **Alignment**: Frameworks reflect how you *actually* work, not how you think you should work
- [ ] **Freshness**: All files are dated; nothing is >6 months old

---

## Rollout Plan: Sales Team (Weeks 1–4)

**Week 1: Jamie (Pilot)**
- [ ] Complete full onboarding (Phases 0–4)
- [ ] Share with Shannon & David
- [ ] Gather feedback: What's confusing? What's missing?

**Week 2: Sebastian (Peer Validation)**
- [ ] Sebastian completes onboarding using same process
- [ ] Compare his brain structure to Jamie's (where do they align? differ?)
- [ ] Document lessons learned

**Week 3: Rest of Sales Team**
- [ ] Roll out template and checklist to 5–7 other AEs
- [ ] Weekly check-ins: "Which phase are you in? Any blockers?"
- [ ] Share best practices from Jamie & Sebastian

**Week 4: Integration & Testing**
- [ ] All brains exist; some are more mature than others (that's OK)
- [ ] Test federation: Can we query all sales brains at once?
- [ ] Identify contradictions across brains (Are all AEs using the same negotiation approach? Where do they differ?)

---

## Multi-Function Scaling (Month 2+)

Once Sales is stable (3+ functional brains), onboard Product using same process:

1. **Adapt baseline**: Which frameworks must Product have? (Feature prioritization, roadmap planning, research synthesis)
2. **Same interview process**: Gather operating style, spiky POVs, decision authority
3. **Same 7-day kickoff**: 1 product person as pilot, then 1–2 peers, then full team
4. **Cross-function federation**: Can we query Sales + Product at once? (e.g., "What features should we commit to this customer?")

---

## Troubleshooting

| Problem | Root Cause | Solution |
|---------|-----------|----------|
| **Too overwhelmed** | Trying to build all at once | Do 7-day plan; focus on Phase 1–3. Enhancements can wait. |
| **Brain feels hollow** | Not filling in enough detail | Frameworks should be 300–500 words, not 100. Real examples matter. |
| **Nothing connects** | Forgot wikilinks | Go back through each framework and add 3–5 links per file. |
| **Can't decide what to share** | Unclear on is_shareable | Default: shareable = yes. Only mark private if it's personal development or sensitive customer data. |
| **Questioning if this is worth it** | Hasn't used brain yet | Query it once. Make a decision using your framework. Notice: faster? Better aligned? More confident? If yes, keep going. |

---

## Maintenance Plan

### Weekly (5 min)
- [ ] Open brain once
- [ ] Scan one MOC or framework
- [ ] Ask: "Does this still reflect how I work?"

### Monthly (30 min)
- [ ] Review TRAVERSAL-INDEX
- [ ] Mark any files >3 months old as stale
- [ ] Add 1 new case study or update 1 framework based on recent work

### Quarterly (1 hour)
- [ ] Full audit: Are frontmatters consistent? Are links broken?
- [ ] Update profile: Any new spiky POVs? Growth edges?
- [ ] Prune: Delete irrelevant files

---

## Success Metrics

Your brain is working if:
- ✅ You consult it before making decisions (not just Googling)
- ✅ Peers ask to see specific frameworks or case studies
- ✅ You notice yourself referencing your own operating systems (not external sources)
- ✅ Your decision quality improves (faster, more consistent, better outcomes)
- ✅ AI agents can query it and return useful recommendations
- ✅ You update at least one file per week

Your brain needs rework if:
- ❌ Files are gathering dust (>1 month without updates)
- ❌ No wikilinks (feels like a filing cabinet, not a knowledge graph)
- ❌ You can't explain your brain's structure in 2 minutes
- ❌ You still default to searching instead of querying your brain

---

## Final Reminder

**This is not meant to be perfect.** Your brain will be messy at first. Frameworks will be incomplete. Connections will be missing. That's fine—you refine as you go.

**Start small. Build quality. Share selectively.**

In 2 weeks, you'll have a brain. In 2 months, you'll use it daily. In 6 months, it'll be irreplaceable.

---

**Questions?** Contact your manager or the Entropy governance team.
