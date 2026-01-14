---
layout: default
website_title: Energy System
parent: /problem/external-drivers/
parent_title: External drivers
prev_page_url: /problem/external-drivers/climate.html
next_page_url: /problem/external-drivers/economy-financing.html
website_page_authors:
  - J. Brandt
  - D. Zanutto
---

### Energy System {#sec:energy-model}

The energy system in the BWF is modeled through three macro-drivers: electricity prices, greenhouse gas emission factor, and solar panels prices.

The electricity price is assumed to vary annually, influenced by inflation but subject to high uncertainty.
On a higher resolution, prices also fluctuate hourly throughout the day.
The electricity purchased by the grid has an associated greenhouse gas emissions factor, which can not be influcenced by the utilities but is adjusted yearly to account for the evolution of the national electricity generation mix.

As an alternative to grid electricity, participants may install solar photovoltaic panels.
The unit cost of solar energy is modeled as a dynamic variable, changing annually to reflect improvements in the technology.

The capital investment associated with the installation of solar panels in water utility $w$ at year $y$ is:

$$
K^\text{solar}_w(y)
= \sum_{v \in \mathcal{V}_{w}} \mathbf{1}_{\{\tau_v = y\}}\cdot c^\text{solar}(y) \cdot P_v
$${#eq:solar-capital-investment}

where $v$ is the solar installation index within the set of photovoltaic systems in the water utility ($\mathcal{V}_{w}$), $\tau_v$ is the installation time, $\mathbf{1}_{\{\tau_v = y\}}$ is an indicator function equal to 1 if the installation happened in year $y$ (0 otherwise), $c^\text{solar}(y)$ is the unit cost per kilowatt of capacity in year $y$, and $P_v$ is the nominal power capacity of the solar system $v$.

No cost is associated with the operation of the solar panels.
These components have a fixed lifespan of 25 years, after which competitors must choose between investing in a replacement installation or reverting to full dependence on the electrical grid.

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| Electricity price | Dynamic Exogenous  | National | $\text{€}/kWh$
| Emission factor | Dynamic Exogenous | National | $tCO2eq/kWh$
| Unit cost - solar panel | Dynamic Endogenous | National | $\text{€}/kW$

: Energy system model's properties review. {#tbl:es-properties}