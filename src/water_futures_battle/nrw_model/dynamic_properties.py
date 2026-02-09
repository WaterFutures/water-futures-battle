from ..core.base_model import DynamicProperties, bwf_database

@bwf_database
class NRWModelDB(DynamicProperties):
    NAME = 'nrw_model-dynamic_properties'
    
    COST = 'nrw_intervention-unit_cost'

    EXOGENOUS_VARIABLES = [
        COST
    ]
