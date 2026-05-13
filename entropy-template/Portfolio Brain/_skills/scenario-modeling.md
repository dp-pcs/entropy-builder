# Portfolio Brain Skill: Portfolio Scenario Modeling

Model the impact of portfolio-level interventions before committing resources. Use when Jay asks "what if we raise prices on Floor Price accounts?", "which at-risk accounts should I prioritize?", "what's my projected churn this quarter?", or any question that requires modeling outcomes across multiple accounts simultaneously.

**Design principle:** Individual playbooks answer "what should I do with this account?" Scenario modeling answers "what should I do with my time and my portfolio?" It's the strategic layer above account-level tactics.

## What to Load

1. `Portfolio Brain/_Prediction_Ledger.md` — Signal Combination Registry + Pattern Library for empirical churn/renewal rates
2. `Portfolio Brain/_analytics/metrics.md` — Health score bands, segment definitions
3. `Portfolio Brain/_analytics/schemas.md` — Frontmatter fields for querying (avoid full file reads)
4. Intelligence summary **frontmatter only** for the accounts in scope — scan YAML, don't read bodies unless a specific account needs deeper analysis

Do NOT load: Company-Rules (unless the scenario involves pricing), vault MOCs, individual playbooks, email histories.

## Scenario Types

### 1. Portfolio Churn Forecast

**Trigger:** "What's my projected churn this quarter?" / "How many accounts am I going to lose?"

**Method:**
1. Pull all accounts with `renewal_date` in the forecast window.
2. For each, extract: health_score, health velocity (from Health History if available), segment, status, sentiment combo, whether a playbook exists.
3. Build each account's signal profile (per Prediction Ledger's Signal Combination dimensions).
4. Check Signal Combination Registry for empirical rates. Where no match exists, use base rates:

| Signal Profile | Base Churn Probability |
|---------------|----------------------|
| Health 🟢 + Positive/Neutral renewal sentiment | 5% |
| Health 🟢 + Negative renewal sentiment | 15% |
| Health 🟡 + Positive/Neutral renewal sentiment | 20% |
| Health 🟡 + Negative renewal sentiment | 40% |
| Health 🔴 + any sentiment | 60% |
| Health 🔴 + Negative renewal sentiment + no playbook | 75% |
| Active+Cancelled status | 85% (unless win-back playbook exists, then 50%) |

5. Override base rates with Signal Combination Registry matches where confidence is Medium+.
6. Compute: `expected_churn_arr = sum(arr × churn_probability)` for all accounts in window.

**Output:**
```
PORTFOLIO CHURN FORECAST: [Quarter/Period]
Accounts renewing: [N]
Total renewing ARR: $[X]

PROJECTED CHURN:
Expected churn ARR: $[X] ([Y]% of renewing ARR)
Expected churn count: [N] accounts

HIGH-RISK ACCOUNTS (churn probability > 50%):
| Customer | Product | ARR | Health | Churn Prob | Playbook? | Key Signal |

AT-RISK ACCOUNTS (churn probability 20-50%):
| Customer | Product | ARR | Health | Churn Prob | Playbook? | Key Signal |

CONFIDENCE: [Low/Medium/High] — based on data quality and Signal Registry coverage
```

### 2. Intervention Prioritization

**Trigger:** "Which accounts should I focus on?" / "If I can only save 5 of these, which 5?"

**Method:**
1. Identify the accounts in scope (at-risk, declining, renewing soon, etc.).
2. For each, compute: `saveable_arr = arr × churn_probability × save_probability`
   - `save_probability` estimates how likely intervention is to change the outcome. Factors:
     - Active playbook exists → +0.2
     - Engaged champion contact (Last Engaged < 30d) → +0.15
     - Health velocity is stabilizing or improving → +0.1
     - Support issues are actively being resolved → +0.1
     - EoE product or corporate decision → -0.3 (intervention unlikely to matter)
     - Single-threaded + champion silent 60d+ → -0.2
3. Rank by `saveable_arr` descending. This prioritizes accounts where intervention has the highest expected value — not just the biggest ARR or the most distressed.

**Output:**
```
INTERVENTION PRIORITY RANKING

| Rank | Customer | Product | ARR | Churn Prob | Save Prob | Saveable ARR | Recommended Action |
|------|----------|---------|-----|-----------|-----------|-------------|-------------------|

TOP [N] ACCOUNTS BY EXPECTED VALUE:
[List with one-sentence action for each]

ACCOUNTS WHERE INTERVENTION WON'T HELP:
[List accounts with save_probability < 0.15 and why — e.g., EoE product, corporate decision]
```

### 3. Pricing Impact Modeling

**Trigger:** "What happens if we raise Floor Price accounts by X%?" / "What's the churn impact of a 25% increase across the board?"

**Method:**
1. Identify accounts in scope (e.g., all Floor Price, all accounts renewing in Q3).
2. For each, apply the price change and estimate the churn probability delta:
   - Accounts with Price Sensitivity = high (from Contact Persona) → churn_probability += 0.25
   - Accounts with Negative renewal sentiment → churn_probability += 0.15
   - Accounts with active playbook → churn_probability += 0.10 (playbook may absorb the shock)
   - Accounts with health 🟢 + Positive sentiment → churn_probability += 0.05 (resilient)
3. Compute new vs. old expected ARR under each scenario.

**Output:**
```
PRICING IMPACT MODEL: [Description of change]

CURRENT STATE:
Accounts affected: [N]
Current total ARR: $[X]
Current expected retained ARR: $[X] (using base churn probabilities)

AFTER PRICE CHANGE:
New total ARR (if all renew at new price): $[X]
New expected retained ARR: $[X] (with adjusted churn probabilities)
Net expected ARR delta: +$[X] or -$[X]

ACCOUNTS MOST LIKELY TO CHURN FROM THIS CHANGE:
| Customer | Current ARR | New ARR | Current Churn Prob | New Churn Prob | Risk Factor |

RECOMMENDATION: [Is the expected revenue gain worth the churn risk?]
```

### 4. Segment Scenario Comparison

**Trigger:** "What if I focus all my time on HVO accounts?" / "Should I invest in saving low-ARR accounts or expanding high-ARR ones?"

**Method:**
1. Define two or more resource allocation scenarios.
2. For each scenario, model the portfolio impact over 90/180/365 days:
   - Accounts receiving attention: improved save probability (+0.15 to +0.25)
   - Accounts NOT receiving attention: baseline or degraded save probability (-0.1 for accounts currently in crisis)
3. Compare total expected ARR across scenarios.

**Output:**
```
SCENARIO COMPARISON: [Scenario A] vs [Scenario B]

| Metric | Scenario A | Scenario B | Delta |
|--------|-----------|-----------|-------|
| Accounts receiving attention | | | |
| Accounts neglected | | | |
| Expected retained ARR (90d) | | | |
| Expected retained ARR (180d) | | | |
| Expected churn count | | | |
| Highest-risk neglected account | | | |

RECOMMENDATION: [Which scenario maximizes expected ARR and why. Flag any high-value accounts that get neglected in the recommended scenario.]
```

## Rules

- **All probabilities are estimates, not predictions.** Always include a confidence rating and flag where data is thin.
- **Never present a single number without showing the range.** Use ±X% or best/worst case bounds.
- **Cite Signal Combination Registry entries** when they inform a probability. Transparency in how numbers were derived lets Jay calibrate his own judgment.
- **Output is conversational only.** Don't save scenario models as files. They're point-in-time analysis, not persistent records. If an insight is worth preserving, it goes into the Prediction Ledger's Pattern Library.
- **Update the Prediction Ledger** when a modeled scenario resolves. If you forecasted 30% churn on a cohort and actual churn was 45%, that calibration data matters.

## Integration Points

- **playbook.md** — Individual playbooks model scenarios for one account. Scenario modeling provides the portfolio context: "Should this account even get a playbook, or is intervention effort better spent elsewhere?"
- **dashboard.md** — Portfolio Dashboard shows current state. Scenario modeling projects forward from that state.
- **alerting.md** — Alerts flag individual accounts. Scenario modeling aggregates those alerts into portfolio-level risk assessment.
- **Prediction Ledger** — The empirical foundation. Every probability used in scenario modeling should trace back to either a Signal Combination Registry entry or a documented base rate.
