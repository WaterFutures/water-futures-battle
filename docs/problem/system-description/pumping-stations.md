---
layout: default
website_title: Pumps
parent: /problem/system-description/
parent_title: System Description
prev_page_url: /problem/system-description/sources.html
next_page_url: /problem/system-description/pipes.html
website_page_authors:
  - C. Michalopoulos
  - D. Zanutto
---

### Pumping stations

Pumping stations are the infrastructure connecting water sources to municipalities and are responsible for distributing the water produced by each source into the network.
Each pumping station contains a variable number of identical pumps operating in parallel.

Whenever a new source is opened, participants must define which pump option (selected exclusively from a pre-defined list of available pumps) and how many units are installed at that source's pumping station.
Similarly, participants can decide to replace pumps at existing locations.

While a water source's daily outflow is constrained by its nominal capacity, the pumping station's configuration limits the source's peak outflow rate.

The only operational cost component of a pumping station is its energy expenditure, calculated during the network hydraulic simulation based on the energy consumption and tariffs.
Peak demand charges are not included, as we assume utilities have fixed-rate agreements in place with electrical grid providers (see more details in @sec:energy-model).
Maintenance costs and other fixed yearly operational costs are included in the initial construction cost of each pump.

Pumps performances remain constant over time (no degradation in efficiency or similar wear effects).
However, pumps do age normally and have an expected lifetime.
The actual lifetime is randomized, and when a pump reaches its end of life, it must be replaced.
Participants do not need to communicate this decision, as replacements will be automatically implemented, but they must account for this "unexpected" cost in their planning.

| Property | Type | Scope | Unit |
| :--- | :--- | :--- |
| Identifier | Static | Pumping station |
| Assigned source | Static | Pumping station |
| Pump option | Static [Decision]| Pumping station |
| Number of pumps | Static [Decision] | Pumping station | unit

: Pumping stations' properties review. {#tbl:ps-properties}

| Property | Type | Scope | Unit |
| :--- | :--- | :--- |
| Identifier | Static | Pump option |
| Pump curve | Static | Pump option |
| Efficiency curve | Static | Pump option |
| Expected lifetime | Static [Uncertain] | Pump option | years

: Pumps' properties review. {#tbl:pu-properties}

Note that the provided pump curves only describe the working range of the pumps and must not be extrapolated beyond the values presented in the tables.