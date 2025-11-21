---
layout: level_two
title: Pipes
parent: /problem/system-description/
parent_title: System Description
---

# Pipes

Part of [network options](./network-options).

Participants may select from a predefined set of pipe installation options listed in Table X in appendix A. A total of 10 pipe diameters is available. Each option is characterized by its material, hydraulic properties, installation cost, and associated carbon emissions.

The Darcy friction factor of a new pipe is provided for every option. However, the rate at which the friction factor increases over time (decay rate) is uncertain and is defined by a minimum and maximum value.

Pipe installation costs (in €/m) are provided for the year 2025. Any adjustments to costs or discount rates are specified in Section.

Associated carbon emissions (in kg CO₂-eq per meter of pipe installed) are also given. These emission factors may change over time and can be recalculated as described in Section. 


**Table 1:** possible pipe locations

| id | from | to | length | duplicate |
| --- | --- | --- | --- | --- |
| 12443 | Utrecht | Amsterdam | 45 | true |

**Table 2:** possible pipe options

| id | diameter | material | cost | cost duplicate | ? |
| --- | --- | --- | --- | --- | --- |
| 2453a | 200 | pvc | 1000 | 1200 | ? |
| 2453b | 200 | iron | 1000 | 1200 | ? |
| 2454a | 400 | pvc | 1150 | 1200 | ? |
| 2454b | 400 | iron | 1170 | 1200 | ? |

