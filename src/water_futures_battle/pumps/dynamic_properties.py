from ..core.base_model import DynamicProperties, bwf_database, BWFResult

@bwf_database
class PumpOptionsDB(DynamicProperties):
    NAME = 'pump_options-dynamic_properties'

    COST = 'new_pump-cost'

    ENDOGENOUS_VARIABLES = [
        COST
    ]

class PumpsResults(BWFResult):
    NAME = 'pumps-results'

    ELE_ENERGY = 'electrical_energy'

    TRACKED_VARIABLES = [
        ELE_ENERGY
    ]