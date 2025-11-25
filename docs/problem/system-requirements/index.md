---
layout: default
website_title: System Requirements
parent: /problem/
parent_title: Problem
prev_page_url: /problem/system-description/pipes.html
next_page_url: /problem/system-interventions/
website_page_authors:
  - D. Zanutto
---

## System Requirements

Each team’s plan will be evaluated using a set of **hydraulic, economic, environmental, and fairness metrics**.  
Each metric combines outputs from:
- **Hydraulic simulations** (EPANET): pressures, flows, energy 
- **Financial simulations**: CAPEX, OPEX, bond costs, and tariffs.  
- **Socioeconomic data**: income distribution, population, node classifications.


### Total Annualized Cost

- **Formula:** $TAC = \sum_j \frac{K_j}{L_j} + OPEX + (coupon × P_{issue})$
- Calculated over all dimensions (utility, time). Ranked based on cumulative amount across time and utilities.
- unit: €

### Total Annualized GHG Emissions

- **Formula:** $\text{GHG} = \sum_j \frac{K_j \times EF^{\text{emb}}_j}{L_j} + \sum_t \frac{E_t \times EF}{1000}$
- Calculated over all dimensions (utility, time). Ranked based on cumulative amount across time and utilities.
- unit: CO2eq

### Service Reliability

- **Formula:** ??
  **MODIFY: adjust based on undelivered demand over requested demand**
-  Calculated over all dimensions (municipality, household class, and time). Participants will be ranked based on **one specific combination** of these dimensions, which is kept uncertain and can change between stages.
- unit: dimensionless between 0 and 1 (1 is better)

### Affordability Fairness

- **Formula:** $AF = \frac{p_v × V_{lifeline} + F_{fixed}}{I_{p20}} × 100$
-  Calculated over all dimensions (municipality, household class, and time). Participants will be ranked based on **one specific combination** of these dimensions, which is kept uncertain and can change between stages.
- unit: percent?

---


Organizers will provide or link to the following open datasets:

| Category | Description | Example Source |
|-----------|--------------|----------------|
| **Energy & Carbon** | Electricity price & emission factor (kg CO2/kWh) | IEA Emissions Factors 2024 |
| **Materials & Construction** | Embedded CO2 of pipes, tanks, pumps | Ecoinvent, World Bank WSS |
| **Demographics & Income** | Population, income percentiles (p20, median, p80) per municipality | CBS StatLine (NL) |
| **Water Tariffs** | Fixed & volumetric price per m³ | ??? |
| **Leakage & NRW Benchmarks** | Reference values for NRW reduction cost and baseline loss | ??? |
| **Renewable Energy Factors** | Solar/wind/biogas capacity factors | IEA |

This section defines all variables and notation used in the KPI formulas.

| Symbol | Units | Description |
|:-------|:-------|:------------|
| **General / Indices** |||
| i | — | Index of node or municipality |
| t | — | Time index (e.g., hourly step) |
| j | — | Index of intervention |
| C | — | Set of critical nodes (e.g., hospitals, schools, farms) |
| N | - | Total number of nodes |
| T | hours | Total number of simulation hours in the evaluation period |
| **Hydraulic Variables** |||
| $P_{i,t}$ | m | Pressure at node *i* at time *t*, from EPANET simulation |
| $P_{\min}$ | m | Minimum acceptable service pressure (e.g., 25 m) |
| $P_{\text{crit}}$ | m | Minimum acceptable pressure for critical users (e.g., 35 m) |
| $SR_i$| — | Service reliability for node *i* = $\frac{\sum_t 1_{P_{i,t} \geq P_{\text{min}}}}{T} \times 100$ |
| $\overline{SR}$ | — | Weighted average service reliability across all nodes = $\frac{\sum_i w_i \times SR_i}{\sum_i w_i}$ |
| $CU_i$ | % | Critical-user reliability for node *i* = $\frac{\sum_t 1_{P_{i,t} \geq P_{\text{crit}}}}{T} \times 100$ |
| $Age_{i,t}$ | h | Water age at node *i* and time *t* |
| $Age_{\text{thr}}$ | h | Threshold for stale water (typically 48 h) |
| $Stale_i$ | % | Water stalness for node *i* = $\frac{\sum_t D_{i,t} × 1_{Age_{i,t} > Age_{\text{thr}}}}{\sum_t D_{i,t}}$ |
| **Demand and Flow Variables** |||
| $D_{i,t}$ | m³/h | Water demand at node *i* and time *t* |
| $V_{\text{prod}}$ | m³ / yr | Total produced water volume |
| $V_{\text{billed}}$ | m³ / yr | Total billed (consumed) volume |
| $V_{\text{leak}}$ | m³ / yr | Leaked or non-revenue water = $V_{\text{prod}} – V_{\text{billed}}$ |
| **Financial Variables** |||
| $K_j$ | € | Capital expenditure (CAPEX) for intervention *j* |
| $L_j$ | yr | Asset lifetime of intervention *j* |
| OPEX | €/yr | Operating expenditures (energy, maintenance, chemicals) |
| $r_f$ | — | Risk-free rate (e.g., 0.03 = 3 %) |
| cs | — | Base credit spread (e.g., 0.01 = 1 %) |
| a | — | Spread sensitivity to demand (e.g., 0.02 = 2 %) |
| d | — | Random investor demand factor $\in$ [0.8, 1.2] |
| $\text{coupon}$ | — | Coupon rate of issued bond = $r_f + cs + a(1 – d)$ |
| $P_{\text{issue}}$ | € | Principal amount of issued bond |
| **Environmental Variables** |||
| $E_t$ | kWh | Pumping energy at time *t* |
| $EF$ | kg CO2/kWh | Electricity emission factor |
| $EF^{emb}_j$ | t CO2 / € or unit | Embedded emission factor for intervention *j* |
| **Socio-Economic Variables** |||
| $p_v$ | €/m³ | Volumetric tariff |
| $F_{\text{fixed}}$ | €/month | Fixed charge per household |
| $V_{\text{lifeline}}$ | m³/month | Lifeline volume (e.g., 1.5 m³/person/month) |
| $I_{p20}$ | €/month | 20th-percentile monthly income across nodes |
| $w_i$ | — | Weight of node *i* in population or connection share |

