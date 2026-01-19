from ..base_model import DynamicProperties, bwf_database

@bwf_database
class WaterUtilityDB(DynamicProperties):
    NAME = 'water_utilities-dynamic_properties'

    BALANCE = 'balance'
    WPRICE_FIXED = 'water_price-fixed'
    WPRICE_VARIA = 'water_price-variable'
    WPRICE_SELL = 'water_price-selling'

    ENDOGENOUS_VARIABLES = [
        BALANCE,
        WPRICE_FIXED,
        WPRICE_VARIA,
        WPRICE_SELL
    ]

