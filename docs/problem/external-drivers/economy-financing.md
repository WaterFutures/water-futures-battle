---
layout: level_two
title: Economy and financing
parent: /problem/external-drivers/
parent_title: External drivers
---
# 💧 Financing Options and Budget Rules

## 1. Overview

Every team must fund its interventions (e.g., pipe change, leak reduction, production locations, renewable energy installations) using a combination of:

1. **Base budget allocation** between the utilities
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

## 5. Budget Allocation Among Nodes

Each team must decide **how to distribute its total available budget** among its municipalities or network nodes.

- Let $s_i$ be the share of budget allocated to node *i*.
- The shares must satisfy: $\sum_i s_i = 1$

- Allocations can reflect:
  - Strategic priorities (e.g., large cities, critical users, low-income areas)
  - Infrastructure condition (pipe age, leak rate, etc.)
  - Affordability objectives

The allocation influences **which nodes receive upgrades investments** in the simulation.

---

## 6. Competitor Output Format (`solution.json`)

Teams must specify their financial decisions in the solution file as follows (assuming 4 stages ($<u>PARAMETER</u>$)):

```json
{
  "finance": [{
    "budget_share": 0.15,
    "bond_issuance": {
      "issue_amount_eur": 80000000
    },
    "budget_allocation": {
      "Node_001": 0.25,
      "Node_002": 0.35,
      "Node_003": 0.40
    }
  },
{
    "budget_share": 0.45,
    "bond_issuance": {
      "issue_amount_eur": 0
    },
    "budget_allocation": {
      "Node_001": 0.55,
      "Node_002": 0.15,
      "Node_003": 0.30
    }
  }
{
    "budget_share": 0.20,
    "bond_issuance": {
      "issue_amount_eur": 60000000
    },
    "budget_allocation": {
      "Node_001": 0.25,
      "Node_002": 0.35,
      "Node_003": 0.40
    }
  }
{
    "budget_share": 0.20,
    "bond_issuance": {
      "issue_amount_eur": 10000000
    },
    "budget_allocation": {
      "Node_001": 0.20,
      "Node_002": 0.60,
      "Node_003": 0.20
    }
  }]
}
