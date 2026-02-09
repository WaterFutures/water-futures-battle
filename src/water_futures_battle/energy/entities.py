from dataclasses import dataclass
from typing import Any, Dict, List, Self, Set, Union

import pandas as pd

from ..sources.entities import WaterSource, SourcesContainer
from ..pumping_stations.entities import PumpingStation

@dataclass(frozen=True)
class SolarFarm:
    
    bwf_id: str
    ID = 'solar_farm_id'
    ID_PREFIX = 'SF' # Solar Farm
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SolarFarm):
            return NotImplemented
        return self.bwf_id == other.bwf_id
    
    def __hash__(self) -> int:
        return hash(self.bwf_id)
    
    capacity: float
    CAPACITY = 'capacity'
    installation_date: pd.Timestamp
    INSTALLATION_DATE = 'installation_date'
    decommission_date: pd.Timestamp
    DECOMMISSION_DATE = 'decommission_date'
    connected_entity: Union[WaterSource, PumpingStation]
    CONN_ENTITY_ID = 'connected_entity_id'

    @classmethod
    def from_row(
        cls,
        row_data: pd.Series,
        sources: SourcesContainer,
        pumping_stations: Set[PumpingStation]
    ) -> Self:
        
        connected_entity_id: str = row_data[SolarFarm.CONN_ENTITY_ID]

        if connected_entity_id.startswith(PumpingStation.ID_PREFIX):
            connected_entity = next(ps for ps in pumping_stations if ps.bwf_id ==connected_entity_id)
        else:
            connected_entity = next(s for s in sources if s.bwf_id == connected_entity_id)

        instance = cls(
            bwf_id=row_data[SolarFarm.ID],
            capacity=row_data[SolarFarm.CAPACITY],
            installation_date=pd.to_datetime(row_data[SolarFarm.INSTALLATION_DATE], errors='raise'),
            decommission_date=pd.to_datetime(row_data[SolarFarm.DECOMMISSION_DATE], errors='raise'),
            connected_entity=connected_entity
        )

        return instance
    
    def __post_init__(self):

        # Register this solar farm on the connected entity
        self.connected_entity.register_solar_farm(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            self.ID: self.bwf_id,
            self.CAPACITY: self.capacity,
            self.INSTALLATION_DATE: self.installation_date,
            self.DECOMMISSION_DATE: self.decommission_date,
            self.CONN_ENTITY_ID: self.connected_entity.bwf_id
        }
    
    @classmethod
    def file_columns(cls) -> List[str]:
        return [
            cls.ID,
            cls.CAPACITY,
            cls.INSTALLATION_DATE,
            cls.DECOMMISSION_DATE,
            cls.CONN_ENTITY_ID
        ]