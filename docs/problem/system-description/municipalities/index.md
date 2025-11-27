---
layout: default
website_title: Municipalities
parent: /problem/system-description/
parent_title: problem
prev_page_url: /problem/system-description/water-utilities.html
next_page_url: /problem/system-description/municipalities/water-demand.html
website_page_authors:
  - D. Zanutto
---

### Municipalities

Each municipality (gemeente) is represented as a single junction point with positive demand, abstracting the entire secondary and tertiary distribution network within that jurisdiction.
This node serves as the sole supply point for all water within the municipality's boundaries, with characteristics such as population, land area, and housing stock consolidated at this level.

The system presents two main challenges.
First, municipal parameters evolve over time as cities grow and change.
Second, the network topology itself is dynamic: municipalities can merge or be absorbed by larger neighbors, causing the number of nodes to vary throughout the planning horizon.

---

**Excursus on the Modelling Approach**

To model this administrative restructuring, municipalities can only open or close on January 1st of each year.
When a municipality closes, its delivery point disappears from the network.

*Absorption by existing municipalities*: When a municipality is absorbed by a larger neighbor that already exists, all attributes of the closing municipality (population, land area, housing stock, etc.) transfer to the destination municipality.
Any pipe that previously connected these two entities becomes hidden, as it formally becomes part of the destination municipality's internal distribution network.

*Clustering into new municipalities*: When multiple municipalities close and cluster together to form a new entity, all their delivery points disappear and a new supply point emerges at the location of the newly formed municipality.
The new municipality inherits all pipeline connections and attributes from the closing municipalities.
This modelling approach mirrors real-world dynamics in densely populated countries like the Netherlands.
When a new municipality forms through clustering, typically a new city center is established while former city centers become secondary neighborhoods.
These moments of urban reorganization present natural opportunities for water utilities to lay new connections and redesign substantial portions of the distribution system.

---

Municipalities have many attributes that influence the other modules of the system.
The full list can be seen in @tbl:muni-properties, while the actual values for these variables can be inspected within the data files, which are mapped in Appendix A.

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| Name | Static | Municipality |
| Identifier | Static | Municipality |
| Latitude | Static | Municipality | degrees
| Longitude | Static | Municipality | degrees
| Elevation | Static | Municipality | m
| Province | Static | Municipality |
| Begin date | Static | Municipality | date
| End date | Static [Optional] | Municipality | date 
| End reason and destination | Static [Optional] | Municipality |
| Population | Dynamic Exogenous | Municipality | inhabitants
| Surface land | Dynamic Exogenous | Municipality | $km^2$ |
| Surface water (inland) | Dynamic Exogenous | Municipality | $km^2$ |
| Surface water (open water) | Dynamic Exogenous | Municipality | $km^2$ |
| Number of houses | Dynamic Exogenous | Municipality | units
| Average age distribution network | Dynamic Endogenous | Municipality | years

: Municipalities' properties review. {#tbl:muni-properties}

Along with these attributes, the only observable quantity for each municipality is the total water demand divided in its two components: consumption (delivered demand) and the quota of undelivered demand.

More precisely, the total water demand comprises two volumetric quantities, though this breakdown is not observable to participants:

- billable water demand (the sum of household and business water demands) described in @sec:water-dem, and
- non-revenue water (accounting for leaks, flushing, measurement errors and other losses), described in @sec:nrw.

Instead, only two outputs are observable: actual consumption and undelivered demand.
These two variables are extracted from an EPANET simulation of the network run in pressure-driven analysis (PDA) mode with a minimum pressure threshold of 30 m.
This threshold accounts for the requirement to deliver 20 m of pressure at the consumer tap, plus an allowance of 5 m pressure drop in the secondary network and 5 m in the tertiary portion.

