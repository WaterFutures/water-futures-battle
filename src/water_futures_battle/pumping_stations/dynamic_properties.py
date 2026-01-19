from ..base_model import DynamicProperties, bwf_database, bwf_results

# Pumping station don't have dynamic properties but they will have results

@bwf_results
class PumpingStationResults(DynamicProperties):
    NAME = 'pumping_station-results'
