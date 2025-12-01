---
layout: default
website_title: Economy and financing
parent: /problem/external-drivers/
parent_title: External drivers
prev_page_url: /problem/external-drivers/energy-system.html
next_page_url: /problem/system-interventions/
website_page_authors:
  - P. Samartzis
  - D. Zanutto
---

###  Economy

#### Bond Issuance
The bond issuance governs how additional capital is raised when a utility exhausts its allocated budget for a period. When the available budget is fully utilized, a bond is automatically issued to cover the costs of planned interventions. The price and yield of this bond are determined by the modeled bond demand and market conditions specific to the issuance year. These bonds introduce future repayment obligations, and all associated interest payments accumulate as part of the total financial cost of the interventions.
While utilities cannot directly control bond yields, they can anticipate debt accumulation through scenario analysis and adopt strategies that maintain financial sustainability. For instance, utilities may design pacing of interventions to minimize borrowing, or evaluate alternative interventions that reduce the likelihood of large bond issuances during periods with unfavorable yield conditions.

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| Remaining budget in year *t*             | Dynamic Endogenous | Utility  ID                           |
| Bond issuance trigger (budget exhausted) | Dynamic Endogenous | Utility  ID                           |
| Bond amount issued                       | Dynamic Endogenous | Utility  ID                           |
| Bond price (issue price)                 | Dynamic Exogenous  | Simulation model                      |
| Bond yield                               | Dynamic Exogenous  | Simulation model                      |
| Bond demand curve                        | Dynamic Exogenous  | Simulation model                      |
| Interest payments                        | Dynamic Endogenous | Utility  ID                           |
| Total financial cost (capex + interest)  | Dynamic Endogenous | Utility  ID                           |

: Bonds model's properties review. {#tbl:eb-properties}


#### Budget Allocation 
The budget allocation module governs how national funding is distributed across provincial water utilities, each of which operates and maintains its own water distribution system. This allocation affects the resources available to implement interventions and support operations. Budget distribution can follow several principled rules: proportional allocation to population size; inverse-proportional schemes favoring smaller regions; income-based allocations reflecting socioeconomic considerations; inverse-proportional schemes favoring less wealthy regions; or fully customized schemes. 

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| National total budget                                 | Static             | National                        |
| Population size                                       | Dynamic Endogenous | Municipality ID                 |
| Income index (socio-economic)                         | Dynamic Endogenous | Municipality ID                 |
| Per-capita allocation weight                          | Option             | Rule                            |
| Inverse-population allocation weight                  | Option             | Rule                            |
| Income-based allocation weight                        | Option             | Rule                            |
| Equity priority score (favoring less wealthy regions) | Option             | Rule                            |
| Customized allocation vector                          | Option             | Participant-defined             |

: Budget allocation model's properties review. {#tbl:ea-properties}

#### Inflation Dynamics
Inflation represents the annual rate at which general price levels evolve over the planning horizon. In the BWF setting, inflation affects all monetary flows: capital expenditures, operating expenses, various costs, and prices for energy consumption and water tariffs. Because inflation compounds over time, it can significantly alter the real purchasing power of fixed budgets and shape the financial feasibility of long-term interventions.
Interventions on inflation are limited, as inflation is an exogenous macroeconomic indicator outside the direct control of water utilities. However, utilities may adopt strategies that account for inflation, such as front-loading major investments to avoid future cost escalation, or stress-testing the interventions under alternative inflation trajectories. The primary goal is to design actions and financial flows that remain robust despite uncertain future price conditions.

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| Inflation rate in year *t*           | Dynamic Exogenous  | National (Simulation model)     |

: Inflation's properties review. {#tbl:ei-properties}

#### Water Tariffs 
The water tariffs module models how utilities generate revenue through a pricing scheme commonly used in real-world systems: a fixed component (e.g., service charge) combined with a volumetric component (per-m³ charge). Both components evolve annually according to the prevailing inflation rate, ensuring that real revenue tracks changes in general price levels. 
Both the fixed and volumetric tariff components are exogenously given and evolve solely according to the uncertain inflation dynamics defined in the scenario generator. Participants must therefore design plans that remain financially robust under tariff paths they cannot control. This constraint emphasizes the importance of planning under deep uncertainty: utilities must cope with potential revenue volatility driven by inflation.

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| Fixed tariff component (service charge) | Dynamic Exogenous  | Utility  ID                             |
| Volumetric tariff component       | Dynamic Exogenous  | Utility  ID| $€/m^3$
| Annual tariff escalation rule           | Dynamic Exogenous  | National (inflation-indexed)            |

: Water price model's properties review. {#tbl:et-properties}