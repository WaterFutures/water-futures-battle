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

## System Levers

Participants make two types of strategic decisions: policies and interventions.

This chapter provides a summary of all the options available to participants in the BWF competition (they have all been introduced in previous sections already).

Here, we consolidate this information to give participants a complete overview of the decision space they can navigate when developing their masterplan.

### Policies

Policies encompass regulatory and operational rules, such as pricing structures, budget allocations, and maintenance protocols.
Once set, policies remain in effect until explicitly amended.

#### National Budget Allocation (National)

Participants must decide the strategy to allocate the national budget across the water utilities.
The policy can be a predefined one or follow a custom allocation of the funds:

  - *by_population*: Allocate the funds according to each province population.

  - *by_inverse_population*: Allocate the funds to provinces with less population (less revenue).

  - *by_income*: Allocate the funds according to each province economic activity.

  - *by_inverse_income*: Allocate the funds to provinces with less economic activity (less revenue).

  - *custom*: Allocate the budget according to the specified share for each water utility. Shares must sum to 1.

  ```YAML
  YEAR: 2025
    NATIONAL_POLICIES:                               
      BUDGET_ALLOCATION:
        POLICY: BY_POPULATION <OR> BY_INCOME <OR> ...
  ```
  ```YAML
  YEAR: 2025
    NATIONAL_POLICIES:                               
      BUDGET_ALLOCATION:
        POLICY: CUSTOM
        POLICY_ARGS:
          WU01: 0.12
          WU02: 0.25 # and so on... 
  ```

#### Non-Revenue Water Reduction Budget (Utility)

Participants must decide each water utility's yearly budget used to reduce non-revenue water (NRW).
This budget is used to improve the municipalities innner distribution network (IDN).
More precisely, this budget descreases the municipalities IDN's average age, which in turn improves the NRW class of the municipality, leading to a reduction of the NRW component.
The policy can be a predefined one or follow a custom allocation of the funds:

  - *by_leak_class*: Allocate the budget to improve by one leak class each municipality in a greedy way (worst cases first) until no budget is left in that year.
  - *by_population*: Allocate the budget according to each municipality population.
  - *custom*: Allocate the budget according to the specified share for each municipality. Shares must sum to 1.

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
      NRW_REDUCTION:
        BUDGET: 30000
        POLICY: CUSTOM
        POLICY_ARGS:
          GM0001: 0.02
          GM0002: 0.02 # and so on...
```

#### Water Pricing (Utility)

Participants must decide the water pricing increase strategy for each year.
They have two options: increase all water price components according to inflation, or define a custom policy by specifying the percentage increase for each component (e.g., 2%).

```YAML
YEAR: 2025
  WATER_UTILITY: WU01
    POLICIES:
      PRICING:
        POLICY: BY_INFLATION
```

```YAML
YEAR: 2025
  WATER_UTILITY: WU01
    POLICIES:
      PRICING:
        POLICY: CUSTOM
        # Specify the percentage increase for each pricing component
        POLICY_ARGS:
          FIXED_COMPONENT: 0.03      # Annual increase for fixed costs (3%)
          VARIABLE_COMPONENT: 0.02   # Annual increase for variable costs (2%)
          SELLING_PRICE: 0.05        # Annual increase for water sales to other provinces (5%) 
```

### Interventions

Interventions are physical modifications to the system, such as infrastructure upgrades or new installations.
Interventions are specified annually and are always implemented.
Note that if a utility contracts debt, a bond is issued automatically to cover the unbudgeted expenses.

#### Opening New Sources (Utility)

Participants can open new water sources to meet potential increases in demand.
Available sources are predefined by location, and participants must specify a capacity within the allowable bounds.

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

#### Closing Sources (Utility)

Similarly, participants can close selected sources to improve the overall system efficiency.

```YAML
YEAR: 2025
  WATER_UTILITY: WU01
    INTERVENTIONS:
      CLOSE_SOURCE: # Provide only the source identifier
        - SOURCE_ID: SG0173    

          # Multiple sources can be removed like this.
        - SOURCE_ID: SG0174
```

#### Installing Pipes (National or Utility)

Participants can decide to install new pipes or replace existing ones in the system.
Each installation requires specifying the connection identifier and selecting a pipe option from a predefined list.

```YAML
YEAR: 2025
  WATER_UTILITY: WU01
    INTERVENTIONS:
      INSTALL_PIPE: # Provide connection identifier and pipe option
        - CONNECTION_ID: CS0112
          PIPE_ID: PI001

          # Multiple pipes can be added like this.             
        - CONNECTION_ID: CS0113
          PIPE_ID: PI008
```

#### Installing Pumps (Utility)

Participants can decide to install or replace pumps in pumping stations to calibrate the peak outflow of water sources.
Each source is associated with one pumping station, which contains multiple identical pumps operating in parallel.
Pump options must be selected from a predefined list.
When installing pumps at an already-open pumping station, participants must specify whether to replace or add to the existing pumps.
If the selected pump option differs from those already installed, all existing pumps will be automatically replaced, as only one pump type is allowed per station.

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

#### Installing Solar (water utility)

Participants can decide to install behind-the-meter solar panels at water sources to reduce electricity costs and emissions for pumping stations.
The solar panels offset electricity consumption and emissions but cannot be used as a profit-generating investment.
Panels can be installed multiple times at different points in time.
*Note: Solar panels have a given lifespan (see @sec:energy-model); participants must decide whether to replace them upon expiration.*

```YAML
YEAR: 2025
  WATER_UTILITY: WU01
    INTERVENTIONS:
      INSTALL_SOLAR: # Provide location and capacity
        - SOURCE_ID: SG0158
          CAPACITY: 20

          # Multiple sources can be added like this
        - SOURCE_ID: SG0159              
          CAPACITY: 20
```