import itertools
import os
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import numpy as np
import pandas as pd

from ..core import Settings
from ..core.base_model import StaticProperties
from ..core.utility import timestampify
from ..core.views import get_snapshot, YearlyView
from ..nrw_model import NRWClass, NRWModelSettings
from ..nrw_model.dynamic_properties import NRWModelDB
from ..water_demand_model import WaterDemandModelPatterns
from ..water_demand_model.properties import WaterDemandModelDB
from ..jurisdictions import (
    State,
    Municipality,
    MunicipalitySize,
    generate_nrw_demand,
    generate_water_demand,
    age_distribution_networks
)



from ..sources.entities import WaterSource, SourcesContainer
from ..pumping_stations.entities import PumpingStation
from ..pumps.entities import PumpOption
from ..economy.entities import BondIssuance
from ..energy.entities import SolarFarm
from ..energy.services import get_solar_radiation_of_year, get_solar_yield
from ..pipes.dynamic_properties import PipeOptionsDB
from ..pipes.entities import PipeOption
from ..connections.entities import Connection, SupplyConnection, PeerConnection, SelfLoopConnection, ClosedWSourceConnection
from ..connections.services import age_pipes, resolve_current_cnn


from ..nrw_model.policies import NRWMitigation

from .dynamic_properties import WaterUtilityDB, WaterUtilityResults
from .entities import WaterUtility
from .policies import WaterPricingAdjustment
from .interventions import (
    OpenSource,
    CloseSource,
    InstallPipe,
    InstallPumps,
    InstallSolarFarm,
)

def configure_water_utilities(
        desc: Dict,
        a_state: State,
        sources: SourcesContainer,
        pumping_stations: Set[PumpingStation],
        connections: Set[Connection],
        utilities_bonds: Dict[str, Set[BondIssuance]],
        solar_farms: Set[SolarFarm],
        data_path: str,
        settings: Settings
    ) -> Tuple[Set[WaterUtility], Set[Connection]]:
    
    # First of all, let's setup the common database for the dyn prop.
    wu_db = WaterUtilityDB.load_from_file(os.path.join(data_path, desc[WaterUtilityDB.NAME]))
    WaterUtility.set_dynamic_properties(wu_db)
    WaterUtility.set_results(WaterUtilityResults())

    # Then, let's start creating the entities
    wu_st_properties = desc['water_utilities-static_properties']

    if isinstance(wu_st_properties, str):
        wu_st_properties = pd.read_excel(
            os.path.join(data_path, Path(wu_st_properties)),
            sheet_name=None
        )

    wutilities: Set[WaterUtility] = set()
    assigned_connections: Set[Connection] = set()
    for idx, row in wu_st_properties['entities'].iterrows():
        wutility_id = str(row[WaterUtility.ID])

        assgn_prov_ids = str(row[WaterUtility.ASSGN_PROVINCES]).split(';')

        wu_provinces = set([a_state.province(pv_id) for pv_id in assgn_prov_ids])
        
        wu_sources = set([s for s in sources if s.province in wu_provinces])
        
        wu_supplies: Dict[WaterSource, Tuple[PumpingStation, Connection]] = {}
        for source in wu_sources:
            pumping_station = next(ps for ps in pumping_stations if ps.source == source)
        
            connection = next(c for c in connections if isinstance(c, SupplyConnection) and c.from_node == source)

            wu_supplies[source] = (pumping_station, connection)

            assigned_connections.add(connection)

        wu_peer_connections: Set[Connection] = set()
        for connection in connections:
            if not isinstance(connection, PeerConnection):
                continue
            
            if (connection.from_node.province in wu_provinces and 
                connection.to_node.province in wu_provinces):
                
                wu_peer_connections.add(connection)
                assigned_connections.add(connection)

        wu_solar_farms = set([sf for sf in solar_farms if sf.connected_entity.province in wu_provinces])
        
        wutilities.add(
            WaterUtility(
                bwf_id=wutility_id,
                m_provinces=wu_provinces,
                m_supplies=wu_supplies,
                m_peer_connections=wu_peer_connections,
                m_bonds=utilities_bonds.get(wutility_id, set()),
                m_solar_farms=wu_solar_farms
            )
        )

    unassigned_connections = connections - assigned_connections

    return wutilities, unassigned_connections

def apply_nrw_interventions(
        water_utility: WaterUtility,
        year: int,
        policy_desc: Dict[str, Any],
        settings: Settings,
        nrw_settings: NRWModelSettings,
        nrw_info_db: NRWModelDB
    ) -> float:
    """
    Spends a given budget on the the municpalities of a given water utility.
    Note that the budget might not be enough to cover all municipalities.

    Parameters
    ----------
    budget : `float`
        Available budget.
    utility : `WaterUtility`
        Water utilitiy, containing a set of municipalities.
    year : `int`
        Current year.
    policy : `str`
        Policy for deciding the priority of the municipalities.
        Must be one of the following values:

            - "by_nrw_class"
            - "by_population"
    nrw_info_db : `NRWModelDB`
        Database.

    Returns
    -------
    `float`
        Budget spent.
    """

    utility_Y = get_snapshot(water_utility, year)
    municipalities = [get_snapshot(m, year) for m in sorted(utility_Y.municipalities, key=lambda x: x.cbs_id)]

    budget = policy_desc['budget']

    # Let's distribute the budget based on the policy
    if policy_desc['policy'] == NRWMitigation.BY_NRW_CLASS:
        budget_allocation_plan = NRWMitigation.distribute_budget_by_nrw_class(
            budget,
            municipalities,
            year,
            nrw_info_db
        )
    elif policy_desc['policy'] == NRWMitigation.BY_POPULATION:
        budget_allocation_plan = NRWMitigation.distribute_budget_by_population(
            budget,
            municipalities
        )
    elif policy_desc['policy'] == NRWMitigation.CUSTOM:
        budget_allocation_plan = NRWMitigation.distribute_budget_custom(
            budget,
            municipalities,
            policy_desc['policy_args']
        )
    else:
        raise ValueError(f"Unknown policy for NRW mitigation: {policy_desc['policy']}")

    # However, not every year we get the same success, let's get the random generator
    RNG = settings.get_random_generator('nrw_model-intervention_succes_prob')
    
    success_probabilities = RNG.uniform(
            low=nrw_settings.success_proba_bounds[0],
            high=nrw_settings.success_proba_bounds[1],
            size=len(NRWClass) * len(MunicipalitySize)
    )
    success_probabilities_map = { 
        (nrw_class, muni_size_class): success_probabilities[i]
        for i, (nrw_class, muni_size_class) in enumerate(itertools.product(NRWClass, MunicipalitySize))
    }
    
    # Spend budget on the municipalities
    def budget_to_years(a_budget: float, a_municipality: YearlyView[Municipality]) -> float:
        
        # unit cost is in €/km/year
        unit_cost = nrw_info_db[NRWModelDB.COST].loc[
            timestampify(year),
            f'{a_municipality.state.cbs_id}-{a_municipality.nrw_class.name}-{a_municipality.size_class.name}'
        ]
        
        # A perfect investement with this budget in this city would give me 
        ideal_years = a_budget / (unit_cost*a_municipality.dist_network_length)

        success_proba = success_probabilities_map[(a_municipality.nrw_class, a_municipality.size_class)]

        years_dec = ideal_years * success_proba
        if a_municipality.dist_network_avg_age - years_dec <= 0:
            return a_municipality.dist_network_avg_age
        else:
            return years_dec
        
    budget_spent = 0
    for muni in municipalities:
        if muni not in budget_allocation_plan or budget_allocation_plan[muni] == 0:
            continue

        budget_muni = budget_allocation_plan[muni]
        
        if budget_spent + budget_muni > budget:
            budget_muni = budget - budget_spent

        budget_spent += budget_muni
        muni.update_dist_net_age(when=year, by=-1 * budget_to_years(budget_muni, muni))

    return budget_spent

def apply_water_pricing_adjustments(
        water_utility: WaterUtility,
        year: int,
        policy_desc: Dict[str, Any],
        settings: Settings,
        inflation: pd.Series
    ) -> Tuple[float, float, float]:

    # To set the water prices in this year, we need to take the previous year prices.
    # We are assuming that they are already there
    
    last_year = timestampify(year-1)
    base_values = (
        water_utility.price_fix_comp.loc[last_year],
        water_utility.price_var_comp.loc[last_year],
        water_utility.price_sel_comp.loc[last_year]
    )

    if policy_desc['policy'] == WaterPricingAdjustment.BY_INFLATION:
        new_values = WaterPricingAdjustment.apply_by_inflation(
            *base_values,
            inflation.loc[last_year]/100 # As inflation is expressed in % points
        )

    elif policy_desc['policy'] == WaterPricingAdjustment.CUSTOM:
        new_values = WaterPricingAdjustment.apply_custom(
            *base_values,
            **policy_desc['policy_args']
        )

    else:
        raise ValueError(f"Unknown policy for water pricing adjustments: {policy_desc['policy']}")

    water_utility.set_water_prices(year, *new_values)

    return new_values

def apply_bond_to_debt_ratio(
        water_utility: WaterUtility,
        year: int,
        policy_desc: Dict[str, Any]
    ) -> float:

    value = policy_desc["value"]
    #check if the given value is between 1 and 2.5
    if value > 2.5 or value < 1:
        raise ValueError(f"Invalid bond to debt ratio: {value}. It must be between 1 and 2.5.")
    
    water_utility.set_bond_ratio(year, value)
    
    return value

def work_on_sources(
        water_utility: WaterUtility,
        year: int,
        interventions_open_desc: List[Dict[str, Any]],
        interventions_close_desc: List[Dict[str, Any]],
        pump_options: Set[PumpOption],
        pipe_options: Set[PipeOption],
        settings: Settings
    ) -> float:

    capex = 0.0

    for intervention in interventions_open_desc:
        capex += OpenSource.execute(
            water_utility=water_utility,
            year=year,
            intervention_desc=intervention,
            pipe_options=pipe_options,
            pump_options=pump_options,
            settings=settings
        )

    for intervention in interventions_close_desc:
        capex += CloseSource.execute(
            water_utility=water_utility,
            year=year,
            intervention_desc=intervention,
            settings=settings
        )

    return capex

def work_on_connections(
        water_utility: WaterUtility,
        year: int,
        interventions_desc: List[Dict[str, Any]],
        pipe_options: Set[PipeOption],
        settings: Settings
    ) -> float:
    
    capex = 0.0

    # First, install new pipes, like asked by the masterplan.
    # If a pipe replaces an already existing pipe on the same connection, we change 
    # the end_date of the old pipe (handled at the connection level).
    # However, if such a pipe that is being replaced has the same diameter and 
    # was installed in the last 25 years, we assume it failed before being 
    # replaced and so we skip the intervention (handled at the intervention level).
    
    for intervention in interventions_desc:
        capex += InstallPipe.execute(
            water_utility=water_utility,
            year=year,
            intervention_desc=intervention,
            pipe_options=pipe_options,
            settings=settings
        )

    # Once, we have installed of the utility pipes, we can see if there are pipes 
    # that are failing this year and for which we need emergency interevention.
    for connection in sorted(water_utility.connections, key=lambda c: c.bwf_id):
        
        if connection.replaced_by_cnn_id == "":
            # the connection doesn't get replaced, if it fails we re-install a pipe here
            capex += connection.inspect_and_replace(
                year=year,
                lifetime_rng=settings.pipes_lifetime_rng
            )

        else:
            # the connection does get replaced, if it fails we install a new one on the new connection
            failed_pipe = connection.inspect(when=year)
            if failed_pipe is None:
                # status is ok, we didn't do anything on it, move on
                continue
            # status is not ok, the pipe failed and the connection is not active anymore.
            # get the current connection (recursively in case the new connection also got replaced)
            new_connection = resolve_current_cnn(connection, year, water_utility.m_peer_connections)

            if isinstance(new_connection, SelfLoopConnection) or isinstance(new_connection, ClosedWSourceConnection):
                # the connection basically disappeared, we don't need to replace it
                continue

            # if everything goes to plan, new connection is another connection bu not yet used.
            # however if one connection replaces more than one, it could be that the first one failing
            # installs the new pipe. we don't want that, when a connection replaces more than one, we need 
            # to deal with all of them at the same time... 
            assert len(new_connection.replaces_cnn_ids) < 2, "A pipe that gets replaced by a connection replacing more than one failed."

            new_pipe = new_connection.install_pipe(
                pipe_option=failed_pipe._pipe_option,
                installation_date=failed_pipe.decommission_date,
                lifetime_rng=settings.pipes_lifetime_rng
            )

            pipe_unit_cost = new_pipe._pipe_option.unit_cost.loc[new_pipe.installation_date]

            capex += pipe_unit_cost * new_connection.distance
    
    return capex

def work_on_pumps(
        water_utility: WaterUtility,
        year: int,
        interventions_desc: List[Dict[str, Any]],
        pump_options: Set[PumpOption],
        settings: Settings
    ) -> float:
    
    capex = 0.0

    for intervention in interventions_desc:
        capex += InstallPumps.execute(
            water_utility=water_utility,
            year=year,
            intervention_desc=intervention,
            pump_options=pump_options,
            settings=settings
        )

    for pumping_station in sorted(water_utility.pumping_stations, key=lambda ps: ps.bwf_id):
        capex += pumping_station.inspect_and_replace(
            year=year,
            lifetime_rng=settings.get_random_generator('pumps-lifetime')
        )

    return capex

def work_on_solar_farms(
        water_utility: WaterUtility,
        year: int,
        interventions_desc: List[Dict[str, Any]],
        settings: Settings
    ) -> float:

    capex = 0.0 

    for intervention in interventions_desc:
        capex += InstallSolarFarm.execute(
            water_utility=water_utility,
            year=year,
            intervention_desc=intervention,
            settings=settings
        )

    return capex

def realise_demands(
        water_utility: WaterUtility,
        year: int,
        water_demand_model_data: Tuple[WaterDemandModelPatterns, WaterDemandModelDB],
        nrw_model_data: Tuple[NRWModelSettings, NRWModelDB],
        temperature: float,
        settings: Settings
) -> Dict[str, np.ndarray]:
    
    municipalities = water_utility.active_municipalities(when=year)

    for municipality in sorted(municipalities, key=lambda x: x.cbs_id):

        household_demand, business_demand = generate_water_demand(
            water_demand_model_data,
            municipality,
            year,
            max_yearly_temperature=temperature,
            settings=settings
        )
        bill_demand = household_demand + business_demand

        nrw_demand = generate_nrw_demand(
            municipality,
            year,
            nrw_info_db=nrw_model_data[1],
            water_demand=bill_demand,
            settings=settings
        )

        total_demand = bill_demand + np.repeat(nrw_demand, 24, axis=0)
        
        municipality.track_total_demand(when=year, values=total_demand)
        municipality.track_billable_demand(when=year, values=bill_demand)

        # end municipalities for loop

    return {} 

def realise_solar_yields(
        water_utility: WaterUtility,
        year: int,
        solar_irradiance: np.ndarray,
        settings: Settings
    ) -> Dict[str, np.ndarray]:

    solar_farms = water_utility.active_solar_farms(when=year)
    solar_yields = {}

    for solar_farm in sorted(solar_farms, key=lambda x: x.bwf_id):

        solar_yield = get_solar_yield(
            solar_farm=solar_farm,
            solar_radiation=solar_irradiance,
            settings=settings
        )
        solar_yields[solar_farm.bwf_id] = solar_yield

        # solar_farm.track_yield(
        #     when=year,
        #     values=solar_yield
        # )

    return solar_yields

def age_water_utility(
        wu: WaterUtility,
        year: int,
        settings: Settings,
        nrw_info_db: NRWModelDB
    ) -> None:

    wu_y = get_snapshot(wu, year=year)
    wu_Ny = get_snapshot(wu, year=year+1)

    munis_y: Set[Municipality] = wu_y.municipalities
    munis_Ny: Set[Municipality] = wu_Ny.municipalities
    non_closing_munis = munis_y & munis_Ny
    closing_munis = munis_y - non_closing_munis

    #------ Inner distribution network age.
    new_munis = age_distribution_networks(
        closing_munis,
        non_closing_munis,
        year,
        nrw_info_db
    )

    #------ Pipes friction factor
    age_pipes(
        wu_y.connections,
        year,
        settings.get_random_generator('pipes-fric_f_decay')
    )

    #------ Other

def dump_water_utilities(
        water_utilities: Set[WaterUtility],
        output_dir: Path
    ) -> Dict[str, Any]:

    full_out_dir = output_dir / "water_utilities"
    def as_rel_path(a_path: Path) -> str:
        return os.path.relpath(a_path, output_dir)
    
    entities_df = pd.DataFrame(
        data=[wu.to_dict() for wu in sorted(water_utilities, key= lambda x: x.bwf_id)]
    )

    dfs = {
        'entities': entities_df
    }

    sproperties = StaticProperties(
        name="water_utilities-static_properties",
        dataframes=dfs
    )

    sp_path = sproperties.dump(full_out_dir)
    dp_path = WaterUtility._dynamic_properties.dump(full_out_dir)

    return {
        sproperties.name: as_rel_path(sp_path),
        WaterUtilityDB.NAME: as_rel_path(dp_path)
    }