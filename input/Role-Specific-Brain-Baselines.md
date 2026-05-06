# Role-Specific Second Brain Baselines
**Concrete Examples of Must-Have Frameworks by Function**

**Version 1.0** | April 2026

---

## Overview

This document provides **concrete examples** of frameworks, MOCs, and knowledge structures for each role. Use these as templates—adapt, modify, or completely rewrite based on your actual operating system.

**Key principle**: These are starting points, not dogma. Your brain should reflect how *you* work.

---

## Sales (Enterprise / Account Management)

### Core Identity Elements

**Profile (Sales)**
```yaml
type: profile
role: "Enterprise Account Executive" | "Account Manager" | "Sales Director"
operating_style: "Relationship-driven, strategic, multi-threaded stakeholder engagement"
spiky_povs:
  - "Customer success is revenue success—align incentives first"
  - "Enterprise deals close on strategic fit, not features"
  - "We lose renewals because we don't invest in relationship depth early"
```

### Must-Have Frameworks (Minimum 4)

#### 1. **Enterprise Sales Process**
```markdown
# Enterprise Sales Process (MEDDIC Adapted)

## The 5 Stages
1. **Discovery** (Metrics, Economic buyer, Decision criteria)
   - Identify economic buyer AND end-user champion
   - Qualify budget and timeline
   - Understand decision criteria (cost vs. capability vs. risk)
   
2. **Exploration** (Dig into their world)
   - Map org structure and decision committee
   - Understand their current solution and pain with it
   - Identify competitive alternatives they're considering
   
3. **Positioning** (Show fit)
   - Demonstrate how our product solves their specific pain
   - Position vs. competitors using their own criteria
   - Begin relationship building with key stakeholders
   
4. **Negotiation** (Align economics)
   - Structure deal (pricing, terms, scope)
   - Use negotiation framework to create value (not just discounts)
   - Get buy-in from economic buyer
   
5. **Close + Onboard** (Secure renewal)
   - Ensure successful implementation
   - Establish QBR cadence
   - Identify expansion opportunities within first 90 days

## Real Example
[Customer name]. Economic buyer was CFO (cost-focused). End-user champion was ops director (capability-focused). We positioned cost-of-ownership vs. alternatives, won CFO with TCO analysis, won ops director with feature fit.

## Common Mistakes
- Talking to wrong stakeholder (technical contact, not economic buyer)
- Skipping discovery (jumping to features too fast)
- Treating all deals the same (enterprise deals require multi-threading)

## Related Frameworks
- [[Account Planning Framework]]
- [[Negotiation Framework]]
- [[Tivian Product Positioning]]
```

---

#### 2. **Account Planning Framework**
```markdown
# Account Planning Framework

## Pre-Sale Planning
### Stakeholder Map
- Economic buyer (controls budget): [Title, name, priorities]
- End-user champion (drives capability): [Title, name, priorities]
- Technical evaluator (assesses fit): [Title, name, priorities]
- Other influencers: [Titles, how they influence]

### Opportunity Score (Pre-engagement)
- Budget available: [Y/N + size]
- Timeline: [Next 30 / 60 / 90 days or unclear]
- Current vendor (if applicable): [Name + relationship strength]
- Competitive threat: [Yes / No + who]

### Approach
- Which stakeholder to engage first? (Usually: economic buyer or champion)
- What's the conversation (not the pitch)?
- What do they get from meeting with us?

## Post-Sale Planning (Renewal Prep)
### Account Health Score
- Engagement level: [High / Medium / Low] (how often do we talk?)
- Customer sentiment: [Positive / Neutral / At risk] (are they happy?)
- Product adoption: [>80% / 50-80% / <50%] (are they using us?)
- Expansion potential: [High / Medium / Low] (more products? more users?)
- Churn risk: [Low / Medium / High] (likelihood they leave?)

### Renewal Strategy
- Key risks (why might they leave?): [Risk 1, Risk 2]
- Key wins (why they stay?): [Win 1, Win 2]
- Executive sponsor (relationship at C-level?): [Y/N]
- QBR frequency: [Monthly / Quarterly / Semi-annual]
- Expansion plan (what to sell next?): [Feature/product + timeline]

## Real Example
[Customer]. Health score: High engagement (weekly calls), positive sentiment, 90%+ adoption, medium expansion (could add 3 products). Churn risk: low. Renewal strategy: lean into adoption success (ROI story), position add-on products Q2.

## When This Breaks
- If customer has gone through leadership change (previous relationships don't matter)
- If they've been acquired (new decision-makers, new priorities)
- If there's a technical incident (health score flips immediately)

## Related Frameworks
- [[Enterprise Sales Process]]
- [[Expansion Playbook]]
```

---

#### 3. **Negotiation Framework**
```markdown
# Negotiation Framework

## Pre-Negotiation Prep
### Their Position
- Stated budget: [Amount]
- Stated walkaway: [What they claim is non-negotiable]
- Actual constraints: [What they *really* won't flex on]
- What they want (stated): [Features, price, terms]
- What they *need* (unstated): [Relationship, proof of concept, timeline]

### Our Position
- Walkaway (what we truly won't do): [e.g., "won't discount below 20%"]
- What we're willing to flex on: [Terms? Scope? Timeline? Payment?]
- Anchoring statement: [Our opening ask, slightly optimistic]

## The Negotiation
### Tactics
1. **Anchor high** (start with >what you expect to get)
2. **Use their criteria** (they value X, we address X)
3. **Make first move only if it advantages us** (otherwise let them anchor)
4. **Ask calibrated questions** ("Help me understand why that budget?" vs. "Your budget is too low")
5. **Create value, don't just split difference**

### Creating Value (Instead of Discounting)
- **Payment terms**: Instead of 20% discount, offer 90-day payment terms (costs us nothing, saves them cash flow)
- **Scope**: Instead of discounting, bundle with another product (increases LTV)
- **Timeline**: Instead of discount, promise faster implementation (risky but possible)
- **Relationship**: Instead of discount, commit to quarterly C-level business review (builds relationship)

## Real Example
Customer wanted 25% discount. Budget constraint was real, but they also needed faster implementation. We offered 10% discount + 90-day payment terms + expedited onboarding (cost us ~$5k, not 25% of deal). They got cash flow relief + speed; we got healthier margin.

## When This Breaks
- If they have a real alternative that's cheaper (we're not solving their core problem)
- If they have multiple concurrent vendors (decision not yet made on us vs. them)
- If the CFO just got replaced (new person, no relationship)

## Related Frameworks
- [[Sources: Never Split the Difference]]
- [[Enterprise Sales Process]]
- [[Pricing Policy]]
```

---

#### 4. **Renewal Playbook**
```markdown
# Renewal Playbook

## Timeline (Plan Backwards from Renewal Date)

### 180 Days Before Renewal
- [ ] Add to CRM as renewal opportunity
- [ ] Assign owner
- [ ] Run account health score
- [ ] Schedule executive business review

### 120 Days Before Renewal
- [ ] Document ROI / usage metrics
- [ ] Identify expansion opportunities
- [ ] Document any support incidents or requests
- [ ] Schedule discovery call: "What's worked? What hasn't? What's next?"

### 90 Days Before Renewal
- [ ] Present renewal proposal (with expansion recommendations)
- [ ] Address any concerns from 120-day call
- [ ] Propose new terms (if applicable)
- [ ] Get economic buyer involved if not already

### 60 Days Before Renewal
- [ ] Send formal renewal contract
- [ ] Set legal/finance review timeline
- [ ] If stalled, escalate to SVP

### 30 Days Before Renewal
- [ ] Follow up on signed contract
- [ ] Confirm payment / contract execution
- [ ] Plan onboarding for any new features/products
- [ ] Schedule kick-off call for renewed period

### At Renewal
- [ ] Contract signed & payment received
- [ ] Document final terms & expansion items
- [ ] Reset 180-day timeline for next renewal

## Churn Prevention Script (If At Risk)

**If Health Score is "At Risk":**
- [ ] Schedule urgent call with economic buyer
- [ ] Ask: "What would it take for you to stay?" (not "Please don't leave")
- [ ] Listen for specific concerns (technical, commercial, relationship)
- [ ] Solve or escalate (if we can't solve, executive may need to)

## Real Example
[Customer]. 180-day check: health score low (adoption was 40%, support tickets for bugs). 120-day call revealed: product wasn't living up to expectations. 90-day move: offered extended POC + dedicated resources + product roadmap commitment. Renewed at 15% increase because we solved their problems.

## Related Frameworks
- [[Account Planning Framework]]
- [[Expansion Playbook]]
- [[Negotiation Framework]]
```

---

#### 5. **Expansion Playbook** (Optional but Common)
```markdown
# Expansion Playbook (Land-Expand-Consume)

## Identify Expansion Opportunities (Post-Sale)
- **Additional users**: Are they using all user licenses? (If not, why expand?)
- **Additional products**: What other problems do they have that we solve?
- **Increased usage**: Are they hitting limits (storage, API calls, seats)?
- **Deeper integration**: Are they integrated with other systems? Can we deepen our role?

## Approach
- **Timing**: 90 days post-renewal (when they're happy)
- **Lead with value, not sales**: "We noticed you're using only 60% of licenses. Here's how to unlock more value."
- **Use internal champion**: End-user champion (not economic buyer) usually drives expansion
- **Keep original economic buyer in loop**: So renewal pricing reflects expanded scope

## Real Example
Customer (Tivian). 90-day review: using 50 of 75 licenses. We helped them unlock remaining users (changed behavior + training). 180-day review: they were hitting API limits. Upsold to premium tier. 270 days: introduced them to complementary product (Influitive). By 365 days, NRR was 125%.

## Common Mistakes
- Trying to expand before customer has seen ROI
- Expanding without economic buyer's knowledge (wastes goodwill)
- Over-expanding and then churning on price increase

## Related Frameworks
- [[Account Planning Framework]]
- [[Renewal Playbook]]
- [[The Expansion Sale (Source)]]
```

---

### Sales-Specific MOCs

```markdown
# Enterprise Sales MOC

## Strategic (Account Strategy)
- [[Account Planning Framework]]
- [[Expansion Playbook]]
- [[Competitive Intelligence]]
- [[Shannon Ramsey]] (mentor on enterprise strategy)

## Tactical (Deal Execution)
- [[Enterprise Sales Process]]
- [[Negotiation Framework]]
- [[Renewal Playbook]]
- [[Tivian Product Positioning]]

## Operational
- [[SLA Policy]]
- [[Discount Authority Matrix]]
- [[Case Studies - Wins & Losses]]

# Renewal Strategy MOC

## Framework
- [[Renewal Playbook]]
- [[Account Planning Framework]]
- [[Negotiation Framework]]

## Execution
- [[Renewal Case Studies]]
- [[Churn Prevention Playbook]]
- [[Expansion Playbook]]

## Support
- [[Company Rules (Renewal Constraints)]]
- [[Product Roadmap (Renewal Leverage)]]
```

---

### Sales Knowledge Base

```
knowledge/
├── Tivian/
│   ├── Tivian Features & Use Cases.md
│   ├── Tivian Pricing & Packaging.md
│   ├── Tivian vs. Competitor Positioning.md
│   ├── Tivian Roadmap (Next 2 Qtrs).md
│   └── Tivian Known Issues & Workarounds.md
├── Influitive/
│   └── [Same as above]
├── Lyris/
│   └── [Same as above]
├── QuickSilver/
│   └── [Same as above]
├── Company Policies/
│   ├── Discount Policy.md
│   ├── Engagement Authority.md
│   ├── SLA Policy.md
│   └── Data Privacy & Confidentiality.md
└── Industry Intelligence/
    ├── Market Trends (2025–2026).md
    ├── Competitive Landscape Overview.md
    ├── Buyer Personas (Procurement vs. End-User vs. Executive).md
    └── Economic Headwinds & Customer Budget Cycles.md
```

---

## Product Management

### Core Identity Elements

**Profile (Product)**
```yaml
type: profile
role: "Senior Product Manager" | "Product Director" | "Head of Product"
operating_style: "Data-driven + intuitive, analytical, bias toward action"
spiky_povs:
  - "Feature requests are opinions; metrics are facts"
  - "Shipping is better than planning; iterate fast"
  - "Customer success is the best product feedback"
```

### Must-Have Frameworks (Minimum 4)

#### 1. **Feature Prioritization Framework**
```markdown
# Feature Prioritization Framework (RICE Adapted)

## RICE Scoring
- **Reach**: How many customers/users will this affect? (1-100 scale)
- **Impact**: How much will it improve their outcome? (1-3: 3=massive, 2=medium, 1=small)
- **Confidence**: How confident are we in reach + impact? (1-100%)
- **Effort**: How long will it take? (in weeks)

**Score** = (Reach × Impact × Confidence) / Effort

## Threshold
- **Score >75**: High priority (ship soon)
- **Score 50-75**: Medium priority (queue for next quarter)
- **Score <50**: Low priority (shelf or rethink)

## Real Example
Feature A (multi-org support): Reach 60 (affects mid-market + enterprise), Impact 3, Confidence 90%, Effort 4 weeks = (60 × 3 × 0.9) / 4 = 40.5 (medium priority).

Feature B (dashboard redesign): Reach 100, Impact 2, Confidence 70%, Effort 8 weeks = (100 × 2 × 0.7) / 8 = 17.5 (low priority).

## When This Breaks
- If strategic importance overrides RICE (new market entry, existential threat)
- If effort is wildly uncertain (brand new technology)
- If there's high risk of inaction (security flaw, competitor feature)

## Related Frameworks
- [[Roadmap Planning Framework]]
- [[User Research Synthesis]]
- [[Technical Debt Assessment]]
```

---

#### 2. **Roadmap Planning Framework**
```markdown
# Roadmap Planning Framework

## Buckets (% of Capacity)

**New Features** (50%)
- High-impact features based on RICE prioritization
- Strategic initiatives (market expansion, new segment)

**Technical Debt & Scaling** (30%)
- Refactoring, performance, infrastructure
- Necessary for long-term sustainability

**Bugs & Stability** (15%)
- Critical bugs (impacting customers)
- Stability improvements (uptime, reliability)

**Exploration** (5%)
- Experiments, prototypes, moonshots
- Innovation budget

## Quarterly Planning Process
1. **Audit current state**: What's shipped? What's broken? What are customers asking for?
2. **Set OKRs**: What do we want to achieve this quarter?
3. **Assign to buckets**: New features vs. debt vs. bugs
4. **Prioritize within buckets**: Use RICE score
5. **Communicate**: Share roadmap with Sales, Support, Executive team
6. **Execute**: Daily standup, bi-weekly review, monthly adjustment

## Real Example
Q2 Roadmap:
- 50% (New): Multi-org support (RICE 40), Dashboard rebuild (RICE 35), API v2 (RICE 38)
- 30% (Debt): Refactor auth (blocking performance), migrate DB (reducing cost), improve observability
- 15% (Bugs): Address top 3 customer-reported issues
- 5% (Exploration): Prototype AI-powered feature recommendations

## When This Breaks
- If debt is ignored (technical bankruptcy)
- If exploration is 0% (become reactive)
- If customer requests override all strategy

## Related Frameworks
- [[Feature Prioritization Framework]]
- [[Technical Debt Assessment]]
```

---

#### 3. **User Research Synthesis Framework**
```markdown
# User Research Synthesis Framework

## Data Collection
- Customer interviews (what are they trying to do?)
- Usage metrics (what are they actually doing?)
- Support tickets (what's breaking?)
- Feature requests (what do they ask for?)
- NPS/satisfaction surveys (are they happy?)

## Themes
Cluster findings into patterns:
- **Jobs to be done**: What are users trying to accomplish?
- **Pain points**: What frustrates them?
- **Feature requests**: What do they ask for?
- **Workarounds**: How do they solve problems today?
- **Unmet needs**: What's implied but not stated?

## Synthesis
- Identify which themes are widespread (affects >20% of users)
- Separate "customer is wrong" from "we're wrong"
- Distinguish "nice to have" from "job to be done"

## Output
Link research to roadmap decisions:
- Why are we building X? (Research says Y pain point)
- Why NOT building Y? (Research shows <5% care)

## Real Example
Research synthesis: 40% of users have multi-org use cases. They're all using workarounds (exporting/importing data). Support gets 5+ tickets/month on this. Multi-org support went to top of roadmap.

## Related Frameworks
- [[Feature Prioritization Framework]]
- [[Roadmap Planning Framework]]
```

---

#### 4. **Technical Debt Assessment Framework**
```markdown
# Technical Debt Assessment Framework

## Debt Inventory
- **Scaling risk**: Can we 10x users without rewriting?
- **Performance debt**: Response times > acceptable threshold?
- **Code quality debt**: Refactoring needed to maintain velocity?
- **Infrastructure debt**: Old tech stack blocking new features?
- **Process debt**: Manual QA, deployment, monitoring?

## Impact Scoring
- **High**: Blocks new features or risks outage
- **Medium**: Slows down development or increases costs
- **Low**: Tech debt, but can ship features around it

## Timeline
- **Critical** (fix now): Blocks shipping, security risk, outage risk
- **Important** (next quarter): Slows team, increases cost
- **Nice-to-have** (backlog): Can live with it

## Real Example
Debt inventory:
- Auth system (scaling risk: HIGH - bottleneck at 10x users) → Critical
- Dashboard (performance: MEDIUM - loads in 3s, should be 1s) → Important
- Logging (process debt: MEDIUM - manual log review) → Important
- Old API v1 (code quality: MEDIUM - but can deprecate) → Nice-to-have

## When This Breaks
- If you ignore it (tech bankruptcy)
- If you over-invest in debt paydown (ship no features)
- If you use "tech debt" as excuse to delay features

## Related Frameworks
- [[Roadmap Planning Framework]]
- [[Feature Prioritization Framework]]
```

---

#### 5. **Metrics & Analytics Framework** (Optional but Valuable)
```markdown
# Metrics & Analytics Framework

## Product Health Metrics
- **Activation**: % of new users reaching [key milestone] in first 7 days
- **Adoption**: % of active users using [key feature]
- **Retention**: % of users returning after 30/90 days
- **NRR** (Net Revenue Retention): Revenue from existing customers this year vs. last year (>100% = growing)
- **Churn**: % of customers leaving each month

## Engagement Metrics
- **DAU / MAU** (Daily / Monthly Active Users)
- **Feature adoption**: % of users using each feature
- **Session frequency**: How often do users log in?
- **Session length**: How long do they spend?

## Business Metrics
- **Revenue per user**: ARPU / MRR
- **Customer acquisition cost**: CAC
- **Lifetime value**: LTV
- **LTV/CAC ratio**: Should be >3:1

## How These Drive Roadmap
- Low activation? → Improve onboarding
- Low adoption of feature X? → Is it solving a real problem or hard to find?
- Churn increasing? → Which cohort? When did they churn? Why?
- NRR <100%? → Expansion strategy failing

## Real Example
Metrics review: NRR = 95% (shrinking). Retention = 80% at 90 days. Churn cohort analysis: customers who didn't adopt feature X churned 2x more. Root cause: feature wasn't obvious. Roadmap fix: improve feature discovery in onboarding.

## Related Frameworks
- [[Roadmap Planning Framework]]
- [[User Research Synthesis]]
```

---

### Product-Specific MOCs

```markdown
# Roadmap Planning MOC

## Strategic Input
- [[Feature Prioritization Framework]]
- [[User Research Synthesis]]
- [[Metrics & Analytics Framework]]
- [[Product Roadmap (current)]]
- [[Competitive Feature Analysis]]

## Execution
- [[Technical Debt Assessment]]
- [[Roadmap Planning Framework]]
- [[Cross-functional Dependencies]]

# User Research & Insights MOC

## Sources
- [[Customer Interviews (Synthesis)]]
- [[Support Ticket Themes]]
- [[Feature Request Analysis]]
- [[Usage Data Deep Dives]]

## Application
- [[Feature Prioritization Framework]]
- [[User Research Synthesis Framework]]
- [[Roadmap Planning Framework]]

# Technical Roadmap MOC

## Current State
- [[Architecture Overview]]
- [[Scaling Constraints]]
- [[Technical Debt Inventory]]

## Future State
- [[Technical Debt Assessment]]
- [[Scalability Roadmap]]
- [[Technology Stack Decisions]]
```

---

### Product Knowledge Base

```
knowledge/
├── Product Documentation/
│   ├── User Handbook.md
│   ├── API Documentation.md
│   ├── Admin Guide.md
│   └── Known Issues & Bugs.md
├── Competitive Intelligence/
│   ├── Competitor A - Features & Positioning.md
│   ├── Competitor B - Features & Positioning.md
│   └── Feature Gap Analysis.md
├── Roadmap & Planning/
│   ├── Current Roadmap (Q2 2026).md
│   ├── Committed Features.md
│   └── Future Vision (2-year).md
├── User Research/
│   ├── Customer Interview Themes.md
│   ├── Feature Request Backlog.md
│   └── Cohort Analysis (Churn, Expansion, etc).md
├── Metrics & Analytics/
│   ├── Product Health Dashboard.md
│   ├── Engagement Metrics.md
│   └── Business Metrics.md
└── Company Policies/
    ├── Data Privacy & GDPR.md
    ├── Security Requirements.md
    └── SLA Commitments.md
```

---

## Marketing

### Core Identity Elements

**Profile (Marketing)**
```yaml
type: profile
role: "VP Marketing" | "Marketing Manager" | "Demand Gen Lead"
operating_style: "Visionary + analytical, story-driven, data-conscious"
spiky_povs:
  - "Brand is the accelerant to every campaign"
  - "Attribution is messy but necessary; don't hide from it"
  - "Content is not a tactic, it's a strategy"
```

### Must-Have Frameworks (Minimum 4)

#### 1. **Campaign Planning Framework**
```markdown
# Campaign Planning Framework

## Campaign Design
- **Goal**: What are we trying to achieve? (Awareness, consideration, conversion, retention)
- **Target**: Who? (Persona, firmographic, behavioral)
- **Message**: What's the story? (Problem, solution, differentiation)
- **Channel**: Where? (Email, content, paid, events, partnerships)
- **Timeline**: When? (Duration, key milestones)

## Metrics
- **Input metrics**: How much content/spend did we put in?
- **Output metrics**: How many impressions/clicks did we get?
- **Outcome metrics**: How many leads/customers?
- **Success metric**: Primary KPI (e.g., meetings booked, pipeline created)

## Attribution
- **Campaign source**: Where did the lead come from?
- **First touch**: Which campaign introduced them?
- **Multi-touch**: Multiple campaigns before conversion?
- **CAC**: How much did this campaign cost per customer?

## Real Example
Campaign: "Is [Your Company] Winning?" (webinar + email series)
- Goal: Consideration (get them to compare us to alternatives)
- Target: VP Operations at mid-market SaaS (50–500 employee range)
- Message: "How companies like yours reduced costs by 40%"
- Channel: LinkedIn ads → webinar → nurture email
- Results: 500 registrations, 120 attendees, 45 demos booked, 8 customers (CAC: $2500)

## When This Breaks
- If you optimize for wrong metric (clicks instead of pipeline)
- If attribution is incomplete (missing touchpoints)
- If timing is off (campaign launches when buyers aren't shopping)

## Related Frameworks
- [[Buyer Persona Development]]
- [[Content Strategy Framework]]
- [[Attribution & Funnel Model]]
```

---

#### 2. **Content Strategy Framework**
```markdown
# Content Strategy Framework

## Content Inventory
- What content exists? (Blog, case studies, whitepapers, webinars, guides)
- What's performing? (Which topics get reads/shares/leads?)
- What's not? (Which content is gathering dust?)
- What's gaps? (Topics your audience cares about but you don't cover)

## Buyer Journey Mapping
- **Awareness**: Buyer has a problem but doesn't know about us (educational content)
- **Consideration**: Buyer is comparing vendors (comparison content)
- **Decision**: Buyer is deciding (case studies, pricing, testimonials)
- **Retention**: Buyer is using us (onboarding, best practices, updates)

## Content Pillars
- **Pillar 1**: Core topic (e.g., "Digital Transformation")
  - Sub-topics: Cloud migration, process automation, change management
  - Content: Blog posts, guides, webinars on each
- **Pillar 2**: Core topic (e.g., "ROI & Cost")
  - Sub-topics: Cost reduction, efficiency, benchmarking
  - Content: Calculators, case studies, reports

## Distribution
- **Owned**: Your website, email, blog
- **Earned**: PR, partnerships, influencers sharing
- **Paid**: Ads to amplify content

## Real Example
Content gap: Competitors are publishing ROI calculators; we're not. We built one. Inbound leads from calculator increased 40%.

## Related Frameworks
- [[Campaign Planning Framework]]
- [[Buyer Persona Development]]
- [[Attribution & Funnel Model]]
```

---

#### 3. **Buyer Persona Development Framework**
```markdown
# Buyer Persona Development Framework

## Data Collection
- **Firmographic**: Company size, industry, revenue, location
- **Role**: Job title, reporting structure, goals
- **Challenges**: What keeps them up at night?
- **Buying process**: How do they evaluate vendors?
- **Decision-making style**: Analytical? Intuitive? Collaborative?
- **Budget**: How much can they spend?
- **Information sources**: Where do they research solutions?

## Persona Profile (Template)

### Persona: [Title] [Name]
- **Company**: [Size, industry]
- **Goals**: [Primary goal 1, Primary goal 2]
- **Challenges**: [Challenge 1, Challenge 2, Challenge 3]
- **Buying criteria**: [What matters most: price, fit, vendor stability, etc.]
- **Objections**: [Common reasons they say no]
- **Information sources**: [Where they research]
- **Success metric**: [How they measure if solution works]

## Real Example
**Persona: Procurement Manager (Sarah)**
- Company: Mid-market SaaS, 200 people, $50M revenue
- Goals: Reduce vendor costs, streamline procurement process
- Challenges: Manual vendor management, no visibility into spending, contract compliance
- Buying criteria: TCO, ease of integration, compliance features
- Objections: "Will require IT involvement to integrate"
- Information sources: LinkedIn, Capterra, peer recommendations
- Success metric: Reduced vendor costs by 15%+ within 1 year

## When This Breaks
- If persona is too generic (applies to everyone, predicts nothing)
- If you create personas without data (stereotyping instead of research)
- If you ignore secondary personas (only focus on primary)

## Related Frameworks
- [[Campaign Planning Framework]]
- [[Content Strategy Framework]]
- [[Attribution & Funnel Model]]
```

---

#### 4. **Attribution & Funnel Model Framework**
```markdown
# Attribution & Funnel Model Framework

## Funnel Stages
- **Awareness**: Prospect knows we exist
- **Consideration**: Prospect is comparing us to alternatives
- **Decision**: Prospect is about to buy
- **Adoption**: Customer is using us
- **Expansion**: Customer is buying more
- **Retention**: Customer keeps buying

## Conversion Rates (Baseline to Compare)
- Awareness → Consideration: [%]
- Consideration → Decision: [%]
- Decision → Adoption: [%]
- Adoption → Expansion: [%]
- Expansion → Retention: [%]

## Tracking
- **Multi-touch attribution**: Which campaigns touch prospect at each stage?
- **First touch**: Which campaign introduced them?
- **Last touch**: Which campaign convinced them?
- **Custom**: [Your company's custom attribution model]

## Real Example
Funnel analysis:
- 10,000 aware (from ads, content, word of mouth)
- 1,000 considering (requested demo)
- 250 deciding (entered negotiation)
- 50 adopted (signed contract)

Conversion: Awareness→Consideration = 10%, Consideration→Decision = 25%, Decision→Adoption = 20%

Attribution analysis: 70% of customers had touched at least 3 campaigns before purchase. First campaign was usually content (blog), last campaign was usually sales team.

## When This Breaks
- If you have incomplete data (some leads tracked, some not)
- If offline sales aren't tracked (sales calls, partnerships)
- If you assume correlation = causation (customer saw your ad, so it caused the sale—maybe they were already buying)

## Related Frameworks
- [[Campaign Planning Framework]]
- [[Buyer Persona Development]]
- [[Content Strategy Framework]]
```

---

### Marketing-Specific MOCs

```markdown
# Campaign Planning MOC

## Planning
- [[Campaign Planning Framework]]
- [[Buyer Persona Development]]
- [[Content Strategy Framework]]

## Execution
- [[Current Campaign Calendar]]
- [[Campaign Assets Inventory]]
- [[Distribution Channels]]

## Measurement
- [[Attribution & Funnel Model]]
- [[Campaign Performance Dashboard]]

# Content Strategy MOC

## Strategy
- [[Content Strategy Framework]]
- [[Buyer Journey Mapping]]
- [[Content Pillars]]

## Execution
- [[Content Calendar (Q2 2026)]]
- [[Blog Topics & Ideas]]
- [[Case Studies In Progress]]

## Performance
- [[Content Performance Analytics]]
- [[Keyword Strategy]]
- [[SEO Roadmap]]

# Buyer Intelligence MOC

## Personas
- [[Procurement Persona (Sarah)]]
- [[IT Persona (Marcus)]]
- [[Executive Persona (Patricia)]]

## Research
- [[Firmographic Data]]
- [[Psychographic Research]]
- [[Buying Process Studies]]

## Application
- [[Persona-Based Campaign Examples]]
- [[Message Testing]]
```

---

### Marketing Knowledge Base

```
knowledge/
├── Content Inventory/
│   ├── Blog Posts (Performance Ranking).md
│   ├── Case Studies.md
│   ├── Whitepapers & Guides.md
│   ├── Webinars Archive.md
│   └── Content Calendar (Current).md
├── Buyer Insights/
│   ├── Buyer Persona Profiles.md
│   ├── Firmographic Breakdown.md
│   ├── Buying Process Research.md
│   └── Customer Interview Themes.md
├── Competitive Intelligence/
│   ├── Competitor Content Analysis.md
│   ├── Competitor Messaging.md
│   ├── Content Gaps.md
│   └── Share of Voice Analysis.md
├── Attribution & Analytics/
│   ├── Funnel Performance Baseline.md
│   ├── Campaign Performance 2026.md
│   ├── Attribution Model.md
│   └── Customer Journey Mapping.md
├── Brand & Messaging/
│   ├── Brand Voice & Tone.md
│   ├── Core Messaging Pillars.md
│   ├── Elevator Pitch.md
│   └── Brand Visual Guidelines.md
└── Company Policies/
    ├── Customer Data Privacy.md
    ├── Approval Workflow.md
    └── Budget Authority.md
```

---

## Cross-Functional: Operations / Leadership

### Core Identity Elements

**Profile (Operations / Leadership)**
```yaml
type: profile
role: "VP Operations" | "SVP" | "Managing Director"
operating_style: "Systems-thinker, strategic, process-oriented"
spiky_povs:
  - "Culture and process are inseparable; design both"
  - "Metrics drive behavior; choose them carefully"
  - "Scaling requires removing leaders, not adding them"
```

### Must-Have Frameworks (Minimum 3)

#### 1. **Organizational Decision-Making Framework**
```markdown
# Organizational Decision-Making Framework

## Decision Type
- **Strategic**: Multi-year impact, affects multiple functions
- **Tactical**: 1-year impact, affects one function
- **Operational**: <3 months, affects day-to-day

## Decision Authority
- **CEO decides**: Strategic direction, M&A, major hires
- **SVP decides**: Tactical plans, annual budgets, function-level strategy
- **Manager decides**: Operational decisions, daily execution

## Decision Process
1. **Gather data**: What do we know? What do we not?
2. **Frame options**: What are the realistic choices?
3. **Decide**: Which is best?
4. **Execute**: Make it happen
5. **Review**: Did it work? What would we do differently?

## Real Example
Decision: Should we hire or outsource customer success?
- Data: Current cost, quality, scale capacity
- Options: Full hire, hybrid, full outsource
- Decision: Hybrid (in-house for strategic accounts, outsource for SMB)
- Execution: 60-day transition plan
- Review (90 days): Cost savings 20%, quality intact

## Related Frameworks
- [[RACI Matrix Framework]]
- [[Communication Framework]]
```

---

#### 2. **RACI Matrix Framework** (Decision Ownership)
```markdown
# RACI Matrix Framework

## Template
Who is:
- **Responsible**: Does the work
- **Accountable**: Final decision, owns outcome
- **Consulted**: Provides input before decision
- **Informed**: Notified after decision

## Real Example
Decision: Launch new product feature

| Decision | Responsible | Accountable | Consulted | Informed |
|----------|-------------|-------------|-----------|----------|
| Prioritization | Product Manager | VP Product | Sales, Support | Engineering |
| Technical feasibility | Engineer | VP Eng | Product | Cross-function |
| Go-to-market | Marketing | VP Marketing | Sales, Product | All |
| Support readiness | Support Lead | Support Manager | Product | Engineering |

## When to Use
- Large decisions with multiple stakeholders
- Cross-functional projects
- Ambiguous decision rights
- Recurring decisions (annual planning, hiring, etc.)

## Related Frameworks
- [[Organizational Decision-Making Framework]]
- [[Communication Framework]]
```

---

#### 3. **Communication Framework** (Strategy + Execution)
```markdown
# Communication Framework

## Types of Messages
- **Strategic**: Org-wide direction, vision, long-term
- **Tactical**: Team-level plans, quarterly goals
- **Operational**: Daily standup, status updates

## Communication Channels
- **All-hands**: Strategic messages, company updates
- **Department meetings**: Tactical messages, quarterly plans
- **1-on-1s**: Operational, personal development
- **Slack/async**: Quick updates, questions
- **Email**: Formal communications, records

## How to Communicate a Decision
1. **Why are we making this?** (Context)
2. **What are we doing?** (Decision)
3. **How will it impact you?** (Personal relevance)
4. **What happens next?** (Timeline)
5. **Questions?** (Feedback loop)

## Real Example
Communication: "We're shifting our pricing strategy"

Why: Market research shows customers want value-based pricing instead of seat-based
What: Moving from per-user pricing to per-organization pricing
Impact: Sales team gets new collateral and training; Support needs to update docs; Product needs to update billing system
Timeline: Implementation in 60 days; training starts in 30 days
Questions: Open Q&A session Thursday at 2pm

## Related Frameworks
- [[Organizational Decision-Making Framework]]
```

---

### Leadership MOCs

```markdown
# Strategic Planning MOC

## Planning Process
- [[Annual Planning Framework]]
- [[OKR Setting Process]]
- [[Budget Planning]]
- [[Resource Allocation Framework]]

## Execution
- [[Quarterly Business Review]]
- [[RACI Matrix Framework]]
- [[Communication Framework]]

## Monitoring
- [[Metrics Dashboard]]
- [[Red/Yellow/Green Status Tracking]]

# Organizational Design MOC

## Current State
- [[Org Structure (Current)]]
- [[Reporting Lines]]
- [[Cross-functional Dependencies]]

## Design Frameworks
- [[RACI Matrix Framework]]
- [[Span of Control Guidelines]]
- [[Team Composition Strategy]]

## Hiring & Development
- [[Hiring Criteria by Role]]
- [[Leadership Development Plan]]
- [[Performance Management Framework]]

# Cultural Frameworks MOC

## Culture Definition
- [[Company Values & Operating Principles]]
- [[Decision-Making Norms]]
- [[Communication Norms]]

## Reinforcement
- [[Hiring Alignment]]
- [[Feedback & Recognition]]
- [[Offboarding Process]]
```

---

## Conclusion

These examples are starting points. Your frameworks should:
- ✅ Reflect how you *actually* work
- ✅ Be specific enough to guide decisions (not generic)
- ✅ Link to your operating constraints (CLAUDE.md)
- ✅ Connect to other frameworks and sources

**Adapt these. Don't copy them verbatim.** If something doesn't match your reality, change it.

The best framework is one you'll actually use.

---

**Questions?** Contact your manager or the Entropy governance team.
