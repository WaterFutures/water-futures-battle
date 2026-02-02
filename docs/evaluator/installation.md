---
layout: default
website_title: Climate
parent: /evaluator/
parent_title: The BWF Evaluator
prev_page_url: /evaluator/
next_page_url: /evaluator/basic-usage.html
website_page_authors:
  - D. Zanutto
  - A. Artelt
---

## Installation

The Python package supports Python 3.11 - 3.14

### PyPI

```
pip install water-futures-battle
```

### Git
Download or clone the repository:
```
git clone https://github.com/WaterFutures/water-futures-battle.git
cd water-futures-battle
```

Build the package (note that [uv](https://docs.astral.sh/uv/) is used as a build system):
```
uv build
```

Install the package:
```
pip install .
```

## Data download

The latest data describing the scenarios can either be obtained by **manually downloading** the `water_futures_battle-data.zip` folder from [Zenodo](https://zenodo.org/records/17698299) and **unzip** it with the name `data` **in your working directory**, or by using the CLI of the Python package:
```
water_futures_battle_configure_system
```
Be aware that the CLI overrides any existing data in the `data` folder -- you should backup any changes that you made before running the CLI command.

Once the data and configuration files have been downloaded, the user can freely modify those and evaluate their influence on the masterplan.

> **Note that we only provide the present data. If you want to run an evaluation on the future, you have to create the configuration files yourself!**