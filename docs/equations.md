
# Evaluation Metrics

## 2.4.1 Metric 1: Total System Cost

One of the objectives is to minimise the **Total System Cost ($C_{total}$)** over the planning horizon $\mathcal{T}$. In this context, the metric represents the aggregate **actual (nominal) price** paid over time, accounting for the effect of inflation on base costs.

The total cost is calculated by inflating the annual base-year costs by the cumulative inflation index:

$$
C_{total} = \sum_{t \in \mathcal{T}} [K_{\text{cap}}(t) + \mathrm{OPEX}(t) + C_{\text{bonds}}(t)]
$$

where $C_{total}$ is the total system cost in year $t$, **$K_{\text{cap}}(t)$** is the total capital expenditures, **$\mathrm{OPEX}(t)$** the total operational expenditures, and **$C_{\text{bonds}}(t)$** the cost of bond coupons in year $t$.

Capital costs $K_{\text{cap}}$ are incurred in the year an intervention is executed:

$$
K_{\text{cap}}(t) = K_{\text{sources}}(t) + K_{\text{pipes}}(t) + K_{\text{pumps}}(t) + K_{\text{solar}}(t) + K_{\text{leak}}(t)
$$
where $K_{\text{sources}}(t)$ is the construction cost of new water production sources, $K_{\text{pipes}}(t)$ the installation cost for new network connections, $K_{\text{pumps}}(t)$ the installation cost for new or replacement pumps,  $K_{\text{solar}}(t)$ the installation cost for PV panels at pumping stations, and $K_{\text{leak}}(t)$ the budget allocated to non-revenue water (NRW) reduction policies.

Operational costs ($\mathrm{OPEX}$) are calculated annually as the sum of:

$$
\mathrm{OPEX}(t) = \mathrm{OPEX}_{\text{sources}}(t) + \mathrm{OPEX}_{\text{pumps}}(t)
$$

$\mathrm{OPEX}_{\text{sources}}(t)$ includes fixed maintenance, volumetric energy and non-energy related costs, and penalties for capacity exceedance, and $\mathrm{OPEX}_{\text{pumps}}(t)$ the net grid electricity costs for pumping (total demand minus onsite PV generation).

> **Note on Uncertainty and Inflation:**  
> Wherever unit prices are given only in base-year terms, their value in year $t$ is obtained by multiplying by the cumulative inflation index
> $$
> I(t) = \prod_{\tau = 1}^{t} \bigl(1 + \pi(\tau)\bigr), \qquad I(0) = 1,
> $$
> where $\pi(t)$ is the inflation rate in year $t$.  
> The inflation rate $\pi(t)$ is a dynamic exogenous uncertainty. Future inflation trajectories are unknown and outside the utilities' control, so participants must design masterplans that remain financially robust under different inflation scenarios.

## 2.4.2 Metric 2: Total GHG emissions

The total GHG emissions ($\mathrm{GHG}_{total}$) over the planning horizon are:

$$
\mathrm{GHG_{total}}
= \sum_{t \in \mathcal{T}} [\mathrm{GHG}_{\text{emb}}(t)
+ \mathrm{GHG}_{\text{op}}(t)] 
$$

where $\mathrm{GHG}_{\text{emb}}(t)$ the embedded (construction) emissions, and $\mathrm{GHG}_{\text{op}}(t)$ the operational emissions from electricity use in year $t$.

Only new pipes have embedded GHG emissions. The embedded emissions in year $t$ are:

$$
\mathrm{GHG}_{\text{emb}}(t)
=  \sum_{j \in J_{\text{new-pipe}}}
\mathbf{1}_{\{t_j = t\}} \,
EF^{\text{pipe}}(D_j, M_j, t) \,
L_j
$$

where $J_{\text{new-pipe}}$ is the set of all new pipe interventions, $t_j$ is year when pipe $j$ is built, $\mathbf{1}_{\{t_j = t\}}$ is 1 if pipe $j$ is built in year $t$, 0 otherwise, $D_j$: diameter of pipe $j$, $M_j$: material of pipe $j$, $EF^{\text{pipe}}(D_j, M_j, t)$ dynamic emission factor for a new pipe installed in year $t$ [$tCO_2eq/m$]. This value accounts for changes in material carbon intensity over time. $L_j$ is the length of pipe $j$.

The operational emissions are calculated based on the total electricity purchased from the grid, covering both water treatment (sources) and transport (pumping).

$$
\mathrm{GHG}_{\text{op}}(t) = \bigl[ E_{\text{src}}(t) + E_{\text{pump}}(t) \bigr] \cdot EF^{\text{el}}(t)
$$
with $EF^{\text{el}}(t)$ the grid electricity emission factor in year $t$ ($tCO_2eq/kWh$).

Energy consumed for water treatment at active sources:

$$
E_{\text{src}}(t) = \sum_{s \in S_{\text{act}}(t)} c_s^{E}(t) \cdot V_s(t)
$$

where  $c_s^{E}(t)$: Energy consumption per unit of water produced at source $s$ ($kWh/m^3$) and $V_s(t)$: Volume of water produced at source $s$ in year $t$.

Energy consumed for water transport, net of local solar generation:

$$
E_{\text{pump}}(t) = \sum_{s \in S} E^{\text{grid}}_s(t)
$$

where $E^{\text{grid}}_s(t)$ is the net grid electricity demand of pumping station $s$ (total pump demand minus PV generation).

> **Note on Uncertainty:** The emission factors for both grid electricity ($EF^{el}$) and pipe manufacturing ($EF^{pipe}$) are dynamic exogenous uncertainties. The future decarbonization rate of the national grid and technological improvements in material production are unknown, requiring robust planning against different environmental scenarios.

## 2.4.3 Metric 3: Service Reliability

-

## 2.4.4 Metric 4: Affordability Fairness
- 

----


# Equations Per Chapter

## 2.1.3 Water Sources

Capital investment for new sources at year \(t\):

$$
K_{\text{sources}}(t)
= \sum_{s \in S_{\text{new-src}}}
\mathbf{1}_{\{t_s = t\}} \,
c_{\text{unit}}^{\text{source}}(t) \,
\text{Capacity}_{\text{nominal},s}
$$

where:

- $S_{\text{new-src}}$: set of all sources that are newly built (activated).  
- $t_s$: year when source $s$ is built.  
- $\mathbf{1}_{\{t_s = t\}}$: 1 if source $s$ is built in year $t$, 0 otherwise.  
- $c_{\text{unit}}^{\text{source}}(t)$: unit construction cost of sources in year $t$ ($\text{€}/m^3/day$).  
- $\text{Capacity}_{\text{nominal},s}$: nominal capacity of source $s$ ($m^3/day$).
Here, $S_{\text{new-src}}$ denotes the set of all newly activated sources, and $t_s$ is the year when source $s$ is built. The indicator $\mathbf{1}_{\{t_s = t\}}$ is 1 if source $s$ is built in year $t$ and 0 otherwise. The term $c_{\text{unit}}^{\text{source}}(t)$ represents the unit construction cost of sources in year $t$ (€/m³/day), while $\text{Capacity}_{\text{nominal},s}$ is the nominal capacity of source $s$ (m³/day).

Operational costs for water sources at year \(t\):

$$
\mathrm{OPEX}_{\text{sources}}(t)
= \sum_{s \in S_{\text{act}}(t)}
\Big[
F_s(t)
+ p^{\text{el}}(t)\, c_s^{E}(t)\, V_s(t)
+ c_s^{\text{NE}}(t)\, V_s(t)
+ c_s^{\text{NE}}(t)\, (m_s - 1)\, V_s^{\text{extra}}(t)
\Big]
$$

with

$$
V_s^{\text{extra}}(t)
= \max\bigl(V_s(t) - V_s^{\text{permit}}(t),\, 0\bigr),
\qquad
V_s^{\text{plan}}(t)
= f_s^{\text{target}}\, \text{Capacity}_{\text{nominal},s}\, N_{\text{days}}(t).
$$

$S_{\text{act}}(t)$ is the set of active sources in year $t$, and $F_s(t)$ represents the fixed operational cost of source $s$ in year $t$ (covering personnel, planned maintenance, taxes, fixed fees, and overheads). $V_s(t)$ is the total annual production volume of source $s$. The variable $c_s^{E}(t)$ denotes the energy use per unit of water for source $s$, while $p^{\text{el}}(t)$ is the average electricity price in year $t$. $c_s^{\text{NE}}(t)$ is the non-energy volumetric cost (chemicals, filters, etc.), and $m_s$ is the multiplier for extra non-energy costs when operating above planned capacity. $\text{Capacity}_{\text{nominal},s}$ refers to the nominal production capacity, and $f_s^{\text{target}}$ is the capacity target factor (ideal loading level). Finally, $N_{\text{days}}(t)$ is the number of operating days in year $t$, $V_s^{\text{plan}}(t)$ represents the planned annual production volume, and $V_s^{\text{extra}}(t)$ is the production above that planned volume.

## 2.1.4 Pumping Stations

Total pump CAPEX in year \(t\) is the sum of new installations and replacements:

$$
K_{\text{pumps}}(t)
= K_{\text{pumps,new}}(t) + K_{\text{pumps,repl}}(t)
$$

Pumps for new sources are calculated as:

$$
K_{\text{pumps,new}}(t)
= \sum_{s \in S_{\text{new-src}}}
\mathbf{1}_{\{t_s = t\}} \,
c_{\text{unit}}^{\text{pump}}(o_s, t) \,
N_{\text{pump},s}
$$

Here, $S_{\text{new-src}}$ is the set of newly opened sources, and $t_s$ is the year source $s$ is opened. The indicator $\mathbf{1}_{\{t_s = t\}}$ equals 1 if the source opens in year $t$ and 0 otherwise. $o_s$ represents the pump option chosen for source $s$, $c_{\text{unit}}^{\text{pump}}(o_s, t)$ is the cost of one pump of option $o_s$ in year $t$, and $N_{\text{pump},s}$ is the number of pumps installed.

Replacements use the same pump option $o_s$ as originally chosen for source $s$:

$$
K_{\text{pumps,repl}}(t)
= \sum_{s \in S}
c_{\text{unit}}^{\text{pump}}(o_s, t) \,
N_{\text{pump},s}^{\text{repl}}(t)
$$

$S$ denotes the set of all sources with pumps (existing and new), and $N_{\text{pump},s}^{\text{repl}}(t)$ is the number of pumps at source $s$ that are replaced in year $t$ (which is 0 if no replacement occurs).

Operational costs for pumps at year \(t\) are purely electricity-driven:

$$
\mathrm{OPEX}_{\text{pumps}}(t)
= \sum_{s \in S}
p^{\text{el}}(t)\, E^{\text{grid}}_s(t)
$$

with

$$
E^{\text{grid}}_s(t)
= \max\bigl(E^{\text{pump}}_s(t) - E^{\text{PV}}_s(t),\, 0\bigr)
$$

Here, $S$ is the set of all sources with pumping stations, and $p^{\text{el}}(t)$ is the electricity price in year $t$. $E^{\text{pump}}_s(t)$ represents the annual electricity demand of the pumping station at source $s$ (derived from hydraulic/energy simulation without PV). $E^{\text{PV}}_s(t)$ is the annual electricity generated by the PV installed at source $s$, computed based on installed capacity $C_{\text{PV}}(s, t)$ and its lifetime. Finally, $E^{\text{grid}}_s(t)$ denotes the net grid electricity use, which is never negative.

## 2.1.5 Connections

Capital investment for new pipes at year \(t\):

$$
K_{\text{pipes}}(t)
= \sum_{j \in J_{\text{new-pipe}}}
\mathbf{1}_{\{t_j = t\}} \,
c_{\text{unit}}^{\text{pipe}}(D_j, M_j, t) \,
L_j
$$

where $J_{\text{new-pipe}}$ is the set of all new pipe interventions. $t_j$ indicates the year when pipe $j$ is built, and $\mathbf{1}_{\{t_j = t\}}$ is 1 if that occurs in year $t$, 0 otherwise. $D_j$ and $M_j$ represent the diameter and material of pipe $j$, respectively. The term $c_{\text{unit}}^{\text{pipe}}(D_j, M_j, t)$ is the unit construction cost of such a pipe in year $t$ (€/m), and $L_j$ is the length of pipe $j$.

## 2.2.2 Energy System

Capital investment for solar PV at year \(t\):

$$
K_{\text{solar}}(t)
= c_{\text{unit}}^{\text{PV}}(t) \,
\sum_{s \in S_{\text{PV}}}
C_{\text{PV}}^{\text{new}}(s, t)
$$

Here, $S_{\text{PV}}$ represents the set of sources where PV can be installed (i.e., those with an associated pumping station suitable for PV). $c_{\text{unit}}^{\text{PV}}(t)$ is the unit cost of solar PV panels in year $t$ (€/kW), and $C_{\text{PV}}^{\text{new}}(s, t)$ is the new PV capacity (kW) installed at source $s$ in year $t$.

## 2.2.3.1 Bond financing costs at year \(t\)

The coupon rate in year \(t\) is given by:

$$
\text{coupon}(t)
= r_f(t) + cs(t) + a(t)\,\bigl(1 - d(t)\bigr)
$$

The annual bond cost in year \(t\) is:

$$
C_{\text{bonds}}(t)
= \text{coupon}(t)\, P_{\text{issue}}(t)
$$

where $r_f(t)$ is the risk-free rate, $cs(t)$ is the base credit spread, and $a(t)$ is the spread sensitivity to demand in year $t$. The variable $d(t)$ represents the investor demand factor (between 0.8 and 1.2). $\text{coupon}(t)$ is the resulting coupon rate of the bond portfolio. $P_{\text{issue}}(t)$ denotes the total principal of all bonds outstanding in year $t$ (the amount borrowed but not yet repaid), and $C_{\text{bonds}}(t)$ is the interest paid on bonds in year $t$.

## 2.3.1.2 Non-Revenue Water Interventions (water utility)

Non-revenue water (leakage reduction) spending at year \(t\):

$$
K_{\text{leak}}(t)
= \sum_{u \in U} \beta_u(t)\, B_u^{\text{avail}}(t)
$$

Here, $U$ is the set of all water utilities. $\beta_u(t)$ is the share (fraction) of the yearly budget of utility $u$ spent on non-revenue water reduction in year $t$ (a decision variable, e.g., between 0 and 1). $B_u^{\text{avail}}(t)$ represents the total budget available to utility $u$ in year $t$, and $K_{\text{leak}}(t)$ is the total amount spent in year $t$ on improving pipe infrastructure to reduce non-revenue water, summed over all utilities.