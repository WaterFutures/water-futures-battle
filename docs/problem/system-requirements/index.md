---
layout: level_two
title: System Requirements
parent: /problem/
parent_title: Problem
---

# 💧 Evaluation Metrics & KPIs

## 1. Overview

Each team’s plan will be evaluated using a set of **hydraulic, economic, environmental, and fairness metrics**.  
Each metric combines outputs from:
- **Hydraulic simulations** (EPANET): pressures, flows, energy 
- **Financial simulations**: CAPEX, OPEX, bond costs, and tariffs.  
- **Socioeconomic data**: income distribution, population, node classifications.


### 1. Total Annualized Cost (€)

- **Formula:** $TAC = \sum_j \frac{K_j}{L_j} + OPEX + (coupon × P_{issue})$
- Calculated over all dimensions (utility, time). Ranked based on cumulative amount across time and utilities.

### 2. Water-Age Above Threshold (hours)
**REMOVED AFTER DISCUSSION WITH THE TEAM ON 2025-10-24**
Reason: doesn't make sense at transport level but only distribution.

### 3. GHG Emissions (tCO₂e/year)

- **Formula:** $\text{GHG} = \sum_j \frac{K_j \times EF^{\text{emb}}_j}{L_j} + \sum_t \frac{E_t \times EF}{1000}$
- Calculated over all dimensions (utility, time). Ranked based on cumulative amount across time and utilities.

### 4. Service Fairness / Reliability (0–1)

- **Formula:** ??
  **MODIFY: adjust based on undelivered demand over requested demand**
-  Calculated over all dimensions (municipality, household class, and time). Participants will be ranked based on **one specific combination** of these dimensions, which is kept uncertain and can change between stages.

### 5. Affordability Fairness (%)

- **Formula:** $AF = \frac{p_v × V_{lifeline} + F_{fixed}}{I_{p20}} × 100$
-  Calculated over all dimensions (municipality, household class, and time). Participants will be ranked based on **one specific combination** of these dimensions, which is kept uncertain and can change between stages.
  
### 6. Fairness for Critical Users (%)
**REMOVED AFTER DISCUSSION ON 2025-10-24**
Reason: we don't distinguish between critical and non critical users

### 7. Water Losses (%)

- **Formula:** ??
  **MODIFY: adjust based on the new leak model**
  Goal: reduce the class in which the municipalities stay for most of the time.
  We can use the municipality NRW class directly and track it over time).
  Final calculation could be the amount (or share) of municipalities in a given class of worse (e.g., C), summed over time. See what the EU goal is.


---

## 2. External Input Datasets

Organizers will provide or link to the following open datasets:

| Category | Description | Example Source |
|-----------|--------------|----------------|
| **Energy & Carbon** | Electricity price & emission factor (kg CO₂/kWh) | IEA Emissions Factors 2024 |
| **Materials & Construction** | Embedded CO₂ of pipes, tanks, pumps | Ecoinvent, World Bank WSS |
| **Demographics & Income** | Population, income percentiles (p20, median, p80) per municipality | CBS StatLine (NL) |
| **Water Tariffs** | Fixed & volumetric price per m³ | ??? |
| **Leakage & NRW Benchmarks** | Reference values for NRW reduction cost and baseline loss | ??? |
| **Renewable Energy Factors** | Solar/wind/biogas capacity factors | IEA |

---

## 3. Required JSON Structures

### 3.1 Competitor Solution File (`solution.json`)

This sample file contains all decisions for one team and one stage.

```json
{
  "team_id": "TeamAlpha",
  "stage": 1,
  "finance": {
    "budget_share": 0.15,
    "bond_issuance": {
      "issue_amount_eur": 80000000
    }
  },
  "allocations": {
    "node_allocations": {
      "Node_001": 0.25,
      "Node_002": 0.35,
      "Node_003": 0.40
    }
  },
  "interventions": [
    {
      "year": 2028,
      "node": "Node_001",
      "type": "leak_reduction"
    },
    {
      "year": 2029,
      "node": "Node_002",
      "type": "desalination"
    }
  ]
}
```

### 3.2 Data for Evaluation

These files include all time-series and static data used to compute KPIs. The first file incudes data with parameters and information for each possible intervention (`intervention_typs.json`):

```json
{
    "leak_reduction": {
      "description": "Program to reduce non-revenue water via active leakage control (pressure management, repairs).",
      "asset_life_years": 20,
      "capex_per_m3_day_eur": 1500.0,
      "expected_leak_reduction_m3_per_day_per_eur": 0.003,
      "embedded_ef_tco2e_per_m3": 0.05,
      "energy_kwh_per_m3": 0.45
    },
    "desalination": {
      "description": "Desalination plant.",
      "asset_life_years": 25,
      "capex_per_m3_day_eur": 1500.0,
      "capacity_m3_day_per_eur": 0.0007,
      "energy_kwh_per_m3": 3.5,
      "embedded_ef_tco2e_per_m3": 0.2
    },
    "pipe_replacement": {
      "description": "Replace distribution mains; reduces bursts/leak background and improves hydraulics.",
      "asset_life_years": 80,
      "capex_per_km_eur": 600000.0,
      "embedded_ef_tco2e_per_km": 50.0,
      "expected_leak_reduction_m3_per_day_per_km": 20.0
    },
    "new_pump": {
      "description": "New pump to increase pressure/head.",
      "asset_life_years": 20,
      "capex_per_kw_eur": 1200.0,
      "embedded_ef_tco2e_per_kw": 0.2
    },
    "storage_tank": {
      "description": "New storage to buffer peaks and improve service.",
      "asset_life_years": 50,
      "capex_per_m3_eur": 500.0,
      "embedded_ef_tco2e_per_m3": 0.1
    },
    "renewable_pv": {
      "description": "On-site solar PV for self-consumption.",
      "asset_life_years": 25,
      "capex_per_kw_eur": 900.0,
      "capacity_factor": 0.15,
      "energy_kwh_per_km_saved": 0.15,
      "embedded_ef_tco2e_per_kw": 0.6
    },
    "smart_meter": {
      "description": "Smart meters & DMA analytics to detect leaks.",
      "asset_life_years": 15,
      "capex_per_connection_eur": 120.0,
      "embedded_ef_tco2e_per_connection": 0.01,
      "expected_leak_reduction_m3_per_day_per_connection": 0.007
}
```

The second file contains information about various parameters and outputs from EPANET (`parameters.json`):

```json
{
  "financial_parameters": {
    "discount_rate": 0.04,
    "risk_free_rate": 0.03,
    "base_credit_spread": 0.01,
    "spread_slope": 0.02,
    "demand_factor": 1.05
  },
  "policy_constants": {
    "pressure_min": 25.0,
    "pressure_critical": 35.0,
    "water_age_threshold": 48,
    "v_lifeline_m3_per_capita_per_month": 1.5,
    "average_household_size_persons": 3
  },
  "tariffs": {
    "volumetric_eur_per_m3": 1.60,
    "fixed_fee_eur_per_month": 5.0
  },
  "node_data": {
    "population": {
      "Node_001": 100000,
      "Node_002": 150000,
      "Node_003": 80000
    },
    "income_p20_eur_per_month": {
      "Node_001": 1600,
      "Node_002": 1500,
      "Node_003": 1400
    },
    "critical_nodes": ["Node_002"]
  },
  "hydraulic_outputs": {
    "hourly_pressures": {
      "Node_001": [...],
      "Node_002": [...],
      "Node_003": [...]
    },
    "hourly_water_age": {
      "Node_001": [...],
      "Node_002": [...],
      "Node_003": [...]
    },
    "hourly_demand_m3_per": {
      "Node_001": [...],
      "Node_002": [...],
      "Node_003": [...]
    },
    "hourly_source_inflows_m3_per_h": {
      "Source_A": [...],
      "Source_B": [...]
    },
    "tank_volumes_m3": {
      "Tank_1": [ ... ]
    },
    "pump_energy_kwh_per_hour": [...]
  },
  "energy_blocks_kwh_annual": {
    "desalination": 1500000,
    "other_facilities": 250000
  },
  "emission_factors": {
    "grid_kgco2_per_kwh": 0.25
  }
}
```

---
## 4. Variable Definitions

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
| $SR_i$| — | Service reliability for node *i* = $\frac{\sum_t 1_{P_{i,t} ≥ P_{\text{min}}}}{T} \times 100$ |
| $\overline{SR}$ | — | Weighted average service reliability across all nodes = $\frac{\sum_i w_i \times SR_i}{\sum_i w_i}$ |
| $CU_i$ | % | Critical-user reliability for node *i* = $\frac{\sum_t 1_{P_{i,t} ≥ P_{\text{crit}}}}{T} \times 100$ |
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
| d | — | Random investor demand factor ∈ [0.8, 1.2] |
| $\text{coupon}$ | — | Coupon rate of issued bond = $r_f + cs + a(1 – d)$ |
| $P_{\text{issue}}$ | € | Principal amount of issued bond |
| **Environmental Variables** |||
| $E_t$ | kWh | Pumping energy at time *t* |
| $EF$ | kg CO₂/kWh | Electricity emission factor |
| $EF^{emb}_j$ | t CO₂ / € or unit | Embedded emission factor for intervention *j* |
| **Socio-Economic Variables** |||
| $p_v$ | €/m³ | Volumetric tariff |
| $F_{\text{fixed}}$ | €/month | Fixed charge per household |
| $V_{\text{lifeline}}$ | m³/month | Lifeline volume (e.g., 1.5 m³/person/month) |
| $I_{p20}$ | €/month | 20th-percentile monthly income across nodes |
| $w_i$ | — | Weight of node *i* in population or connection share |

---


## 5. KPI Formulas

### 1. Total Annualized Cost (€)

- **Formula:** $TAC = \sum_j \frac{K_j}{L_j} + OPEX + (coupon × P_{issue})$

### 2. Water-Age Above Threshold (hours)

- **Formula:** $WAAT = \frac{\sum_i w_i × Stale_i}{\sum_i w_i}$

### 3. GHG Emissions (tCO₂e/year)

- **Formula:** $\text{GHG} = \sum_j \frac{K_j \times EF^{\text{emb}}_j}{L_j} + \sum_t \frac{E_t \times EF}{1000}$

### 4. Service Fairness (0–1)

- **Formula:** $SF = 1 - \frac{\sum_i w_i \times |SR_i - \overline{SR}|}{\overline{SR}}$

### 5. Affordability Fairness (%)

- **Formula:** $AF = \frac{p_v × V_{lifeline} + F_{fixed}}{I_{p20}} × 100$

### 6. Fairness for Critical Users (%)

- **Formula:** $Fairness_{crit} = \frac{\sum_i w_i \times CU_i}{\sum_i w_i}$

### 7. Water Losses (%)

- **Formula:** $Losses = \frac{V_{leak}}{V_{prod}} × 100$


---

## 6. Example Output (`results.json`)

```json
{
  "team_id": "TeamAlpha",
  "stage": 1,
  "kpis": {
    "total_annualized_cost_eur": 105000000,
    "water_age_above_threshold_h": 3.4,
    "ghg_emissions_tco2_per_year": 1250,
    "service_fairness_index": 0.08,
    "affordability_fairness_pct": 3.6,
    "critical_user_fairness_pct": 98.5,
    "water_losses_pct": 7.2
  }
}
```
