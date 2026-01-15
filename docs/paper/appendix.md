\newpage

\appendix

# Appendix A

This appendix describes the data contained within the supplementary material (zipped data folder). Four types of data are included in the folder and they are described independently in the following sections.

## EPANET Networks Files {.unnumbered .unlisted}

The provided network files were generated using EPANET 2.3.
Unfortunately, most common EPANET libraries and software (e.g., WNTR and EPANET for Windows) are not keeping up with the versions and they may generate warnings upon opening or fail to open them at all.
When using a library based on an outdated version of EPANET, the hydraulic results will also differ, as EPANET 2.3 features numerous bug fixes with respect to previous versions.

For these compatibility reason and to ensure consistency between results, the solutions will be submitted through an ad-hoc form and inp files will be rejected.
The sole reference for correctness is the evaluator's computations, which uses the latest EPANET 2.3 library.

At the time of writing, we suggest using [EPANET.js](https://epanetjs.com) to visualize the networks overlaid on a map of the Netherlands, while for hydraulic computations, we recommend using the EPANET-PLUS Python library, as it is currently the only one offering EPANET 2.3 support [@github:epanetplus].

## Configuration File {.unnumbered .unlisted}

The configuration file `configuration.yaml` tells the evaluator how to build the system.
Specifically, it indicates:

- The locations of Excel input files containing the variables needed to build the various system components
- The parameters and settings that control the simulation

This makes the configuration file the central reference point that connects all the input data sources with the simulation engine.
By modifying these parameters (e.g., switching input files), participants can quickly simulate the system under different scenarios.

### Settings {.unnumbered .unlisted}
  - Start year (`start_year`) [ - ]
  - End year (`end_year`) [ - ]
  - National budget (`national_budget`) [€]

## Evaluator Input Files {.unnumbered .unlisted}

The evaluator input files fully describe the system entities (municipalities, sources, etc.) and modules (energy system, water demand module, etc.).
By modifying these files, participants can simulate different scenarios and system configurations.

### Static Properties Files {.unnumbered .unlisted}

Static Properties files define the characteristics of each entity, with one entity per row and properties in columns.
Multiple sheets can be used to distinguish between subtypes of the same object (e.g., water sources are divided into desalination, groundwater, and surface water).

### Dynamic Properties Files {.unnumbered .unlisted}

Dynamic Properties files contain time-varying data for both exogenous inputs and initial values of endogenous variables.
Each property has its own sheet within the Excel file, organized as follows:

- Rows: Each row represents a snapshot in time, with the first column containing the timestamp
- Columns: Each column represents a scope, i.e., which entity or group of entities the value applies to.
For example, while 'GMxxxx' indicates the value applies only to that specific municipality, 'NL0000' indicates a national scope and therefore applies to all municipalities.

**When future values are reported** (e.g., timestamp after 2024 for the first stage), **they can be regarded as expert-driven scenarios.**
Actual values will override these parameters in subsequent stages.

### Multi-Parameter (Static and Dynamic) Properties {.unnumbered .unlisted}

When a property requires multiple parameters, column headers use a dash separator ('-') to indicate:

- Uncertainty bounds: `['NL0000-min', 'NL0000-max']`
- Multi-dimensional scope: `['A-SMALL', 'A-MEDIUM', ...]` (e.g., variable varying by both class and size)
- Time series patterns: `['NL0000-1', 'NL0000-2', ...]` (e.g., electricity price profiles at national level)

### Modules {.unnumbered .unlisted}

#### Water Utilities {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

- Entity: **Water Utility**
  - File: `water_utilities/water_utilities-static_properties.xlsx`
  - Sheet: `entities`
  - Properties:
    - Identifier (`water_utility_id`) [ - ]
    - Assigned provinces (`assigned_provinces`) [ - ]

#### Jurisdictions {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

- Entity: **State**
  - File: `configuration.yaml`
  - Properties: 
    - Identifier (`id`) [ - ]
    - Name (`name`) [ - ]

- Entity: **Region**
  - File: `jurisdictions/jurisdictions-static_properties.xlsx`
  - Sheet: `regions`
  - Properties: 
    - Region name (`name`) [ - ]
    - Region ID (`cbs_id`) [ - ]
    - State (`state`) [ - ]

- Entity: **Province**
  - File: `jurisdictions/jurisdictions-static_properties.xlsx`
  - Sheet: `provinces`
  - Properties:
    - Province name (`name`) [ - ]
    - Province ID (`cbs_id`) [ - ]
    - Region (`region`) [ - ]

- Entity: **Municipality**
  - File: `jurisdictions/jurisdictions-static_properties.xlsx`
  - Sheet: `municipalities`
  - Properties:
    - Municipality name (`name`) [ - ]
    - Municipality ID (`cbs_id`) [ - ]
    - Municipality elevation (`elevation`) [ - ]       #TODO DECIDE WHICH PARAMETERS WE SHOULD INCLUDE

##### Dynamic Properties {.unnumbered .unlisted}

- Property: **Population**
  - File: `jurisdictions/municipalities-dynamic_properties.xlsx`
  - Sheet: `population`
  - Scope: Municipality ID
  - Unit: [ inhabitants ]

- Property: **Surface land**
  - File: `jurisdictions/municipalities-dynamic_properties.xlsx`
  - Sheet: `surface-land`
  - Scope: Municipality ID
  - Unit: [ $km^2$ ]
  
- Property: **Surface water (inland)**
  - File: `jurisdictions/municipalities-dynamic_properties.xlsx`
  - Sheet: `surface-water-inland`
  - Scope: Municipality ID
  - Unit: [ $km^2$ ]
  
- Property: **Surface water (open water)**
  - File: `jurisdictions/municipalities-dynamic_properties.xlsx`
  - Sheet: `surface-water-open`
  - Scope: Municipality ID
  - Unit: [ $km^2$ ]
  
- Property: **Number of houses**
  - File: `jurisdictions/municipalities-dynamic_properties.xlsx`
  - Sheet: `n_houses`
  - Scope: Municipality ID
  - Unit: [ houses ]

- Property: **Number of businesses**
  - File: `jurisdictions/municipalities-dynamic_properties.xlsx`
  - Sheet: `n_businesses`
  - Scope: Municipality ID
  - Unit: [ businesses ]

- Property: **Associated water demand pattern - Residential**
  - File: `jurisdictions/municipalities-dynamic_properties.xlsx`
  - Sheet: `assoc_dem_pat-residential`
  - Dimension: Pair
  - Scope: Municipality ID
  - Unit: [ - ]

- Property: **Associated water demand pattern - Business**
  - File: `jurisdictions/municipalities-dynamic_properties.xlsx`
  - Sheet: `assoc_dem_pat-business`
  - Scope: Municipality ID
  - Unit: [ - ]

- Property: **Average age of the Inner Distribution Network**
  - File: `jurisdictions/municipalities-dynamic_properties.xlsx`
  - Sheet: `dist_network-age-avg`
  - Scope: Municipality ID
  - Unit: [ years ]

- Property: **Average disposable income**
  - File: `jurisdictions/municipalities-dynamic_properties.xlsx`
  - Sheet: `disposable_income-avg`
  - Scope: Municipality ID
  - Unit: [ k€ ]

#### Water Sources {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

- Entity: **Water Source**
  - File: `sources/sources-static_properties.xlsx`
  - Sheet: `groundwater`, `surface_water`, `desalination`
  - Properties:   
    - Source ID (`source_id`) [ - ]
    - Source elevation (`elevation`) [ m ]
    - Province (`province`) [ - ]
    - Closest municipality (`closest_municipality`)
    - Activation date (`activation_date`) [ - ]
    - Closure date (`closure_date`) [ - ]
    - Nominal capacity (`capacity-nominal`) [ $m^3/day$ ]
    - Specific energy (`opex-volum-energy_factor`) [ $kWh/m^3$ ]
    - Source permit (`permit`) [ m$m^3/year$ ] *Only groundwater*
    - Basin (`basin`) [ - ] *Only surface water*

##### Dynamic Properties {.unnumbered .unlisted}

- Property: **Unit cost of construction**
  - File: `sources/{source_type}-dynamic_properties.xlsx`
  - Sheet: `new_source-unit_cost`
  - Scope: National
  - Dimension: Source size
  - Unit: [ $\text{€}/(m^3/day)$ ]

- Property: **Unit Operational costs - fixed**
  - File: `sources/{source_type}-dynamic_properties.xlsx`
  - Sheet: `opex-fixed`
  - Scope: National
  - Dimension: Source size $\times$ Uniform Uncertain
  - Unit: [ $\text{€}/(m^3)$ ]
  - Notes: gets multiplied by annual nominal capacity

- Property: **Operational costs - volumetric for non-energy**
  - File: `sources/{source_type}-dynamic_properties.xlsx`
  - Sheet: `opex-volum-other`
  - Scope: National
  - Dimension: Source size $\times$ Uniform Uncertain
  - Unit: [ $\text{€}/(m^3)$ ]

- Property: **Availability factor**
  - File: `sources/{source_type}-dynamic_properties.xlsx`
  - Sheet: `availability_factor`
  - Scope: National
  - Unit: [ - ]

- Property: **Water displacement fine amount**
  - File: `sources/groundwater-dynamic_properties.xlsx`
  - Sheet: `water_displacement-fine_amount`
  - Scope: National
  - Dimension: Displacement severity
  - Unit: [ € ]

#### Pumping Stations {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

  - File: `pumps\pump_options-static_properties.xlsx`

  - Sheet: `options`
  
  - Properties:
  
    - Pump ID (`option_id`) [ - ]
    - Nominal Flowrate (`flow_rate-nominal`) [ $m^3/hour$ ]
    - Lifespan (`lifespan-min`) [ years ]

  - Sheet: `PU01`, `PU02`, `PU03`, `PU04`
  
  - Properties:
  
    - Flowrate (`flowrate`) [ $m^3/hour$ ]
    - Head (`head`) [ m ]
    - Efficiency (`efficiency`) [ - ]
  
##### Dynamic Properties {.unnumbered .unlisted}

- Property: **Unit cost for a new pump**
  - File: `pumps/pump_options-dynamic_properties.xlsx`
  - Sheet: `new_pump-cost`
  - Scope: Pump Option
  - Unit: [ € ]

#### Connections {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}


  - File: `connections\connections-static_properties.xlsx`
  
  - Sheet: `provincial`

  - Properties:

    - Connection ID (`connection_id`) [ - ]  
    - Starting Node (`from_node`) [ - ]
    - Ending Node (`to_node`) [ - ]
    - Distance (`distance`) [ meters ]
    - Pipe Type (`pipes-options_ids`) [ - ]

  - Sheet: `sources`

  - Properties:

    - Connection ID (`connection_id`) [ - ]  
    - Starting Node (`from_node`) [ - ]
    - Ending Node (`to_node`) [ - ]
    - Distance (`distance`) [ meters ]
    - Pipe Type (`pipes-options_ids`) [ - ]

  - Sheet: `cross-provincial`

  - Properties:

    - Connection ID (`connection_id`) [ - ]  
    - Starting Node (`from_node`) [ - ]
    - Ending Node (`to_node`) [ - ]
    - Distance (`distance`) [ meters ]

##### Dynamic Properties {.unnumbered .unlisted}

- Property: **New Pipe Unit Cost**
  - File: `connections/pipe_options-dynamic_properties.xlsx`
  - Sheet: `new_pipe-unit_cost`
  - Unit: [ $\text{€}/m$ ]

- Property: **New Pipe Emission Factor**
  - File: `connections/pipe_options-dynamic_properties.xlsx`
  - Sheet: `new_pipe-emissions_factor`
  - Unit: [ $\text{tCO2eq}/m$ ]

#### Climate {.unnumbered .unlisted}

##### Dynamic Properties {.unnumbered .unlisted}

- Property: **Temperature**
  - File: `climate/climate-dynamic_properties.xlsx`
  - Sheet: `temperature-avg`, `temperature-min-avg`,`temperature-max-avg`, `temperature-warmest_day`, `temperature-coldest_day`
  - Scope: National
  - Unit: [ $\text{°C}$ ]

- Property: **Precipitation**
  - File: `climate/climate-dynamic_properties.xlsx`
  - Sheet: `precipitation`
  - Scope: National
  - Unit: [ $\text{mm}/day$ ]

- Property: **Solar Radiation**
  - File: `climate/climate-dynamic_properties.xlsx`
  - Sheet: `solar_radiation-avg`
  - Scope: National
  - Unit: [ $\text{W}/m^2$ ]

- Property: **Standardized Precipitation-Evotranspiration Index**
  - File: `climate/climate-dynamic_properties.xlsx`
  - Sheet: `SPEI`
  - Scope: National
  - Unit: [ - ]

#### Energy System {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

##### Dynamic Properties {.unnumbered .unlisted}

- Property: **Electricity Price**
  - File: `energy/energy_system-dynamic_properties.xlsx`
  - Sheet: `electricity_price-unit_cost`
  - Scope: National
  - Unit: [ $\text{€}/kWh$ ]

- Property: **Electricity Price Pattern**
  - File: `energy/energy_system-dynamic_properties.xlsx`
  - Sheet: `electricity_price-pattern`
  - Scope: National
  - Unit: [ - ]

- Property: **Grid Emission factor**
  - File: `energy/energy_system-dynamic_properties.xlsx`
  - Sheet: `grid_emission_factor`
  - Scope: National
  - Unit: [ - ]

- Property: **Solar Panel Unit Cost**
  - File: `energy/energy_system-dynamic_properties.xlsx`
  - Sheet: `solar_panel-unit_cost`
  - Scope: National
  - Unit: [  $\text{€}/kW$ ]

#### Economy {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

##### Dynamic Properties {.unnumbered .unlisted}
- Property: **Inflation**
  - File: `economy/economy-dynamic_properties.xlsx`
  - Sheet: `inflation`
  - Scope: National
  - Unit: [ % ]

- Property: **Inflation Expected**
  - File: `economy/economy-dynamic_properties.xlsx`
  - Sheet: `inflation-expected`
  - Scope: National
  - Unit: [ % ]

- Property: **Investor Demand**
  - File: `economy/economy-dynamic_properties.xlsx`
  - Sheet: `investor_demand`
  - Scope: National
  - Unit: [ - ]

## Masterplan Files {.unnumbered .unlisted}

This appendix describes how to complete the solution template (file named masterplan in the supplementary materials).

The masterplan for each competition stage should be prepared using one of the template files provided in the supplementary materials.
All three file formats are accepted to provide a trade-off between flexibility and usability.

The Excel file is the most user-friendly way to describe the solution.
Each lever is described in a separate sheet and requires adding one entry per row and filling in the columns.
The advantage is that most options can simply be selected using the dropdown menus in the columns.
The downside is that it doesn't offer the flexibility to produce custom policies for budget allocation (@sec:policy-budget-allocation) and NRW interventions (@sec:policy-nrw-mitigation).

The YAML format describes the masterplan using the same structure we introduce for all the levers outlined in @sec:system-levers.
It allows users to define custom policies and to populate the file programmatically.
However, preparing it may be somewhat more difficult as it needs to follow the specific structure shown in @lst:yaml-format.
The masterplan can be provided in either JSON or YAML format as long as the structure remains unchanged.

```{#lst:yaml-format .yaml caption="Structure of the masterplan in YAML."}
years:
  - year: YYYY                                                                                  
    national_policies:
      # Amend here budget allocation and other national policies
    national_interventions:
      # Install here inter-provincial pipes connecting water utilities
    water_utilities:
      - water_utility: WUxx
        policies:
        # Amend here policies for this water utility
        interventions:
        # Report here interventions for this water utility (e.g., pipe installations)
```
