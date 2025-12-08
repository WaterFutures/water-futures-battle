---
layout: default
website_title: System Description
parent: /problem/system-description/
parent_title: System Description
prev_page_url: /problem/system-description/
next_page_url: /problem/system-description/municipalities.html
website_page_authors:
  - D. Zanutto
---

### Water Utilities

Within the BWF, Water Utilities (WUs) act as the entities responsible for managing the assets and delivering drinking water across their assigned provinces.

WUs must choose the policies to apply to their own system (e.g, setting the budget for non-revenue water reduction) and decide the interventions to take on their system (e.g., replacing a pipe).

Multiple WUs can also join their efforts to pursue common interventions, for example, the cost of placing a pipe connecting two water utilities will be shared between the two utilities.
If WU are connected with each other and there is an exchange of water, the receiving utility pays a volumetric fee to the supplying utility.
More detailed information about the water tariff scheme are available in @sec:water-tariff.

The structure of the system is static.
The number of WUs and their specific geographic responsibilities (assigned provinces) will not change through the competition.

The key parameters and decision variables governing the Water Utility Module are detailed in @tbl:wu-properties.
The actual values for these variables can be inspected within the data files, which are mapped in Appendix A.

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :---
| Identifier | Static | Water Utility |
| Assigned province | Static | Water Utility |

: Water utilities' properties review. {#tbl:wu-properties}
