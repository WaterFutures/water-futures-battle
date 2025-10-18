---
layout: default
title: Demand Nodes
parent: /problem/network-options/
parent_title: Network & Design Options
---

# Demand Nodes

Part of [network options](./network-options).

Every muncipality is represent as a unique entity in the system.
The demand is the cumulative demand for all type of activities within the municipalities.
The idea is that the transport network delivers all the demand to a single delivery point and that then it is up to the city wate distirbution system to deliver it to the consumers. 
Which is not our concern.
See demand-model.

On top of demand, each urban system will have a leak associated.
See [leak-model](./leak-model).
Given the pipe distribution by age, diameter, pressure at the delivery point, and length of the urban system, we generate an additional leak.
Perhaps the first 3 params will genrate m3/km which gets multiplied by the length of the urban systems

Each municipality has the following properties
- Geographical
    - Name [CBS]
    - Coordinates [??]
    - elevation [??]
    - CBS code [CBS]
    - province where it belongs
    - land area [CBS]
    - water area [CBS]
    - more ?
- All the properties necessary to generate the demands
    - TO be decided based on the demand-model
        - population (by age)
- Hydraulic characteristics
    - pipe distribution by diameter
    - pipe distribution by age
    - pipe distribution by length
- Economic data on population for fairness assessment
    - Disposable income (gemiddeld inkomen)
See all [CBS Interesting properties](./cbs-interesting).


---

Optionally, we can think about modelling farmers.
Meeting demand for agricutlure and deciding not to fullfill it could be a policy option too. 
What should we use?
DO we pay simply pay them back?


---
Motivation behind the decisions
- Why single delivery point per municipalities?
Because we need to simplify the problem and we have no informaiton on how to split the municipality in subnodes (or at least it will require a careful inspection od the urban systems from a GIS and still it would not be realistic).
Also, if the additional modelling of the nodes doesn't produce any change in the hydraulics that can be appreciated than it is unnecesary. 
- Why modelling leaks as additional demand instead of orifice and using pressure driven analysis?
Because emitters work well for small background leaks in pipes. Whe nwe need to represent all the cumulative leaks of the whole system no modelling has been done here.
We keep it simple.
- Why neglect leaks at the transport level?
Because we can put them together with the one at the city level as the hydraulic impact in term of pressure drop would be irrelevant. 
Transport netowrks have high flows and high diameters and a leak would probably be big neought to be noticeable, more of a burst in my opinion.