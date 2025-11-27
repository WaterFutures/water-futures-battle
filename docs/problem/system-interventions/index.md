---
layout: default
website_title: System Interventions
parent: /problem/
parent_title: Problem
prev_page_url: /problem/system-requirements/
next_page_url: /problem/external-drivers/
website_page_authors:
  - D. Zanutto
---

## System Interventions

This chapter provides a summary of all possible interventions available to participants in the BWF competition.
All interventions have been introduced in previous sections.
Here, we consolidate this information to give participants a complete overview of the decision space they can navigate when developing their strategies.

### Non-Revenue Water Interventions 

Participants can decide how much (as a percentage) of each water utility's yearly budget should be spent on improving pipe infrastructure to reduce non-revenue water. Improving the pipe infrastructure means decreasing its average age, which is linked to the different leak classes and implies the amount of non-revenue water.
There exist two policies that distribute a utility's budget across its municipalities:

  - *by_leak_class* Uses the budget to improve the leak class (by one) of each municipality in a greedy way (worst cases first) until no budget is left.
  - *by_population* Distributes the budget proportionally to the municipalities' population size.
