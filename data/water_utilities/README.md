# Water Utilities

## Overview

The water utilities module represents the drinking water companies that operate
the national water grid. Each water utility is assigned one or more
provinces and is responsible for the assets within its assigned area.

## Raw Data

### Assumptions

Water utility assignments to provinces are manually defined.

### Vewin

[Vewin](https://www.vewin.nl/) is the national association of Dutch drinking
water companies. 

Approximate fixed and variable consumer water prices are
based on the utility-level prices reported in [Vewin's 2022 report](https://www.vewin.nl/wp-content/uploads/2024/06/vewin-dutch-drinking-water-statistics-2022-eng-web.pdf).
The values are used as calibration points rather than as an exact historical 
reconstruction.

## Preprocessing Scripts for Initial Dataset Generation

### Static Properties

The notebook [`water_utilities-static_properties-generator.ipynb`](./preprocessing-scripts/water_utilities-static_properties-generator.ipynb)
creates the water utility entity table by manually assigning each utility to one
province or a small group of provinces.

### Dynamic Properties

The notebook [`water_utilities-dynamic_properties-generator.ipynb`](./preprocessing-scripts/water_utilities-dynamic_properties-generator.ipynb)
creates the initial balance and water-price properties.

#### Funds balance

The balance of every water utility is set to zero throughout the historical period
2000-2024 because the financing mechanism is not active yet.

#### Water prices

Fixed and variable price components are sampled from skew-normal distributions
calibrated to the approximate Vewin values. The selling price for water
exchanged between utilities is sampled as 30% to 50% of the variable consumer
price. The resulting 2021 price values are back-propagated to the initial
period using the national inflation series from the economy module.

## Initial Dataset Structure

**Table 1.** Overview of the water utilities module properties.

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `water_utilities-static_properties.xlsx` | `entities` | Water utility ID (`water_utility_id`) | - | Static | | | Water utility |
| | | Assigned province IDs (`assigned_provinces`) | - | Static | | | Water utility |
| `water_utilities-dynamic_properties.xlsx` | `balance` | Utility funds balance (`balance`) | € | Dynamic endogenous | Deterministic | | Time × Water utility |
| | `water_price-fixed` | Fixed component of the consumer water tariff (`water_price-fixed`) | €/year | Dynamic endogenous | Deterministic | | Time × Water utility |
| | `water_price-variable` | Variable component of the consumer water tariff (`water_price-variable`) | €/m³ | Dynamic endogenous | Deterministic | | Time × Water utility |
| | `water_price-selling` | Selling price for inter-utility water exchanges (`water_price-selling`) | €/m³ | Dynamic Endogenous | Deterministic | | Time × Water utility |

## The Narrative

This module has no independent narrative because it contains no dynamic exogenous 
variables. Also, the province assignments remain fixed throughout the stages.

## Preprocessing Scripts for Stage Extension

There is no separate stage-extension preprocessing script for this module.

## Selected Parameters to Reflect the Narrative

No parameter is narrative dependent.
