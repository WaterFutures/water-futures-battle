---
layout: default
website_title: Evaluator Scenario Analysis
parent: /evaluator/
parent_title: The BWF Evaluator
prev_page_url: /evaluator/basic-usage.html
next_page_url: /team.html
website_page_authors:
  - D. Zanutto
  - A. Artelt
---

## How to run different scenarios with the BWF evaluator

If the Python package has been installed, the CLI can be used for running and evaluating different scenarios.

Assuming that the scenario data and configuration is stored in the `data` folder, and the masterplan is stored in `masterplan.yaml`, we can evaluate the masterplan by running:
```
water_futures_battle_run_eval masterplan.yaml data/configuration.yaml
```

This will run all simulations and evaluations of the interventions specified by the user in `masterplan.yaml`.