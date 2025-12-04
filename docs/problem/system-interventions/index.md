---
layout: default
website_title: System Interventions
parent: /problem/
parent_title: Problem
prev_page_url: /problem/external-drivers/economy-financing.htmnl
next_page_url: /problem/system-requirements/
website_page_authors:
  - D. Zanutto
---

## System Interventions

This chapter provides a summary of all possible interventions available to participants in the BWF competition.
All interventions have been introduced in previous sections.
Here, we consolidate this information to give participants a complete overview of the decision space they can navigate when developing their strategies.

### Policies

ADD: policies set in a given year remain in place until amended.

#### Budget allocation (national)

Participants must decide the strategy to allocate the national budget across the water utilities.
The policy can be a predefined one or follow a custom allocation of the funds:

  - *by_population*: Allocate the funds according to each province population.

  - *by_inverse_population*: Allocate the funds to provinces with less population (less revenue).

  - *by_income*: Allocate the funds according to each province economic activity.

  - *by_inverse_income*: Allocate the funds to provinces with less economic activity (less revenue).

  - *custom*: Explicitly allocated the budget based on some other pre-defined rule by the participants. Note that the shares must sum to 1.

  ```YAML
  YEAR: 2025
    NATIONAL_POLICIES:                               
      BUDGET_ALLOCATION: BY_POPULATION <OR> BY_INCOME <OR> ...
  ```
  ```YAML
  YEAR: 2025
    NATIONAL_POLICIES:                               
      BUDGET_ALLOCATION: CUSTOM
      POLICY_ARGS:
        WU01: 0.12
        WU02: 0.25 # and so on... 
  ```

#### Non-Revenue Water Interventions (water utility)

Participants must decide each water utility's yearly budget used to reduce non-revenue water (NRW).
This budget is used to improve the municipalities innner distribution network (IDN).
More precisely, this budget descreases the municipalities IDN's average age, which in turn improves the NRW class of the municipality, leading to a reduction of the NRW component.
The policy can be a predefined one or follow a custom allocation of the funds:

  - *by_leak_class*: Allocated the budget to improve by one leak class each municipality in a greedy way (worst cases first) until no budget is left in that year.
  - *by_population*: Allocate the budget according to each municipality population.

```YAML
YEAR: 2025
  WATER_UTILITY: WU01
    POLICIES:
      NRW_REDUCTION:
        BUDGET: 30000
        POLICY: BY_LEAK_CLASS <OR> BY_POPULATION 
```
```YAML
YEAR: 2025
  WATER_UTILITY: WU01
    POLICIES:
      NRW_REDUCTION::
        BUDGET: 30000
        POLICY: CUSTOM
        POLICY_ARGS:
          GM0001: 0.02
          GM0002: 0.02 # and so on...
```

#### Tariffs (water utility)

ADD.

### Interventions

ADD: interventions are specified for each year. All interventions are takend and if the utility contracts debt a bond will be issued automatically to cover the unbudgetted expenses.

#### Open a new source (water utility)

Participants can open new water sources to meet potential increases in demand. These sources must be chosen from a predefined list of available locations and capacities.

```YAML
YEAR: 2025
  WATER_UTILITY: WU01
    INTERVENTIONS:
      OPEN_SOURCE: # Provide source identifier and capacity
        - SOURCE_ID: SG0158
          SOURCE_CAPACITY: 100

          # Multiple sources can be added like this
        - SOURCE_ID: SG0159
          SOURCE_CAPACITY: 50
```

#### Close a source (water utility)

Similarly, participants can close selected sources to improve the overall system efficiency.

```YAML
YEAR: 2025
  WATER_UTILITY: WU01
    INTERVENTIONS:
      CLOSE_SOURCE: # Provide only the source identifier
        - SOURCE_ID: SG0173    

          #Multiple sources can be removed like this.
        - SOURCE_ID: SG0174
```

#### Install a pipe (national or water utility)

To install new pipes in the system or replace existing ones, participants must communicate the connection identifier and select the pipe option from a predefined list of available options.
```YAML
YEAR: 2025
  WATER_UTILITY: WU01
    INTERVENTIONS:
      INSTALL_PIPE: # Provide connection identifier and pipe option
        - CONNECTION_ID: CS0112
          PIPE_ID: PI001

          #Multiple pipes can be add like this.             
        - CONNECTION_ID: CS0113
          PIPE_ID: PI008
```

#### Install a pump(s) (water utility)

Participants can also install or replace pumps in the pumping stations, calibrating the peak outflow of the sources.
Every source is associated with one and only one pumping station, which has multiple identical pumps in parallel.
The pump option must be selected from a predefined list of available options.
If the competitors intend to install one or more pumps in an already open pumping station, they must specify wheter they replace or add to the current pool of pumps at that location.
If the selected pump option differs from that already in place, the latter will automatically replace all of those installed as only one type of pump is allowed.

```YAML
YEAR: 2025
  WATER_UTILITY: WU01
    INTERVENTIONS:
      INSTALL_PUMPS: # Provide source identifier, pump option and quantity for a new pumping station                                       
        - SOURCE_ID: SG0158
          PUMP_ID: PU002
          NUM_PUMPS: 3

          # Provide source identifier, pump option, quantity, AND BEHAVIOUR for an already open station
        - SOURCE_ID: SG0159
          PUMP_ID: PU003                                                             
          NUM_PUMPS: 3
          BEHAVIOUR: REPLACE <OR> NEW 
```

#### Install solar (water utility)

ADD.