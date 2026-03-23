from ..core.base_model import DynamicProperties, bwf_database, BWFResult

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

class WaterUtilityResults(BWFResult):
    NAME = 'water_utilities-results'

    NET_WATER_EXCHANGE = 'net_water_exchange'

    DEBT = 'debt'
    BA2D_RATIO = 'bond_ratio'

    CAPEX = 'capex'
    OPEX = 'opex'
    REV = 'revenue'
    WLR = 'NRW_mitigation_budget'
    WIC = 'water_import_cost'
    WUIB = 'investment_budget'
    INT = 'interests_paid'
    PRI = 'principal_amount_paid'

    GHG_EMB = 'ghg_embedded_emissions'
    GHG_OPE = 'operations_ghg_emissions'

    TRACKED_VARIABLES = [
        NET_WATER_EXCHANGE,
        DEBT,
        BA2D_RATIO,

        CAPEX,
        OPEX,
        REV,
        WLR,
        WIC,
        WUIB,
        INT,
        PRI,

        GHG_EMB,
        GHG_OPE
    ]