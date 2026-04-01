from dataclasses import dataclass
from typing import Any, Dict, List, Self, Set, Union

import numpy as np
import pandas as pd

from ..core.base_model import bwf_entity
from ..core.utility import BWFTimeLike, timestampify
from ..sources.entities import WaterSource, SourcesContainer
from ..pumping_stations.entities import PumpingStation

from .dynamic_properties import SolarFarmsResults, EnergySysDB


@bwf_entity(db_type=EnergySysDB, results_type=SolarFarmsResults)
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
        
        assert self._dynamic_properties is not None
        assert self._results is not None

        # Register this solar farm on the connected entity
        self.connected_entity.register_solar_farm(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            self.ID: self.bwf_id,
            self.CAPACITY: self.capacity,
            self.INSTALLATION_DATE: self.installation_date.strftime('%Y-%m-%d'),
            self.DECOMMISSION_DATE: self.decommission_date.strftime('%Y-%m-%d'),
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
    
    def is_active(self, when: BWFTimeLike) -> bool:
        ts = timestampify(when)
        return (
            ts >= self.installation_date and 
            (pd.isna(self.decommission_date) or ts < self.decommission_date)
        )
    
    def track_yield(
            self,
            when: BWFTimeLike,
            values: np.ndarray
        ) -> Self:
        """
        This function tracks the source production (outflow).

        It expects an array of values with an hourly frequency.
        
        :param self: Description
        :param when: Description
        :type when: BWFTimeLike
        :param values: Description
        :type values: np.ndarray
        :return: Description
        :rtype: Self
        """
        # We expect one year of values at hourly frequence
        assert len(values) == 24*365

        self._results.commit(
            a_property=SolarFarmsResults.YIELD,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=len(values),
                freq='h'
            ),
            entity=self.bwf_id,
            values=values
        )

        return self
    
    @property
    def construction_unit_costs(self) -> pd.Series:
        return self._dynamic_properties[EnergySysDB.SOLAR_COST][self.connected_entity.province.state.cbs_id]

    @property
    def electricity_yield(self) -> pd.Series:
        df = self._results[SolarFarmsResults.YIELD]
        if self.bwf_id not in df.columns:
        
            return pd.Series(data=[], index=pd.DatetimeIndex([]))
        return df[self.bwf_id]
    
@dataclass(frozen=True)
class ElectricityPricePattern:

    # Begin date to represent when the electricity price created, since only one 
    # at a time is in place at every time, we can use as unique id.
    begin_date: pd.Timestamp

    values: np.ndarray

    def __eq__(self, other):
        if not isinstance(other, ElectricityPricePattern):
            return NotImplemented
        return self.begin_date == other.begin_date

    def __hash__(self):
        return int(self.begin_date.timestamp() * 1000)
    
    @classmethod
    def from_row(
        cls,
        timestamp: pd.Timestamp,
        values: pd.Series,
        scope: str
    ) -> Self:
        return cls(
            begin_date=timestamp,
            values=values[[
                scope+'-'+str(i) for i in range(24*7)
            ]].to_numpy()
        )

    @classmethod
    def from_array(
        cls,
        timestamp: pd.Timestamp,
        values: np.ndarray
    ) -> Self:
        return cls(
            begin_date=timestamp,
            values=values
        )