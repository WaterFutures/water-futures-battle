from ..base_model import DynamicProperties, bwf_database

@bwf_database
class EconomyDB(DynamicProperties):
    NAME = 'economy-dynamic_properties'

    INFLATION = 'inflation'
    INFEXPECT = 'inflation-expect'
    INVDEMAND = 'investor_demand'

    EXOGENOUS_VARIABLES = [
        INFLATION,
        INFEXPECT,
        INVDEMAND
    ]

