# Jurisdictions

## Overview

The jurisdictions module represents a state administrative hierarchy: the national government, regions, provinces, and municipalities.
These entities model the socio-demographic system, for example, population dynamics and their impact on the national water grid.

Municipalities and their boundaries change over time through reorganisation, such as mergers or the absorption of a smaller municipality by a larger neighbour.
Thus, municipalities are dynamic entities with opening and closing dates and destination IDs.

Each municipality represents a single drinking water delivery point
for the national grid, behind which an independent, hidden
(i.e., not modelled by the BWF) inner distribution
network (IDN) conveys water to residential and business consumers and is subject to systematic leakage.

## Raw Data

### CBS 

CBS (Centraal Bureau voor de Statistiek) is the Dutch statistical office ([CBS](https://www.cbs.nl/en-gb/about-us)).
They provide relevant and independent figures on a wide range of societal issues, such as population, labour, and income.
CBS dashboards provide datasets and plots for various variables modelled in the BWF.
Specifically, data have been downloaded from CBS databases, e.g., [CBS cijfers database](https://www.cbs.nl/nl-nl/cijfers/detail/70739ned) and [CBS regional key figures database](https://opendata.cbs.nl/#/CBS/nl/dataset/70072ned/table?dl=B01D1&ts=1761565609309), and news articles on their websites, e.g., [Dutch population forecast](https://www.cbs.nl/en-gb/news/2024/51/forecast-population-of-the-netherlands-will-reach-19-million-in-2037), and [Dutch companies overview](https://longreads.cbs.nl/the-netherlands-in-numbers-2021/how-many-companies-in-the-netherlands/).

**Table 1.** Datasets Downloaded from CBS dashboards.

| Variable | Measure | Unit | Coverage | Notes |
| --- | --- | --- | --- | --- |
| Administrative history (Gebieden, overzicht vanaf 1830) | Jurisdiction names and codes, hierarchy, municipality dates, and descriptions of administrative changes | - | 1830-2025 | |
| Number of Businesses | Total number of businesses on 1 January | businesses | 2013-2024 | By activity class and municipality |
| Disposable income | Average disposable income on 1st of Jan | € | 2011-2023 | By municipality |
| Area | Total land and water area on 1st of Jan | $km^2$ | 2000-2024 | By municipality |
| Housing stock | Total number of dwellings on 1 January | dwellings | 2013-2024 | By municipality |
| Population | Total population figure on 1st of Jan | persons | 2000-2024 | By urban class and municipality |
| Population projections | Total population figure on 1st of Jan | persons | 2000-2024 | National |
| Tourism info | Assigned tourism class on 1st of Jan | - | 2000-2024 | By municipality |

### Nominatim/OpenStreetMap

[Nominatim](https://nominatim.org/) uses [OpenStreetMap](https://www.openstreetmap.org/) data to find locations on Earth by name and address (geocoding). It can also do the reverse, find an address for any location on the planet.

Municipality latitudes and longitudes were retrieved via the Nominatim service, which relies on OpenStreetMap data.

### Open-Elevation

[Open-Elevation](https://open-elevation.com) is a free and open-source alternative to the Google Elevation API and similar offerings.

Municipality elevations were retrieved via the Open-Elevation API service.

### Vewin 

[Vewin](https://www.vewin.nl/) is the national association of water companies in the Netherlands.

Key figures on population and pipe-network length over time were retrieved from [Vewin's 2022 report](https://www.vewin.nl/wp-content/uploads/2024/06/vewin-dutch-drinking-water-statistics-2022-eng-web.pdf).

### Assumptions 

The demand curves associated with residential and business water use were manually defined based on the tourism codes in [`Municipality_AssociatedCurves.csv`](./raw-data/Municipality_AssociatedCurves.csv).

## Preprocessing Scripts for Initial Dataset Generation

### Static Properties

The notebook [`jurisdictions-static_properties-generator.ipynb`](./preprocessing-scripts/jurisdictions-static_properties-generator.ipynb) reorganises the [CBS gebieden dataset](./raw-data/70739ned-202502190000.zip) in `regions`, `provinces`, and `municipalities` following the BWF testbed convention.
It then uses the Nominatim API to obtain municipality coordinates and the Open-Elevation API to retrieve their elevations.
Finally, it appends tourism information for each municipality.

### Dynamic Properties

The notebook [`jurisdictions-dynamic_properties-generator.ipynb`](./preprocessing-scripts/jurisdictions-dynamic_properties-generator.ipynb) defines the municipalities' dynamic properties over the historical period.

First, the notebook reorganises the CBS regional-key-figure population records by municipality IDs.
This information is also used to reconstruct kilometres of pipes per capita over time.
Population projections for the entire country are also appended.
The same reorganisation is then applied to land and water areas, buildings, businesses (with earlier values reconstructed back to 2000), average disposable income, and associated demand patterns.
Finally, the average age of each inner distribution network in 2000 is sampled uniformly between 25 and 45 years. This parameter influences NRW demand and was calibrated against the NRW figure for 2000 in the Vewin report. It is the only endogenous dynamic municipality property.

### Water Demands

The notebook [`jurisdictions-view_demands-historical.ipynb`](./preprocessing-scripts/jurisdictions-view_demands-historical.ipynb) runs the socio-demographic system alongside the water demand and NRW models to visualise historical water demand. It must therefore run after those modules have been generated.

## Initial Dataset Structure

**Table 2.** Overview of the jurisdictions module properties.

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `configuration.yaml` | `state` | Name of the state (`name`) | - | Static | | | Nation |
| | | ID of the state (`id: ID0000`) | - | Static | | | Nation |
| `jurisdictions-static_properties.xlsx` | `regions` | Name of the region (`name`) | - | Static | | | Region |
| | | ID of the region (`cbs_id: LDxx`) | - | Static | | | Region |
| | | ID of the region's state (`state`) | - | Static | | | Region |
| | `provinces` | Name of the province (`name`) | - | Static | | | Province |
| | | ID of the province (`cbs_id: PVxx`) | - | Static | | | Province |
| | | ID of the province's region (`region`) | - | Static | | | Province |
| | `municipalities` | Name of the municipality (`name`) | - | Static | | | Municipality |
| | | ID of the municipality (`cbs_id: GMxxxx`) | - | Static | | | Municipality |
| | | ID of the municipality's province (`province`) | - | Static | | | Municipality |
| | | Date of establishment of the municipality (`begin_date`) | Date | Static | | | Municipality |
| | | Date of dissolution of the municipality (`end_date`) | Date | Static | | | Municipality |
| | | Reason for dissolution of the municipality (`end_reason`) | - | Static | | | Municipality |
| | | ID of the appearing/absorbing municipalities (`destination_cbs_ids`) | - | Static | | | Municipality |
| | | ID of the main appearing/absorbing municipality (`main_destination_municipality`) | - | Static | | | Municipality |
| | | Latitude (`latitude`), longitude (`longitude`) | degrees | Static | - | - | Municipality |
| | | Elevation (`elevation`) | m | Static | - | - | Municipality |
| | | Tourism area and group IDs (`touristic_area_cbs_id` and `touristic_group_cbs_id`)  | - | Static | - | - | Municipality |
| `municipalities-dynamic_properties.xlsx` | `population` | Population | persons | Dynamic Exogenous | Deterministic | | Time $\times$ [Municipality, State] |
| | | Population projection | persons | Prediction | Deterministic | | Time $\times$ State |
| | `surface-land` | Land area | km² | Dynamic Exogenous | Deterministic | | Time $\times$ Municipality |
| | `surface-water-inland` | Inland-water area | km² | Dynamic Exogenous | Deterministic | | Time $\times$ Municipality |
| | `surface-water-open` | Open-water area | km² | Dynamic Exogenous | Deterministic | | Time $\times$ Municipality |
| | `n_houses` | Housing stock | dwellings | Dynamic Exogenous | Deterministic | | Time $\times$ Municipality |
| | `n_businesses` | Number of businesses | businesses | Dynamic Exogenous | Deterministic | | Time $\times$ Municipality |
| | `disposable_income-avg` | Average disposable income of private households, excluding students | thousand €/year | Dynamic Exogenous | Deterministic | | Time $\times$ Municipality |
| | `assoc_dem_pat-residential-1`, `assoc_dem_pat-residential-2`, `assoc_dem_pat-business` | Assigned demand-pattern IDs | - | Dynamic Exogenous | Deterministic | | Time $\times$ Municipality |
| | `dist_network-age-avg` | Average age of the municipality's inner distribution network | years | Dynamic endogenous | Deterministic | | Time $\times$ Municipality |

## The Narrative

### Stage 1: The Urban Acceleration (2025–2049)

The first phase broadly reflects a continuation of historical demographic trends. Population grows steadily, driven by sustained migration toward major urban centres, while rural and peripheral municipalities see their populations gradually thin out. Housing demand keeps pace with population, but the composition of households shifts: a rising share of single-person dwellings means that the number of houses grows faster than raw population figures alone would suggest. The business landscape expands in step with population, with new establishments appearing at a regular and predictable rate. Disposable income continues to grow at a steady pace, supported by gradual productivity improvements.

### Stage 2: The Period of Demographic Stress (2050–2074)

The second phase represents a more challenging demographic and economic environment. Population growth decelerates markedly as the cumulative effects of earlier trends level off, and economic turbulence suppresses entrepreneurial activity. Against this backdrop of financial pressure, household formation patterns reverse: people increasingly consolidate living arrangements, with average occupancy per dwelling rising as cohabitation becomes a more common response to difficult conditions. Disposable income fails to keep pace with inflation, gradually eroding household purchasing power.

### Stage 3: The Rural Renaissance (2075–2099)

This period sees population growth resume on a stable and sustained footing, but the spatial pattern of the previous century is inverted. Improvements in transport infrastructure reduce travel times so much that proximity to city centres no longer commands the premium it once did. Net migration flows now favour the countryside, and smaller municipalities recover.

## Preprocessing Scripts for Stage Extension

The script [`municipalities_related-static_properties-stage_extender.py`](../preprocessing-scripts/municipalities_related-static_properties-stage_extender.py) updates the static properties of jurisdictions and connections based on the predefined municipality merger and absorption events. Given a YAML input file describing municipality merger and absorption events, the script appends the newly defined municipalities and relevant event information (e.g. dissolution dates) to the municipalities static properties file. It also updates the connections static properties file
with the new connections replacing old existing connections.

The script [`municipalities-dynamic_properties-stage_extender.py`](./preprocessing-scripts/municipalities-dynamic_properties-stage_extender.py) extends municipality dynamic properties, which, except for the inner distribution network average age, are  all exogenous and modelled independently.

Population projections are not updated.

### Mergers and Absorption

No merger or absorption is defined during the BWF competition.

### Population

Each year $y$, the population $P_m(y)$ of municipality $m$ is updated by multiplying the previous year's value by a growth rate drawn uniformly from a range that depends on the municipality's current size class:
 
$$P_m(y) = P_m(y-1) \cdot \mathcal{U}\!\left(r^-_{c_m}(y-1),\; r^+_{c_m}(y-1)\right)$$
 
Here $\mathcal{U}(r^-_{c_m}(y), r^+_{c_m}(y))$ denotes a uniform draw whose lower and upper bounds $r^-_{c_m}(y)$ and $r^+_{c_m}(y)$ are determined by the municipality's size class ${c_m}$.
 
When a merger (or absorption) occurs, the receiving municipality $m$ inherits the combined population of all predecessor municipalities $i$, plus a fixed annual inflow $\Delta_{\text{flow}}$ that persists for the following ten years (or until the end of the stage):
$$P_m(y) = \sum_i P_i(y-1) + \Delta_{\text{flow}}$$
The value $\Delta_{\text{flow}}$ is a constant annual increment specified as part of the merger event definition.

### Number of Houses and Businesses

The number of houses $H_m(y)$ and businesses $B_m(y)$ are updated each year in proportion to the population change, using fixed per-capita conversion factors:
 
$$H_m(y) = H_m(y-1) + \left\lfloor \Delta P_m(y) \cdot f_H \right\rfloor$$
 
$$B_m(y) = B_m(y-1) + \left\lfloor \Delta P_m(y) \cdot f_B \right\rfloor$$
 
where $\Delta P_m(y) = P_m(y) - P_m(y-1)$ is the annual population change.
The factors $f_H$ and $f_B$ are the stage dependent housing and business conversion rates, expressed in units per capita.

Upon a merger (or absorption), the new municipality inherits the sum of its predecessors' values.

### Municipality's Surfaces (Land Area, Inland Water Area, Open Water Area)

A municipality's jurisdictional area, i.e., its land, inland water, and open water surfaces, does not change over time.
Upon a merger (or absorption), the receiving municipality inherits the sum of all areas from the merging entities.
 
### Associated Water Demand Patterns (Residential and Business)
 
Demand patterns (the intra-annual shape of water consumption) remain fixed throughout a stage unless manually updated.
When a new municipality is created through a merger, its demand patterns are defined explicitly as part of the merger event specification and remain constant thereafter.
 
### Average Disposable Income
 
The average disposable income $\mathrm{ADI}_m(y)$ evolves each year according to a process that combines a structural trend, inflation, and stochastic volatility:
 
$$\mathrm{ADI}_m(y) = \mathrm{ADI}_m(y-1)\cdot\Bigl(1 + k\bigl(\mu_g + \pi(y)\bigr) + \sigma_g \cdot Z(y)\Bigr)$$
 
where $Z(y) \sim \mathcal{N}(0,1)$ is a standard normal draw realised in year $y$.
The four parameters governing this process are as follows.
- The pass-through weight $k$ is the fraction of the combined trend-and-inflation signal that is actually transmitted into income growth. A value of one means income tracks the full nominal signal; smaller values dampen this sensitivity.
- The structural growth rate $\mu_g$ is a stage-specific constant representing the long-run real trend in incomes, independent of inflation.
- The realised inflation rate $\pi(y)$ is the aggregate price inflation in year $y$, drawn from the scenario and shared across all municipalities.
- The volatility $\sigma_g$ scales the year-to-year random fluctuations; larger values produce more erratic income trajectories around the trend.
 
Upon a merger (or absorption), the new municipality's income is initialised as the population-weighted average of its predecessors:
$$\mathrm{ADI}_m(y) = \frac{\displaystyle\sum_i \mathrm{ADI}_i(y-1)\cdot P_i(y-1)}{\displaystyle\sum_i P_i(y-1)}$$

## Selected Parameters to Reflect the Narrative

### Mergers and absorptions.

Merger and absorption events are specified in [`new_municipalities_events.yaml`](./raw-data/new_municipalities_events.yaml).

### Population

**Table 3.** Municipality population-growth-factor bounds by period and size class.

| Stage | Municipality size class ($c_m$) | Growth-factor bounds ($r_{c_m}^-$,$r_{c_m}^+$) |
|:---:|:---:|:---:|
| 1 (2040) | SMALL | (0.972, 0.990) |
| | MEDIUM | (0.994, 1.028) |
| |  LARGE | (1.003, 1.030) |
| |  G4 | (1.006, 1.017) |
| 1-2 (2055) |  SMALL | (0.940, 0.990) |
| | MEDIUM | (1.007, 1.011) |
| | LARGE | (1.013, 1.017) |
| | G4 | (1.013, 1.017) |
| 2 (2070) | SMALL | (0.980, 1.020) |
| | MEDIUM | (0.980, 1.020) |
| | LARGE | (0.980, 1.020) |
| | G4 | (0.980, 1.020) |
| 2–3 (2100) | SMALL | (1.015, 1.018) |
| | MEDIUM | (1.015, 1.018) |
| | LARGE | (0.998, 1.002) |
| | G4 | (0.998, 1.002) |

### Number of Houses and Businesses

**Table 4.** Stage parameters for housing and business growth.

| Stage | Population per house ($f_H$)| New businesses per additional person ($f_B$) |
|:---:|---:|---:|
| 1 | 2.5 | 0.11 |
| 2 | 3.2 | 0.02 |
| 3 | 3.0 | 0.13 |

### Average Disposable Income

**Table 5.** Stage parameters for average disposable income.

| Stage | Inflation pass-through weight ($k$) | Structural trend ($\mu_g$) | Volatility ($\sigma_g$) |
|:---:|---:|---:|---:|
| 1 | 0.25 | 0.015 | 0.005 |
| 2 | 0.40 | 0.023 | 0.010 |
| 3 | 0.17 | 0.010 | 0.001 |
