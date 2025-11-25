

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


- Why single delivery point per municipalities?
Because we need to simplify the problem and we have no informaiton on how to split the municipality in subnodes (or at least it will require a careful inspection od the urban systems from a GIS and still it would not be realistic).
Also, if the additional modelling of the nodes doesn't produce any change in the hydraulics that can be appreciated than it is unnecesary. 
- Why modelling leaks as additional demand instead of orifice and using pressure driven analysis?
Because emitters work well for small background leaks in pipes. Whe nwe need to represent all the cumulative leaks of the whole system no modelling has been done here.
We keep it simple.
- Why neglect leaks at the transport level?
Because we can put them together with the one at the city level as the hydraulic impact in term of pressure drop would be irrelevant. 
Transport netowrks have high flows and high diameters and a leak would probably be big neought to be noticeable, more of a burst in my opinion.