# Energy

## Overview

The energy system represents electricity costs and grid emissions, as well as the cost and generation of utility-connected solar farms. Electricity prices and their hourly pattern affect pumping costs; the grid emission factor represents emissions associated with electricity use; and solar panel unit costs inform solar-farm construction. Solar farms can be connected to a water source or pumping station.

## Raw Data

### Eurostat

Eurostat is the statistical office of the European Union. It publishes harmonised statistics covering EU member states ([Eurostat](https://ec.europa.eu/eurostat)). The energy module uses Eurostat's [household electricity price dataset](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205__custom_18701019/default/table) and [gross electricity production dataset](https://ec.europa.eu/eurostat/databrowser/view/nrg_bal_c__custom_18717923/default/table).

**Table 1.** Datasets downloaded from Eurostat.

| Variable | Measure | Unit | Notes |
| --- | --- | --- | --- |
| Household electricity price | 6-month average price | €/kWh | National for the period 2007–2025. |
| Gross electricity production | Annual production amount | GWh | National for the period 1990–2023. |

### European Environment Agency

The European Environment Agency (EEA) is an EU agency that provides information on Europe's environment ([EEA](https://www.eea.europa.eu)). The energy module uses the EEA's [greenhouse-gas emissions data viewer](https://www.eea.europa.eu/en/analysis/maps-and-charts/greenhouse-gases-viewer-data-viewers).

**Table 2.** Datasets downloaded from the EEA dashboard.

| Variable | Measure | Unit | Notes |
| --- | --- | --- | --- |
| Greenhouse-gas emissions from energy supply | Annual emissions | kt CO2 | National for the period 1990–2023. |

### Our World in Data

Our World in Data (OWID) is a research publication that presents data and analysis on global changes ([OWID](https://ourworldindata.org)). The energy module uses OWID's [solar photovoltaic module price dataset](https://ourworldindata.org/grapher/solar-pv-prices).

**Table 3.** Datasets downloaded from the OWID dashboard.

| Variable | Measure | Unit | Notes |
| --- | --- | --- | --- |
| Solar photovoltaic module price | Yearly average price | USD/W | Worldwide for the period 1975–2024. |

### Battle of the Water Network II

The Battle of the Water Networks II (BWN-II) was a previous edition in the Battle of the Water Networks series and it concerned water distribution network optimization [Marchi et al. (2014)](https://scholar.google.com/scholar?q=%22Battle+of+the+Water+Networks+II%22+Marchi+2014).
The energy module uses the previous battle electricity-price weekly pattern.

**Table 4.** Datasets reconstructed from BWN-II.

| Variable | Measure | Unit | Notes |
| --- | --- | --- | --- |
| Electricity-price | Week's hourly prices | € | Fixed for the competition.|

### ENTSO-E Transparency Platform

The ENTSO-E Transparency Platform provides electricity-system and wholesale-market data across Europe ([ENTSO-E](https://transparency.entsoe.eu)). The energy module is inspired by the data shown in the ENTSO-E [day-ahead prices data view](https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show).

## Preprocessing Scripts for Initial Dataset Generation

### Static Properties

The notebook [`solar_farms-static_properties-generator.ipynb`](./preprocessing-scripts/solar_farms-static_properties-generator.ipynb) creates the solar-farm entity table.
There are no solar farms defined in 2025, so the generated table is intentionally empty while retaining its expected columns.

### Dynamic Properties

The notebook [`energy-dynamic_properties-generator.ipynb`](./preprocessing-scripts/energy-dynamic_properties-generator.ipynb) assembles the energy system's dynamic exogenous variables.

#### Electricity Prices

Electricity prices use Eurostat observations for the Netherlands. The series begins in 2007; the preprocessing script estimates earlier values by extending it backward to 1990 using a trend with added random noise.

#### Electricity Price Patterns

Patterns are recorded only when they change.
The weekly price pattern is based on the Battle of the Water Networks II profile through 2014 and on the ENTSO-E profile from 2015 onward.
From 2015, separate summer and winter patterns are recorded in April and October, respectively.

#### Electrical Grid Emission Factors

The grid emission factor is calculated by dividing total emissions from the energy-supply sector by gross electricity production.

#### Solar Panel Unit Costs

Solar panel unit costs use Our World in Data observations, converted to €/kW.

## Initial Dataset Structure

**Table 5.** Overview of the energy system properties.

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `solar_farms-static_properties.xlsx` | `entities` | Solar farm ID (`solar_farm_id: 'SFxxxx'`) | - | Static | - | - | Solar farm |
| | | Capacity (`capacity`) | kW | Static | - | - | Solar farm |
| | | Installation date (`installation_date`) | Date | Static | - | - | Solar farm |
| | | Decommission date (`decommission_date`) | Date | Static | - | - | Solar farm |
| | | Connected entity ID (`connected_entity_id`) | - | Static | - | - | Solar farm |
| `energy_system-dynamic_properties.xlsx` | `electricity_price-unit_cost` | Electricity price per unit of energy | €/kWh | Dynamic Exogenous | Deterministic | | Time $\times$ State |
| | `electricity_price-pattern` | Electricity-price multiplier | - | Dynamic Exogenous | Deterministic | - | Time $\times$ State $\times$ Hour-of-the-week |
| | `grid_emission_factor` | Grid emissions per unit of electricity | kg CO2/kWh | Dynamic Exogenous | Deterministic | - | Time $\times$ State |
| | `solar_panel-unit_cost` | Solar panel unit cost | €/kW | Dynamic Exogenous | Deterministic | - | Time $\times$ State |

## The Narrative

### Stage 1: The Managed Transition (2025–2049)

The first phase continues broad historical economic trends. Electricity prices evolve broadly with inflation as renewables expand while fossil fuels remain part of the mix. Grid emissions decline along current decarbonisation-policy trajectories, with the decline slowing toward 2050. A strategic partnership agreed during the 2025 Masterplan negotiations gives water utilities a fixed electricity-price pattern for the year. In 2035, the rates are renegotiated and flatten slightly as renewable-energy storage expands. Solar panel costs continue to fall through incremental technological improvements and manufacturing scale.

### Stage 2: The Period of Structural Stress (2050–2074)

The second phase represents a more challenging macroeconomic environment. Electricity prices increase broadly in line with inflation, reflecting investment needed to expand energy infrastructure. Grid decarbonisation plateaus, then efforts accelerate in 2070 with a plan to complete decarbonisation. Electricity-price patterns undergo several renegotiations; from 2070, expanded storage and flexible energy sources keep prices constant throughout the year. Solar technology has matured, so solar costs track realised inflation rather than learning-driven declines.

### Stage 3: The Technological Stabilization Era (2075–2099)

The final phase is characterized by greater macroeconomic stability and stronger productivity gains. Electricity prices continue to evolve broadly with inflation, but with significantly lower volatility. The grid becomes carbon neutral, and solar costs continue to grow with inflation. With large-scale energy storage fully deployed, electricity prices remain steady across the day and year.

## Preprocessing Scripts for Stage Extension

Since participants cannot influence the energy market, the energy variables are treated as exogenous signals and modelled independently using simplified dynamic processes.

#### Electricity Price

Electricity prices are modelled as a multiplicative process driven by structural trend, partial pass-through of realised inflation, stochastic variation, and discrete shocks:

$$E_t = E_{t-1} \cdot \left(w_\pi \cdot \pi_t + \mathcal{N}(1 + \mu_e, \sigma_e) + \begin{cases} \text{shock} & \text{with probability } p \\ 0 & \text{otherwise} \end{cases}\right)$$

Here, $\mu_e$ is the stage structural trend, $w_\pi$ is the inflation pass-through weight applied to realised inflation $\pi_t$, and $\sigma_e$ scales random volatility. A discrete shock occurs with probability $p$.

#### Electricity-Price Patterns

Weekly electricity-price patterns are manually defined to reflect the narrative for each stage.

#### Solar Panel Costs

Before 2050, solar costs follow a secular decline consistent with historical learning-rate dynamics. Each year's value is the previous year's value scaled by a normally distributed factor:

$$S_t = S_{t-1} \cdot \mathcal{N}(1 - \mu_s, \sigma_s)$$

Here, $\mu_s$ is the stage decline trend and $\sigma_s$ is volatility. From 2050 onward, the structural decline is treated as exhausted and solar costs track realised inflation.

#### Grid Emission Factor

The grid emission factor follows a multiplicative random walk, with each year's value scaled by a normally distributed reduction factor:

$$EF_t = EF_{t-1} \cdot \mathcal{N}(\mu_r, \sigma_r)$$

Here, $\mu_r < 1$ represents a persistent declining trend and $\sigma_r$ controls year-to-year variability. From 2073, the process switches to a linear decline calibrated to reach zero over the following 18 years. The value is floored at zero: the grid can become neutral but is not modelled as a carbon sink.

## Selected Parameters to Reflect the Narrative

### Electricity Price

**Table 6.** Electricity-price stage parameters.

| Stage | Inflation pass-through ($w_\pi$) | Trend ($\mu_e$) | Volatility ($\sigma_e$) | Shock probability ($p$) | Shock magnitude |
|:---:|---:|---:|---:|---:|---:|
| 1 | 0.25 | -0.015 | 0.05 | 3% | 0.1 |
| 2 | 0.4 | 0.018 | 0.07 | 1% | 0.2 |
| 3 | 0.1 | -0.02 | 0.02 | 1% | 0.05 |

#### Electricity-Price Patterns

The future electricity-price patterns are manually defined and stored in [`future_electricity_patterns.csv`](./raw-data/future_electricity_patterns.csv).

### Solar Panel Costs

**Table 7.** Solar panel cost stage parameters.

| Stage | Trend ($\mu_s$) | Volatility ($\sigma_s$) |
|:---:|---:|---:|
| 1 | 0.035 | 0.02 |
| 2 | 0.015 | 0.02 |
| 3 | - | - |

### Grid Emission Factor

**Table 8.** Grid-emission-factor stage parameters.

| Stage | Until | Trend ($\mu_r$) | Volatility ($\sigma_r$) |
|:---:|---:|---:|---:|
| 1 | 2045 | 0.929 | 0.065 |
| 1 | 2049 | 0.978 | 0.065 |
| 2 | 2072 | 1 | 0.065 |
| 2 | 2074 | - | - |
| 3 | 2099 | - | - |
