from dataclasses import dataclass
from typing import Any, Dict, Self, Set, Tuple

import pandas as pd

from ..core.base_model import bwf_entity
from ..core.utility import BWFTimeLike, timestampify
from ..jurisdictions.entities import Province, Municipality
from ..sources.entities import WaterSource
from ..pumping_stations.entities import PumpingStation
from ..connections.entities import Connection
from ..economy.entities import BondIssuance
from ..energy.entities import SolarFarm

from .dynamic_properties import WaterUtilityDB

@bwf_entity(db_type=WaterUtilityDB, results_type=None)
@dataclass(frozen=True)
class WaterUtility():
    NAME = 'water_utility'

    bwf_id: str
    ID = 'water_utility_id'
    ID_PREFIX = 'WU' # Water Utility

    m_provinces: Set[Province]
    ASSGN_PROVINCES = 'assigned_provinces'

    m_supplies: Dict[WaterSource, Tuple[PumpingStation, Connection]]

    m_peer_connections: Set[Connection]

    m_bonds: Set[BondIssuance]

    m_solar_farms: Set[SolarFarm]

    def __post_init__(self):
        pass

    def __eq__(self, other):
        if not isinstance(other, WaterUtility):
            return NotImplemented
        # Define equality based on the unique identifier
        return self.bwf_id == other.bwf_id

    def __hash__(self):
        # Base the hash only on the unique identifier (cbs_code)
        return hash(self.bwf_id)
 
    # Declaration of dynamic properties, i.e., those that have some type of time dependency
    # and how the yearlyView object will handle them
    # If they return a pd.Series, we declare the casting type (e.g., population)
    # If they have a time-agnostic method and a corresponding time-aware one, we map them
    DYNAMIC_PROPERTIES = {
        'municipalities': 'active_municipalities',
        'connections': 'active_connections',
        'balance': float,
        'price_fix_comp': float,
        'price_var_comp': float,
        'price_sel_comp': float
    }

    @property
    def municipalities(self) -> Set[Municipality]:
        return set([m for p in self.m_provinces for m in p.municipalities])
    
    def active_municipalities(self, when: BWFTimeLike) -> Set[Municipality]:
        """
        """
        return set([m for m in self.municipalities if m.is_active(when=when)])
       
    @property
    def connections(self) -> Set[Connection]:
        all_connections = self.m_peer_connections | set(
            [c for s, (ps, c) in self.m_supplies.items()]
        )
        return all_connections
    
    def active_connections(self, when: BWFTimeLike) -> Set[Connection]:
        return set([c for c in self.connections if c.is_active(when=when)])
    
    @property
    def pumping_stations(self) -> Set[PumpingStation]:
        return set([
            ps for s, (ps, c) in self.m_supplies.items()
        ])

    @property
    def balance(self) -> pd.Series:
        return self._dynamic_properties[WaterUtilityDB.BALANCE][self.bwf_id]
    
    def set_balance(
            self,
            when: BWFTimeLike,
            value: float
        ) -> Self:
        
        ts = timestampify(when)

        self._dynamic_properties[WaterUtilityDB.BALANCE].loc[ts, self.bwf_id] = value

        return self
    
    @property
    def price_fix_comp(self) -> pd.Series:
        return self._dynamic_properties[WaterUtilityDB.WPRICE_FIXED][self.bwf_id]
    
    @property
    def price_var_comp(self) -> pd.Series:
        return self._dynamic_properties[WaterUtilityDB.WPRICE_VARIA][self.bwf_id]
    
    @property
    def price_sel_comp(self) -> pd.Series:
        return self._dynamic_properties[WaterUtilityDB.WPRICE_SELL][self.bwf_id]
    
    def set_water_prices(
            self,
            when: BWFTimeLike,
            price_fix_comp: float,
            price_var_comp: float,
            price_sel_comp: float
    ) -> Self:
        
        ts = timestampify(when)
        
        self._dynamic_properties[WaterUtilityDB.WPRICE_FIXED].loc[ts, self.bwf_id] = price_fix_comp

        self._dynamic_properties[WaterUtilityDB.WPRICE_VARIA].loc[ts, self.bwf_id] = price_var_comp

        self._dynamic_properties[WaterUtilityDB.WPRICE_SELL].loc[ts, self.bwf_id] = price_sel_comp

        return self
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            self.ID: self.bwf_id,
            self.ASSGN_PROVINCES: ';'.join([pv.cbs_id for pv in self.m_provinces])
        }