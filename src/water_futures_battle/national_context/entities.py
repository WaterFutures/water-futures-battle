from dataclasses import dataclass
from typing import Dict, Optional, Self, Set, Tuple

from epanet_plus import EPyT
import pandas as pd 

from ..core.utility import filter_columns, BWFTimeLike, timestampify
from ..climate.dynamic_properties import ClimateDB
from ..economy.dynamic_properties import EconomyDB
from ..economy.entities import BondsSettings
from ..jurisdictions.dynamic_properties import MunicipalitiesDB, MunicipalitiesResults
from ..jurisdictions.entities import State, Municipality
from ..water_demand_model.properties import WaterDemandModelDB
from ..water_demand_model.entities import WaterDemandModelPatterns
from ..nrw_model.dynamic_properties import NRWModelDB
from ..nrw_model.entities import NRWModelSettings, NRWInterventionCostTable
from ..sources.properties import SourcesDB, SourceCostTable, SourceUncertainCostTable, SourcesResults
from ..sources.entities import WaterSource, GroundWater, SurfaceWater, Desalination, SourcesContainer, SourcesSettings
from ..pumps.dynamic_properties import PumpOptionsDB, PumpsResults
from ..pumps.entities import PumpOption, Pump
from ..pumping_stations.entities import PumpingStation
from ..energy.dynamic_properties import EnergySysDB, SolarFarmsResults
from ..energy.entities import SolarFarm, ElectricityPricePattern
from ..pipes.dynamic_properties import PipeOptionsDB, PipesDB
from ..pipes.entities import PipeOption, Pipe
from ..connections.entities import PeerConnection, Connection
from ..water_utilities.dynamic_properties import WaterUtilityDB, WaterUtilityResults
from ..water_utilities.entities import WaterUtility

class WaterUtilitiesCluster:
    """
    Class to represent a set of water utilities connected between them through 
    some peer connections.
    """
    def __init__(self,
                 water_utilities: Set[WaterUtility],
                 cross_utility_connections: Set[PeerConnection],
                 year: int,
                 network: Optional[EPyT] = None
        ):
        self.water_utilities = water_utilities
        self.cross_utility_connections = cross_utility_connections
        self.year = year
        self.network = network

    @property
    def n_water_utilities(self) -> int:
        return len(self.water_utilities)

    @property
    def water_sources(self) -> Set[WaterSource]:
        return set([
            s for wu in self.water_utilities for s in wu.active_sources(when=self.year)
        ])
    
    @property
    def filename(self) -> str:
        utilities_names = '_'.join(
            wu.bwf_id
            for wu in sorted(self.water_utilities, key= lambda x: x.bwf_id)
        )
        return utilities_names+'-'+str(self.year)
    
    def get_connections_sign_map_between(
            self,
            wu_from: WaterUtility,
            wu_to: WaterUtility
        ) -> Dict[str, int]:
        """
        Returns a map (dictionary) that tells for each connection between the water utility
        if it has been installed with in the same directionas requested.
        
        :param self: Description
        :param wu_from: Description
        :type wu_from: WaterUtility
        :param wu_to: Description
        :type wu_to: WaterUtility
        :return: Description
        :rtype: Dict[str, int]
        """
        out_map: Dict[str, int] = {}

        wu_from_municipalities = [wu.cbs_id for wu in wu_from.municipalities]
        wu_to_municipalities = [wu.cbs_id for wu in wu_to.municipalities]
        for c in self.cross_utility_connections:
            if (c.from_node.cbs_id in wu_from_municipalities or 
                c.to_node.cbs_id in wu_from_municipalities
                ):
            
                if c.from_node.cbs_id in wu_to_municipalities:
                    out_map[c.bwf_id] = -1
                
                if c.to_node.cbs_id in wu_to_municipalities:
                    out_map[c.bwf_id] = 1
                
                # else maybe the connection is for the from municipality but not
                # in the to municipality

            # endif
        # endfor

        return out_map

@dataclass(frozen=True)
class NationalContext:
    NAME = 'national_context'

    # Static properties and settings
    state: State
    water_utilities: Set[WaterUtility]
    cross_utility_connections: Set[PeerConnection]
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
    def water_utilities_results(self) -> WaterUtilityResults:
        return WaterUtility._results

    @property
    def municipalities_db(self) -> MunicipalitiesDB:
        return Municipality._dynamic_properties
    
    @property
    def municipalities_results(self) -> MunicipalitiesResults:
        return Municipality._results
    
    def track_municipalities_undelivered_demand(
            self,
            when: BWFTimeLike,
            values: pd.Series
    ) -> Self:
        """
        Bulk version of Municipality.track_undelivered_demand
        
        :param self: Description
        :param year: Description
        :type year: int
        :param values: Description
        :type values: pd.Series
        :return: Description
        :rtype: Self
        """
        Municipality._results.commit(
            MunicipalitiesResults.DEMAND_UNDELIVERED,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            data=values
        )

    @property
    def sources_results(self) -> SourcesResults:
        return GroundWater._results
    
    def track_sources_production(
            self, 
            when: BWFTimeLike,
            values: pd.DataFrame
        ) -> Self:
        """
        Bulk version of Source.track_production
        """
        self.sources_results.commit(
            SourcesResults.PRODUCTION,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=len(values),
                freq='h'
            ),
            data=values
        )

        return self
    
    @property
    def pumps_results(self) -> PumpsResults:
        return Pump._results
    
    def track_pumps_electrical_energy(
            self,
            when: BWFTimeLike,
            values: pd.DataFrame
    ) -> Self:
        """
        Bulk version of Pump.track_ele_energy
        
        :param self: Description
        :param when: Description
        :type when: BWFTimeLike
        :param values: Description
        :type values: pd.DataFrame
        :return: Description
        :rtype: Self
        """
        Pump._results.commit(
            PumpsResults.ELE_ENERGY,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=len(values),
                freq='h'
            ),
            data=values
        )

        return self
    
    @property
    def solar_farms_results(self) -> SolarFarmsResults:
        return SolarFarm._results

    @property
    def average__maximum_temperature(self) -> pd.Series:
        return self.climate[ClimateDB.TEMPERATURE_MAX_AVG][self.state.cbs_id]
    
    @property
    def average_solar_irradiance(self) -> pd.Series:
        return self.climate[ClimateDB.SOLARRAD][self.state.cbs_id].tz_localize(self.state.time_zone)
    
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
    
    @property
    def electricity_price(self) -> pd.Series:
        return self.energy_sys[EnergySysDB.EPRICE_UNIT][self.state.cbs_id]
    
    @property
    def electricity_price_pattern(self) -> pd.Series:
        df = self.energy_sys[EnergySysDB.EPRICE_PATT]
        
        return df.apply(
            lambda row: ElectricityPricePattern.from_row(
                timestamp=row.name,
                values=row,
                scope= self.state.cbs_id
            ),
            axis=1
        )

    def track_solar_farms_yields(
            self, 
            when: BWFTimeLike,
            values: pd.DataFrame
        ) -> Self:
        """
        Bulk version of SolarFarm.track_yield
        """
        self.solar_farms_results.commit(
            SolarFarmsResults.YIELD,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=len(values),
                freq='h'
            ),
            data=values
        )

        return self
    
    def get_wu_clusters(self, year: int) -> Set[WaterUtilitiesCluster]:
        """
        Get the clusters (connected ater utilities)
        
        :param self: Description
        :param when: Description
        :type when: BWFTimeLike
        :return: Description
        :rtype: Set[WaterUtilitiesCluster]
        """
        muni_to_utility = {}
        wuid_to_wu = {}
        for wu in self.water_utilities:
            wuid_to_wu[wu.bwf_id] = wu

            for muni in wu.active_municipalities(year):
                muni_to_utility[muni.effective_cbs_id(year)] = wu.bwf_id

        all_wu = [wu.bwf_id for wu in self.water_utilities]
        merged_wu = []
        wu_add_connections = []

        for con in self.cross_utility_connections:
            if con.is_active(year) and con.has_active_pipe(year):
                m_id_1 = con.from_node.effective_cbs_id(year)
                m_id_2 = con.to_node.effective_cbs_id(year)

                # Merge two water utilties
                wu_1, wu_2 = muni_to_utility[m_id_1], muni_to_utility[m_id_2]
                if wu_1 not in all_wu and wu_2 not in all_wu:
                    wu_1_group_idx = None
                    wu_2_group_idx = None

                    for idx, group in enumerate(merged_wu):
                        if wu_1 in group:
                            wu_1_group_idx = idx
                        if wu_2 in group:
                            wu_2_group_idx = idx

                    if wu_2_group_idx != wu_1_group_idx:
                        merged_wu.append(merged_wu[wu_1_group_idx] + merged_wu[wu_2_group_idx])
                        wu_add_connections.append(wu_add_connections[wu_1_group_idx] + wu_add_connections[wu_2_group_idx] + [con])
                        merged_wu[wu_1_group_idx] = []
                        merged_wu[wu_2_group_idx] = []
                        wu_add_connections[wu_1_group_idx] = []
                        wu_add_connections[wu_2_group_idx] = []
                    else:
                        wu_add_connections[wu_1_group_idx].append(con)
                elif wu_1 not in all_wu and wu_2 in all_wu:
                    all_wu.remove(wu_2)

                    for idx, group in enumerate(merged_wu):
                        if wu_1 in group:
                            merged_wu[idx].append(wu_2)
                            wu_add_connections[idx].append(con)
                            break
                elif wu_1 in all_wu and wu_2 not in all_wu:
                    all_wu.remove(wu_1)

                    for idx, group in enumerate(merged_wu):
                        if wu_2 in group:
                            merged_wu[idx].append(wu_1)
                            wu_add_connections[idx].append(con)
                            break
                else:
                    all_wu.remove(wu_1)
                    all_wu.remove(wu_2)
                    merged_wu.append([wu_1, wu_2])
                    wu_add_connections.append([con])

        #print(merged_wu)
        for wu_id in all_wu:
            merged_wu.append([wu_id])
            wu_add_connections.append([])

        clusters = set(
            WaterUtilitiesCluster(
                water_utilities=set(wuid_to_wu[w_id] for w_id in wu_group),
                cross_utility_connections=wu_add_cons,
                year=year
            )
            for wu_group, wu_add_cons in zip(merged_wu, wu_add_connections)
        )

        return clusters