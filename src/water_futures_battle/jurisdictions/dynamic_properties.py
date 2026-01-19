from ..base_model import DynamicProperties, bwf_database, bwf_results
from ..nrw_model.enums import NRWClass

@bwf_database
class MunicipalitiesDB(DynamicProperties):
    NAME = 'municipalities-dynamic_properties'

    POPULATION = 'population'
    # POPULATION_VSURBAN = 'population-very_strong_urban'
    # POPULATION_SURBAN = 'population-strong_urban'
    # POPULATION_MURBAN = 'population-moderate_urban'
    # POPULATION_LURBAN = 'population-little_urban'
    # POPULATION_NURBAN = 'population-non_urban'
    AREA_LAND = 'surface-land'
    AREA_WATERIN = 'surface-water-inland'
    AREA_WATEROUT = 'surface-water-open'
    N_HOUSES = 'n_houses'
    N_BUSINESSES = 'n_businesses'
    ADI = 'disposable_income-avg'
    ASSOC_DM_R1 = 'assoc_dem_pat-residential-1'
    ASSOC_DM_R2 = 'assoc_dem_pat-residential-2'
    ASSOC_DM_B = 'assoc_dem_pat-business'

    DISTNET_AVG_AGE = 'dist_network-age-avg'

    EXOGENOUS_VARIABLES = [
        POPULATION,
        # POPULATION_VSURBAN,
        # POPULATION_SURBAN,
        # POPULATION_MURBAN,
        # POPULATION_LURBAN,
        # POPULATION_NURBAN,
        AREA_LAND,
        AREA_WATERIN,
        AREA_WATEROUT,
        N_HOUSES,
        N_BUSINESSES,
        ADI,
        ASSOC_DM_R1,
        ASSOC_DM_R2,
        ASSOC_DM_B
    ]
    ENDOGENOUS_VARIABLES = [
        DISTNET_AVG_AGE
    ]


@bwf_results
class MunicipalitiesResults(DynamicProperties):
    NAME = 'municipalites-results'

    NRW_DEMAND = 'non_revenue_water-demand'
    DEMAND = 'demand'

    TRACKED_VARIABLES = [
        DEMAND
    ]