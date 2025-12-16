\newpage

\appendix

# Appendix A

This Appendix A describes the data contained within the supplementary material (zipped data folder).

## EPANET Networks Files {.unnumbered .unlisted}

The provided network files were generated using EPANET 2.3.
Unfortunately, most common EPANET libraries and software (e.g., WNTR and EPANET for Windows) are not keeping up with the versions and they may generate warnings upon opening or fail to open them at all.
When using a library based on an outdated version of EPANET, the hydraulic results will also differ, as EPANET 2.3 features numerous bug fixes with respect to previous versions.

For these compatibility reason and to ensure consistency between results, the solutions will be submitted through an ad-hoc form and inp files will be rejected.
The sole reference for correctness is the evaluator's computations, which uses the latest EPANET 2.3 library.

At the time of writing, we suggest using [EPANET.js](https://epanetjs.com) to visualize the networks overlaid on a map of the Netherlands, while for hydraulic computations, we recommend using the EPANET-PLUS Python library, as it is currently the only one offering EPANET 2.3 support [@github:epanetplus].

## System Entities {.unnumbered .unlisted}

### Water Utilities {.unnumbered .unlisted}

- File: `water_utilities/water_utilities-static_properties.xlsx`

  Variables:
  - Identifier (`water_utility_id`) [ - ]
  - Assigned provinces (`assigned_provinces`) [ - ]

### Municipalities {.unnumbered .unlisted}

- File: `jurisdictions/jurisdictions-static_properties.xlsx`

  Sheet: `regions`

    Variables:
    - Region name (`name`) [ - ]
    - Region ID (`cbs_id`) [ - ]      #I DID NOT INCLUDE STATE

  Sheet: `provinces`

    Variables:
    - Province name (`name`) [ - ]
    - Province ID (`cbs-id`) [ - ]
    - Region (`region`) [ - ]

  Sheet: `municipalities`

    Variables:
    - Municipality name (`name`) [ - ]
    - Municipality ID (`cbs_id`) [ - ]
    - Municipality elevation (`elevation`) [ - ]       #TODO DECIDE WHICH PARAMETERS WE SHOULD INCLUDE
 
- File: `jurisdictions/municipalities-dynamic_properties.xlsx`
  
  Sheet: `population`

  Variables:

  - Municipality ID  [ - ] 
  - Population [ inhabitants ]
  
  Sheet: `surface-land`

  Variables:
  
  - Municipality ID  [ - ] 
  - Land Area [ $km^2$ ]

  Sheet: `surface-water-inland`
  
  Variables:
  
  - Municipality ID  [ - ] 
  - Water Area [ $km^2$ ]

  Sheet: `surface-water-open`
  
  Variables:
  
  - Municipality ID  [ - ] 
  - Water Area [ $km^2$ ]

  Sheet: `n_houses`
  
  Variables:
  
  - Municipality ID  [ - ] 
  - Number Houses [ houses ]

  Sheet: `n_businesses`
  
  Variables:
  
  - Municipality ID  [ - ] 
  - Number businesses [ businesses ]

  Sheet: `dist_network-age-avg`
  
  Variables:
  
  - Municipality ID  [ - ] 
  - Network Age [ years ]

### Water Sources {.unnumbered .unlisted}

- File: `sources\sources-static_properties.xlsx`
  
  Sheet: `groundwater`

    Variables:
  
    - Source ID (`source_id`) [ - ]
    - Source elevation (`elevation`) [ m ]
    - Province (`province`) [ - ]
    - Closest municipality (`closest_municipality`)
    - Source nominal capacity (`capacity-nominal`) [ meters<sup>3</sup> ]
    - Source permit (`permit`) [ meters<sup>3</sup> ]

  Sheet: `surface_water`

    Variables:
  
    - Source ID (`source_id`) [ - ]
    - Source elevation (`elevation`) [ m ]
    - Province (`province`) [ - ]
    - Closest municipality (`closest_municipality`)
    - Source nominal capacity (`capacity-nominal`) [ m<sup>3</sup> ]

  Sheet: `desalination`

    Variables:
  
    - Source ID (`source_id`) [ - ]
    - Source elevation (`elevation`) [ m ]
    - Province (`province`) [ - ]
    - Closest municipality (`closest_municipality`)

- File: `sources\groundwater-dynamic_properties.xlsx`, `surface-dynamic_properties.xlsx`, `desalination-dynamic_properties.xlsx`

  Sheet: `new_source-unit_cost`
  
  Variables:
  
  - Source Size [ - ]
  - Cost [ $\text{€}/m^3$]

  Sheet: `opex-fixed`
  
  Variables:
  
  - Source Size [ - ]
  - Cost [ $\text{€}/m^3$ ]

  Sheet: `opex-volum-other`
  
  Variables:
  
  - Source Size [ - ]
  - Cost [ $\text{€}/m^3$ ]

  Sheet: `availability_factor`
  
  Variables:
  
  - Source  [ - ]
  - Availability [ - ]

### Pumping Stations {.unnumbered .unlisted}

  - File: `pumps\pump_options-static_properties.xlsx`

  Sheet: `options`
  
  Variables:
  
    - Pump ID (`option_id`) [ - ]
    - Nominal Flowrate (`flow_rate-nominal`) [ $m^3/hour$ ]
    - Lifespan (`lifespan-min`) [ years ]

  Sheet: `PU01`, `PU02`, `PU03`, `PU04`
  
  Variables:
  
    - Flowrate (`flowrate`) [ $m^3/hour$ ]
    - Head (`head`) [ m ]
    - Efficiency (`efficiency`) [ - ]
  
### Connections {.unnumbered .unlisted}

  - File: `connections\connections-static_properties.xlsx`
  
  Sheet: `provincial`

  Variables:

    - Connection ID (`connection_id`) [ - ]  
    - Starting Node (`from_node`) [ - ]
    - Ending Node (`to_node`) [ - ]
    - Distance (`distance`) [ meters ]
    - Pipe Type (`pipes-options_ids`) [ - ]

  Sheet: `sources`

  Variables:

    - Connection ID (`connection_id`) [ - ]  
    - Starting Node (`from_node`) [ - ]
    - Ending Node (`to_node`) [ - ]
    - Distance (`distance`) [ meters ]
    - Pipe Type (`pipes-options_ids`) [ - ]

  Sheet: `cross-provincial`

  Variables:

    - Connection ID (`connection_id`) [ - ]  
    - Starting Node (`from_node`) [ - ]
    - Ending Node (`to_node`) [ - ]
    - Distance (`distance`) [ meters ]

## System External Drivers {.unnumbered .unlisted}

These data has not been released in a formatted way yet.
Have a look at the `raw-data` folder.

### Climate {.unnumbered .unlisted}

### Energy System {.unnumbered .unlisted}

### Economy {.unnumbered .unlisted}

## Problem Settings {.unnumbered .unlisted}

- File: `configuration.yaml`

  Variables:

  - Start year (`start_year`) [ - ]
  - End year (`end_year`) [ - ]
  - National budget (`national_budget`) [€]