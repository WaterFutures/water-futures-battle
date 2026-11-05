# Water Demand Model

## Overview

The water demand model transforms climate and socio-demographic properties into
water demand for each municipality. It combines hourly residential and
business demand patterns with per-house and per-business demand values.

## Raw Data

### Private demand patterns

The yearly residential and business demand patterns are anonymized private data
in the possession of the authors. The patterns are normalized and used as
dimensionless hourly profiles.

### Vewin

[Vewin](https://www.vewin.nl/) is the national association of Dutch drinking
water companies. The yearly consumptions in figures 3.8 and 3.9 are used to calibrate
the historical per-unit consumption by dividing the national
consumption by the number of units extracted from the jurisdictions module.

## Preprocessing Scripts for Initial Dataset Generation

### Static Properties

The notebook [`water_demand_model-static_properties-generator.ipynb`](./preprocessing-scripts/water_demand_model-static_properties-generator.ipynb)
reads the anonymized yearly demand patterns, separates residential and
business profiles, normalizes each profile by its mean, and stores the
resulting 8,760-hour profiles in the `residential` and `business` sheets.

### Dynamic Properties

The notebook [`water_demand_model-dynamic_properties-generator.ipynb`](./preprocessing-scripts/water_demand_model-dynamic_properties-generator.ipynb)
calculates historical per-house and per-business demand from Vewin data. It
also generates short-term predictions and stage-based future bounds for these
two per-unit demand properties.

## Initial Dataset Structure

**Table 1.** Overview of the water demand model properties.

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `water_demand_model-static_properties.xlsx` | `residential`, `business` | Demand pattern ID (`demand_pattern_id: DPxx`) | - | Static | | | Demand pattern |
| | | Pattern demand multiplier (`year_hour`) | - | Static | Deterministic | | Demand pattern $\times$ Hour-of-the-year |
| `water_demand_model-dynamic_properties.xlsx` | `per_house_demand` | Per-house demand | $m^3/house/hour$ | Dynamic Exogenous | Uncertain | Uniform ([`min`, `max`]) | Time $\times$ State |
| | `per_business_demand` | Per-business demand | $m^3/business/hour$ | Dynamic Exogenous | Uncertain | Uniform ([`min`,`max`]) | Time $\times$ State |

## The Narrative

### Stage 1: Efficiency Gains & First Industrial Reuse (2025–2045)

No significant changes in per-capita demand across residential and non-residential sectors are observed in the first decade (2025-2035).
From 2035 to 2045, modest demand reductions emerge in the residential sector, driven by more efficient appliances, building retrofits, and gradual improvements in housing standards.
Non-residential demand follows a similar downward trend, as commercial and service buildings progressively adopt more efficient systems.
Toward the end of this period, two municipalities (GM0014 and GM0268) complete the deployment of industrial wastewater reuse systems, resulting in a marked reduction in non-residential demand per activity in those locations.

### Stage 2: Industrial Reuse Expansion (2050–2075)

Residential per-capita demand continues its gradual decline through improvements in building efficiency, smart home technologies, and greywater reuse, without major discontinuities.
A structural shift accelerates in the non-residential sector.
Industrial and productive facilities in municipalities GM0034, GM0344, GM0363, GM0518, and GM0855 implement large-scale wastewater reuse and internal water-recycling systems.
As these technologies become widespread, non-residential demand per activity drops sharply relative to the previous period.
No shift in consumer behaviour alters the daily and seasonal patterns of water demand.

### Stage 3: Policy-Driven Demand Reduction (2080–2100)

Residential per-capita demand undergoes its most pronounced decline, driven by stricter regulatory measures in the largest municipalities.
These include tighter efficiency standards, usage limits, and mandatory reuse systems in residential buildings.
Non-residential demand per activity reaches its lowest levels as water reuse infrastructure is extended to three additional municipalities (GM0599, GM0758, GM0772).
By this time, industrial water reuse has become standard practice and most efficiency gains from technological innovation have already been realized.
No shift in consumer behaviour alters the daily and seasonal patterns of water demand.

## Preprocessing Scripts for Stage Extension

The script [`water_demand_model-dynamic_properties-stage_extender.py`](./preprocessing-scripts/water_demand_model-dynamic_properties-stage_extender.py)
appends the stage-specific demand values to the dynamic-properties workbook.

Given the complexity of modelling per-capita demand, the following projections are based on a manually defined demand pathway.
No dynamic model is used to derive base demand values; instead, each stage defines residential per-capita demand and non-residential demand per activity as a ratio relative to the 2024 baseline.

Consequently, any percentage change in the demand ratio results in an identical, proportional change in total water demand for a given municipality and sector.
The deployment of industrial water reuse systems is treated as a discrete, municipality-specific event, applied at the start of the period in which it is introduced.

## Selected Parameters to Reflect the Narrative

The parameters are recorded in the input files `raw-data/futures_{type}_demands.csv`.