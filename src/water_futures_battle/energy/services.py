from typing import Set, Tuple

from ..sources.entities import SourcesContainer
from ..pumping_stations.entities import PumpingStation

from .dynamic_properties import EnergySysDB
from .entities import SolarFarm

def configure_energy_system(
        config: dict,
        sources: SourcesContainer,
        pumping_stations: Set[PumpingStation]
    ) -> Tuple[EnergySysDB, Set[SolarFarm]]:
    
    energysys_db = EnergySysDB.load_from_file(config[EnergySysDB.NAME])

    solar_farms = set()

    return energysys_db, solar_farms