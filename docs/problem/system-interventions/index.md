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

## System Levers {#sec:system-levers}

Participants make two types of strategic decisions: policies and interventions.

This chapter provides a summary of all the options available to participants in the BWF competition (they have all been introduced in previous sections already).

Here, we consolidate this information to give participants a complete overview of the decision space they can navigate when developing their masterplan.

### Policies

Policies encompass regulatory and operational rules, such as pricing structures, budget allocations, and maintenance protocols.
Once set, policies remain in effect until explicitly amended.

#### National Budget Allocation (National) {#sec:policy-budget-allocation}

Participants must decide the strategy to allocate the national budget across the water utilities.
The policy can be a predefined one or follow a custom allocation of the funds:

  - *by_population*: Allocate the funds according to each province population.

  - *by_inverse_population*: Allocate the funds to provinces with less population (less revenue).

  - *by_income*: Allocate the funds according to each province economic activity.

  - *by_inverse_income*: Allocate the funds to provinces with less economic activity (less revenue).

  - *custom*: Allocate the budget according to the specified share for each water utility (must sum to 1).

  ```YAML
  year: 2025
    national_policies:                               
      budget_allocation:
        policy: by_population # or "by_income" or the corresponding inverse policies
  ```
  ```YAML
  year: 2026
    national_policies:                               
      budget_allocation:
        policy: custom
        policy_args:
          WU01: 0.12
          WU02: 0.25 # and so on... 
  ```

#### Non-Revenue Water Mitigation Budget (Utility) {#sec:policy-nrw-mitigation}

Participants must decide each water utility's yearly budget used to mitigate non-revenue water (NRW).
This budget is used to improve the municipalities innner distribution network (IDN).
More precisely, this budget descreases the municipalities IDN's average age, which in turn improves the NRW class of the municipality, leading to a reduction of the NRW component.
The policy can be a predefined one or follow a custom allocation of the funds:

  - *by_nrw_class*: Allocate the budget to improve by one NRW-class each municipality in a greedy way (worst cases first) until no budget is left in that year.
  - *by_population*: Allocate the budget according to each municipality population.
  - *custom*: Allocate the budget according to the specified share for each municipality (must sum to 1).

```YAML
year: 2025
  water_utility: WU01
    policies:
      nrw_mitigation:
        budget: 30000
        policy: by_nrw_class # or "by_population"
```
```YAML
year: 2026
  water_utility: WU01
    policies:
      nrw_mitigation:
        budget: 30000
        policy: custom
        policy_args:
          GM0001: 0.02
          GM0002: 0.02 # and so on...
```

#### Water Pricing (Utility)

Participants must decide the water pricing adjustment strategy for each year.
They have two options: increase all water price components according to inflation, or define a custom policy by specifying the percentage increase for each component (e.g., 2%).

```YAML
year: 2025
  water_utility: WU01
    policies:
      pricing_adjustment:
        policy: by_inflation
```

```YAML
year: 2026
  water_utility: WU01
    policies:
      pricing_adjustment:
        policy: custom
        # Specify the percentage increase for each pricing component
        policy_args:
          fixed_component: 0.03      # Annual increase for fixed costs (3%)
          variable_component: 0.02   # Annual increase for variable costs (2%)
          selling_price: 0.05        # Annual increase for water sales to other provinces (5%) 
```

#### Bond Issuance (Utility)

Whenever the water utility is unable to cover its expenditures in a specific year, it finances the resulting deficit by issuing nationally backed bonds. Given that the raised amount is uncertain participants can cover this uncertainty increasing the bond amount ratio.This adjustment is determined by the parameter k, which can be any real number ranging from 1 to 2.5. More details in @sec:bonds.

```YAML
year: 2025
  water_utility: WU01
      policies:
          bond_ratio:
            value: 2.0

```
### Interventions

Interventions are physical modifications to the system, such as infrastructure upgrades or new installations.
Interventions are specified annually and are always implemented.
Note that if a utility contracts debt, a bond is issued automatically to cover the unbudgeted expenses.

#### Opening New Sources (Utility)

Participants can open new water sources to meet potential increases in demand.
Available sources are predefined by location, and participants must specify a capacity within the allowable bounds.

```YAML
year: 2025
  water_utility: WU01
    interventions:
      open_source: # Provide source identifier, capacity, and info about the connection
        - source_id: SG0158
          source_capacity: 100
          pump_option_id: PU003
          n_pumps: 6
          pipe_option_id: PI002

          # Multiple sources can be added like this
        - source_id: SG0159
          source_capacity: 50
          pump_option_id: PU001
          n_pumps: 4
          pipe_option_id: PI003
```

#### Closing Sources (Utility)

Similarly, participants can close selected sources to improve the overall system efficiency.

```YAML
year: 2025
  water_utility: WU01
    interventions:
      close_source: # Provide only the source identifier
        - source_id: SG0173    

          # Multiple sources can be removed like this.
        - source_id: SG0174
```

#### Installing Pipes (National or Utility)

Participants can decide to install new pipes or replace existing ones in the system.
Each installation requires specifying the connection identifier and selecting a pipe option from a predefined list.

```YAML
year: 2025
  water_utility: WU01
    interventions:
      install_pipe: # Provide connection identifier and pipe option
        - connection_id: CG0112
          pipe_option_id: PI001

          # Multiple pipes can be added like this.             
        - connection_id: CG0113
          pipe_option_id: PI008
```

#### Installing Pumps (Utility)

Participants can decide to install or replace pumps in pumping stations to calibrate the peak outflow of water sources.
Each source is associated with one pumping station, which contains multiple identical pumps operating in parallel.
Pump options must be selected from a predefined list.
When installing pumps at an already-open pumping station, participants must specify whether to replace or add to the existing pumps.
If the selected pump option differs from those already installed, all existing pumps will be automatically replaced, as only one pump type is allowed per station.

```YAML
year: 2025
  water_utility: WU01
    interventions:
      install_pumps: # Provide source identifier, pump option and quantity for a new pumping station                                       
        - source_id: SG0159
          pump_option_id: PU003                                                             
          n_pumps: 3
          behaviour: replace # or "new" 
```

#### Installing Solar (Utility)

Participants can decide to install behind-the-meter solar panels at water sources to reduce electricity costs and emissions for pumping stations.
The solar panels offset electricity consumption and emissions but cannot be used as a profit-generating investment.
Panels can be installed multiple times at different points in time.
*Note: Solar panels have a given lifespan (see @sec:energy-model); participants must decide whether to replace them upon expiration.*

```YAML
year: 2025
  water_utility: WU01
    interventions:
      install_solar: # Provide location and capacity
        - source_id: SG0158
          capacity: 20

          # Multiple sources can be added like this
        - source_id: SG0159              
          capacity: 20
```