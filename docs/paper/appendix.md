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

- The relative paths of the Excel input files describing the system
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
Actual values will override these parameters in subsequent stages of the competition.

### Multi-Parameter (Static and Dynamic) Properties {.unnumbered .unlisted}

When a property requires multiple parameters, column headers use a dash separator ('-') to indicate:

- Uncertainty bounds: `['NL0000-min', 'NL0000-max']`
- Multi-dimensional scope: `['A-SMALL', 'A-MEDIUM', ...]` (e.g., variable varying by both class and size)
- Time series patterns: `['NL0000-1', 'NL0000-2', ...]` (e.g., electricity price profiles at national level)

### Modules {.unnumbered .unlisted}

#### State {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

- Entity: **State**
  - File: `configuration.yaml`
  - Properties: 
    - State name (`name`) [ - ]
    - State ID (`id`) [ - ]

- Entity: **Region**
  - File: `jurisdictions/jurisdictions-static_properties.xlsx`
  - Sheet: `regions`
  - Properties: 
    - Region name (`name`) [ - ]
    - Region ID (`cbs_id`) [ - ]
    - State ID (`state`) [ - ]

- Entity: **Province**
  - File: `jurisdictions/jurisdictions-static_properties.xlsx`
  - Sheet: `provinces`
  - Properties:
    - Province name (`name`) [ - ]
    - Province ID (`cbs_id`) [ - ]
    - Region ID (`region`) [ - ]

- Entity: **Municipality**
  - File: `jurisdictions/jurisdictions-static_properties.xlsx`
  - Sheet: `municipalities`
  - Properties:
    - Municipality name (`name`) [ - ]
    - Municipality ID (`cbs_id`) [ - ]
    - Province ID (`province`) [ - ]
    - Opening date (`begin_date`) [ - ]
    - Closure date (`end_date`) [ - ]
    - Reason for the closure (`end_reason`) [ - ]
    - Municipalities IDs that acquired the municipality's assets (`destination_cbs_ids`) [ - ]
    - Coordinates (`latitude`, `longitude`, `elevation`) [ degrees, degrees, m ]
    - Area characteristics (`touristic_area_cbs_id`, `touristic_group_cbs_id`) [ -, - ]
    
##### Dynamic Properties {.unnumbered .unlisted}

- Property: **Population**
  - File: `jurisdictions/municipalities-dynamic_properties.xlsx`
  - Sheet: `population`
  - Scope: Municipality ID, National
  - Unit: [ inhabitants ]
  - Notes: National values are for future projection

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

#### Water Demand Model {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

- Entity: **Water Demand Pattern**
  - File: `water_demand_model/water_demand_model-static_properties.xlsx`
  - Sheet: `residential`, `business`
  - Properties:
    - Water Demand Pattern ID (`demand_pattern_id`) [ - ]
    - Pattern values (`year_hour`) [ - ] *Dimension: hours of the year*

##### Dynamic Properties {.unnumbered .unlisted}

- Property: **Business Demand**
  - File: `water_demand_model/water_demand_model-dynamic_properties.xlsx`
  - Sheet: `per_business_demand`
  - Scope: National
  - Dimension: Uniform Uncertain
  - Unit: [ $m^3/business/hour$ ]

- Property: **House Demand**
  - File: `water_demand_model/water_demand_model-dynamic_properties.xlsx`
  - Sheet: `per_house_demand`
  - Scope: National
  - Dimension: Uniform Uncertain
  - Unit: [ $m^3/house/hour$ ]

#### Non-Revenue Water Model {.unnumbered .unlisted}

##### Static Properties {.unnumbered .unlisted}

- Property: **NRW Intervention success probability**
  - File: `configuration.yaml`
  - Label: `nrw_model-intervention_success_prob`
  - Scope: National
  - Dimension: Uniform Uncertain
  - Unit: [ - ]

##### Dynamic Properties {.unnumbered .unlisted}

- Property: **NRW Intervention Unit cost**
  - File: `jurisdictions/nrw_model-dynamic_properties.xlsx`
  - Sheet: `nrw_intervention-unit_cost`
  - Scope: National
  - Dimension: NRW class $\times$ Municipality size class
  - Unit: [ $\text{€}/year/km$ ]

#### Sources {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

- Entity: **Water Source** (Groundwater, Surface water, Desalination)
  - File: `sources/sources-static_properties.xlsx`
  - Sheet: `groundwater`, `surface_water`, `desalination`
  - Properties:   
    - Source Name (`name`) [ - ]
    - Source ID (`source_id`) [ - ]
    - Coordinates (`latitude`, `longitude`, `elevation`) [ degrees, degrees, m ]
    - Province (`province`) [ - ]
    - Closest municipality ID (`closest_municipality`)
    - Activation date (`activation_date`) [ - ]
    - Closure date (`closure_date`) [ - ]
    - Nominal capacity (`capacity-nominal`) [ $m^3/day$ ]
    - Specific energy (`opex-volum-energy_factor`) [ $kWh/m^3$ ]
    - Source permit (`permit`) [ m$m^3/year$ ] *Only groundwater*
    - Basin (`basin`) [ - ] *Only surface water*

##### Static Properties {.unnumbered .unlisted}

- Property: **Capacity Target Factor**
  - File: `sources/sources-static_properties.xlsx`
  - Sheet: `global`
  - Label: `capacity-target_factor`
  - Scope: Source Type
  - Unit [ - ]

- Property: **Operational costs - volumetric for non-energy - multiplier**
  - File: `sources/sources-static_properties.xlsx`
  - Sheet: `global`
  - Label `opex-volum-other-multiplier`
  - Scope: Source Type
  - Unit [ - ]

- Property: **Construction time**
  - File: `sources/sources-static_properties.xlsx`
  - Sheet: `global`
  - Scope: Source Type
  - Dimension: Uniform Uncertain
  - Unit [ - ]

- Property: **Operational costs - volumetric for energy (specific energy)**
  - File: `sources/sources-static_properties.xlsx`
  - Sheet: `global`
  - Scope: Source Type
  - Dimension: Uniform Uncertain
  - Unit [ - ]
  - Notes: sampled for new sources

##### Dynamic Properties {.unnumbered .unlisted}

- Property: **Unit cost of construction**
  - File: `sources/{source_type}-dynamic_properties.xlsx`
  - Sheet: `new_source-unit_cost`
  - Scope: National
  - Dimension: Source size
  - Unit: [ $\text{€}/(m^3/day)$ ]

- Property: **Operational costs - fixed (unit cost)**
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
  - Scope: National, Basin 
  - Unit: [ - ]

- Property: **Water displacement fine amount**
  - File: `sources/groundwater-dynamic_properties.xlsx`
  - Sheet: `water_displacement-fine_amount`
  - Scope: National
  - Dimension: Displacement severity
  - Unit: [ € ]

#### Pumping Infrastructure {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

- Entity: **Pumping Station**
  - File: `pumping_stations/pumping_stations-static_properties.xlsx`
  - Sheet: `entities`
  - Properties:   
    - Pumping Station ID (`pumping_station_id`) [ - ]
    - Assigned source (`assigned_source`) [ - ]
    - Installed pumps - options IDs (`pumps-option_ids`) [ - ]
    - Installed pumps - installation date (`pumps-installation_dates`) [ - ]
    - Installed pumps - decomission date (`pumps-end_dates`) [ - ]

- Entity: **Pump Options**
  - File: `pumps/pump_options-static_properties.xlsx`
  - Sheet: `options`
  - Properties:   
    - Pump Option ID (`option_id`) [ - ]
    - Name (`name`) [ - ]
    - Nominal Flow rate (`flow_rate-nominal`) [ $m^3/hour$ ]
    - Lifetime (`lifetime`) [ years ] Dimension: Uniform Uncertain
    
- Entity: **Pump Curve**
  - File: `pumps/pump_options-static_properties.xlsx`
  - Sheet: `{option_id}`
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

#### Piping Infrastructure {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

- Entity: **Connection**
  - File: `connections/connections-static_properties.xlsx`
  - Sheet: `provincial`, `sources`, `cross-provincial`
  - Properties:   
    - Connection ID (`connection_id`) [ - ]
    - From node (`from_node`) [ - ]
    - To node (`to_node`) [ - ]
    - Distance (`distance`) [ m ]
    - Minor loss coefficient (`minor_loss_coeff`) [ - ]
    - Installed pipes - options IDs (`pipes-option_ids`) [ - ]
    - Installed pipes - installation date (`pipes-installation_dates`) [ - ]

- Entity: **Pipe Options**
  - File: `pipes/pipe_options-static_properties.xlsx`
  - Sheet: `options`
  - Properties:   
    - Pipe Option ID (`option_id`) [ - ]
    - Diameter (`diameter`) [ mm ]
    - Material (`material`) [ - ]
    - Darcy friction factor - New pipe (`darcy_friction_factor-new_pipe`) [ - ]
    - Darcy friction factor - Decay rate (`darcy_friction_factor-decay_rate`) [ - ] Dimension: Uniform Uncertain
    - Lifetime (`lifetime`) [ years ] Dimension: Uniform Uncertain

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

- Property: **Temperature** (Average, Average of minimum/maximum daily temperatures, Maximum/Minimum temperature recorded)
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

#### Economy {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

- Entity: **Bonds**
  - File: `economy/bonds-static_properties.xlsx`
  - Sheet: `entities`
  - Properties:
    - Bond issuance ID (`bond_issuance_id`) [ - ]
    - Number of bonds (`n_bonds`) [ - ]
    - Issue date (`issue_date`) [ - ]
    - Maturity date (`maturity_date`) [ - ]
    - Coupon rate (`coupon_rate`) [ - ]
    - Water Utility ID (`water_utility_id`) [ - ]

##### Dynamic Properties {.unnumbered .unlisted}
- Property: **Inflation**
  - File: `economy/economy-dynamic_properties.xlsx`
  - Sheet: `inflation`
  - Scope: National
  - Unit: [ % ]

- Property: **Inflation Expectation**
  - File: `economy/economy-dynamic_properties.xlsx`
  - Sheet: `inflation-expected`
  - Scope: National
  - Unit: [ % ]

- Property: **Investor Demand**
  - File: `economy/economy-dynamic_properties.xlsx`
  - Sheet: `investor_demand`
  - Scope: National
  - Unit: [ - ]

#### Energy System {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

- Entity: **Solar Farm**
  - File: `energy/solar_farms-static_properties.xlsx`
  - Sheet: `entities`
  - Properties:
    - Solar farm ID (`solar_farm_id`) [ - ]
    - Capacity (`capacity`) [ - ]
    - Installation date (`installation_date`) [ - ]
    - Decommission date (`decommission_date`) [ - ]
    - Connected entity ID source/pumping station (`connected_entity_id`) [ - ]

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
  - Dimension: Hour of the week
  - Unit: [ - ]

- Property: **Grid Emission factor**
  - File: `energy/energy_system-dynamic_properties.xlsx`
  - Sheet: `grid_emission_factor`
  - Scope: National
  - Unit: [ $kgCO_2eq/kWh$ ]

- Property: **Solar Panel Unit Cost**
  - File: `energy/energy_system-dynamic_properties.xlsx`
  - Sheet: `solar_panel-unit_cost`
  - Scope: National
  - Unit: [  $\text{€}/kW$ ]

#### Water Utilities {.unnumbered .unlisted}

##### Entities {.unnumbered .unlisted}

- Entity: **Water Utility**
  - File: `water_utilities/water_utilities-static_properties.xlsx`
  - Sheet: `entities`
  - Properties:
    - Identifier (`water_utility_id`) [ - ]
    - Assigned provinces (`assigned_provinces`) [ - ]

##### Dynamic Properties {.unnumbered .unlisted}

- Property: **Funds Balance**
  - File: `water_utilities/water_utilities-dynamic_properties.xlsx`
  - Sheet: `balance`
  - Scope: Water Utility
  - Unit: [ € ]

- Property: **Water Price Fixed Component**
  - File: `water_utilities/water_utilities-dynamic_properties.xlsx`
  - Sheet: `water_price-fixed`
  - Scope: Water Utility
  - Unit: [ €/house ]

- Property: **Water Price Variable Component**
  - File: `water_utilities/water_utilities-dynamic_properties.xlsx`
  - Sheet: `water_price-variable`
  - Scope: Water Utility
  - Unit: [ $\text{€}/m^3$ ]

- Property: **Water Price Exchange Rate**
  - File: `water_utilities/water_utilities-dynamic_properties.xlsx`
  - Sheet: `water_price-selling`
  - Scope: Water Utility
  - Unit: [ $\text{€}/m^3$ ]

## Masterplan Files {.unnumbered .unlisted}

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
