---
layout: level_two
title: System Description
parent: /problem/
parent_title: Problem
---


# System

## Nodes

- [Demand Nodes](./demand-nodes)

- [Sources](./sources)

## Links

- [Pipes](./pipes)

- [Pumps](./pumps)

## Finances

### Income

There is a national budget every year for investments coming from the central government (basically free money).
This budget is shared between the utilities and together with the revenue (money that comes from selling water only) makes up the total utility budget.
Each utility will have its own account and they can save money to use it at later stages or spend it all or even more.
Debt is brought from one year to the other.
If the utility can't **reduce** (or close) its debt **the next year** (or how many?), it will be forced to issue a bond.
A bond will fix the debit but will produce additional costs for the following years (based on the horizon).
A bond can also be issued willingly to face some big infrastructure, e.g., desalination plant. 
Bonds will have the same rate for water utilities (the government issues them as a guarantor(?right term)).
Horizon will also be fixed.
A bond can be national, in this case will reduce the budget before the division, or linked to a set of water utilities (or just one).

Budget is then allocated between the different activities:
- total direct costs is defined by the direct costs of the decsion variables on the trasnport systems plus fixed costs for managing the system
- an additional component is to manage and improve the WDS within the cities:
For example, every Euro invested on leak localisation and detection will bring an improvement to the parameter of "city x" water loss evey km [m^3/km]
same for improving the current system 


## Expenses

### Direct

Infrastructure interventions [(see options)](#Options).
Energy costs.
Fixed management cost
--> how ? function of population and age fo the system? we must use this to balance out all the costs and revenues
It can't be changed (not a decision variable).

### Indirect

Water leaks (non revenue water).


# Options

Here a recap of what are the possible options and what is necessary

## Network

- open sources
    - date (start of construction)
    - option id
    - option args

- close sources
    - date (start of turning-off will be instantaneous)
    - source name

- new connections
    - date (start of construction)
    - option id (where)
    - option args
    
## Financial

- allocation from national budget:
    - share for each water utility. (between 0 and 1)
    - share for national level works (inter-province works) (between 0 and 1)
    - They will sum to one.
    - Can be decided every **5 years**.
    - How to communicate: value between 0 and 1 for each utility, the remain of the budget will be for shared interventions

- debt:
    - date
    - how much
    - for whom (national vs utility vs utilities group)
    
- for each utility, budget allocation
    - 
