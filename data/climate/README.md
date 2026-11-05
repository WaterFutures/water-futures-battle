# Climate

## Overview

The climate system represents the meteorological variables that affect the other modelled systems. Temperature and precipitation influence water demand, while all climate variables affect the hydrological cycle, including groundwater levels and river flows. Extreme events could also affect infrastructure directly: flooding, for example, could disrupt part of the network or disable a pumping station. Over longer timescales, changes in sea level and ocean salinity could alter the operation of desalination plants.

The BWF model represents these relationships at a simplified level, consistent with the available data and the scope of the competition:

- season-average maximum temperatures are an input to the water demand generation algorithm;
- climate variables determine the SPEI, which in turn determines surface water source availability by basin.

## Raw Data

### KNMI

KNMI (Koninklijk Nederlands Meteorologisch Instituut) is the Dutch meteorological institute ([KNMI](https://www.knmi.nl)).
It provides calibrated historical observations and long-term climate scenarios for the Netherlands.
The climate module relies on the [KNMI climate dashboard](https://www.knmi.nl/klimaat#klimaatdashboard).
The KNMI climate dashboard provides historical trends and future scenarios for temperature, precipitation, precipitation deficit, wet and dry conditions (SPEI), sea level, wind speed, solar radiation, and fog.

**Table 1.** Datasets downloaded from KNMI climate dashboard.

| Variable | Measure | Unit | Notes |
| --- | --- | --- | --- | 
| Temperature (temperatuur & temperatuur-dagen) | Season-average temperature (gemiddelde) | °C | Taken in 'De Bilt' by season |
| | Season-average maximum temperature (gemiddelde-maximum) | °C | Taken in 'De Bilt' by season |
| | Season-average minimum temperature (gemiddelde-minimum) | °C | Taken in 'De Bilt' by season |
| | Season-maximum daily-average-temperature [warmest day] (warmste dag) | °C | Taken in 'De Bilt' by season |
| | Season-minimum daily-average-temperature [coldest day] (koudste dag) | °C | Taken in 'De Bilt' by season |
| Precipitation (neerslaghoeveelheid) | Season cumulative precipitation (neerslagsom) | mm/season | Taken in 'De Bilt' by season |
| Solar radiation (zonnestraling) | Season average solar radiation | $W/m^2$ | Taken at national level (landelijk) by season |
| SPEI [Standardised Precipitation-Evapotranspiration Index] | SPEI | - | Taken at national level (landelijk) by season |

De Bilt lies near the center of the Netherlands and hosts KNMI, so the dataset uses it as the representative location for variables measured at a point. Measurements from additional locations could capture spatial variation, but the BWF model does not represent that variation.

The dataset uses seasonal aggregates rather than daily or monthly historical observations. This resolution matches the limited influence of climate on the other modelled variables and avoids adding detail that the current model cannot use.

The dashboard also provides the relevant Dutch climate scenarios alongside the historical data. Each scenario combines an emissions pathway, high (H) or low (L), with a precipitation regime, dry (d) or wet (n). This produces four scenarios, each with a 90% uncertainty band.

## Preprocessing Scripts for Initial Dataset Generation

### Static Properties

This module defines no entities or static properties.

### Dynamic Properties

The notebook [`climate-dynamic_properties-generator.ipynb`](./preprocessing-scripts/climate-dynamic_properties-generator.ipynb) converts all variables in Table 1 to the dataset's input format.

As described above, the dataset uses De Bilt values as the representative point for the Netherlands. The preprocessing script loads the seasonal data, combines the variables into a single dataframe, orders the records by time, and selects and renames the measurement columns required by the model.

The script appends the four climate scenarios. For each scenario, it stores the median projection together with the lower and upper bounds of the 90% uncertainty band.

## Initial Dataset Structure

**Table 2**: Overview of the climate module properties.

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | ---| --- |
| `climate-dynamic_properties.xlsx` | `temperature-avg` | Season-average temperature | °C | Dynamic Exogenous | Deterministic | - | Time  $\times$ State |
| | | Future season-average temperature | °C | Prediction | Stochastic | Unknown (`[min, median, max]`) | Time $\times$ State  $\times$ Scenarios (`[Hn, Hd, Ln, Ld]`) |
| | `temperature-min-avg` | Season-average minimum temperature | °C | Dynamic Exogenous | Deterministic | - | Time $\times$ State  |
| | | Future season-average minimum temperature | °C | Prediction | Stochastic | Unknown (`[min, median, max]`) | Time  $\times$ State $\times$ Scenarios (`[Hn, Hd, Ln, Ld]`) |
| | `temperature-max-avg` | Season-average maximum temperature | °C | Dynamic Exogenous | Deterministic | - | Time $\times$ State  |
| | | Future season-average maximum temperature | °C | Prediction | Stochastic | Unknown (`[min, median, max]`) | Time $\times$ State $\times$ Scenarios (`[Hn, Hd, Ln, Ld]`) |
| | `temperature-warmest_day` | Season-maximum daily-average temperature [warmest day] | °C | Dynamic Exogenous | Deterministic | - | Time  $\times$ State |
| | | Future season-maximum daily-average temperature [warmest day] | °C | Prediction | Stochastic | Unknown (`[min, median, max]`) | Time $\times$ State  $\times$ Scenarios (`[Hn, Hd, Ln, Ld]`) |
| | `temperature-coldest_day` | Season-minimum daily-average temperature [coldest day] | °C | Dynamic Exogenous | Deterministic | - | Time $\times$ State  |
| | | Future season-minimum daily-average temperature [coldest day] | °C | Prediction | Stochastic | Unknown (`[min, median, max]`) | Time $\times$ State  $\times$ Scenarios (`[Hn, Hd, Ln, Ld]`) |
| | `precipitation` | Season cumulative precipitation | mm/season | Dynamic Exogenous | Deterministic | - | Time $\times$ State  |
| | | Future season cumulative precipitation | mm/season | Prediction | Stochastic | Unknown (`[min, median, max]`) | Time $\times$ State  $\times$ Scenarios (`[Hn, Hd, Ln, Ld]`) |
| | `solar_radiation-avg` | Season-average solar radiation | $W/m^2$ | Dynamic Exogenous | Deterministic | - | Time $\times$ State  |
| | | Future season-average solar radiation | $W/m^2$ | Prediction | Stochastic | Unknown (`[min, median, max]`) | Time $\times$ State  $\times$ Scenarios (`[Hn, Hd, Ln, Ld]`) |
| | `SPEI` | Standardised Precipitation-Evapotranspiration Index | - | Dynamic Exogenous | Deterministic | - | Time $\times$ State  |

## The Narrative

### Stage 1: The Warming Continuity (2025–2049)

The current climate trend continues and Europe experiences an above-average rise in temperatures.
Precipitation in the Netherlands does not decline significantly, and the trajectory aligns with the High Emission, Wet scenario from the KNMI 2025 projections.

### Stage 2: The Drying Turn (2050–2074)

The high-emission pathway is now unambiguous.
Decades after the Paris Agreement pledges, the Netherlands and much of Europe bear the cumulative consequences.
Temperatures remain elevated, and a new signal emerges: after years of warmth, the precipitation regime begins to shift.
The dominant scenario transitions toward High Emission, Dry.

### Stage 3: The Residual Climate (2075–2100)

The global energy transition is structurally complete, arresting further forcing.
The climate does not reverse but it stabilises at an elevated, drier state, reflecting the inertia of two centuries of industrial emissions.
Variability persists, but the direction of travel is no longer worsening.

## Preprocessing Scripts for Stage Extension 

Since running a custom climate model is outside the scope of this work and participants cannot influence the climate, climate realisations are random samples drawn from the KNMI climate scenarios.

### Temperature, Precipitation, and Solar Radiation

First, a scenario is selected coherently with the narrative below.
Then, for each climate variable, a random value is drawn to represent where the outcome falls within that scenario's projected range.
This gives a target value for each season at the end of the stage.
Values are then interpolated annually from the end of the previous stage to the sampled target.
Finally, noise is applied to the interpolated series with a distribution type chosen to reflect the physical character of each climate variable.
Distribution parameters are set to reflect the scenario's projected uncertainty for each variable, plus an additional variability factor that increases across stages.

| Variable | Distribution | Inverted | Additive noise |
| --- | --- | --- | --- |
| Temperature - Average | Normal | False | True |
| Temperature - Average minimum | Gumbel | False | True |
| Temperature - Average maximum | Gumbel | False | True |
| Temperature - Warmest day | Gumbel | False | True |
| Temperature - Coldest day | Gumbel | *True* | True |
| Precipitation | Gamma | False | *False* |
| Solar radiation | Normal | False | True |

### SPEI

Given the absence of SPEI projections, values are calculated from precipitation and temperature alone.
Potential evapotranspiration is estimated as:

$$\text{PET} = 0.17 \cdot \max(T, 0)$$

where the factor 0.17 is manually calibrated to produce plausible values at the seasonal level given that only monthly averages are available.

The water balance deficit is then $D = P - \text{PET}$, and SPEI is computed by standardising $D$ against its historical mean and standard deviation for each season:

$$\text{SPEI} = \frac{D - \mu_{\text{hist}}}{\sigma_{\text{hist}}}$$

Values are clipped to [−3,3] to stay within the conventional SPEI range.

## Selected Parameters to Reflect the Narrative

### Temperature, Precipitation, and Solar Radiation

**Table 3.** Scenario and variability parameters by stage.

| Stage | Scenario | Additional model variability [%] |
| --- | --- | ---: |
| 1 | Hn | 0 |
| 2 | Hd | 20 |
| 3 | Hd | 30 |

