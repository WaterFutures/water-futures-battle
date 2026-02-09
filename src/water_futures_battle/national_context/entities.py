from dataclasses import dataclass
from typing import Self, Set, Tuple

import pandas as pd

from ..core.utility import filter_columns
from ..climate.dynamic_properties import ClimateDB
from ..economy.dynamic_properties import EconomyDB
from ..economy.entities import BondsSettings
from ..jurisdictions.dynamic_properties import MunicipalitiesDB
from ..jurisdictions.entities import State, Municipality
from ..water_demand_model.properties import WaterDemandModelDB
from ..water_demand_model.entities import WaterDemandModelPatterns
from ..nrw_model.dynamic_properties import NRWModelDB
from ..nrw_model.entities import NRWModelSettings, NRWInterventionCostTable
from ..sources.properties import SourcesDB, SourceCostTable, SourceUncertainCostTable
from ..sources.entities import GroundWater, SurfaceWater, Desalination, SourcesContainer, SourcesSettings
from ..pumps.dynamic_properties import PumpOptionsDB
from ..pumps.entities import PumpOption
from ..pumping_stations.entities import PumpingStation
from ..energy.dynamic_properties import EnergySysDB
from ..energy.entities import SolarFarm
from ..pipes.dynamic_properties import PipeOptionsDB, PipesDB
from ..pipes.entities import PipeOption, Pipe
from ..connections.entities import Connection
from ..water_utilities.dynamic_properties import WaterUtilityDB
from ..water_utilities.entities import WaterUtility

@dataclass(frozen=True)
class NationalContext:
    NAME = 'national_context'

    # Static properties and settings
    state: State
    water_utilities: Set[WaterUtility]
    cross_utility_connections: Set[Connection]
    bonds_settings: BondsSettings 
    water_demand_patterns: WaterDemandModelPatterns
    nrw_settings: NRWModelSettings
    sources_settings: SourcesSettings
    pump_options: Set[PumpOption]
    pipe_options: Set[PipeOption]

    # Dynamic properties
    climate: ClimateDB
    economy: EconomyDB
    water_demand_model_db: WaterDemandModelDB
    nrw_model_db: NRWModelDB
    energy_sys: EnergySysDB

    # "Private" collections
    _all_sources: SourcesContainer
    _all_pumping_stations: Set[PumpingStation]
    _all_solar_farms: Set[SolarFarm]
    _all_connections: Set[Connection]

    @property
    def water_utilities_db(self) -> WaterUtilityDB:
        return WaterUtility._dynamic_properties

    @property
    def municipalities_db(self) -> MunicipalitiesDB:
        return Municipality._dynamic_properties

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
    def nrw_model_data(self) -> Tuple[NRWModelSettings, NRWModelDB]:
        return self.nrw_settings, self.nrw_model_db

    @property
    def nrw_intervention_costs(self) -> pd.DataFrame:
        df = self.nrw_model_db[NRWModelDB.COST]
        national_columns = filter_columns(df, self.state.cbs_id)
        return df[national_columns]
    
    def set_nrw_intervention_costs(
            self,
            when: pd.Timestamp,
            value: pd.Series
    ) -> Self:
        self.nrw_model_db[NRWModelDB.COST].loc[when, value.index] = value.values
        return self

    @property
    def gw_sources_db(self) -> SourcesDB:
        return GroundWater._dynamic_properties

    @property
    def gw_sources_unit_cost(self) -> pd.DataFrame:
        df = self.gw_sources_db[SourcesDB.UNIT_COST]
        national_columns = filter_columns(df, self.state.cbs_id)
        return df[national_columns]
    
    def set_gw_sources_unit_cost(
            self,
            when: pd.Timestamp,
            value: pd.Series
        ) -> Self:
        self.gw_sources_db[SourcesDB.UNIT_COST].loc[when, value.index] = value.values
        return self

    @property
    def gw_sources_opex_fixed_cost(self) -> pd.DataFrame:
        df = self.gw_sources_db[SourcesDB.OPEX_FIXED]
        national_columns = filter_columns(df, self.state.cbs_id)
        return df[national_columns]

    def set_gw_sources_opex_fixed_cost(
            self,
            when: pd.Timestamp,
            value: pd.Series
        ) -> Self:
        self.gw_sources_db[SourcesDB.OPEX_FIXED].loc[when, value.index] = value.values
        return self

    @property
    def gw_sources_opex_volum_other_cost(self) -> pd.DataFrame:
        df = self.gw_sources_db[SourcesDB.OPEX_VOLUM_OTHER]
        national_columns = filter_columns(df, self.state.cbs_id)
        return df[national_columns]

    def set_gw_sources_opex_volum_other_cost(
            self,
            when: pd.Timestamp,
            value: pd.Series
        ) -> Self:
        self.gw_sources_db[SourcesDB.OPEX_VOLUM_OTHER].loc[when, value.index] = value.values
        return self
    
    # Surface Water (sw) getters and setters
    @property
    def sw_sources_db(self) -> SourcesDB:
        return SurfaceWater._dynamic_properties

    @property
    def sw_sources_unit_cost(self) -> pd.DataFrame:
        df = self.sw_sources_db[SourcesDB.UNIT_COST]
        national_columns = filter_columns(df, self.state.cbs_id)
        return df[national_columns]

    def set_sw_sources_unit_cost(
            self,
            when: pd.Timestamp,
            value: pd.Series
        ) -> Self:
        self.sw_sources_db[SourcesDB.UNIT_COST].loc[when, value.index] = value.values
        return self

    @property
    def sw_sources_opex_fixed_cost(self) -> pd.DataFrame:
        df = self.sw_sources_db[SourcesDB.OPEX_FIXED]
        national_columns = filter_columns(df, self.state.cbs_id)
        return df[national_columns]

    def set_sw_sources_opex_fixed_cost(
            self,
            when: pd.Timestamp,
            value: pd.Series
        ) -> Self:
        self.sw_sources_db[SourcesDB.OPEX_FIXED].loc[when, value.index] = value.values
        return self

    @property
    def sw_sources_opex_volum_other_cost(self) -> pd.DataFrame:
        df = self.sw_sources_db[SourcesDB.OPEX_VOLUM_OTHER]
        national_columns = filter_columns(df, self.state.cbs_id)
        return df[national_columns]

    def set_sw_sources_opex_volum_other_cost(
            self,
            when: pd.Timestamp,
            value: pd.Series
        ) -> Self:
        self.sw_sources_db[SourcesDB.OPEX_VOLUM_OTHER].loc[when, value.index] = value.values
        return self

    # Desalination (des) getters and setters
    @property
    def des_sources_db(self) -> SourcesDB:
        return Desalination._dynamic_properties

    @property
    def des_sources_unit_cost(self) -> pd.DataFrame:
        df = self.des_sources_db[SourcesDB.UNIT_COST]
        national_columns = filter_columns(df, self.state.cbs_id)
        return df[national_columns]

    def set_des_sources_unit_cost(
            self,
            when: pd.Timestamp,
            value: pd.Series
        ) -> Self:
        self.des_sources_db[SourcesDB.UNIT_COST].loc[when, value.index] = value.values
        return self

    @property
    def des_sources_opex_fixed_cost(self) -> pd.DataFrame:
        df = self.des_sources_db[SourcesDB.OPEX_FIXED]
        national_columns = filter_columns(df, self.state.cbs_id)
        return df[national_columns]

    def set_des_sources_opex_fixed_cost(
            self,
            when: pd.Timestamp,
            value: pd.Series
        ) -> Self:
        self.des_sources_db[SourcesDB.OPEX_FIXED].loc[when, value.index] = value.values
        return self

    @property
    def des_sources_opex_volum_other_cost(self) -> pd.DataFrame:
        df = self.des_sources_db[SourcesDB.OPEX_VOLUM_OTHER]
        national_columns = filter_columns(df, self.state.cbs_id)
        return df[national_columns]

    def set_des_sources_opex_volum_other_cost(
            self,
            when: pd.Timestamp,
            value: pd.Series
        ) -> Self:
        self.des_sources_db[SourcesDB.OPEX_VOLUM_OTHER].loc[when, value.index] = value.values
        return self
    
    @property
    def pump_options_db(self) -> PumpOptionsDB:
        return PumpOption._dynamic_properties

    @property
    def new_pumps_costs(self) -> pd.DataFrame:
        return self.pump_options_db[PumpOptionsDB.COST]
    
    def set_new_pumps_costs(
            self,
            when: pd.Timestamp,
            value: pd.Series
    ) -> Self:
        self.new_pumps_costs.loc[when, value.index] = value.values
        return self
    
    @property
    def pipe_options_db(self) -> PipeOptionsDB:
        return PipeOption._dynamic_properties

    @property
    def new_pipes_costs(self) -> pd.DataFrame:
        return self.pipe_options_db[PipeOptionsDB.COST]

    def set_new_pipes_costs(
            self,
            when: pd.Timestamp,
            value: pd.Series
    ) -> Self:
        self.new_pipes_costs.loc[when, value.index] = value.values
        return self
    
    @property
    def pipes_db(self) -> PipesDB:
        return Pipe._dynamic_properties
