from dataclasses import dataclass
from typing import Dict, Self, Set, Tuple

import pandas as pd

from ..base_model import bwf_entity
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
        'balance': float,
        'price_fix_comp': float,
        'price_var_comp': float,
        'price_sel_comp': float
    }

    @property
    def municipalities(self):
        return set([m for p in self.m_provinces for m in p.municipalities])
    
    def active_municipalities(self, when: int | str | pd.Timestamp) -> set[Municipality]:
        """
        """
        return set([muni for muni in self.municipalities if muni.is_active(when=when)])
       
    @property
    def balance(self) -> pd.Series:
        return self._dynamic_properties[WaterUtilityDB.BALANCE][self.bwf_id]
    
    @property
    def price_fix_comp(self) -> pd.Series:
        return self._dynamic_properties[WaterUtilityDB.WPRICE_FIXED][self.bwf_id]
    
    @property
    def price_var_comp(self) -> pd.Series:
        return self._dynamic_properties[WaterUtilityDB.WPRICE_VARIA][self.bwf_id]
    
    @property
    def price_sel_comp(self) -> pd.Series:
        return self._dynamic_properties[WaterUtilityDB.WPRICE_SELL][self.bwf_id]
    
    