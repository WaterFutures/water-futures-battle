from ..base_model import DynamicProperties, bwf_database, bwf_results

@bwf_database
class PipeOptionsDB(DynamicProperties):
    NAME = 'pipe_options-dynamic_properties'

    COST = 'new_pipe-unit_cost'
    EMISSION = 'new_pipe-emissions_factor'

    EXOGENOUS_VARIABLES = [
        EMISSION
    ]

    ENDOGENOUS_VARIABLES = [
        COST
    ]



@bwf_results
class PipesResults(DynamicProperties):
    NAME = 'pipes-results'

    FLOWRATE = 'flow_rate'

    TRACKED_VARIABLES = [
        FLOWRATE
    ]