# Connections

## Overview

Connections are passive links that transfer water between municipalities or from a pumping station to a municipality. The module represents these links as static entities that contain the physical assets installed on each connection: pipes. This distinction reflects that different pipes can be installed on the same connection.

The [pipes module](../pipes/) describes pipe assets and pipe options, including common physical and economic properties such as diameter and embodied emissions.

## Raw Data

The connections module has no dedicated raw dataset. Its generator relies on the output of other modules; see the [data README](../README.md) for the generation order.

## Preprocessing Scripts for Initial Dataset Generation

### Static Properties

The notebook [`connections-static_properties-generator.ipynb`](./preprocessing-scripts/connections-static_properties-generator.ipynb) generates:

- the connections' static properties
- the pipes static properties
- the pipes dynamic properties

Pipe static properties are stored as semicolon-separated values in the connection static properties file.

Connection static properties are grouped by connection type:

- `provincial`: links between municipalities within a province;
- `cross-provincial`: links between municipalities in different provinces;
- `sources`: supply links from a pumping station or other water source to a municipality.

#### Provincial and Sources Connections
The methodology defines all connections between 2000 and 2025:

1. Define connections province by province:
    1. For each municipality that gets absorbed by a larger neighbour between 2000 and 2025, define a connection to the absorbing municipality only.
    2. Define one connection for each water source to its closest municipality. Size its pipe option for a velocity of 0.75 m/s at the source's nominal capacity.
    3. Create a full Delaunay triangulation among the municipalities that exist in 2000 and will not be absorbed by their larger neighbours. This includes the normal mergers and renaming of municipalities.
2. Apply manual corrections to remove impossible or unrealistic connections.
3. Use a heuristic to disable, rather than delete, excess connections. Each municipality is allowed a number of connections equal to its class size plus one. Retain the *n* shortest connections, applying the heuristic from the largest municipalities down.
4. Apply manual corrections to reactivate critical connections.
5. At this stage, each connection's creation year is the later of its two endpoints' creation dates. Adjust pipe ages so the network has a target average age of 45 years in 2000. Since pipe options (and therefore materials) have not yet been selected, sample the relative friction-factor decay from installation to 2000. Once the material is selected, this allows the pipe's friction factor in 2000 to be determined.
6. Run a bi-objective optimisation to select pipe options and pumping-station speeds, minimising pipe volume and maximising delivered demand.
7. Select a compromise solution from each province's Pareto front. This determines the pipe options and friction factors for 2000.
8. Evolve the system over time. When municipalities merge, replace connections between them with the `SELF_LOOP` placeholder. Each new municipality receives as many connections as its merging municipalities had to the rest of the network, excluding self-loops.
9. Age the system through 2025 and determine which pipes reach the end of their service life during the historical period.
10. Apply manual corrections.
11. Repeat the Delaunay triangulation for 2025 to check for missing connections.

#### Cross-provincial Connections

Cross-provincial connections are defined manually from the map. All cross-provincial connections are disabled in 2025.

## Initial Dataset Structure

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `connections-static_properties.xlsx` | `provincial`, `sources`, `cross-provincial` | Connection ID (`connection_id: 'C{type}xxxx'`) | - | Static |  |  | Connection |
| | `provincial`,  `cross-provincial` | Municipality ID (`from_node`) | - | Static |  |  | Connection |
| | `sources` | Source ID (`from_node`) | - | Static |  |  | Connection |
| | `provincial`, `sources`, `cross-provincial` | Municipality ID `to_node` | - | Static |  |  | Connection |
| | | Length (`distance`) | m | Static |  |  | Connection |
| | | Minor Loss coefficient (`minor_loss_coeff`) | - | Static |  |  | Connection |
| | | Pipe option ID of each connection's pipe (`pipes-option_ids`) | - | Static |  |  | Connection |
| | | Installation date of each connection's pipe (`pipes-installation_dates`) | - | Static |  |  | Connection |
| | | Decommission date of each connection's pipe (`pipes-decommission_dates`) | - | Static |  |  | Connection |
| | | Replacement connection ID (`replaced_by`) | - | Static |  |  | Connection |
| | | Replaced connection ID (`replaces`) | - | Static |  |  | Connection |
| | | *[Unused]* Notify participants if the connection is usable at the competition start (`usable_in_2025`) | - | Static |  |  | Connection |


## The Narrative

This module has no independent narrative because it contains no dynamic exogenous variables. New connections are defined when municipalities are reorganised, so this module follows the jurisdictions narrative.

## Preprocessing Scripts for Stage Extension

The connections module has no dedicated stage-extension preprocessing script. New municipality connections appear when a new municipality (or source) opens or when existing municipalities merge. The script [`municipalities_related-static_properties-stage_extender.py`](../preprocessing-scripts/municipalities_related-static_properties-stage_extender.py) updates the connections static properties, closes connections that can't be used anymore, and creates replacement connections for the new municipality.
