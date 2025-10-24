# 💧 Financing Options and Budget Rules

## 1. Overview

Every team must fund its interventions (e.g., pipe change, leak reduction, desalination, renewable energy installations) using a combination of:

1. **Base budget allocation** (shared across all participants)
2. **Utility revenues** from water sales (automatically simulated)
3. **Optional bond issuance** for additional capital needs

Teams must balance **capital expenditures (CAPEX)**, **operating costs (OPEX)**, and **debt sustainability** while ensuring service reliability.

---

## 2. Total Available Budget

A **national investment budget** is provided at the start of each stage (e.g., every 25 years ($<u>PARAMETER</u>$)).

- Let:
  - $B_{\text{total}}$: total national budget (€/stage)
  - $s_i$: share of total budget selected by node *i*, with
    $\sum_i s_i \le 1$

Each node's available budget is therefore:

$B_i = s_i \cdot B_{\text{total}}$

Each team can select a fraction of the total available budget at each stage, which can be anything between 0% (no budget will be utilized) and 100% (all the budget will be utilized).

---

## 3. Financing Options

### 3.1 Base Budget

- Represents **government-provided capital** that does not need to be repaid.
- Can be used for any type of investment (pipes, tanks, pumps, leak reduction, etc.).
- Once spent, it reduces the remaining available funds.

### 3.2 Operational Revenue

- **Water tariff revenues** are automatically simulated based on consumption and prices.
- They primarily cover day-to-day **OPEX** (energy, maintenance, chemicals) and are **not** a direct decision variable in this stage.

### 3.3 Bond Issuance (Optional)

If a team needs additional funds beyond its allocated budget, it may issue a **bond** under the following standardized terms, at the start of each stage.

#### Bond Parameters

| Parameter | Symbol | Value / Range | Description |
|------------|---------|---------------|--------------|
| Maturity | $M$ | 25 years ($<u>PARAMETER</u>$) | Bullet repayment (principal repaid at maturity) |
| Risk-free rate | $r_f$ | 3 % ($<u>PARAMETER</u>$) | Long-term government yield |
| Base credit spread | $cs$ | 1 % ($<u>PARAMETER</u>$) | Typical spread under normal conditions |
| Spread slope | $a$ | 2 % ($<u>PARAMETER</u>$) | Sensitivity of spread to investor demand |
| Demand factor | $d$ | Random ∈ [0.8, 1.2] ($<u>PARAMETER</u>$) | Randomly selected |

---

## 4. Coupon Determination

The **coupon rate** of each issued bond is determined as:

$\text{coupon} = r_f + cs + a \times (1 - d)$

- If **investor demand is strong** (`d` > 1.0), the coupon is **lower** (cheaper borrowing).
- If **investor demand is weak** (`d` < 1.0), the coupon is **higher** (more expensive financing).

This mechanism simulates **real-world bond pricing**, where investor appetite determines the final borrowing cost.

Example (assuming $r_f = 3\%$, $cs = 1\%$, $a = 2\%$):

| Demand Factor (d) | Coupon (%) |
|--------------------|------------|
| 1.2 (strong demand) | 3.6 |
| 1.0 (neutral) | 4.0 |
| 0.8 (weak demand) | 4.4 |

---

After meeting 2025-10-24 (notes fixed with AI):

### **1. Annual Budget Allocation**

The total 25-year budget is divided **equally** across all 25 years to determine the **Yearly Budget**. This annual amount is split into two parts based on a pre-defined policy:

1. **Water Utilities' Share:** Funds distributed among the **12 water utilities**.
    
2. **National Budget:** Funds reserved for **common interventions** (e.g., interconnections, desalination).
    

#### **Budget Sharing Policies**

Competitors must specify a policy to determine the annual split. This policy remains in effect until a simulated management change overwrites it.

- **"By Population":** A fixed percentage (x%) goes to the national budget; the remaining funds are distributed to the 12 utilities proportionally to their **population size**.
    
- **"By Revenue":** A fixed percentage (x%) goes to the national budget; the remaining funds are distributed to the 12 utilities proportionally to their **previous year's revenue**.
    
- **"Custom":** A specific percentage (x%) is allocated to _each_ of the 12 water utilities; the remaining balance funds the national budget (the sum of all allocations must equal 100%).

> note we could also hae the 25-years budget split only between the water utilities and any common intervention would result in a shared bond. Probably easier to express like this.

---

### **2. Financial Mechanics**

The yearly **Cash Inflow** is the sum of **water revenue** and the **yearly budget** allocation.

The yearly **Cash Outflow** includes **interventions** (new pipes, leak reduction, etc.), **operational costs**, and **coupon payments** (on bonds).

- If the Cash Inflow is **less** than the Cash Outflow, a **bond** will be automatically issued to cover the deficit.
    
- Any **budget surplus** will be carried over as retained earnings into the following year.
    
---

### **3. Water Tariffs**

Water tariffs are determined **per household type** (to be determined based on CBS data) and consist of two independent components:

1. A **fixed component**.
    
2. A **volumetric component**.
    

Competitors have the flexibility to adjust these two components **independently** and can choose to apply different adjustments across different household classes and utilities or the same adjustment across all classes.

However, such increase can not happen more before 5 years have passed from the previous increase.

---

## 6. Competitor Output Format (`solution.json`)

Teams must specify their financial decisions in the solution file as follows (assuming 4 stages ($<u>PARAMETER</u>$)):

```json
{
  year_2025: {
    "finance": {
      "budget_sharing_policy": "by_population",
      ... more TBD
    },
    "leak_reduction_interventions": {
        ...
    },
    "connections_interventions": {
      "pipe A", ...
  },
  year_2030: {
    "finance": {
      "budget_sharing_policy": "custom",
      "budget_sharing_args": {
          "water_utility_1": 0.1,
          "water_utility_2": 0.06,
          ...
      },
      "water_price_tariffs": {
        "increase": [
            {
                "fixed_component": {
                    "class_A": 2, # %
                    "class_C": 4, 
                    "all": 3 # classes B and D
                },
          }
      ]
      # TO BE IMPROVED
    },
    "leak_reduction_interventions": {
        ...
    },
    "connections_interventions": {
      "pipe A", ...
  },
