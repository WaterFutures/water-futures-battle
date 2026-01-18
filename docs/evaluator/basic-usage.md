---
layout: default
website_title: Climate
parent: /evaluator/
parent_title: The BWF Evaluator
prev_page_url: /evaluator/installation.html
next_page_url: /team.html
website_page_authors:
  - D. Zanutto
  - A. Artelt
---

## How to use the Python package

The system configuration can be loaded and processed by calling the `water_futures_battle.services.configure_system` function, which returns the Python objects provding access to the parsed settings, the national context, and all water utilities.

Note that all necessary data and configuration files are organized in a dedicated folder, which must be passed as an argument to `configure_system()` -- if none is specified, "data" is used as a default folder. While the user may decide to manually download the data and store it anywhere on their machine, the Python package automatically downloads all necessary data and stores it in the given folder if it can not find the data and configuration files in the specified folder.

Once the data and configuration files have been downloaded, the user can freely modify those and evaluate their influence on the overal policy.

### Quick example

```python
from water_futures_battle.services import configure_system

# Load and parse all data and coniguration files
settings, national_context, water_utilities = configure_system()

# Get the total number of water utilities
print(f"Number of water utilities: {len(water_utilities)}")
```

More examples can be found in the [examples folder](https://github.com/WaterFutures/water-futures-battle/tree/main/examples).