from ..base_model import DynamicProperties, bwf_database

@bwf_database
class ClimateDB(DynamicProperties):
    NAME = 'climate-dynamic_properties'

    TEMPERATURE_AVG = 'temperature-avg'
    TEMPERATURE_MIN_AVG = 'temperature-min-avg'
    TEMPERATURE_MAX_AVG = 'temperature-max-avg'
    TEMPERATURE_WARMDAY = 'temperature-warmest_day'
    TEMPERATURE_COLDDAY = 'temperature-coldest_day'
    PRECIPITATION = 'precipitation'
    SOLARRAD = 'solar_radiation-avg'
    SPEI = 'SPEI'

    EXOGENOUS_VARIABLES = [
        TEMPERATURE_AVG,
        TEMPERATURE_MIN_AVG,
        TEMPERATURE_MAX_AVG,
        TEMPERATURE_WARMDAY,
        TEMPERATURE_COLDDAY,
        PRECIPITATION,
        SOLARRAD,
        SPEI
    ]