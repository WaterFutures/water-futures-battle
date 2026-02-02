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

> **Note that you can only run the BWF evaluator on the present data. If you want to run an evaluation on the future, you have to create the configuration files yourself!**

### Example: How to investigate the effect of changes in the inflation

In this illustrative example, we assume that we want to use the provided BWF evaluator to investigate the effect of changes in the inflation.
For this, we will proceed in the following steps:

1. Parse the economy configuration file (this is where the inflation can be set) -- note that you might have to adjust the file path depending on your local installation:
```python
import pandas as pd

economy_dict = pd.read_excel("data/economy/economy-dynamic_properties.xlsx", index_col='timestamp', sheet_name=None)
```

2. Modify the inflation -- here, we simply set it 4% for the years 2025-2035:
```python
inflation_df = economy_dict['inflation']
inflation_df.loc[2025:2035, 'NL0000'] = 4
```

3. Save the modified economics configuration -- we store it in a new file, and keep the original configuration file as a backup:
```python
from water_futures_battle.base_model import DynamicProperties

new_economy_dps = DynamicProperties(name='economy-my_dynamic_properties', dataframes=economy_dict)
new_economy_dps.dump("data/economy/economy-my_dynamic_properties.xlsx")
```

Finally, we have to set the new economics configuration in the `configuration.yaml` file in the data folder -- search for the property `economy-dynamic_properties` and replace the old filename with the new one:
```yaml
economy:
  economy-dynamic_properties: ./economy-my_dynamic_properties.xlsx
```

4. Run the BWF evaluator:
```
water_futures_battle_run_eval masterplan.yaml data/configuration.yaml
```