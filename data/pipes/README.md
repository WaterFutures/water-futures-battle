# Pipes

## Overview

The pipes module describes pipe assets and pipe options, including common physical and economic properties such as diameter and embodied emissions.
The [connections module](../connections/) describes where pipes can be installed.

Each pipe has exactly one pipe option. Each connection can have zero, one, or more pipes.

## Raw Data

### Assumptions

Diameters and common materials were selected using general domain knowledge and online references.

## Preprocessing Scripts for Initial Dataset Generation

### Excel file

The Excel file [`CO2_emissions calculations.xlsx`](./preprocessing-scripts/CO2_emissions%20calculations.xlsx) computes 
each pipe option's embodied emissions by multiplying the amount of material needed
to build that pipe option by the material's embodied emissions factor.

### Static Properties

The notebook [`pipe_options-static_properties-generator.ipynb`](./preprocessing-scripts/pipe_options-static_properties-generator.ipynb) 
defines the pipe options file combining the predefined options.

### Dynamic Properties

The notebook [`pipe_options-dynamic_properties-generator.ipynb`](./preprocessing-scripts/pipe_options-dynamic_properties-generator.ipynb)
back-propagates current costs and embedded emissions of pipe options to 2000.

## Initial Dataset Structure

**Table 1**: Overview of the pipe options properties.

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pipe_options-static_properties.xlsx` | `options` | ID (`option: PIxx`) | - | Static |  |  | Pipe option |
| | | Diameter (`diameter`) | mm | Static |  |  | Pipe option |
| | | Material (`material`) | | Static |  |  | Pipe option |
| | | Darcy friction coefficient of a new pipe (`darcy_friction_factor-new_pipe`) | - | Static |  |  | Pipe option |
| | | Darcy friction coefficient decay (`darcy_friction_factor-decay`) | $year^-1$ | Static | Uncertain | Uniform ([`min`,`max`]) | Pipe option |
| | | Design life (`lifetime`) | years | Static | Uncertain | Uniform ([`min`,`max`]) | Pipe option |
| `pipe_options-dynamic_properties.xlsx` | `new_pipe-unit_cost` | Unit cost of a new pipe | €/m | Dynamic Endogenous | Deterministic | | Time $\times$ Pipe option |
| | `new_pipe-emission_factor` | Embedded emission factor of a new pipe | kgCO2eq/m | Dynamic Endogenous | Deterministic | | Time $\times$ Pipe option |


**Table 2**: Overview of the pipes properties.

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `connections-static_properties.xlsx` | `provincial`, `sources`, `cross-provincial` | Pipe option ID of each connection's pipe (`pipes-option_ids`) | - | Static |  |  | Pipe |
| | | Installation date of each connection's pipe (`pipes-installation_dates`) | - | Static |  |  | Pipe |
| | | Decommission date of each connection's pipe (`pipes-decommission_dates`) | - | Static |  |  | Pipe |
| `pipes-dynamic_properties.xlsx` | `friction_factor` | Darcy friction coefficient | - | Dynamic Endogenous | Deterministic | | Time $\times$ Pipe |

*Note: pipes static properties are concatenated by the `';'` separator as static
 properties of the connection owning them.*

## The Narrative

### Stage 1: The Decade of Efficiency & The Steel Pivot (2025–2049)

Similarly to the electricity grid, the emission factors of the pipe options in the initial decade see limited changes, as both PVC and steel industries focus on process optimization.
Around 2035, a structural "decarbonization shock" hits the steel sector.
The industry moves aggressively away from coal-fired blast furnaces toward Electric Arc Furnaces (EAF) and green hydrogen reduction.
By the end of this era, steel has successfully decoupled production from high-carbon feedstocks, achieving a massive 65% reduction in embodied emissions.
PVC, hampered by its reliance on fossil-fuel-derived ethylene, manages only a modest 25% reduction through grid greening and incremental recycling.

### Stage 2: The Molecular Revolution (2050–2074)

In the early 2050s, the chemical industry achieves a commercial breakthrough in Chemical Recycling (Pyrolysis) and bio-attributed feedstocks.
This allows PVC to bypass the carbon-heavy extraction of virgin natural gas.
In a sudden leap between 2050 and 2055, PVC’s emission factor drops to 40% of its original value.
During this period, steel continues its refinement, reaching an 80% total reduction by 2075.
The focus shifts from "how we make the material" to "how we keep the material in a closed loop," with secondary (recycled) material becoming the primary source for all new water mains.

### Stage 3: The Net-Zero Horizon (2075–2100)

As the global energy grid reaches 100% renewables, the "Process" and "Energy" variables of the emission equation effectively drop to zero.
The remaining challenges are addressed through advanced bio-chemistry and carbon-negative solutions.
By the turn of the century, the embodied carbon of a water pipe is no longer a debt to the environment but a neutral variable. 

## Preprocessing Scripts for Stage Extension

All cost components are endogenous and grow with inflation over time. 
Similarly, pipes dynamic properties (friction factor) are also endogenous and calculated internally by the evaluator.
The only exogenous pipe-option variable is its emission factor.

### Pipe Option's Emission Factor

The following projections are based on a constant-design model.
While manufacturing processes evolve, we assume that the physical dimensions and structural performance requirements (e.g., wall thickness, pressure rating, and density) of the PVC and welded steel pipes remain unchanged over the 75-year horizon.

Consequently, any percentage reduction in the material's embodied emission factor (kgCO2e/kg) results in an identical, linear reduction in the total emissions per meter of pipe.

Given the complexity and uncertainty of forecasting global industrial variables, this model uses manually defined reduction pathways.

## Selected Parameters to Reflect the Narrative

### Pipe Option's Emission Factor

These are the reduction factors with respect to the 2024 values to represent the decarbonisation pathway of pipes.

| Year | PVC Factor (Mpvc) | Steel Factor (Msteel) | Pathway Milestone |
|------|-------------------|----------------------|-------------------|
| **2025** | 1.00              | 1.00                 | Baseline          |
| 2030 | 0.96              | 0.95                 | Efficiency Gains  |
| 2035 | 0.92              | 0.90                 | Decarbonization Pivot |
| 2040 | 0.88              | 0.72                 | Steel EAF Scaling |
| 2045 | 0.85              | 0.53                 | Advanced Steel Circularity |
| **2050** | 0.80              | 0.35                 | Steel -65% Realized |
| 2055 | 0.58              | 0.31                 | PVC Chemical Breakthrough |
| 2060 | 0.36              | 0.27                 | Deep Grid Decarbonization |
| 2065 | 0.32              | 0.24                 | Bio-feedstock Dominance |
| 2070 | 0.28              | 0.22                 | Residual Emission Cleanup |
| **2075** | 0.23              | 0.20                 | Steel -80% Realized |
| 2080 | 0.17              | 0.16                 | Secondary Market Maturation |
| 2085 | 0.11              | 0.07                 | Zero-Carbon Logistics |
| 2090 | 0.05              | 0.00                 | Net Zero Target Steel |
| 2095 | 0.01              | 0.00                 | Near-Zero Finality |
| 2100 | 0.00              | 0.00                 | Net Zero Target    |