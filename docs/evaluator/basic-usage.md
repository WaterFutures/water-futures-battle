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

Note that the library does't contain the input data but it can automatically download them from Zenodo.
When calling `configure_system()`, the library checks for the data and initiates the download.
However, Zenodo sometimes limits API calls, and this function fails.
In this case, you need to **manually download** the `water_futures_battle-data.zip` folder and **unzip** it with the name `data` **in your working directory**.

Once the data and configuration files have been downloaded, the user can freely modify those and evaluate their influence on the masterplan.

### Quick example

```python
from water_futures_battle.services import configure_system

# Load and parse all data and coniguration files
settings, national_context, water_utilities = configure_system()

# Get the total number of water utilities
print(f"Number of water utilities: {len(water_utilities)}")
```

More examples can be found in the [examples folder](https://github.com/WaterFutures/water-futures-battle/tree/main/examples).