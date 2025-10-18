---
layout: default
title: The BWF Problem
---

# Problem description and objective

The Battle of the Water Futures takes place in a not so ficticious world, with a blend of real data and assumptions.
The BWF is concerned with the optimal planning and operation of multiple regional water distribution systems in a national landscape.
It is based on The Netherlands where KWR is located and instead of the current water ulitities division, one independent water utility is assumed for every province. 
Each water utility will need to prepare a masterplan for at least the **next 25 years** and run the operations of their systems.
Competitors will also make some decision regarding national and regional policies, like budget allocation and price increase.
Various information about the current status of the system (network model, prices, demands, population, etc) are made available, consult DATA AVAILABLE page.
Together wit hthe current status, future projections of the relevant drivers (e.g., population, electtricity shares) can be used to formulate the plan. 
The masterplan consist of a series of interventions, policy decisions and operations that can be applied over the years of the planning horizon, this effectively requires staged design and applied phased interventions.

Once the masterplan is completed, the utilities will start following it and operate and mantain the system accordingly to the specifications.
The world will evolve, uncertainties will be realized (shown) and, hopefully, they will be able to fullfill their primary objective: satisfying the consumers water demand with adequate level of service.

During the time when the masterplan is being executed, several key performance indicator are extracted, from the main finance health and reliability (level of service), to secondary objectives like GHG emissions and fairness.
The water utilities will also have access to data about their networks, such as pressures, demands, power consumptions etc

After **25 years**, the utilities will have a chance to update their masterplan, adapting it based on the new acquired informaiton (now history), and the cycle will repeat (plan, execute, observe).

Both interventions and input parameters can be assumed to be deep uncertaintites, meaning that only approximate definition of their future evolution are provided and that no probability (or wrong ones) are associated with the realisation of each scenario. Everything should be regarded only as an indication, to the best of the current knowledge, made by some experts.
Take these as an example:
- the time to construct a desalination plant: it can be defined between 5 and 10 years. Once construction starts its actual implementation time can be anything between those bounds
- population evolution: projections of population in the country wille be provided with a mean value and upper and lower bounds with various uncertainty level. However, how this parameter will evolve no one can know
Behind the scenes we blend experts opinions with a dynamic model with tunable parameters to to generate the synthetic time serieses that will be the input of this system.

Planning horizon: free, but at least 25 years 
Interventions resolution (masterplan intervnetions timestep): year/quarter
Stage horizon/masterplan update period: 25 years
Hydraulic simulation timestep: 1 hour
Every other parameter will have its own resolution as defined in the input files.
Simulation approach: every day for the whole stage
> if too computationally demanding (>20 minute per solution), we reduce the number of days mantaining the same timestep, i.e., 1 week representative of each month or 1 week representative of each quarter/season. 

Definitions
Deep uncertainties
Staged Design
Robust planning 
Flexible planning 
Adpative planning

# Details

- [Network options](./network-options)
- [Scenarios and input data](./scenarios)
- [Metrics and KPIs](./metrics)
x
---

## Motivation behind the decisions:


### Why the Netherlands?

Because it is a rich western country with a lot of publicly available data, mild weather that could be significantly influenced by climate change, and an overexploitation of groundwater resources. Moreover, part of the organiser team (KWR) is based there, which makes access to data and expert knowledge easier.

### Why national-level distribution system/transport?

Again, due to data availability and privacy reasons. Focusing on a big city or urban context would have required significant participation from a water utility. At this level of detail, information that needs to be protected (such as neighborhood economics) would have made the work more difficult.

### Why a competition over a 100-year horizon?

Because the world has changed so much in the last 100 years that it is nearly impossible to predict what will happen in the next century. Also, the pipe replacement rate of WDS is usually around 1%, meaning that a whole network is replenished after 100 years.

### Why 25-year masterplans/stages?

Because public entities and governments tend to issue long-term bonds (30 years) when planning for large infrastructure projects (e.g., production location, etc.). Even if they plan for 25 years, new plans could be developed sooner (10–15 years); we will see if this assumption holds or changes.

### Why so much uncertainty? Previous battles were more clearly defined in terms of input and parameters.

Because this is the world we live in now. Even in rich countries, water utilities have very tight budgets and can't focus only on day-to-day operations. Becoming more adaptive in their planning is one way water utilities can become more reliable.

### Why so many objectives when only one solution can be implemented?

Because cost/finances to fulfill the required level of service are not the only objective anymore. Greenhouse gas emissions from system operations and construction are already being considered, and aspects like generational fairness and living in symbiosis with nature are gaining momentum. We don't know how these priorities could change for society in the next 100 years. Every team will give different priorities to the various aspects, just as different management teams can give different priorities (between utilities, and over time, between subsequent management teams at the same water utility).
