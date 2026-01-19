from dataclasses import dataclass
from typing import Self, Set, Tuple

import pandas as pd

from ..climate.dynamic_properties import ClimateDB
from ..economy.dynamic_properties import EconomyDB
from ..economy.entities import BondsSettings
from ..jurisdictions import State
from ..water_demand_model.properties import WaterDemandModelDB
from ..water_demand_model.entities import WaterDemandModelPatterns
from ..nrw_model.dynamic_properties import NRWModelDB
from ..pumps.entities import PumpOption
from ..energy.dynamic_properties import EnergySysDB
from ..pipes.entities import PipeOption
from ..connections.entities import Connection
from ..water_utility_model.entities import WaterUtility

@dataclass(frozen=True)
class NationalContext:
    NAME = 'national_context'

    # Static properties and settings
    state: State
    water_utilities: Set[WaterUtility]
    cross_utility_connections: Set[Connection]
    bonds_settings: BondsSettings 
    water_demand_patterns: WaterDemandModelPatterns
    pump_options: Set[PumpOption]
    pipe_options: Set[PipeOption]

    # Dynamic properties
    climate: ClimateDB
    economy: EconomyDB
    water_demand_model_db: WaterDemandModelDB
    nrw_model_db: NRWModelDB
    energy_sys: EnergySysDB

    @property
    def average__maximum_temperature(self) -> pd.Series:
        return self.climate[ClimateDB.TEMPERATURE_MAX_AVG][self.state.cbs_id]
    
    @property
    def inflation(self) -> pd.Series:
        return self.economy[EconomyDB.INFLATION][self.state.cbs_id]
    
    @property
    def water_demand_model_data(self) -> Tuple[WaterDemandModelPatterns, WaterDemandModelDB]:
        return self.water_demand_patterns, self.water_demand_model_db

    @property
    def nrw_intervention_costs(self) -> pd.DataFrame:
        return self.nrw_model_db[NRWModelDB.COST]