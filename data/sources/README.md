# Sources

## Overview

The Water Resources System (WRS) models three types of drinking water sources: groundwater, surface water,
and desalination. Groundwater sources are typically smaller
and cheaper, owing to higher raw water quality and lighter
treatment requirements, while surface water and desalination
plants are considerably larger but far more capital- and energy-intensive to build and run.

## Raw Data

### Vewin 

[Vewin](https://www.vewin.nl/) is the national association of water companies in 
the Netherlands.

The approximate source locations were retrieved from [Vewin's 2022 report](https://www.vewin.nl/wp-content/uploads/2024/06/vewin-dutch-drinking-water-statistics-2022-eng-web.pdf) by overlaying
a screenshot of the map in figure 2.6 on a GIS service and clicking on the individual 
locations. This process created the kmz files in the [`raw-data` folder](./raw-data/).

The same report provided the total national supply quantity of each source type
and the number of days surface water production locations were closed due to
low river flows.

### Assumptions

Other information, including which sources are active, their capacities, opening
years, and costs, was generated based on the authors' assumptions.

## Preprocessing Scripts for Initial Dataset Generation

### Static Properties

The notebook [`sources-static_properties-generator.ipynb`](./preprocessing-scripts/sources-static_properties-generator.ipynb)
defines all possible water sources by type.

First, the KMZ datasets containing approximate source locations are formatted to
identify each water source entity by type.
Each source is assigned its closest municipality as a connection point, so some
sources may have the same municipality. 
Desalination plants are initially inactive, leaving participants to decide whether to build them,
while surface water plants are all active and configured by the organisers based on
institutional knowledge (approximate connection and size).
Each source's elevation is set to its assigned municipality's elevation plus 3 metres.
When more than one groundwater source is assigned to the same municipality, only
one is kept active at random; the others are left inactive for participants
to decide.
Water source capacities are allocated by an algorithm so that total provincial
supply is a factor of the highest historical yearly peak provincial demand 
extracted by the [view demands notebook](../jurisdictions/preprocessing-scripts/jurisdictions-view_demands-historical.ipynb).
Finally, opex volumetric energy factors and permits are sampled from uniform 
distributions for all open sources.

Global options, such as capacity target, are manually inserted into the dataset.

### Dynamic Properties

All cost factors are manually defined based on the authors' knowledge.

Fine amounts for groundwater permit exceedance are calibrated manually.

Availability factors are set manually to reproduce the data of the Vewin report.

## Initial Dataset Structure

**Table 1**: Overview of the sources properties.

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `configuration.yaml` | `sources` | New groundwater source maximum nominal capacity, surplus over permit (`groundwater-construction_size-max_permit_surplus`) | - | Static | | | Global |
| | | New surface water source nominal capacity bounds (`surface_water-construction_size-{min,max}`)| $m^3/day$ | Static | | | Global |
| | | New desalination plant nominal capacity bounds (`desalination-construction_size-{min,max}`)| $m^3/day$ | Static | | | Global |
| `sources-static_properties.xlsx` | `global` | Nominal capacity factor for target production (`capacity-target_factor`) | - | Static | | | Source type |
| | | Multiplier of OPEX volumetric non-energy factor for production above target (`opex-volum-other-multiplier`) | - | Static | | | Source type |
| | | Construction time (`construction_time`) | - | Static | Uncertain | Uniform ([`min`, `max`]) | Source type |
| | | New source's OPEX volumetric energy factor (`opex-volum-energy_factor`) | $€/m^3$ | Static | Uncertain | Uniform ([`min`, `max`]) | Source type |
| | `groundwater`, `surface_water`, `desalination` | Name of the source (`name`) | - | Static | | | Source |
| | | ID of the source (`source_id: S{type initial}xxxx`) | - | Static | | | Source |
| | | ID of the source's province (`province`) | - | Static | | | Source |
| | | Latitude (`latitude`), longitude (`longitude`) | degrees | Static | | | Source |
| | | Elevation (`elevation`) | m | Static | | | Source |
| | | ID of the feeding municipality (`closest_municipality`) | - | Static | | | Source |
| | | Date of activation of the source (`activation_date`) | Date | Static | | | Source |
| | | Date of closure of the source (`closure_date`) | Date | Static | | | Source |
| | | Nominal capacity (`capacity-nominal`) | $m^3/day$ | Static | | | Source |
| | | OPEX volumetric component, energy factor (`opex-volum-energy_factor`) | $kWh/m^3$ | Static | | | Source |
| | `groundwater` | Yearly extraction permit (`permit`) | $m^3/year$ | Static | | | Source |
| | `surface_water` | River basin (`basin`) | - | Static | | | Source |
| `{groundwater,surface_water,desalination}-dynamic_properties.xlsx` | `new_source-unit_cost` | New source construction unit-cost | $€/(m^3/day)$ | Dynamic endogenous | Deterministic | | State $\times$ SourceSizeClass | 
| | `opex-fixed` | OPEX fixed component | $€/(m^3/day)$ | Dynamic endogenous | Uncertain | Uniform ([`min`, `max`]) | State $\times$ SourceSizeClass | 
| | `opex-volum-other` | OPEX volumetric component, non-energy expenses | $€/m^3$ | Dynamic endogenous | Uncertain | Uniform ([`min`, `max`]) | State $\times$ SourceSizeClass | 
| `{groundwater,desalination}-dynamic_properties.xlsx` | `availability_factor` | Availability factor of nominal capacity | - | Dynamic exogenous | Deterministic | | State |
| `surface_water-dynamic_properties.xlsx`  | `availability_factor` | Availability factor of nominal capacity | - | Dynamic exogenous | Deterministic | | State, Basin |
| `groundwater-dynamic_properties.xlsx` | `water_displacement-fine_amount` | Fine for exceeding water permit | $€$ | Dynamic exogenous | Deterministic | | State $\times$ DisplacementSeverityClass |

## The Narrative

Availability factors are driven entirely by climate and therefore vary across 
scenarios independently of any policy or cost assumptions.

A narrative for the groundwater permit fines is not provided.

## Preprocessing Scripts for Stage Extension

The script [`sources_related-static_properties-stage_extender.py`](../preprocessing-scripts/sources_related-static_properties-stage_extender.py) updates the static properties 
of sources, connections, and pumping stations based on the newly defined source.
Given a CSV input file describing new sources, the script appends each new
source's information and creates its pumping station and connection.

The script [`sources-dynamic_properties-stage_extender.py`](./preprocessing-scripts/sources-dynamic_properties-stage_extender.py) extends all sources dynamic properties, 
which are all endogenous cost components growing with inflation over time, except for:

- the availability factor of surface water production plants across the various 
basins (groundwater and desalination plants are always assumed fully available), and
- groundwater permit exceedance fines.

### Availability Factor 

The availability factor represents the degree to which a surface water production plant can operate at full capacity.
A value of 1.0 means no restriction, while lower values reflect reduced intake capacity due to drought conditions.
 
Restrictions are derived from the Standardized Precipitation-Evapotranspiration Index (SPEI) created by the climate module applied to two key seasons for the Rhine and Meuse basins:
 
| Parameter | Value | Description |
|---|---|---|
| Spring SPEI threshold | −1.0 | Minimum drought severity to trigger a restriction |
| AF at SPEI = −1.0 | 1.0 | No reduction at the drought onset threshold |
| AF at SPEI = −2.0 | 0.0 | Full restriction at extreme drought |
| AF noise | ±0.2 (uniform) | Stochastic perturbation around the linear AF |
| Restriction start | Mar 1 – May 31 | Randomly sampled within spring |
| Duration – recovery (summer SPEI ≥ −1.0) | 15–90 days | Drought does not persist into summer |
| Duration – persistent drought (summer SPEI < −1.0) | 90–110 days | Drought extends into late summer / early autumn |
 
The logic proceeds as follows.
If the spring SPEI is above −1.0, no restriction is applied for that year.
Otherwise, a restriction is triggered for both basins.
The magnitude of the availability factor is determined by a linear interpolation between SPEI = −1.0 (no reduction) and SPEI = −2.0 (full restriction), with a small uniform random perturbation added to reflect real-world variability.
The start date of the restriction is sampled randomly within the spring window (March–May).
The duration depends on the summer SPEI: if conditions recover by summer, the restriction lifts relatively quickly (15–90 days); if the drought persists, the restriction extends into late summer or early autumn (90–110 days).
After the restriction ends, the availability factor returns to 1.0.

### Groundwater Permit Fines

Fines for exceeding groundwater extraction permits are not modelled mechanistically.
Instead, they are set based on observed model outcomes and adjusted to broadly follow inflation over time, reflecting the assumption that regulatory enforcement intensity remains roughly constant in real terms.

## Selected Parameters to Reflect the Narrative

No parameter is narrative dependent.