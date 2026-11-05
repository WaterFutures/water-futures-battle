# Economy

## Overview

The economy module supplies national inflation, inflation expectations, and investor demand. These exogenous variables affect the model's costs and financing: inflation is used to adjust costs over time, while inflation expectations and investor demand inform water-utility bond financing. The module also defines the static record format for bond issuances.

## Raw Data

### World Bank

The World Bank is an international financial institution that provides development data through [World Bank Open Data](https://data.worldbank.org). The economy module uses the Netherlands indicator [Inflation, consumer prices (annual %)](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG?locations=NL), sourced from the International Monetary Fund's International Financial Statistics database.

**Table 1.** Datasets downloaded from the World Bank.

| Variable | Measure | Unit | Notes |
| --- | --- | --- | --- |
| Inflation | Annual change | % | National observations for the period 1999–2024. |

## Preprocessing Scripts for Initial Dataset Generation

### Static Properties

The notebook [`bonds-static_properties-generator.ipynb`](./preprocessing-scripts/bonds-static_properties-generator.ipynb) creates the bond-issuance entity table. There are no active bonds in 2025, so the generated table is intentionally empty while retaining its expected columns.

### Dynamic Properties

The notebook [`economy-dynamic_properties-generator.ipynb`](./preprocessing-scripts/economy-dynamic_properties-generator.ipynb) defines the economy's dynamic exogenous variables.

#### Inflation

Historical inflation values are World Bank observations sourced from the IMF's International Financial Statistics database. The inflation predictions are the European Central Bank's 2% target.

#### Inflation expectations

Inflation expectations are computed as the trailing 3-year average of realised inflation.

#### Investor demand

Investor demand is drawn each period from a uniform distribution on $[0.6,\ 1.4]$.

## Initial Dataset Structure

**Table 2.** Overview of the economy module properties.

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `configuration.yaml` | `economy/bonds` | Risk Free Rate (`risk_free_rate`) | % | Static | | | Global |
| | | Spread sensitivity  (`spread_sensitivity`) | - | Static | | | Global |
| | | Maturity  (`maturity`) | Years | Static | | | Global |
| `bonds-static_properties.xlsx` | `entities` | Bond issuance ID (`bond_issuance_id: 'BI-{water_utilit_id}-{issue_year}'`) | - | Static | | | Bond |
| | | Number of bonds in the issue (`n_bonds`) | Bonds | Static | | | Bond |
| | | Issue date (`issue_date`) | Date | Static | | | Bond |
| | | Maturity date (`maturity_date`) | Date | Static | | | Bond |
| | | Coupon rate (`coupon_rate`) | % | Static | | | Bond |
| | | Issuing water utility ID (`water_utility_id`) | - | Static | | | Bond |
| `economy-dynamic_properties.xlsx` | `inflation` | Annual inflation | % | Dynamic Exogenous | Deterministic | | Time $\times$ State |
| | | Target annual inflation | % | Prediction | Deterministic | | Time $\times$ State |
| | `inflation-expect` | Trailing three-year average of inflation | % | Dynamic Exogenous |Deterministic| | Time $\times$ State |
| | `investor_demand` | Investor demand factor | - | Dynamic Exogenous | Deterministic | | Time $\times$ State |

## The Narrative

### Stage 1: The Managed Transition (2025–2049)

The first phase broadly reflects a continuation of historical economic trends.
Inflation fluctuates around moderate levels, with occasional shocks but generally stable expectations.
Meanwhile, the mechanisms behind inflation expectations and investor demand remain unchanged.

### Stage 2: The Period of Structural Stress (2050–2074)

The second phase represents a more challenging macroeconomic environment.
Inflation becomes structurally higher and more volatile, with occasional spikes driven by energy and supply disruptions.
Meanwhile, the mechanisms behind inflation expectations and investor demand remain unchanged.

### Stage 3: The Technological Stabilization Era (2075–2099)

The final phase is characterized by greater macroeconomic stability and stronger productivity gains.
Inflation stabilizes at relatively low levels, supported by technological efficiency and mature energy systems. 
Meanwhile, the mechanisms behind inflation expectations and investor demand remain unchanged.

## Preprocessing Scripts for Stage Extension

Since participants cannot influence macroeconomic conditions, all variables are treated as purely exogenous signals and modelled independently using simplified dynamic processes.

### Inflation

Inflation follows a mean-reverting process with stochastic shocks, calibrated per stage:

$$
\text{Inflation}_t = \text{Inflation}_{t-1} + k(\pi^* - \text{Inflation}_{t-1}) + \sigma \cdot \mathcal{N}^{-1}(U) + \begin{cases} \text{shock} & \text{with probability } p \\ 0 & \text{otherwise} \end{cases}
$$

Here, $\pi^*$ is the stage target inflation, $k$ controls mean-reversion speed, $\sigma$ scales random volatility, and a discrete shock is applied with probability $p$.

### Inflation Expectations

Inflation expectations are computed as the trailing 3-year average of realised inflation.

### Investor Demand

Investor demand is drawn each period from a uniform distribution on $[0.6,\ 1.4]$.

## Selected Parameters to Reflect the Narrative

### Inflation

**Table 3.** Stage parameters for future inflation.

| Stage | Target inflation ($\pi^*$) [%] | Mean-reversion speed ($k$) | Volatility ($\sigma$) | Shock probability ($p$) | Shock magnitude [%] |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 2.5 | 0.10 | 0.4 | 4% | 4 |
| 2 | 4.0 | 0.15 | 0.7 | 7% | 6 |
| 3 | 2.0 | 0.20 | 0.4 | 3% | 2 |