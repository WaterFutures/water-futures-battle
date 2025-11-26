---
layout: default
website_title: Non Revenue Water Model
parent: /problem/system-description/municipalities
parent_title: Municipalities
prev_page_url: /problem/system-description/municipalities/water-demand.html
next_page_url: /problem/system-description/sources.html
website_page_authors:
  - S. Alvisi
  - A. Artelt
  - D. Eliades
  - D. Zanutto
---

#### Non-Revenue Water Model

Our modelling of non-revenue water (NRW) relies on the average age of the pipe infrastructure in a municipality. Based on this average age, the municipality gets assigned to one of five possible classes (A - E) as follows:

| Age in years | Class | Lower and upper bound of NRW demand in m^3/day |
| ------------ | ------| ---------------------------------------------- |
| 0 - 25       | A     | (0, 12)                                        |
| 25 - 43      | B     | (12, 20)                                       |
| 43 - 54      | C     | (20, 35)                                       |
| 54 - 60      | D     | (35, 55)                                       |
| > 60         | E     | (55, inf)                                      |

Each class is associated with a distribution of non-revenue water (NRW)demands (e.g., leakages), from which we sample to generate the total demand, consisting of the normal demand + NRW demand. Notably, the NRW demand is different for each class -- i.e., older systems suffer from more leaks and therefore have a higher NRW demand. The distribution of NRW demands per class and km of pipes is illustrated in the following figure.

![leak-demands](../../../assets/img/leak_demand.png)

The total number of km of pipes in a given municipality is linked to its population size. Here, we use a linear relationship between the population size and the km of pipes, also illustrated in the following Figure:

$$
km\_pipes = 57.7 * population\_in\_10k
$$

![pop-pipes](../../../assets/img/pop_to_km.png)
