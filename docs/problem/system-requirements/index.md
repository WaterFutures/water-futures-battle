---
layout: default
website_title: System Requirements
parent: /problem/
parent_title: Problem
prev_page_url: /problem/system-interventions/
next_page_url: /team.html
website_page_authors:
  - D. Zanutto
---

## System Requirements

This chapter describes the metrics used to evaluate each solution (masterplan) and the overall system performance in the BWF competition.
These metrics define the many-objective space that participants must navigate, covering the main aspects of economic performance, environmental impact, reliability, and fairness.
Importantly, these are evaluation metrics rather than explicit objectives: the competition ranking formula will not be disclosed to participants.
The ranking may use weighted aggregation (with weights potentially changing over time to reflect shifting social priorities) or custom multi-criteria evaluation methods (e.g., selecting only solutions above a reliability threshold before ranking by other criteria). 
However, participants may choose to treat these metrics as objectives in their own optimization processes when developing their masterplans.

### Maintain Financial Viability

Participants must seek to maintain all water utilities in a financially viable state throughout the planning horizon.
While utilities should not pursue profit, they must avoid insolvency.

Each year ($y$), the financial balance $F_w$ of every water utility $w$ is updated based on the following set of equations:

$$
\begin{aligned}
F^*_{w}(y+1) &= F_{w}(y) + \text{NIB}(y) \cdot \alpha_w(y) + \text{REV}_{w}(y) \\
&\quad - \text{CAPEX}_w(y) - \text{OPEX}_w(y) \\
&\quad - \text{WLR}_w(y) -\text{WIC}_w(y) \\
&\quad - \text{INT}_w(y) - \text{PRI}_w(y)\\
\text{debt}_w(y) &= \begin{cases}
-F_{w}^{*}(y+1) & \text{if } F_{w}^{*}(y+1) < 0 \\
0 & \text{otherwise}
\end{cases} \\
F_{w}(y+1) &= F_{w}^{*}(y+1) + \text{PRO}_w(y)
\end{aligned}
$${#eq:water-utility-finance}

The provisional fund balance $F_{w}^{*}(y+1)$ is calculated by accounting for all inflows and outflows:

- $\text{NIB}(y) \cdot \alpha_w(y)$  is the national investment budget allocated for the water utility $w$ (see [@sec:policy-budget-allocation]),
- $\text{REV}_w(y)$ is the water utility's revenue from the billable water demand ([@eq:revenue-water-utility]),
- $\text{CAPEX}_w(y)$ represents all the utility's interventions capital costs (i.e., the sum of [@eq:capex-sources;@eq:pumping-stations-capital-cost;@eq:pipes-capital-cost;@eq:solar-capital-investment]),
- $\text{OPEX}_w(y)$ accounts for all the utility's operational costs (i.e., the sum of [@eq:op-expends;@eq:pumping-stations-opex]),
- $\text{WLR}_w(y)$ is the budget for NRW mitigation (see [@sec:policy-nrw-mitigation]),
- $\text{WIC}_w(y)$ is the cost for imported water ([@eq:water-purchase-utility]),
- $\text{INT}_w(y)$ the utility's interest payments due ([@eq:bonds-payment]), and
- $\text{PRI}_w(y)$ is the principal amount due ([@eq:bonds-payment]).

If the provisional balance is negative, the deficit defines the debt ($\text{debt}_w(y)$), which triggers bond issuance.
The bond proceeds $\text{PRO}_w(y)$ are determined according to [@sec:bonds] and [@eq:bonds-payment;@eq:coupons-price].

The actual fund balance $F_{w}(y+1)$ is obtained by adding the bond proceeds (if any) to the provisional balance, ensuring the fund remains solvent.
Note that while surpluses are carried forward, deficits are always financed through bond issuance automatically ensuring that the fund balance is always positive.

Therefore, evaluation will focus only on the remaining debt at the end of the planning period.
Final debt measures insolvency risk, not financial optimality.
Competitors are free to pursue any financial strategy they deem appropriate, such as minimising costs, adjusting prices to enable expensive solutions, or adopting other innovative approaches.
The many-objective framework ensures balanced evaluation across all dimensions.
In other words, maintaining financial stability is an achievable target; the real challenge is deciding what to sacrifice.

### Minimize GHG Emissions

Participants must keep the masterplan Greenhouse Gas (GHG) emissions to the lowest feasible level.

The GHG emissions for water utility $w$ in year $y$ are:

$$
\mathrm{GHG}_w(y) = \mathrm{GHG}_w^{\text{emb}}(y)
+ \mathrm{GHG}_w^{\text{op}}(y)
$${#eq:ghg-emissions-calc}

where $\mathrm{GHG}_w^{\text{emb}}(y)$ the embedded (construction) emissions, and $\mathrm{GHG}_w^{\text{op}}(y)$ the operational emissions from electricity use.

Only new pipes have embedded GHG emissions.
The embedded emissions in year $y$ are:

$$
\mathrm{GHG}_w^{\text{emb}}(y)
=  \sum_{c \in \mathcal{C}_w}
\mathbf{1}_{c\text{ activated in }y} \cdot
EF_{p_c}(y) \cdot L_c
$${#eq:ghg-emissions-pipes}


where $\mathcal{C}_w$ is the set of connections of water utility $w$^[as described in @sec:connections, we distinguish between connections and pipes], $\mathbf{1}_{c\text{ activated in }y}$ is 1 if connection $c$ installs a new pipe in year $y$, 0 otherwise, $EF_{p_c}(y)$ is the unit emission factor of the connection's selected pipe option $p_c$, and $L_c$ is the connection length.

The unit emission factor $EF_{p}$ for pipe option $p$ depends on the pipe option diameter $Diam_p$ and material $Mat_p$ and may change over time because of technological advancements, i.e., $EF_{p}(y) = EF(Diam_p, Mat_p, y)$.

The operational emissions are calculated based on the total electricity purchased from the grid, covering both water treatment (sources) and transport (pumping).

$$
\mathrm{GHG}_w^{\text{op}}(y) = \sum_{t \in \mathcal{Y}} \bigl[ \sum_{s \in \mathcal{S_w}} E_s(t) \cdot EF_s(t) + \sum_{p \in \mathcal{P}_w} E_p(t) \cdot EF_p(t) \bigr]
$${#eq:ghg-emissions-operational}

where for each timestep $t$ of a year $y$^[$y$ represent the year, while $\mathcal{Y}$ is the collection of timesteps], $E_s(t)$ and $EF_s(t)$ are the energy consumption and the emission factor of source $s$, while $E_p(t)$ and $EF_p(t)$ represent the same quantities for pump $p$.

Pumps energy consumption is retrieved via the EPANET simulations, while the water sources energy consumption is calculated according to @eq:source-energy$.

The emission factors of both entities (pumping stations $EF_p(t)$ and sources $EF_s(t)$) are dynamic and depend on the size and time of production of the behind-the-meter solar panels installation at that location (if no solar is installed, this variable reduces to the constant electricity grid emission factor in year $y$, i.e., $EF^{\text{el}}(y)$ ).

### Maximize Service Reliability

Participants must ensure high service reliability by minimizing unmet water demand.

Service reliability for municipality $m$ in year $y$ is:

$$
Rel_m(y) = 1 - \frac{U_m(y)}{D^{\text{BIL}}_m(y)}
$${#eq:service-reliability}

where $U_m(y)$ is the undelivered demand and $D^{\text{BIL}}_m(y)$ is the billable water demand.

Evaluation will focus on maintaining adequate service levels across all municipalities of each water utility throughout the entire planning horizon.

### Promote Affordability and Equity

Participants must ensure water remains affordable, particularly for lower-income households, while maintaining equitable pricing across municipalities.

The affordability fairness metric represents the fraction of income that a household at the 20th percentile of the income distribution would spend on essential water consumption.
Affordability fairness (lower is better) for water utility $w$ in year $y$ is:

$$
AF_w(y) = \frac{P_w^{\text{fixed}}(y) + P_w^{\text{variable}}(y) \cdot D^{\text{life}}}{ADI_w^{p20}(y)}
$${#eq:affordability}

where $P_w^{\text{fixed}}(y)$ and $P_w^{\text{variable}}(y)$ are the fixed and variable components of water price, $D^{\text{life}}$ is lifeline volume (minimum water required per person), and $ADI_w^{p20}(y)$ is the 20th percentile of disposable income across all households served by the water utility.

Evaluation will focus on minimizing affordability while maintaining reasonable equity across utilities.