# Pumps

## Overview

The pumps module describes pump assets and pump options, including common physical and economic properties such as pump curves and installation costs.
The [pumping stations module](../pumping_stations/) describes where pumps can be installed.

Each pump has exactly one pump option. Each pumping station can have zero, one, or more pumps.

## Raw Data

### Assumptions

The options are based on general domain knowledge and online references.

## Preprocessing Scripts for Initial Dataset Generation

### Static Properties

The notebook [`pump_options-static_properties-generator.ipynb`](./preprocessing-scripts/pump_options-static_properties-generator.ipynb)
formats the available pump options and their head and efficiency curves.

### Dynamic Properties

The notebook [`pump_options-dynamic_properties-generator.ipynb`](./preprocessing-scripts/pump_options-dynamic_properties-generator.ipynb)
formats the manually defined pump costs.

## Initial Dataset Structure

**Table 1**: Overview of the pump options properties.

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pump_options-static_properties.xlsx` | `options` | ID (`option_id: PUxx`) | - | Static |  |  | Pump option |
| | | Name (`name`) | - | Static | | | Pump option |
| | | Nominal flowrate (`flowrate-nominal`) | $m^3/hour$ | Static |  |  | Pump option |
| | | Lifetime (`lifetime`) | years | Static | Uncertain | Uniform ([`min`, `max`]) | Pump option |
| | `PUxx` | Pump curves | | Static | | | Pump option |
| `pump_options-dynamic_properties.xlsx` | `new_pump-cost` | Cost of installation | € | Dynamic endogenous | Deterministic |  | Pump option |

**Table 2**: Overview of the pumps properties.

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pumping_stations-static_properties.xlsx` | `entities` | Pump option ID of each pumping station's pump (`pumps-option_ids`) | - | Static | | | Pump |
| | | Installation date of each pumping station's pump (`pumps-installation_dates`) | - | Static |  |  | Pump |
| | | Decommission date of each pumping station's pump (`pumps-end_dates`) | - | Static |  |  | Pump |

*Note: pumps static properties are concatenated by the `';'` separator as static
 properties of the pumping station owning them.*

## The Narrative

This module has no independent narrative because it contains no dynamic exogenous variables.

## Preprocessing Scripts for Stage Extension

There is no separate stage-extension preprocessing script for this module.

## Selected Parameters to Reflect the Narrative

No parameter is narrative dependent.
