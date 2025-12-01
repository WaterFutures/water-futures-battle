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

We will model the following three different parameters for the evaluation of the water distribution networks.


| Property | Type | Scope | Unit |
| :--- | :--- | :--- | :--- |
| Elecricity price | Dynamic Exogenous  | National | €/kWh
| Greenhouse gas emission by electricity production | Dynamic Exogenous | National | tCO2eq/kWh
| Unit costs for solar pv panel | Dynamic Endogenous | National | €/kW 

: Energy system model's properties review. {#tbl:es-properties}

We assume yearly changes in electricity price roughly influenced by inflation but with a high uncertainty. Due to different electricity demands during the day, the electricity price will change hourly following a daily pattern with peaks during the working hours and lows during the night. For each kWh obtained from the power suppliers we will estimate the produced greenhouse gas emissions from generating the energy. This value may change yearly due to different compositions of the electricity generation. The alternative to buying electricity from a power supplier is to generate it from solar pv panels that also come with specific costs. These costs may change yearly due to more efficiency and different climate conditions. 

The action the participants can do is to install solar pv panels on pump stations at any time, that will have a lifespan of 25 years. The main objective is to achieve low electricity costs in the water distribution network. As a secondary objective the greenhouse gas emissions produced by the water distribution network should be minimized.

