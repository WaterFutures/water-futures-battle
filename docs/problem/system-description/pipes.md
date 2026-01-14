---
layout: default
website_title: Pipes
parent: /problem/system-description/
parent_title: System Description
prev_page_url: /problem/system-description/pumping-stations.html
next_page_url: /problem/external-drivers/
website_page_authors:
  - L. Tsiami
  - D. Zanutto
---

### Connections (Pipes) {#sec:connections}

Within the BWF, there is a distinction between connections and pipes.
Connections are the entities that define the possible links between the network's nodes, while pipes are the actual physical elements installed to transport water.
This distinction models the fact that different pipes can be installed on the same connection at different points in time.
However, duplicate pipes are not allowed on the same connection.

Similarly to pumps, participants can install new pipes on any unused connection, or replace existing pipes on connections that already have one.
Selection must occur from a predefined set of pipe options.
Pipe options are characterized by material, hydraulic properties, installation cost, and associated carbon emissions, with a detailed overview available in @tbl:pi-properties and actual values provided in the data files mapped in Appendix A.

Whether replacing old pipes or being added in a connection, the capital investment associated with the installation of pipes in water utility $w$ at year $y$ is:

$$
K^\text{pipes}_w(y)
= \sum_{j \in \mathcal{J}_{w}} \mathbf{1}_{\{\tau_j = y\}}\cdot c^\text{pipe}(\theta_j, y) \cdot L_j
$$ {#eq:pipes-capital-cost}

where $\mathcal{J}_{l}$ is the set of all pipes within water utility $w$, $j$ the pipe index, $\tau_j$ is the pipe installation time, $\mathbf{1}_{\{\tau_j = y\}}$ is an indicator function equal to 1 if the installation happened in year $y$ (0 otherwise), $c^\text{pipe}(\theta_j, y)$ the unit cost for the selected pipe option $\theta_j$, and $L_j$ is the length of pipe $j$.

The Darcy friction factor of a new pipe is provided for every option.
However, the rate at which the friction factor increases over time (decay rate) is uncertain and is bounded between minimum and maximum values.

Associated carbon emissions (in kg CO2-eq per meter of pipe installed) are also provided.
These emission factors may change over time due to technological advancements.

Connections are either completely within a province (intra-province) or shared between provinces (inter-province).
The complete lists of intra-province and inter-province connections are included in the data files mapped in Appendix A.
The capital cost for inter-provincial pipes is shared equally between the water utilities operating in the connected provinces (@eq:pipes-capital-cost is used but the pipe's length is half).

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| Identifier | Static | Connection |
| Node A | Static | Connection |
| Node B | Static | Connection | 
| Type | Static | Connection |
| Distance | Static | Connection | m
| Pipe option | Decision | Connection |
| Pipe installation date | Decision | Connection |
| (Minor loss coefficient)  | set to 0 | 

: Connections' properties review. {#tbl:cn-properties}

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| Identifier | Static | Pipe option |
| Diameter | Static | Pipe option |
| Material | Static | Pipe option | 
| Darcy friction factor - new pipe | Static | Pipe option | 
| Darcy friction factor - decay rate | Static [Uncertain] | Pipe option | $years^-1$
| Darcy friction factor - existing pipe | Dynamic endogenous | Pipe option | 
| Lifetime | Static [Uncertain] | Pipe option | $years$
| Unit cost (new pipe) | Dynamic endogenous | Pipe option | $\text{€}/m$
| Equivalent emissions (new pipe) | Dynamic exogenous | Pipe option | $\text{tCO2eq}/m$ 

: Pipes' properties review. {#tbl:pi-properties}

