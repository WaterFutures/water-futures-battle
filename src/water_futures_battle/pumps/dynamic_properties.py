from ..base_model import DynamicProperties, bwf_database, bwf_results

@bwf_database
class PumpOptionsDB(DynamicProperties):
    NAME = 'pump_options-dynamic_properties'

    COST = 'new_pump-cost'

    ENDOGENOUS_VARIABLES = [
        COST
    ]

@bwf_results
class PumpsResults(DynamicProperties):
    NAME = 'pumps-results'

    ENERGY = 'electrical_energy'

    TRACKED_VARIABLES = [
        ENERGY
    ]