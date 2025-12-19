---
layout: default
website_title: Economy and financing
parent: /problem/external-drivers/
parent_title: External drivers
prev_page_url: /problem/external-drivers/energy-system.html
next_page_url: /problem/system-interventions/
website_page_authors:
  - P. Samartzis
  - D. Zanutto
---

###  Economy

#### Inflation Dynamics

Inflation captures the year-over-year change in the general price level.
In the BWF, it affects all costs equally except energy prices, which follow different dynamics [see @sec:energy-model].

As inflation compounds over time, it can substantially erode water utilities' purchasing power and alter the financial viability of capital-intensive interventions.
While inflation is an exogenous macroeconomic variable beyond the direct control of water utilities, competitors can adopt strategic responses: front-loading major investments to lock in current prices, or stress-testing their masterplan against multiple inflation scenarios to ensure robustness.

In the absence of reliable long-term inflation forecasts, a reasonable baseline assumption is the central bank's target rate (e.g., 2% for the European Central Bank).

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| Inflation rate | Dynamic Exogenous  | National | 

: Inflation's properties review. {#tbl:ei-properties}

Note that wherever unit prices are given only in base-year terms (e.g., only in the value in year 2000 is present in the input files), their value in year $y$ ($C(y)$) is obtained by multiplying by the cumulative inflation index

$$
C(y) = C(0) \cdot \prod_{\tau = 1}^{y} \bigl(1 + \pi(\tau)\bigr)
$$

where $C(0)$ is the base-year unit price and $\pi(y)$ is the inflation rate in year $y$.

#### Budget Allocation 

A national budget (predefined over the planning horizon) is distributed annually across utilities to fund infrastructure interventions and operational expenses.

Competitors must decide how to distribute this budget among utilities in every year.
Budget distribution can follow several principled rules: proportional allocation to population size; inverse-proportional schemes favuoring smaller regions; income-based allocations reflecting socioeconomic considerations; inverse-proportional schemes favuoring less wealthy regions; or fully customised schemes. 

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| National total budget | Static | National | €/year |
| Budget allocation policy | Option | Water utility | 

: Budget allocation model's properties review. {#tbl:ea-properties}

#### Water Pricing {#sec:water-pricing}

Water utilities generate revenue selling water to three types of customers: residential users, businesses, and, possibly, other water utilities.
Residential and commercial customers are billed using a two-part pricing scheme: a fixed service charge ($\text{€}/year$) and a volumetric charge based on consumption ($\text{€}/m^3$).
For simplicity, both retail customer types face identical rates within each utility (with also no differentiation by income class or other categories).
Water transactions between utilities, however, use only a volumetric charge based on the net exchange at the end of the year.

Thus, the total revenue for a water utility $w$ in year $y$ is:

$$
REV_w(y) = \sum_{m \in \mathcal{M}_w} P_w^\text{fixed}(y) + P_w^\text{variable}(y) \cdot Q^\text{BIL}_m(y) + \sum_{w' \in \mathcal{W}^-} P_w^\text{sell}(y) \cdot Q^{w'}_w(y)
$$

where $P_w^\text{fixed}(y)$ and $P_w^\text{variable}(y)$ are the fixed and volumetric components of the retail water price, $Q^\text{BIL}_m$ is the delivered billable demand in municipality $m$, $\mathcal{M}_w$ is the set of municipalities in water utility $w$, $P_w^\text{sell}(y)$ is the volumetric charge for inter-utility water sales, and $Q^{w'}_w$ is the net volume of water sold to utility $w'$ ($\mathcal{W}^-$ is the set of water utilities excluding utility $w$).

Note that if a water utility has a negative net exchange with another utility, that will be regarded as a production cost.

Participants must decide the water pricing adjustment strategy.
They can either let all three quantities adjust according to inflation, or define a custom policy by specifying the yearly percentage increase for each of them independently.

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| Fixed tariff component (service charge) | Dynamic Endogenous | Water utility | €/year
| Volumetric tariff component | Dynamic Endogenous  | Water utility | $\text{€}/m^3$
| Water price for other utilities | Dynamic Endogenous | Water utility | $\text{€}/m^3$ 
| Water pricing adjustment policy | Option | Water utility | 

: Water price model's properties review. {#tbl:et-properties}


#### Bond Issuance {#sec:bonds}

Whenever a water utility is unable to cover its expenditures in a given year, it finances the resulting deficit by issuing nationally backed bonds.
Bond dynamics are simplified for tractability.

Bonds are automatically generated with a principal amount sufficient to cover the utility debt in that year.
Specifically, the bond amount ($\mathrm{amount}_i$) is set as a multiple of the debt (e.g., $\mathrm{amount}_i=\kappa \cdot \mathrm{debt}_w(y)$ where $\kappa \in [1,2.5]$) to ensure the utility maintains a cash surplus rather than operating at exactly zero balance.
Bonds are also characterised by a maturity of $M$ years, determining when the bond principal must be repaid, a coupon rate ($\mathrm{coupon}_i$), which determines the interest payments due each year and a yield to maturity ($\mathrm{yield}_i$), which determines the price of the bond ($\mathrm{price}_i$). The price of the bond at issuance will determine the actual amount raised: $\mathrm{amount_raised}_i = \mathrm{price}_i * \mathrm{amount}_i.$
Each year, the utility must repay the sum of principal amounts of all bonds reaching maturity plus the annual interest payments:

$$
\begin{aligned}
&\text{PRI}_w(y) = \sum_{i \in \mathcal {B}_w(y) : y=M} \mathrm{amount}_i \\
&\text{INT}_w(y) = \sum_{i \in \mathcal{B}_w(y)} \mathrm{amount}_i \cdot \mathrm{coupon}_i
\end{aligned}
$$

where $i$ indicates the i-th bond, $\mathcal{B}_w(y)$ is the set of bonds active for water utility $w$ in year $y$ and $\mathcal {B}_w(y) : y=M$ the subset of bonds reaching maturity $M$.

The i-th bond’s coupon, yield and price are given by:

$$
\mathrm{coupon}_i=r_f + $\hat{\pi}(y=t)$,
$$

$$
\mathrm{yield}_i=\mathrm{coupon}_i + a \cdot (1-d(y=t)),
$$

$$
\mathrm{price}_i=\sum_{y=1}^M \frac{\mathrm{coupon}_i}{(1+\mathrm{yield}_i)^y} + \frac{\mathrm{amount}_i}{(1+\mathrm{yield}_i)^M},
$$

where $t$ is the issaunce year, $r_f$​ is the risk-free rate (long-term government yield), $\hat{\pi}(y=t)$ is the inflationary expectations at issuance year, $a$ is the sensitivity to investor demand, and $d(y=t)$​ is the uncertain demand factor for bond $i$ at issuance year.

Strong investor demand (d(y) > 1.0) increases $\mathrm{amount_raised}_i$ (cheaper borrowing), while weak demand (d(y) < 1.0) decreases it.
This simulates real-world bond pricing where investor appetite determines borrowing costs and introduces uncertainty to the utilities budgetting.

While utilities cannot directly control bond yields, they can anticipate debt accumulation through scenario analysis and adopt strategies that maintain financial sustainability.
For instance, utilities may design pacing of interventions to minimize borrowing, or evaluate alternative interventions that reduce the likelihood of large bond issuances during periods with unfavorable yield conditions.

The complete list of the bond model properties can be seen in @tbl:eb-properties, while the actual values for these variables can be inspected within the data files, which are mapped in Appendix A.

| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| Balance | Dynamic Endogenous | Water utility | €
| Bond amount to debt ratio | Static | National | 
| Bond amount | Dynamic Endogenous | Bond | €
| Bond issue date | Dynamic Endogenous | Bond | 
| Bond maturity | Static | National | years |
| Bond yield | Dynamic Endogenous | Bond | 
| Bond price | Dynamic Endogenous | Bond | 
| Risk free rate | Static | National | 
| Inflationary expectations | Static | National | 
| Sensitivity | Static | National |
| Demand factor | Uncertain | National | 

: Bonds model's properties review. {#tbl:eb-properties}
