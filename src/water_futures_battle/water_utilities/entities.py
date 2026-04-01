from dataclasses import dataclass
from typing import Any, Dict, Self, Set, Tuple, Union

import numpy as np
import pandas as pd

from ..core.base_model import bwf_entity
from ..core.utility import BWFTimeLike, timestampify
from ..jurisdictions.entities import State, Region, Province, Municipality
from ..sources.entities import WaterSource, GroundWater, SurfaceWater, Desalination
from ..pumping_stations.entities import PumpingStation
from ..connections.entities import Connection, PeerConnection, SupplyConnection
from ..economy.entities import BondIssuance
from ..energy.entities import SolarFarm

from .dynamic_properties import WaterUtilityDB, WaterUtilityResults

@bwf_entity(db_type=WaterUtilityDB, results_type=WaterUtilityResults)
@dataclass(frozen=True)
class WaterUtility():
    NAME = 'water_utility'

    bwf_id: str
    ID = 'water_utility_id'
    ID_PREFIX = 'WU' # Water Utility

    m_provinces: Set[Province]
    ASSGN_PROVINCES = 'assigned_provinces'

    m_supplies: Dict[WaterSource, Tuple[PumpingStation, SupplyConnection]]

    m_peer_connections: Set[PeerConnection]

    m_bonds: Set[BondIssuance]

    m_solar_farms: Set[SolarFarm]

    def __post_init__(self):
        assert self._dynamic_properties is not None
        assert self._results is not None

    def __eq__(self, other):
        if not isinstance(other, WaterUtility):
            return NotImplemented
        # Define equality based on the unique identifier
        return self.bwf_id == other.bwf_id

    def __hash__(self):
        # Base the hash only on the unique identifier (cbs_code)
        return hash(self.bwf_id)
    
    def named(self, s: pd.Series) -> pd.Series:
        """
        Applies to a series the Water Utility id, so that they can be easily concatenated.
        Helpful for properties series that are generated from entities contained in this class.
        """
        s.name = self.bwf_id
        return s
 
    # Declaration of dynamic properties, i.e., those that have some type of time dependency
    # and how the yearlyView object will handle them
    # If they return a pd.Series, we declare the casting type (e.g., population)
    # If they have a time-agnostic method and a corresponding time-aware one, we map them
    DYNAMIC_PROPERTIES = {
        'municipalities': 'active_municipalities',
        'connections': 'active_connections',
        'solar_farms': 'active_solar_farms',
        'balance': float,
        'price_fix_comp': float,
        'price_var_comp': float,
        'price_sel_comp': float,
        'balance': float,
        'net_water_exchange': 'net_water_exchange_at',
        'net_water_exported': 'net_water_exported_at',
        'net_water_imported': 'net_water_imported_at',
        'debt': float,
        'bond_ratio': float,
        'investment_budget': float,
        'capex': float,
        'opex': float,
        'gw_permit_fine': float,
        'nrw_mitigation_budget': float
    }

    @property
    def state(self) -> State:
        # We assume a water utility operates only inside one state
        states = {pv.state for pv in self.m_provinces}
        assert len(states) == 1, "All provinces must belong to the same state"
        return next(iter(states))
    
    @property
    def regions(self) -> Set[Region]:
        # One w.u. can span multiple regions
        return {pv.region for pv in self.m_provinces}
    
    @property
    def provinces(self) -> Set[Province]:
        return self.m_provinces

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
    
    def active_pumping_stations(self, when: BWFTimeLike) -> Set[PumpingStation]:
        return set(ps for ps in self.pumping_stations if ps.is_active(when=when))
    
    @property
    def sources(self) -> Set[WaterSource]:
        return set(s for s in self.m_supplies.keys())
    
    def active_sources(self, when: BWFTimeLike) -> Set[WaterSource]:
        return set(s for s in self.m_supplies.keys() if s.is_active(when=when))
    
    @property
    def gw_sources(self) -> Set[GroundWater]:
        return set( s
            for s in self.m_supplies.keys()
            if s.bwf_id.startswith(GroundWater.ID_PREFIX)
        )
    
    def active_gw_sources(self, when: BWFTimeLike) -> Set[GroundWater]:
        return set(s for s in self.gw_sources if s.is_active(when=when))
    
    @property
    def solar_farms(self) -> Set[SolarFarm]:
        return self.m_solar_farms.copy()
    
    def active_solar_farms(self, when: BWFTimeLike) -> Set[SolarFarm]:
        return set([
            sf for sf in self.m_solar_farms if sf.is_active(when) and sf.connected_entity.is_active(when)
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
    
    def set_bond_ratio(
            self,
            when: BWFTimeLike,
            value: float
    ) -> Self:
    
        self._results.commit(
            a_property=WaterUtilityResults.BA2D_RATIO,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=self.bwf_id,
            values=value
        )

        return self
    
    @property
    def population(self) -> pd.Series:
        return self.named(sum([pv.population for pv in self.m_provinces]))
        
    @property
    def disp_income_avg(self) -> pd.Series:
        pv_populations = [pv.population for pv in self.m_provinces]
        pv_incomes = [pv.disp_income_avg for pv in self.m_provinces]
        # Compute weighted average for each timestamp
        weighted_sum = sum([inc * pop for inc, pop in zip(pv_incomes, pv_populations)])
        total_population = sum(pv_populations)
        return weighted_sum / total_population
    
    @property
    def net_water_exchange(self) -> pd.DataFrame:
        """
        Returns the net water echange of this utility to all other utilities.
        Positive, means this utility is sending the water out, negative getting it in.
        """

        full_df = self._results[WaterUtilityResults.NET_WATER_EXCHANGE]

        int_columns = [ col
            for col in full_df.columns
            if self.bwf_id in col
        ]
        
        values = {}
        for col in int_columns:
            wu_from, wu_to = col.split('-')

            if self.bwf_id == wu_from:
                # The values was from this utility to another, leave the sign unotuched
                values[wu_to] = full_df[col]
            else:
                # The values are TO THIS w.u., thus we invert the value
                assert self.bwf_id == wu_to
                values[wu_from] = -full_df[col]

        return pd.DataFrame(values).fillna(0.0)

    def net_water_exchange_at(self, when: BWFTimeLike) -> pd.Series:
        """
        Returns the net water exchange for a specific timestamp (row) or an empty series if not found.
        The returned series is named with the timestamp.
        """
        df = self.net_water_exchange
        ts = timestampify(when)
        if ts in df.index:
            return df.loc[ts]
        
        # Return empty series with correct name
        return pd.Series(dtype=float, name=ts)

    @property
    def net_water_exported(self) -> pd.DataFrame:
        """
        Water exported to other utilities (positive net exchanges only).
        """
        net = self.net_water_exchange
        return net.where(net > 0, 0.0)

    def net_water_exported_at(self, when: BWFTimeLike) -> pd.Series:
        """
        Water exported to other utilities for a specific timestamp (positive net exchanges only).
        Returns empty series if timestamp not found.
        """
        net = self.net_water_exchange_at(when)
        return net.where(net > 0, 0.0)

    @property
    def net_water_imported(self) -> pd.DataFrame:
        """
        Water imported from other utilities (negative net exchanges only, as positive values).
        """
        net = self.net_water_exchange
        return net.where(net < 0, 0.0).abs()

    def net_water_imported_at(self, when: BWFTimeLike) -> pd.Series:
        """
        Water imported from other utilities for a specific timestamp (negative net exchanges only, as positive values).
        Returns empty series if timestamp not found.
        """
        net = self.net_water_exchange_at(when)
        return net.where(net < 0, 0.0).abs()

    @property
    def debt(self) -> pd.Series:
        return self._results[WaterUtilityResults.DEBT][self.bwf_id]
    
    @property
    def bond_ratio(self) -> pd.Series:
        return self._results[WaterUtilityResults.BA2D_RATIO][self.bwf_id]

    @property
    def investment_budget(self) -> pd.Series:
        return self._results[WaterUtilityResults.WUIB][self.bwf_id]
    
    @property
    def capex(self) -> pd.Series:
        return self._results[WaterUtilityResults.CAPEX][self.bwf_id]
    
    @property
    def opex(self) -> pd.Series:
        return self._results[WaterUtilityResults.OPEX][self.bwf_id]
    
    @property
    def gw_permit_fine(self) -> pd.Series:
        return self._results[WaterUtilityResults.FIN][self.bwf_id]

    @property
    def nrw_mitigation_budget(self) -> pd.Series:
        return self._results[WaterUtilityResults.WLR][self.bwf_id]

    @property
    def ghg_embedded_emissions(self) -> pd.Series:
        return self._results[WaterUtilityResults.GHG_EMB][self.bwf_id]
    
    @property
    def ghg_operations_emissions(self) -> pd.Series:
        return self._results[WaterUtilityResults.GHG_OPE][self.bwf_id]
    
    def get_debt_service(
            self,
            year: int
        ) -> float:

        interests = 0.0
        princ_amounts = 0.0

        for bond_issuance in self.m_bonds:
            interests += bond_issuance.interest_due(year=year)
            princ_amounts += bond_issuance.principal_due(year=year)

        self.track_interests(
            when=year,
            value=interests
        )

        self.track_principal_amounts(
            when=year,
            value=princ_amounts
        )

        return interests + princ_amounts

    def to_dict(self) -> Dict[str, Any]:
        return {
            self.ID: self.bwf_id,
            self.ASSGN_PROVINCES: ';'.join([pv.cbs_id for pv in self.m_provinces])
        }
    
    def track_net_wat_exchange(
            self,
            when: BWFTimeLike,
            to: 'WaterUtility',
            value: float
        ) -> Self:
        """
        Track the net water exchange between one utility (from, i.e., self) to 
        another one ($Delta Q _w^w'(y)$).

        It expect a single value representing the total net exchange between two utilities
        
        :param self: Description
        :param when: Description
        :type when: int
        :param to: Description
        :type to: 'WaterUtility'
        :param value: Description
        :type value: float
        :return: Description
        :rtype: Self
        """
        assert np.ndim(value) == 0, "Value for net wat exchange is not a scalar"

        self._results.commit(
            a_property=WaterUtilityResults.NET_WATER_EXCHANGE,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=f'{self.bwf_id}-{to.bwf_id}', # for the columns {w.id}-{w'.id}
            values=value
        )

        return self
    
    def track_debt(
            self,
            when: BWFTimeLike,
            value: float
        ) -> Self:
        assert np.ndim(value) == 0, "Value for debt is not a scalar"

        self._results.commit(
            a_property=WaterUtilityResults.DEBT,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=f'{self.bwf_id}',
            values=value
        )

        return self

    def track_capex(
            self,
            when: BWFTimeLike,
            value: float
        ) -> Self:
        assert np.ndim(value) == 0, "Value for capex is not a scalar"

        self._results.commit(
            a_property=WaterUtilityResults.CAPEX,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=f'{self.bwf_id}',
            values=value
        )

        return self

    def track_opex(
            self,
            when: BWFTimeLike,
            value: float
        ) -> Self:
        assert np.ndim(value) == 0, "Value for opex is not a scalar"

        self._results.commit(
            a_property=WaterUtilityResults.OPEX,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=f'{self.bwf_id}',
            values=value
        )

        return self
    
    def track_gw_permit_fine(
            self,
            when: BWFTimeLike,
            value: float
        ) -> Self:
        assert np.ndim(value) == 0, "Value for fine is not a scalar"

        self._results.commit(
            a_property=WaterUtilityResults.FIN,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=f'{self.bwf_id}',
            values=value
        )

        return self

    def track_revenue(
            self,
            when: BWFTimeLike,
            value: float
        ) -> Self:
        assert np.ndim(value) == 0, "Value for revenue is not a scalar"

        self._results.commit(
            a_property=WaterUtilityResults.REV,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=f'{self.bwf_id}',
            values=value
        )

        return self

    def track_nrw_mitigation_budget(
            self,
            when: BWFTimeLike,
            value: float
        ) -> Self:
        assert np.ndim(value) == 0, "Value for nrw mitigation is not a scalar"

        self._results.commit(
            a_property=WaterUtilityResults.WLR,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=f'{self.bwf_id}',
            values=value
        )

        return self

    def track_water_import_cost(
            self,
            when: BWFTimeLike,
            value: float
        ) -> Self:
        assert np.ndim(value) == 0, "Value for wic is not a scalar"

        self._results.commit(
            a_property=WaterUtilityResults.WIC,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=f'{self.bwf_id}',
            values=value
        )

        return self
    
    def track_interests(
            self,
            when: BWFTimeLike,
            value: float
        ) -> Self:
        assert np.ndim(value) == 0, "Value for interests is not a scalar"

        self._results.commit(
            a_property=WaterUtilityResults.INT,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=f'{self.bwf_id}',
            values=value
        )

        return self
    
    def track_principal_amounts(
            self,
            when: BWFTimeLike,
            value: float
        ) -> Self:
        assert np.ndim(value) == 0, "Value for principal amounts is not a scalar"

        self._results.commit(
            a_property=WaterUtilityResults.PRI,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=f'{self.bwf_id}',
            values=value
        )

        return self
    
    def track_embodied_emissions(
            self,
            when: BWFTimeLike,
            value: float
        ) -> Self:
        assert np.ndim(value) == 0, "Value for emissions is not a scalar"

        self._results.commit(
            a_property=WaterUtilityResults.GHG_EMB,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=f'{self.bwf_id}',
            values=value
        )

        return self
    
    def track_operations_emissions(
            self,
            when: BWFTimeLike,
            value: float
        ) -> Self:
        assert np.ndim(value) == 0, "Value for emissions is not a scalar"

        self._results.commit(
            a_property=WaterUtilityResults.GHG_OPE,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=1,
                freq='YS'
            ),
            entity=f'{self.bwf_id}',
            values=value
        )

        return self

    def install_solar_farm(
            self,
            capacity: float,
            installation_date: pd.Timestamp,
            decommission_date: pd.Timestamp,
            connected_entity: Union[WaterSource, PumpingStation]
        ) -> SolarFarm:
            
            # Solar farm ID is SF-{entity_id}-{counter}
            # First let's see how many are there, otherwise is 0, keep only the prefix
            solar_farm_id = f"{SolarFarm.ID_PREFIX}-{connected_entity.bwf_id}-"
            old_sfs = [sf for sf in self.m_solar_farms if sf.bwf_id.startswith(solar_farm_id)]
            new_solar_farm_id = solar_farm_id+str(len(old_sfs))

            solar_farm = SolarFarm(
                bwf_id=new_solar_farm_id,
                capacity=capacity, 
                installation_date=installation_date,
                decommission_date=decommission_date,
                connected_entity=connected_entity
            )

            self.m_solar_farms.add(solar_farm)

            return solar_farm