
from .dynamic_properties import ClimateDB

def configure_climate(
        config: dict
    ) -> ClimateDB:

    return ClimateDB.load_from_file(config[ClimateDB.NAME])