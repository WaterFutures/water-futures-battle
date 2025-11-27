---
layout: default
website_title: Sources
parent: /problem/system-description/
parent_title: System Description
prev_page_url: /problem/system-description/municipalities.html
next_page_url: /problem/system-description/pumping-stations.html
website_page_authors:
  - C. Michalopoulos
  - D. Zanutto
---

### Water Sources

Water sources represent the entire process of water abstraction and treatment consolidated at a single location.
Each source has a nominal production capacity which represents a hard limit on the amount of water that can be delivered in any 24-hour window.

In the BWF, three macro-types of water sources are modelled: groundwater, surface water, and desalination.
The main trade-off is that groundwater sources are generally smaller (< 30 $Mm^3/year$) and cheaper to operate, as the water has higher quality and requires less treatment.
Surface water treatment plants and desalination plants are generally much larger (30-60 $Mm^3/year$) but are considerably more expensive and energy-intensive to run.
Moreover, surface water sources differ as they are affected by climate conditions; specifically, low inflows within rivers could temporarily shut down treatment plants downstream (effectively reducing their capacity to zero for those days).
Instead, groundwater sources have an extraction permit (expressed in $m^3$ per year).
This is not a hard physical constraint such as the nominal production capacity, but rather a "soft" legislative constraint checked by the government at the end of each year.
This penalty effectively represents compensation for the hydrological displacement affecting farmers and natural areas due to the overextraction.
The fine amount is set by law and can therefore change at any time based on political decisions.

The cost of water production at every source is a combination of four components:

- Fixed costs (personnel, taxes, planned maintenance, etc.)
- Volumetric costs for energy
- Volumetric costs for non-energy related expenditures (chemicals, filters, etc.)
- Extra volumetric costs for non-energy related expenditures
This final component is an additional cost paid when the source operates above its planned production capacity, i.e., nominal capacity multiplied by its capacity target factor (which can be interpreted as the ideal efficiency point).

Similarly to municipalities, sources can also open and close over time.
Participants can decide to close production locations and open new ones within the constraints of the problem (available locations and sizes) to make the supply system more efficient.
However, a closed source cannot be reopened and no direct cost is associated with this action.
When activating a new source, participants must decide the nominal capacity, but the possible size is limited by different rules depending on the source type:

- Desalination and surface water sources have an upper limit defined in the competition data (see Appendix A)
- Groundwater sources cannot exceed the permit by more than 30%

New water sources have an uncertain construction time, so participants must communicate the construction start date, and the activation date will be randomized.
The capital investment needed for a new source is simply the unit cost of construction at that year by the required size.

One limitation of the BWF is that we do not model water quality differences between sources, which would typically prevent mixing in practice.
This simplification keeps the problem tractable given its existing complexity.

The key parameters and decision variables governing the Water Sources Module are detailed in @tbl:sources-properties.
The actual values for these variables can be inspected within the data files, which are mapped in Appendix A.

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| Name | Static [Optional] | Source |
| Identifier | Static | Source |
| Source type | Static | Source |
| Latitude | Static | Source | degrees
| Longitude | Static | Source | degrees
| Elevation | Static | Source | m
| Province | Static | Source |
| Connected municipality | Static | Source |
| Activation date | Static | Source | date
| Closure date | Static [Optional] [Decision] | Source | date 
| Capacity - nominal | Static [Optional]  [Decision] | Source | $m^3/day$
| Capacity - target factor | Static | Source Type | %
| Unit cost of construction | Dynamic Endogenous | Source Size Class $\times$ National  | $€/m^3\dot day$
| Operational costs - fixed | Dynamic Endogenous [Uncertain] | Source Size Class $\times$ National  | $€/year$
| Operational costs - volumetric for energy | Dynamic Endogenous [Uncertain] | Source Size Class $\times$ National  | $kWh/m^3$ |
| Operational costs - volumetric for non-energy | Dynamic Endogenous [Uncertain] | Source Size Class $\times$ National  | $€/m^3$ |
| Operational costs - volumetric for non-energy - multiplier | Static | Source Type | %
| Construction time | Static [Uncertain] | Source Type | years
| Availability factor | Dynamic Exogenous | Surface water sources | 
| Permit | Static | Groundwater sources | $m^3/year$
| Fine amount | Dynamic Exogenous | Groundwater source permit excedance Severity Class | $m^3/year$

: Sources' properties review. {#tbl:sources-properties}
