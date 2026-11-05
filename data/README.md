# Data Licensing and Processing

The `data/` directory contains the system description and the tooling used to
create and evolve the competition datasets. More detailed guidance on creating
and managing datasets is available in the documentation as the data format is
tightly coupled to the current library implementation and version.

This folder therefore supports reproducibility of the competition and provides
examples. It contains:

- this [README](README.md);
- the [dataset version](VERSION), which identifies the compatible library
    version;
- masterplan templates in [JSON](masterplan.json), [YAML](masterplan.yaml),
    and [Excel](masterplan.xlsx) formats;
- the [configuration file](configuration.yaml), which describes the system to
    the evaluator; and
- the [Stage 1](bwf_narrative-stage_1.md),
    [2](bwf_narrative-stage_2.md), and
    [3](bwf_narrative-stage_3.md) narratives released to BWF participants
    with their personalised updated datasets.

In principle, the configuration file fully describes the input system. In
practice, a national-scale system contains too much tabular information to keep
in one file, so the configuration references the individual data files within
this folder. Those files are organised into modules, each of which contains a
set of static and dynamic properties. The module boundaries broadly reflect how
the model was developed and how its data sources were assembled. They are
practical ownership and processing boundaries, rather than a strict, a priori
conceptual taxonomy, as described in the
[paper reviewing the competition](http://arxiv.org/abs/2511.22986). Future
versions may use a different structure; consult the latest documentation for
the current data format.

Each module folder, such as [climate](climate/), stores its generated competition
workbooks directly in the module directory. Where needed, a module also
contains:

- `raw-data/`
    - source data downloaded from providers,
    - provenance and licensing information;
- `preprocessing-scripts/`:
    - generator notebooks for the initial dataset (`<module>-<static|dynamic>_properties-generator.ipynb`),
    - Python scripts for extending stages (`<module>-<static|dynamic>_properties-stage_extender.py`), and
    - supporting code (usually `utils.py`);
- supporting documents describing the methodologies and experimental settings:
    `properties_generation_explanation.md` for the initial dataset and
    `dynamic_properties_evolution_narrative.md` for changes between stages.

The generated dataset workbooks are deliberately not kept in version control.
They are binary files whose size grows quickly as they are regenerated, even
when only a small parameter or a dependency implementation changes. Release
datasets are instead available from the [Zenodo archive](https://doi.org/10.5281/zenodo.17698299)
and [GitHub Releases](https://github.com/WaterFutures/water-futures-battle/releases).

## Licensing and Provenance

The content of this folder falls under three different terms.
The preprocessing scripts are source code and, like the rest of the repository, are released under the [MIT License](../LICENSE).
The raw data downloaded from third-party providers are included only for reproducibility and remain subject to the licences set by those providers, as listed in the table below.
The BWF competition dataset, which we derived from the raw data through the preprocessing scripts, is released under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE) licence.
If you use the BWF competition dataset, please cite it as [Zanutto et al. (2025)](https://doi.org/10.5281/zenodo.17698299), and credit the original providers as indicated in the table.

Licence terms were last checked on 2026-10-01.

**Table 1.** *Overview of raw datasets by provider and their licensing terms.*

| Provider | Dataset and version | Source (accessed) | Licence | Attribution | Raw data in repo | Used in | Content and notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CBS | Gebieden, overzicht vanaf 1830 (table 70739ned, version 2025-02-19) | [CBS cijfers database](https://www.cbs.nl/nl-nl/cijfers/detail/70739ned) (2025-10-21) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Source: CBS, table 70739ned (CC BY 4.0); modified | Yes (permitted under CC BY 4.0) | jurisdictions | Downloaded as `70739ned-202502190000.zip`; provides the jurisdiction hierarchy (regions, provinces, municipalities), names, codes, and municipality begin and end dates, with descriptions of administrative changes (mergers, renames). |
| CBS | Regionale kerncijfers Nederland (table 70072ned), 2000-2024 | [CBS StatLine](https://opendata.cbs.nl/#/CBS/nl/dataset/70072ned/table?dl=B01D1&ts=1761565609309) (2025-10-31) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Source: CBS, table 70072ned (CC BY 4.0); modified | Yes (permitted under CC BY 4.0) | jurisdictions | Downloaded as `CBS-regionale_kerncijfers_nederland.zip`; municipality-level series for population by urban class, land and water areas, housing stock, number of businesses by activity, disposable income, and tourism classification. |
| CBS | Population forecast 2024-2070 (news article, 2024 week 51) | [CBS news](https://www.cbs.nl/en-gb/news/2024/51/forecast-population-of-the-netherlands-will-reach-19-million-in-2037) (2026-01-19) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Source: CBS (CC BY 4.0); modified | Yes (permitted under CC BY 4.0) | jurisdictions | National population forecast (measured values, forecast 2024-2070, 67% and 95% prediction intervals) saved as `population-projections.csv` and appended to the national population series from 2025 onward. |
| CBS | The Netherlands in numbers 2021: number of companies (article) | [CBS longread](https://longreads.cbs.nl/the-netherlands-in-numbers-2021/how-many-companies-in-the-netherlands/) (2026-01-19) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Source: CBS (CC BY 4.0) | No (no file downloaded) | jurisdictions | Used only to derive manually the `ratio_to_2015_NoB` year-on-year trend that reconstructs business counts before 2013. |
| Nominatim / OpenStreetMap | Geocoding API (municipality coordinates) | [Nominatim](https://nominatim.org/), data from [OpenStreetMap](https://www.openstreetmap.org/) (2026-03-31) | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | © OpenStreetMap contributors | No (only derived coordinates; query cache in `jurisdictions/.backups/`) | jurisdictions | Queried through the Nominatim API to obtain municipality latitude and longitude; results cached for reproducibility. |
| Open-Elevation | Elevation API (municipality elevations), based on SRTM | [Open-Elevation](https://open-elevation.com) (2026-03-31) | Public domain (SRTM data, NASA/USGS) | Elevation data: NASA SRTM, via Open-Elevation | No (only derived elevations; query cache in `jurisdictions/.backups/`) | jurisdictions | Queried through the Open-Elevation API to obtain municipality elevations; a few values were corrected manually afterwards (see the static properties generator notebook); results cached for reproducibility. |
| Vewin | Dutch Drinking Water Statistics 2022 | [Vewin report](https://www.vewin.nl/wp-content/uploads/2024/06/vewin-dutch-drinking-water-statistics-2022-eng-web.pdf) (2025-09-01) | [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) (report); only statistical values used | Source: Vewin (2022), Dutch Drinking Water Statistics 2022 (CC BY-NC-ND 4.0) | No (only statistical values and author-digitised inputs) | jurisdictions, water_demand_model, sources, water_utilities | Used to calibrate historical NRW, per-unit water consumption, pipe-network length, water prices, and approximate source locations and supply volumes. Approximate source locations were digitised manually from the report's map (Figure 2.6) and stored as `.kmz` files in `sources/raw-data/`. |
| World Bank (data from IMF) | Inflation, consumer prices (annual %), Netherlands (FP.CPI.TOTL.ZG), 1999-2024 | [World Bank Open Data](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG?locations=NL) (2025-10-31) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Source: International Monetary Fund, International Financial Statistics, via World Bank Open Data (CC BY 4.0) | Yes (permitted under CC BY 4.0) | economy | Downloaded as `Inflation_Data.xlsx`. |
| Eurostat | Electricity prices for household consumers (nrg_pc_205), 2007-2025 | [Eurostat databrowser](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205__custom_18701019/default/table) (2025-11-05) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Source: Eurostat (nrg_pc_205) (CC BY 4.0); modified | Yes (permitted under CC BY 4.0) | energy | Netherlands household electricity price, half-yearly values; downloaded as `nrg_pc_205__custom_18701019_linear.csv`. |
| Eurostat | Complete energy balances (nrg_bal_c), gross electricity production, 1990-2023 | [Eurostat databrowser](https://ec.europa.eu/eurostat/databrowser/view/nrg_bal_c__custom_18717923/default/table) (2025-11-05) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Source: Eurostat (nrg_bal_c) (CC BY 4.0); modified | Yes (permitted under CC BY 4.0) | energy | Netherlands annual gross electricity production; downloaded as `nrg_bal_c__custom_18717923_linear_2_0.csv`. |
| European Environment Agency (EEA) | Greenhouse gas emissions from energy supply, 1990-2023 | [EEA greenhouse gases data viewer](https://www.eea.europa.eu/en/analysis/maps-and-charts/greenhouse-gases-viewer-data-viewers) (2025-11-05) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Source: European Environment Agency (CC BY 4.0); modified | Yes (permitted under CC BY 4.0) | energy | Netherlands annual emissions; downloaded as `S_Table.csv` and combined with the Eurostat production data to derive the grid emission factor. |
| Our World in Data (OWID) | Solar photovoltaic module prices, 1975-2024 | [OWID grapher](https://ourworldindata.org/grapher/solar-pv-prices) (2025-11-05) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (OWID processing); original sources retain their own terms | Source: IRENA (2025); Nemet (2009); Farmer and Lafond (2016) – with major processing by Our World in Data | Yes (permitted under CC BY 4.0) | energy | Worldwide yearly average solar PV module price; downloaded as `solar-pv-prices.csv`. |
| Battle of the Water Networks II (BWN-II) | Weekly electricity-price pattern | [Marchi et al. (2014)](https://doi.org/10.1061/(ASCE)WR.1943-5452.0000378) | Copyright ASCE (publication); only numerical values used | Cite Marchi et al. (2014) | No (values reconstructed from the publication) | energy | Hourly weekly electricity-price pattern reconstructed from the previous competition and used up to 2014. |
| ENTSO-E Transparency Platform | Day-ahead prices (data view) | [ENTSO-E](https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show) (2025-11-05) | Not applicable (no data used) | Not required | No (no file downloaded) | energy | Used only as a qualitative reference for the manually defined weekly electricity-price pattern from 2015 onward (`future_electricity_patterns.csv`). |
| KNMI | Klimaatdashboard (temperature, precipitation, solar radiation, SPEI), seasonal, 2000-2025, and KNMI'23 scenarios (Hn, Hd, Ln, Ld) | [KNMI klimaatdashboard](https://www.knmi.nl/klimaat#klimaatdashboard) (2026-01-06) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Source: KNMI | Yes (permitted under CC0) | climate | De Bilt and national seasonal observations and scenario bands; downloaded as per-variable and per-season CSV files (e.g. `KNMI_klimaatdashboard_De Bilt_Temperatuur_*.csv`). |
| Authors (private source) | Anonymised residential and business hourly demand patterns | Not publicly available | Released under CC BY 4.0 as part of the BWF dataset | Cite the BWF dataset (Zanutto et al., 2025) | No (only anonymised, mean-normalised patterns) | water_demand_model | Year-long hourly patterns, normalised by their mean, used to populate the `residential` and `business` sheets of the water demand model static properties. |

Do not treat a public download as permission to redistribute it. Where source
files cannot be redistributed, keep only the retrieval instructions and the
preprocessing code in the repository.

## Initial Dataset Generation

The initial dataset is the first dataset shared with participants. It combines a
description of the system in 2000 with interventions and modifications made
during the 2000-2025 historical period, such as municipality mergers and the
opening and closing of sources.

Ideally, the system would have been generated for 2000, supplied with
historical exogenous variables and external events, and evolved to 2025 with the
evaluator. Development constraints made that impractical, so the resulting
initial dataset combines generated and directly specified historical elements.

### Environment

The initial dataset is generated with Jupyter notebooks in each module's
`preprocessing-scripts/` directory. The project uses `uv`; install the project
environment from the repository root, then make that environment available as a
Jupyter kernel:

```bash
uv sync
source .venv/bin/activate
uv pip install ipykernel
```

You can either open each notebook with the same `water-futures-battle` kernel
or create one kernel per module. The notebooks install the Water Futures Battle
library in editable mode, and some include an installation cell for additional,
notebook-specific dependencies. Run those cells when required, then run the
notebooks in the order below to regenerate the initial dataset.

### Initial Dataset Generation Order

| Order | Module | Generate | Depends on |
| ---: | --- | --- | --- |
| 1 | Climate | Dynamic properties | |
| 2 | Energy | Dynamic properties | |
| 3 | Economy | Dynamic properties | |
| 4 | Pipes | Pipe-option static properties | Economy |
| 5 |       | Pipe-option dynamic properties | Economy, pipe-option static p. |
| 6 | Pumps | Pump-option static properties | Economy |
| 7 |       | Pump-option dynamic properties | Economy, pump-option static p. |
| 8 | Jurisdictions | Static properties | |
| 9 |               | Dynamic properties | Jurisdictions static p. |
| 10 | Water demand model | Static properties | Jurisdictions |
| 11 |                    | Dynamic properties | Jurisdictions |
| 12 | NRW model | Dynamic properties | |
| 13 | Jurisdictions | Historical demands | Jurisdictions static and dynamic p., water demand model static and dynamic p., NRW dynamic p. |
| 14 | Sources | Static properties | Jurisdictions and historical demands |
| 15 |         | Dynamic properties | Jurisdictions and historical demands, Economy |
| 16 | Pumping stations | Static properties | Sources, jurisdictions, and historical demands |
| 17 | Connections | Static properties and pipe dynamic properties | Jurisdictions, sources, pumping stations, and historical demands |
| 18 | Water utilities | Static properties | |
| 19 | Water utilities | Dynamic properties | Economy, water utilities static properties |
| 20 | Economy | Bond static properties | Water utilities |
| 21 | Energy | Solar-farm static properties | Sources static properties, pumping stations static properties |

The initial dataset was generated several times between December 2025 and April
2026 on a MacBook Pro with an M3 processor. Re-running the generators on a
different machine or with different library versions may produce different
results.

## Historical Dataset Generation

The historical dataset describes the system at the start of 2025, when the BWF
competition begins in its parallel universe. Generate it by running the initial
dataset through the evaluator. From the repository root, create an environment,
install the BWF library, and run the evaluation:

```bash
uv venv
source .venv/bin/activate
uv pip install water-futures-battle
water_futures_battle_run_eval data/masterplan.json data/configuration.yaml
```

Alternatively, run `./scripts/bwf_evaluate.sh historical 0`.

Evaluation creates `bwf_results-historical_stage` in the repository root.

## Extending the Dataset Between Stages

During the BWF competition, future conditions were hidden from participants.
This was achieved by withholding the dynamic models and experimental settings
used to produce exogenous-variable values. Future conditions were mainly based
on organiser assumptions or on provider projections, for example for climate.
The narratives describe how variables evolve; the methodology and experimental
settings explain how that story is implemented as a model. Stage-extender
scripts translate those assumptions into code that automatically extends the
input files.

To reproduce the competition datasets, run from the repository root the following
script:

```bash
./scripts/bwf_prepare.sh <team> <stage>
```

The command is implemented by [bwf_prepare.sh](../scripts/bwf_prepare.sh); see
the [scripts README](../scripts/README.md) for related utilities. In short, the
script creates a new input directory for stage `<stage>` from the previous
stage's results. Stage 1 is based on `bwf_results-historical_stage`. It uses
each module's stage-extender script to append future variable values, copies
the files that do not need extension, and updates `VERSION` and
`configuration.yaml` to reference the new files.

Use these scripts as a starting point for creating your own datasets. For
example, they can support testing under different scenarios by changing model
parameters, generating random realisations by changing seeds, implementing
alternative update mechanisms, or changing the number and duration of stages.
Variables have different temporal resolutions: some must be defined at their
required resolution, while others may be omitted because the evaluator uses the
latest available value.

