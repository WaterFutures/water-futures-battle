from ..base_model import DynamicProperties, bwf_database


@bwf_database
class WaterDemandModelDB(DynamicProperties):
    NAME = 'water_demand_model-dynamic_properties'

    PER_HOUSE_DEMAND = 'per_house_demand'
    PER_BUSINESS_DEMAND = 'per_business_demand'

    EXOGENOUS_VARIABLES = [
        PER_HOUSE_DEMAND,
        PER_BUSINESS_DEMAND
    ]
