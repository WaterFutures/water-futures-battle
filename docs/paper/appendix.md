\newpage

\appendix

# Appendix A

This Appendix A describes the data contained within the supplementary material (zipped data folder).
Specifically we listing the variables included in each file along their unit and coded name.

## System Entities {.unnumbered .unlisted}

### Water Utilities {.unnumbered .unlisted}

- File: `water_utilities/water_utilities-static_properties.xlsx`

  Variables:
  - Identifier (`water_utility_id`) [ - ]
  - Assigned provinces (`assigned_provinces`) [ - ]

### Municipalities {.unnumbered .unlisted}

- File: `jurisdictions/jurisdictions-static_properties.xlsx`

 Variables:
 - var 1 () []: file, sheet

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
  - Population [ habitants ]
  
  Sheet: `surface-land`
  Variables:
  - Municipality ID  [ - ] 
  - Land Area [ km<sup>2</sup> ]

  Sheet: `surface-water-inland`
  Variables:
  - Municipality ID  [ - ] 
  - Water Area [ km<sup>2</sup> ]

  Sheet: `surface-water-open`
  Variables:
  - Municipality ID  [ - ] 
  - Water Area [ km<sup>2</sup> ]

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
    - Source elevation (`elevation`) [ meter ]
    - Province (`province`) [ - ]
    - Closest municipality (`closest_municipality`)
    - Source nominal capacity (`capacity-nominal`) [ meters<sup>3</sup> ]
    - Source permit (`permit`) [ meters<sup>3</sup> ]

  Sheet: `surface_water`

    Variables:
    - Source ID (`source_id`) [ - ]
    - Source elevation (`elevation`) [ meter ]
    - Province (`province`) [ - ]
    - Closest municipality (`closest_municipality`)
    - Source nominal capacity (`capacity-nominal`) [ meter<sup>3</sup> ]

  Sheet: `desalination`

    Variables:
    - Source ID (`source_id`) [ - ]
    - Source elevation (`elevation`) [ meter ]
    - Province (`province`) [ - ]
    - Closest municipality (`closest_municipality`)

- File: `sources\groundwater-dynamic_properties.xlsx,surface-dynamic_properties.xlsx,desalination-dynamic_properties.xlsx`

  Sheet: `new_source-unit_cost
  Variables:
  - Source Size [ - ]
  - Cost [ euros / meter<sup>3</sup>]

  Sheet: `opex-fixed`
  Variables:
  - Source Size [ - ]
  - Cost [ euros / meter<sup>3</sup> ]

  Sheet: `opex-volum-other`
  Variables:
  - Source Size [ - ]
  - Cost [ euros / meter<sup>3</sup> ]

  Sheet: `availability_factor`
  Variables:
  - Source  [ - ]
  - Availability [ - ]


### Pumping Stations {.unnumbered .unlisted}

  - File: `pumps\pump_options-static_properties.xlsx`
  Sheet: `options`
    Variables:
    - Pump ID (`option_id`) [ - ]
    - Nominal Flowrate (`flow_rate-nominal`) [ meter<sup>3</sup> / hour ]
    - Lifespan (`lifespan-min`) [ years ]

  Sheet: `PU01`, `PU02`, `PU03`, `PU04`
    Variables:
    - Flowrate (`flowrate`) [ meter<sup>3</sup> / hour ]
    - Head (`head`) [ meter ]
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

### Climate {.unnumbered .unlisted}

### Energy System {.unnumbered .unlisted}

### Economy {.unnumbered .unlisted}

## Problem Settings {.unnumbered .unlisted}

- File: `configuration.yaml`

  Variables:
  - Start year (`start_year`) [ - ]
  - End year (`end_year`) [ - ]