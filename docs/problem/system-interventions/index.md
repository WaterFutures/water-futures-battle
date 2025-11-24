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

# Budget for reducing non-revenue water

Participants can decide how much (as a percentage) of each water utility's yearly budget should be spent on improving pipe infrastructure to reduce non-revenue water. Improving the pipe infrastructure means decreasing its average age, which is linked to the different leak classes and implies the amount of non-revenue water.
There exist two policies that distribute a utility's budget across its municipalities:

  - *by_leak_class* Uses the budget to improve the leak class (by one) of each municipality in a greedy way (worst cases first) until no budget is left.
  - *by_population* Distributes the budget proportionally to the municipalities' population size.
