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

### Water Sources {#sec:water-sources}

Water sources represent the entire process of water abstraction and treatment consolidated at a single location.
Each source has a nominal production capacity which represents a hard limit on the amount of water that can be delivered throughout any consecutive 24-hour window.

In the BWF, three macro-types of water sources are modelled: groundwater, surface water, and desalination.
The main trade-off is that groundwater sources are generally smaller (< 25 $Mm^3/year$) and cheaper to operate, as the water has higher quality and requires less treatment.
Surface water treatment plants and desalination plants are generally much larger (30-45 $Mm^3/year$) but are considerably more expensive and energy-intensive to run.
Moreover, surface water sources differ as they are affected by climate conditions; specifically, low inflows within rivers could temporarily shut down treatment plants downstream (effectively reducing their capacity to zero for those days).
Instead, groundwater sources have an extraction permit (expressed in $m^3$ per year).
This is not a hard physical constraint such as the nominal production capacity, but rather a "soft" legislative constraint checked by the government at the end of each year.
This penalty effectively represents compensation for the hydrological displacement affecting farmers and natural areas due to the overextraction.
The fine amount is set by law and can therefore change at any time based on political decisions.

The cost of water production at every source $s$ is a combination of four components:
$$
\mathrm{OPEX}_s(y) =  F_s + (c^\text{en}_s+c^\text{vol}_s) \cdot Q_s(y) + c^\text{extra}_s \cdot \max\bigl(Q_s(y)-\phi_s \cdot \text{capacity}_s, 0 \bigr)
$$
where: 

- $F_s$ represents fixed costs, including personnel, taxes, and planned maintenance.
- $c^\text{en}_s\cdot Q_s(y)$ represents volumetric costs for energy.
- $c^\text{vol}_s \cdot Q_s(y)$ represents the volumetric costs for non-energy related expenditures, such as chemicals and filters.
- $c^\text{extra}_s \cdot \max\bigl(Q_s(y)-\phi_s \cdot \text{capacity}_s, 0 \bigr)$ represent the extra volumetric costs incurred when production exceeds the planned threshold.

In this formulation, $Q_s(y)$ is the total volume produced, $\text{capacity}_s$ is the source nominal capacity, and $\phi_s$ is the capacity target factor, which defines the ideal efficiency point above which additional costs are applied.

Therefore, the operational expenditure associated with all the sources in water utility $w$ at year $y$ is:
$$
\mathrm{OPEX}^{\text{sources}}_w(y) = \sum_{s \in \mathcal{S}_w} \mathrm{OPEX}_s(y)
$$
where $\mathcal{S}_w$ represents the collection of water sources managed by utility $w$, and $\mathrm{OPEX}_s(y)$ is the individual source cost previously defined.

Similarly to municipalities, sources can also open and close over time.
Participants can decide to close production locations and open new ones within the constraints of the problem (available locations and sizes) to make the supply system more efficient.
However, a closed source cannot be reopened and no direct cost is associated with this action.
When activating a new source, participants must decide the nominal capacity, but the possible size is limited by different rules depending on the source type:

- Desalination and surface water sources have an upper limit defined in the competition data (see Appendix A)
- Groundwater sources cannot exceed the permit by more than 30%

New water sources have an uncertain construction time, so participants must communicate the construction start date, and the activation date will be randomized.

The capital investment associated with the construction of new sources in water utility $w$ at year $y$ is:
$$
K^\text{sources}_w(y)
= \sum_{s \in \mathcal{S}_w} \mathbf{1}_{\{\tau_s = y\}} \cdot c^\text{source}_{\text{class}(s)}(y) \cdot \text{capacity}_s 
$$

where for a source $s$ in the set of the water utility's sources ($\mathcal{S}_w$), $\tau_s$ is its starting construction time, $\mathbf{1}_{\{\tau_s = y\}}$ is an indicator function equal to 1 if the construction begins in year $y$ (0 otherwise), $\text{capacity}_s$ is the requested source nominal capacity, and $c^\text{source}_{\text{class}(s)}(y)$ the unit cost, which depends on the year of construction and the source class (see Table @tbl:sources-classes).

| Source nominal capacity [$Mm^3/year$] | Source Class 
| --- | --- | 
| 4 | SMALL
| 8 | MEDIUM
| 16 | LARGE
| > 16 | VERY LARGE

: Sources classification by their nominal capacity. {#tbl:sources-classes}

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
| Unit cost of construction | Dynamic Endogenous | Source Size Class $\times$ National  | $\text{€}/m^3\dot day$
| Operational costs - fixed | Dynamic Endogenous [Uncertain] | Source Size Class $\times$ National  | $\text{€}/year$
| Operational costs - volumetric for energy | Dynamic Endogenous [Uncertain] | Source Size Class $\times$ National  | $kWh/m^3$ |
| Operational costs - volumetric for non-energy | Dynamic Endogenous [Uncertain] | Source Size Class $\times$ National  | $\text{€}/m^3$ |
| Operational costs - volumetric for non-energy - multiplier | Static | Source Type | %
| Construction time | Static [Uncertain] | Source Type | years
| Availability factor | Dynamic Exogenous | Surface water sources | 
| Permit | Static | Groundwater sources | $m^3/year$
| Fine amount | Dynamic Exogenous | Groundwater source permit excedance Severity Class | $m^3/year$

: Sources' properties review. {#tbl:sources-properties}
