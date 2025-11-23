---
layout: default
title: Non Revenue Water Model
parent: /problem/system-description/municipalities
parent_title: Municipalities
authors:
  - A. Artelt
  - D. Eliades
  - D. Zanutto
---

Regarding the cost of non-revenue-water reduction, we can use something like 500-800 Euros per m3 per day. In the reference below (page 25) Dublin estimated the cost to 750USD, whereas in Asia they may achieve similar targets with 250-500 USD. An example calculation is provided below. 
https://documents1.worldbank.org/curated/en/385761468330326484/pdf/394050Reducing1e0water0WSS81PUBLIC1.pdf

Regarding desalination in Cyprus is ranges between 3.21-3.75 kwh/m3. There is a thermodynamic limit of 1.06kWh/m3. Ideal energy consumption is 1.56kWh/m3, accordig to Science paper below (p 715)
https://albertsk.org/wp-content/uploads/2012/08/science-2011-elimelech-712-71.pdf

Probably there are some economic effects here Pano @pansos(I was not very familiar with it, howeverthe authors of the paper are well known in leakage reduction, not sure if this is relevant)
https://www.leakssuitelibrary.com/wp-content/uploads/2020/11/LambertLalondeHalifaxSep2005.pdf

Example Calculations
1) Inputs
Target leakage reduction: ΔQ = 5,000 m³/day
Unit cost (efficient project): c = 250 $/ (m³/day)
O&M = 5% of CAPEX per year
Variable water value avoided (production + energy + chemicals): v = 0.60 $/m³
Analysis: n = 10 years, discount r = 6%
2) CAPEX from unit cost
CAPEX = c · ΔQ = 250 × 5,000 = 1,250,000 $
3) Annual water saved and avoided cost
Annual volume saved = ΔQ · 365 = 5,000 × 365 = 1,825,000 m³/yr
Annual avoided variable cost = v · volume = 0.60 × 1,825,000 = 1,095,000 $/yr
4) Annual O&M
O&M = 5% · CAPEX = 0.05 × 1,250,000 = 62,500 $/yr
5) Simple payback
Payback = CAPEX / (avoided cost − O&M)
= 1,250,000 / (1,095,000 − 62,500)  ≈1.21 years


# Modelling of Non-Revenue Water

Our modelling of non-revenue water relies on the average age of the pipe infrastructure in a municipality. Based on this average age, the municipality gets assigned to one of five possible leak classes (A - E) as follows:
| Age in years | Leak class |
| ------------ | ---------- |
| 0 - 25       | A          |
| 25 - 43      | B          |
| 43 - 54      | C          |
| 54 - 60      | D          |
| > 60         | E          |

Each leak class is associated with a distribution of leak demands, from which we sample to generate the total demand, consisting of the normal demand + leak demand. Notably, the leak demand is different for each leak class -- i.e., older systems suffer from more leaks and therefore have a higher leak demand. The distribution of leak demands per leak class is illustrated in the following figure.
![leak-demands](leak_demand.png)
