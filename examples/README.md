# Examples

These small scripts demonstrate how to load the Battle of the Water Futures
system and query its data model. They are intended as starting points for
exploration, analysis, and custom workflows.

## Requirements

- Python 3.11 or later.
- The `water-futures-battle` package installed in the active environment:

  ```bash
  pip install water-futures-battle
  ```

- A Battle dataset containing `configuration.yaml`. When working from a clone
  of this repository, the included `data/` directory already satisfies this
  requirement.

`configure_system()` looks for `data/configuration.yaml` relative to the
current working directory. Run the commands below from the repository root:

```bash
python examples/basic_usage.py
```

If the default data directory or configuration file is missing,
`configure_system()` attempts to download the latest public dataset from
Zenodo. To use a different local dataset, pass its path explicitly in your own
script:

```python
from water_futures_battle import configure_system

settings, national_context, water_utilities = configure_system(
    data_path="/path/to/data"
)
```

## Available examples

| Script | What it demonstrates | Run from the repository root |
| --- | --- | --- |
| `basic_usage.py` | Loads the complete system and prints the number of water utilities. | `python examples/basic_usage.py` |
| `inflation.py` | Reads and prints the national inflation time series. | `python examples/inflation.py` |
| `population_over_time.py` | Retrieves Nieuwegein by name and prints its historical population, including the period before the municipality existed. | `python examples/population_over_time.py` |
| `municipalities_attributes.py` | Iterates through every water utility and its active municipalities in 2012, then prints selected static attributes through yearly snapshots. | `python examples/municipalities_attributes.py` |

## Core objects

Every example begins with:

```python
settings, national_context, water_utilities = configure_system()
```

- `settings` contains the simulation period, random seed, and other global
  configuration.
- `national_context` provides national models and data, including the state,
  climate, economy, sources, pipes, and pumping infrastructure.
- `water_utilities` is the collection of water-utility objects used to access
  their municipalities and assets.

For further API details and model documentation, see the
[project documentation](https://waterfutures.github.io/water-futures-battle/).