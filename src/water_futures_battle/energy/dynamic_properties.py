from ..base_model import DynamicProperties, bwf_database

@bwf_database
class EnergySysDB(DynamicProperties):
    NAME = 'energy_system-dynamic_properties'

    EPRICE_UNIT = 'electricity_price-unit_cost' 
    EPRICE_PATT = 'electricity_price-pattern'
    EMISS_FACTOR = 'grid_emission_factor'
    SOLAR_COST = 'solar_panel-unit_cost'
    
    EXOGENOUS_VARIABLES = [
        EPRICE_UNIT,
        EPRICE_PATT,
        EMISS_FACTOR,
        SOLAR_COST
    ]

