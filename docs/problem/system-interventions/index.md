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

#### Budget allocation (national)
Participants can decide the strategy for the funding allocation across all Water Utilities. Budget distribution can follow certain strategies.

  - *POPULATION_BASED*: Allocating the funds according to the population  of each province.

  - *INVERSE_POPULATION_BASED*: Allocating the funds to the areas with low  population.

  - *INCOME BASED*: Allocating the funds to areas with higher economic activity.

  ```YAML
  NATIONAL_POLICY:                               
        BUDGET_ALLOCATION: POPULATION_BASED <OR> INVERSE_POPULATION BASED <OR> INCOME BASED     #This is the national budget allocation policy. If EQUAL is selected the budget will be equally distributed among the provinces. If POPULATION_BASED is selected the budget will be distributed based on the population of each province.
  ```


#### Non-Revenue Water Interventions (water utility)

Participants can decide how much (as a percentage) of each water utility's yearly budget should be spent on improving pipe infrastructure to reduce non-revenue water. Improving the pipe infrastructure means decreasing its average age, which is linked to the different leak classes and implies the amount of non-revenue water.
There exist two policies that distribute a utility's budget across its municipalities:

  - *by_leak_class* Uses the budget to improve the leak class (by one) of each municipality in a greedy way (worst cases first) until no budget is left.
  - *by_population* Distributes the budget proportionally to the municipalities' population size.

```YAML
NRW_ACTION:                 #Actions for the NRW of each municipality.
  BUDGET: 30000             #The allocated budget.
  POLICY: BY_POPULATION
```

#### Tariffs (water utility)

### Interventions

#### Open source (water utility)
Participants can open new water sources to meet potential increases in demand. These sources must be chosen from a predefined list of available locations and capacities.

```YAML
OPEN_SOURCE:                                      
  -SOURCE_ID: SG0158        #Source name.
    SOURCE_CAPACITY: 100    #Capacity of the source.

  -SOURCE_ID: SG0159        #Multiple sources can be added like this.
    SOURCE_CAPACITY: 50
```

#### Close source (water utility)
Similar for opening sources participants can close selected sources if the network has sufficient water.
```YAML
CLOSE_SOURCE:
  - SOURCE_ID: SG0173    #Source name.   

  - SOURCE_ID: SG0174    #Multiple sources can be removed like this.
```

#### Install pipe (national or water utility)
To install new pipes in the system, participants must select connections from a predefined list of available options.
```YAML
INSTALL_PIPE:       
  - CONNECTION_ID: CS0112  #Link ID name.
    PIPE_ID: 1             #Selected pipe id                                

  - CONNECTION_ID: CS0113  #Multiple pipes can be add like this.             
    PIPE_ID: 1 
```

#### Install pumps (water utility)
The participants called to change the pumps that provide water to the network. The pumping stations are location in every source. Every pumping station has to have the same type of pump and all pumps are connected in parallel. The participants must use **only** the pumps that are given. The Behaviour parameter indicates if the listing is about to replace all the pumps that already installed in the system or if a new pumps will be added in the existing configuration. 
```YAML
INSTALL_PUMPS:                                            
  - SOURCE_ID: SG0158             #Source of reference.
    PUMP_ID: 3                    #The ID of the pumps that we would like to install.
    NUM_PUMPS: 3                  #The number of pumps that are installed.                                           
    Behaviour: REPLACE <OR> NEW                                                     

  - SOURCE_ID: SG0159             # Multiple pumping stations can be registered like this. Careful use a unique ID
    PUMP_ID: 3                                                                     
    NUM_PUMPS: 3                                                                  
    Behaviour: REPLACE <OR> NEW 
```


#### Install solar (water utility)
