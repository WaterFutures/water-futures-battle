---
layout: default
website_title: System Requirements
parent: /problem/
parent_title: Problem
prev_page_url: /problem/system-interventions/
next_page_url: /team.html
website_page_authors:
  - D. Zanutto
---

## System Requirements

This chapter describes the metrics used to evaluate each solution (masterplan) and the overall system performance in the BWF competition.
These metrics define the many-objective space that participants must navigate, covering the main aspects of economic performance, environmental impact, reliability, and fairness.
Importantly, these are evaluation metrics rather than explicit objectives: the competition ranking formula will not be disclosed to participants.
The ranking may use weighted aggregation (with weights potentially changing over time to reflect shifting social priorities) or custom multi-criteria evaluation methods (e.g., selecting only solutions above a reliability threshold before ranking by other criteria). 
However, participants may choose to treat these metrics as objectives in their own optimization processes when developing their masterplans.

### Total Annualized Cost

- **Formula:** $TAC = \sum_j \frac{K_j}{L_j} + OPEX + (coupon \times P_{issue})$
- Calculated over all dimensions (utility, time). Ranked based on cumulative amount across time and utilities.
- unit: €

### Total GHG Emissions

- **Formula:** $\text{GHG} = \sum_j K_j \times EF^{\text{emb}}_j + \sum_t E_t \times EF$
- Calculated over all dimensions (utility, time). Ranked based on cumulative amount across time and utilities.
- unit: tCO2eq

### Service Reliability

- **Formula:** $R^{\text{service}} = 1 - \dfrac{\sum_{i,t} U_{i,t}}{\sum_{i,t} D_{i,t}}$
-  Calculated over all dimensions (municipality, household class, and time). Participants will be ranked based on **one specific combination** of these dimensions, which is kept uncertain and can change between stages.
- unit: dimensionless between 0 and 1 (higher is better)

### Affordability Fairness

- **Formula:** $AF = \frac{p_v × V_{lifeline} + F_{fixed}}{I_{p20}} \times 100$
-  Calculated over all dimensions (municipality, household class, and time). Participants will be ranked based on **one specific combination** of these dimensions, which is kept uncertain and can change between stages.
- unit: % (lower is better)

---

This section defines all variables and notation used in the KPI formulas.

| Symbol | Units | Description |
|:-------|:-------|:------------|
| **General / Indices** |||
| i | — | Index of node or municipality |
| t | — | Time index (e.g., hourly step) |
| j | — | Index of intervention |
| N | - | Total number of nodes |
| T | hours | Total number of simulation hours in the evaluation period |
| **Demand Variables** |||
| $D_{i,t}$ | m³/h | Water demand at node *i* and time *t* |
| $Q{i,t}$ | m³/h | Delivered volume at node *i* and time *t* |
| $U_{i,t} = \max(D_{i,t} - Q_{i,t}, 0)$ | m³/h | Undelivered demand at node $i$, time $t$ | 
| **Financial Variables** |||
| $K_j$ | € | Capital expenditure (CAPEX) for intervention *j* |
| $L_j$ | yr | Asset lifetime of intervention *j* |
| OPEX | €/yr | Operating expenditures (energy, maintenance, etc) |
| $r_f$ | — | Risk-free rate (e.g., 0.03 = 3 %) |
| cs | — | Base credit spread (e.g., 0.01 = 1 %) |
| a | — | Spread sensitivity to demand (e.g., 0.02 = 2 %) |
| d | — | Random investor demand factor $\in$ [0.8, 1.2] |
| $\text{coupon}$ | — | Coupon rate of issued bond = $r_f + cs + a(1 - d)$ |
| $P_{\text{issue}}$ | € | Principal amount of issued bond |
| **Environmental Variables** |||
| $E_t$ | kWh | Pumping energy at time *t* |
| $EF$ | t CO2/kWh | Electricity emission factor |
| $EF^{emb}_j$ | t CO2 / € or unit | Embedded emission factor for intervention *j* |
| **Socio-Economic Variables** |||
| $p_v$ | €/m³ | Volumetric tariff |
| $F_{\text{fixed}}$ | €/month | Fixed charge per household |
| $V_{\text{lifeline}}$ | m³/month | Lifeline volume (e.g., 1.5 m³/person/month) |
| $I_{p20}$ | €/month | 20th-percentile monthly income across nodes |

