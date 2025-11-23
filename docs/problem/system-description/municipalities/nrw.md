---
layout: default
website_title: Non Revenue Water Model
parent: /problem/system-description/municipalities
parent_title: Municipalities
prev_page_url: /problem/system-description/municipalities/water-demand.html
next_page_url: /problem/system-description/sources.html
website_page_authors:
  - A. Artelt
  - D. Eliades
  - D. Zanutto
---

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
![leak-demands](../../../assets/img/leak_demand.png)
