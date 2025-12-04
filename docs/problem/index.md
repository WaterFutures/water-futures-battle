---
layout: default
website_title: The BWF Problem
prev_page_url: /participating.html
next_page_url: /problem/system-description/
website_page_authors:
  - D. Zanutto
---

# Problem Description

The Battle of the Water Futures (BWF) problem focuses on a hypothetical national drinking water grid of the Netherlands.
The system structure (demand nodes, sources, and links), available interventions (e.g., pipes, treatment plants), and exogenous drivers (e.g., population, climate) are based on publicly available data about the Dutch context, supplemented by assumptions or insights from other regions as needed.

The main objective of the BWF is to keep the system operational until the end of the century, thereby preventing bankruptcy while fulfilling the required service requirements in each water utility.
Secondary objectives include reducing emissions toward climate neutrality and ensuring fairness across regions and generations.
To achieve these goals, the country's water utilities come together to develop a national masterplan, which they agree to update every 25 years.

The masterplan specifies the interventions to be applied each year, both at the national level (e.g., connecting independent water utilities) and at the individual utility level (e.g., opening new sources).
The masterplan does not need to include the replacement of ageing components (pipes and pumps), as these are automatically replaced when they reach their end of life.
However, to manage this uncertainty, utilities can either schedule replacements in advance or allow components to age naturally and account for replacement costs in the budget.
The masterplan also defines the national and regional policies and whether they are revised during the planning period (note: while interventions must be specified annually, policies can be set initially and remain as they are until amended in the plan).

To prepare the masterplan, information on the current system status is made available, including network models, prices, demands, population, and other relevant parameters.
Future projections of key drivers (e.g., population growth, climate trends) are also provided to complement system knowledge.
However, these scenarios are based on current expert knowledge and should not be treated as precise forecasts as these variables are generally deep uncertainties of the system.

Examples of deep uncertainties include:

- Desalination plant construction time: Planners are confident it can be built in 5 years, but acknowledge that delays could extend completion to 10 years.
- Population evolution: Population is expected to follow the mean values or remain within the upper and lower bounds described by the national statistics agency. However, major external events, such as war or mass migration driven by climate catastrophes, could push evolution beyond these ranges.

Behind the scenes, expert opinions are combined with dynamic models to generate the synthetic time series that drive system evolution.
At each timestep, EPANET hydraulic simulations verify the network's physical capability to transfer water and meet demands under the proposed interventions and operating conditions.

Once the masterplan is defined, utilities begin following it, operating and maintaining their systems according to its specifications.
Around them, the world evolves and uncertainties unfold.
After 25 years, utilities reconvene to update their plan.
All system information is updated, and the performance over the past 25 years along with observed variables can be used to revise or completely redraw the masterplan.
This cycle—plan, execute, observe, adapt—repeats for three rounds, testing the utilities' ability to manage both short-term operations and long-term strategic planning under deep uncertainty.
