from typing import Dict, Set, Tuple
import os
import tempfile

import pandas as pd
from rich.progress import Progress, TaskID
import threading
from joblib import Parallel, delayed

from ..core import Settings, get_snapshot
from ..core.utility import timestampify
from ..jurisdictions import Municipality
from ..economy.services import raise_amount
from ..water_utilities import WaterUtility
from ..national_context import NationalContext
from ..masterplan import Masterplan

from ..water_utilities import services as wu_actions
from ..national_context import services as nat_actions
from ..energy.services import get_solar_radiation_of_year

from .metrics import MetricsT, compute_metrics
from .epanet_utils import run_cluster_hydraulics

def run_eval(
        settings: Settings,
        national_context: NationalContext,
        water_utilities: Set[WaterUtility],
        masterplan: Masterplan
    ) -> Tuple[
        NationalContext,
        Set[WaterUtility],
        MetricsT
    ]:

    # We evaluate the system received in input one year at the time.
    # We use a progress bar to:
    # - tracking the evaluation across years,
    # - applying the inteventions across the utilities
    # - realising the uncertainties
    # - simulating the hydraulic results across the utilities
    with Progress() as progress:
        task_years = progress.add_task("[green]Evaluating the system across the years", total=settings.n_years_to_simulate)
        task_utilities = progress.add_task("[cyan]  Applying policies and working on intervention", total=len(water_utilities)+1)
        task_uncertainties = progress.add_task("[cyan]  Realising uncertainties", total=len(water_utilities)+1)
        task_simu = progress.add_task("[cyan]  Extracting the hydraulic results", total=len(water_utilities))

        for year in settings.years_to_simulate:
            progress.reset(task_utilities)
            progress.reset(task_uncertainties)
            progress.reset(task_simu)

            # Retrieve and apply the national policies:
            # - budget allocation
            national_policies = masterplan.national_policies(year=year)

            nat_actions.share_yearly_budget(
                budget=settings.national_investment_budget,
                national_context=national_context,
                year=year,
                policy_desc=national_policies['budget_allocation']
            )

            # Retrieve and apply the national interventions:
            # - pipe installation
            national_interventions = masterplan.national_interventions(year=year)

            wus_national_capex, wus_national_ghg = nat_actions.work_on_connections(
                national_context=national_context,
                year=year,
                intervention_desc=national_interventions['install_pipe'],
                pipe_options=national_context.pipe_options,
                settings=settings
            )

            # We completed national interventions, we can move to by utility actions
            progress.update(task_utilities, advance=1)
            
            for water_utility in sorted(water_utilities, key=lambda x: x.bwf_id):

                # Retrieve and apply the utility's policies:
                # - nrw mitigation
                # - water pricing
                # - bonds issuance
                wutil_policies = masterplan.water_utility_policies(
                    water_utility=water_utility.bwf_id,
                    year=year
                )

                wu_actions.apply_nrw_interventions(
                    water_utility=water_utility,
                    year=year,
                    policy_desc=wutil_policies['nrw_mitigation'],
                    settings=settings,
                    nrw_settings=national_context.nrw_settings,
                    nrw_info_db=national_context.nrw_model_db
                )

                wu_actions.apply_water_pricing_adjustments(
                    water_utility=water_utility,
                    year=year,
                    policy_desc=wutil_policies['pricing_adjustment'],
                    settings=settings,
                    inflation=national_context.inflation
                )

                wu_actions.apply_bond_to_debt_ratio(
                    water_utility=water_utility,
                    year=year,
                    policy_desc=wutil_policies['bond_ratio']
                )

                # Retrieve and apply the utility's interventions:
                # - opening & closing new sources
                # - installing/replacing pipes
                # - installing/replacing pumps
                # - installing solar
                # Each of these returns its capex and we save only the cumulative value
                wutil_interven = masterplan.water_utility_interventions(
                    water_utility=water_utility.bwf_id,
                    year=year
                )

                sources_capex, sources_ghg = wu_actions.work_on_sources(
                    water_utility=water_utility,
                    year=year,
                    interventions_open_desc=wutil_interven['open_source'],
                    interventions_close_desc=wutil_interven['close_source'],
                    pump_options=national_context.pump_options,
                    pipe_options=national_context.pipe_options,
                    settings=settings
                )

                pipes_capex, pipes_ghg = wu_actions.work_on_connections(
                    water_utility=water_utility,
                    year=year,
                    interventions_desc=wutil_interven['install_pipe'],
                    pipe_options=national_context.pipe_options,
                    settings=settings
                )

                pumps_capex, pumps_ghg = wu_actions.work_on_pumps(
                    water_utility=water_utility,
                    year=year,
                    interventions_desc=wutil_interven['install_pumps'],
                    pump_options=national_context.pump_options,
                    settings=settings
                )

                solar_capex, solar_ghg = wu_actions.work_on_solar_farms(
                    water_utility=water_utility,
                    year=year,
                    interventions_desc=wutil_interven['install_solar'],
                    settings=settings
                )

                wu_capex = (
                    sources_capex +
                    pipes_capex +
                    pumps_capex +
                    solar_capex +
                    wus_national_capex[water_utility.bwf_id]
                )
                water_utility.track_capex(when=year, value=wu_capex)

                wu_ghg = (
                    sources_ghg +
                    pipes_ghg +
                    pumps_ghg +
                    solar_ghg +
                    wus_national_ghg[water_utility.bwf_id]
                )
                water_utility.track_embodied_emissions(when=year, value=wu_ghg)

                # end water utilities for loop
                progress.update(task_utilities, advance=1)
                
            # compute the missing dependent dynamic properties (demand, etc)
            realise_uncertainties(
                year=year,
                national_context=national_context,
                water_utilities=water_utilities,
                settings=settings,
                progress=progress,
                task_uncertainties=task_uncertainties
            )

            run_hydraulic_simulations(
                year=year,
                national_context=national_context,
                water_utilities=water_utilities,
                settings=settings,
                progress=progress,
                task_simu=task_simu
            )
            
            # Update endogenous dynamic properties (inflation, electricity market, components costs)
            # Unless we reached the end and therefore we would need future values
            # for next year (for example inflation or which municipalities close in 2025)
            if not year == settings.years_to_simulate[-1]:
                escalate_costs(
                    year=year,
                    national_context=national_context,
                    water_utilities=water_utilities
                )
            
                age_water_utilities(
                    year=year,
                    national_context=national_context,
                    water_utilities=water_utilities,
                    settings=settings
                )

                age_national_context_assets(
                    year=year,
                    national_context=national_context,
                    water_utilities=water_utilities,
                    settings=settings
                )

            update_financial_balances(
                year=year,
                national_context=national_context,
                water_utilities=water_utilities,
                settings=settings
            )

            # end year for loop
            progress.update(task_years, advance=1)
        
    # end of stage loop, we can calculate all the metrics
    metrics = compute_metrics(settings, national_context, water_utilities)

    return (
        national_context,
        water_utilities,
        metrics
    )


def realise_uncertainties(
        year: int,
        national_context: NationalContext,
        water_utilities: Set[WaterUtility],
        settings: Settings,
        progress: Progress,
        task_uncertainties: TaskID
    )-> None:

    # Extract this year mean max temperature. As we get it by season, 
    # let's take the maximum over the year.
    # The mean max temperature (and not the max max) captures both the 
    # durationand severity of the extreme.
    mean_tempmax = national_context.average__maximum_temperature
    maxtemp_year = mean_tempmax.loc[mean_tempmax.index.year == year].max()

    for water_utility in sorted(water_utilities, key=lambda x: x.bwf_id):
        wu_actions.realise_demands(
            water_utility=water_utility,
            year=year,
            water_demand_model_data=national_context.water_demand_model_data,
            nrw_model_data=national_context.nrw_model_data,
            temperature=maxtemp_year,
            settings=settings
        )

        progress.update(task_uncertainties, advance=1)

    solar_yields = {}
    solar_radiation = get_solar_radiation_of_year(
        year=year,
        state=national_context.state,
        observed_avg_solar_radiation=national_context.average_solar_irradiance,
        settings=settings
    )

    for water_utility in sorted(water_utilities, key=lambda x: x.bwf_id):
        wu_solar_yields = wu_actions.realise_solar_yields(
            water_utility=water_utility,
            year=year,
            solar_irradiance=solar_radiation,
            settings=settings
        )

        solar_yields.update(wu_solar_yields)

    national_context.track_solar_farms_yields(
        when=year,
        values=pd.DataFrame(solar_yields)
    )

    progress.update(task_uncertainties, advance=1)

def run_hydraulic_simulations(
        year: int,
        national_context: NationalContext,
        water_utilities: Set[WaterUtility],
        settings: Settings,
        progress: Progress,
        task_simu: TaskID
    )-> None:

    # Get how many disconnected water utilities are there, each one will have its own simulation
    # Use the shared national resources to understand which are independent and which are not
    wutilities_clusters = national_context.get_wu_clusters(year=year)
    # print(f"Number of utility clusters: {len(wutilities_clusters)} -- Number of utilities: {len(water_utilities)}")

    # Now we are ready for simulation, we apply the demands, simulate and save and repeat in a parralel fashion
    lock = threading.Lock()

    def _run_and_advance(cluster):
        sim_results = run_cluster_hydraulics(
            national_context=national_context,
            cluster=cluster,
            year=year,
            settings=settings
        )
        
        with lock:
            national_context.track_municipalities_undelivered_demand(
                when=year,
                values=sim_results.undelivered_demands.sum(axis=0)
            )
            national_context.track_pumps_electrical_energy(
                when=year,
                values=sim_results.pumps_energy_consumption
            )
            national_context.track_sources_production(
                when=year,
                values=sim_results.sources_production
            )

            # Utilities water exchanges
            # let's sort them to save the results always in order
            sorted_wus = sorted((wu for wu in cluster.water_utilities), key= lambda x: x.bwf_id)
            sim_results.cross_utilities_flows.columns = [
                c[:6] for c in sim_results.cross_utilities_flows.columns
            ] # convert the columns from the pipe name to the connection name
            net_exchanges = sim_results.cross_utilities_flows.sum(axis=0, skipna=True)
            for i, wu_from in enumerate(sorted_wus):
                for j, wu_to in enumerate(sorted_wus[i+1:]):

                    cnns_sign_map = cluster.get_connections_sign_map_between(wu_from, wu_to)

                    # Change the sign of the inverted pipes (from wu_to to wu_from)
                    net_value = 0.0
                    for c_id, x in cnns_sign_map.items():
                        net_value += x * net_exchanges[c_id]

                    wu_from.track_net_wat_exchange(
                        when=year,
                        to=wu_to,
                        value=net_value
                    )

            # Account for opex and greenhouse gas emissions derived by the operations
            for water_utility in sorted_wus:
                opex, ghg_oper, gw_fines = wu_actions.settle_operations_impact(
                    water_utility=water_utility,
                    energy_sys_db=national_context.energy_sys,
                    year=year,
                    settings=settings,
                    pumps_ele_consumption=sim_results.pumps_energy_consumption,
                    sources_production=sim_results.sources_production
                )
        
        progress.advance(task_simu, advance=cluster.n_water_utilities)

    if settings.available_cores > 2:
        # Always leave one core out to avoid going bottlenecks
        Parallel(n_jobs=settings.available_cores-1, prefer="threads")(
            delayed(_run_and_advance)(cluster)
            for cluster in wutilities_clusters
        )
    else:
        for cluster in sorted(wutilities_clusters, key=lambda cl: cl.filename):
            _run_and_advance(cluster=cluster)

    return

def escalate_costs(
        year: int,
        national_context: NationalContext,
        water_utilities: Set[WaterUtility]
    ) -> None:
    """
    Docstring for escalate_costs
    
    :param year: Description
    :type year: int
    :param inflation: Description
    :type inflation: float
    """

    # The costs to inflate are:
    # NRW options
    # Sources construction
    # Pumps construction
    # Pipes costs

    # Other costs that don't follow inflation (they are purely exogenous):
    # - Solar panel unit cost
    # - electricity unit cost

    # We work under the assumption that a value in next_year for inflation is already there.
    
    this_year = timestampify(year)
    next_year = timestampify(year+1)
    inflation_rate = national_context.inflation.loc[next_year]/100
    
    # NRW intervention cost
    base_cost = national_context.nrw_intervention_costs.loc[this_year]
    inflated_cost = (1+inflation_rate) * base_cost
    national_context.set_nrw_intervention_costs(next_year, inflated_cost)
    
    # Sources costs
    # - Groundwater (gw)
    #   - Unit cost of construction
    base_cost = national_context.gw_sources_unit_cost.loc[this_year]
    inflated_cost = (1+inflation_rate) * base_cost
    national_context.set_gw_sources_unit_cost(next_year, inflated_cost)

    #   - Opex fixed
    base_cost = national_context.gw_sources_opex_fixed_cost.loc[this_year]
    inflated_cost = (1+inflation_rate) * base_cost
    national_context.set_gw_sources_opex_fixed_cost(next_year, inflated_cost)

    #   - Opex volumetric other
    base_cost = national_context.gw_sources_opex_volum_other_cost.loc[this_year]
    inflated_cost = (1+inflation_rate) * base_cost
    national_context.set_gw_sources_opex_volum_other_cost(next_year, inflated_cost)

    # - Surface Water (sw)
    #   - Unit cost of construction
    base_cost = national_context.sw_sources_unit_cost.loc[this_year]
    inflated_cost = (1+inflation_rate) * base_cost
    national_context.set_sw_sources_unit_cost(next_year, inflated_cost)

    #   - Opex fixed
    base_cost = national_context.sw_sources_opex_fixed_cost.loc[this_year]
    inflated_cost = (1+inflation_rate) * base_cost
    national_context.set_sw_sources_opex_fixed_cost(next_year, inflated_cost)

    #   - Opex volumetric other
    base_cost = national_context.sw_sources_opex_volum_other_cost.loc[this_year]
    inflated_cost = (1+inflation_rate) * base_cost
    national_context.set_sw_sources_opex_volum_other_cost(next_year, inflated_cost)

    # - Desalination (des)
    #   - Unit cost of construction
    base_cost = national_context.des_sources_unit_cost.loc[this_year]
    inflated_cost = (1+inflation_rate) * base_cost
    national_context.set_des_sources_unit_cost(next_year, inflated_cost)

    #   - Opex fixed
    base_cost = national_context.des_sources_opex_fixed_cost.loc[this_year]
    inflated_cost = (1+inflation_rate) * base_cost
    national_context.set_des_sources_opex_fixed_cost(next_year, inflated_cost)

    #   - Opex volumetric other
    base_cost = national_context.des_sources_opex_volum_other_cost.loc[this_year]
    inflated_cost = (1+inflation_rate) * base_cost
    national_context.set_des_sources_opex_volum_other_cost(next_year, inflated_cost)

    # - Pump options (new pumps)
    base_cost = national_context.new_pumps_costs.loc[this_year]
    inflated_cost = (1+inflation_rate) * base_cost
    national_context.set_new_pumps_costs(next_year, inflated_cost)

    # - Pipe options (new pipes)
    base_cost = national_context.new_pipes_costs.loc[this_year]
    inflated_cost = (1+inflation_rate) * base_cost
    national_context.set_new_pipes_costs(next_year, inflated_cost)

    return

def age_water_utilities(
        year: int,
        national_context: NationalContext,
        water_utilities: Set[WaterUtility],
        settings: Settings
    )-> None:

    for utility in sorted(water_utilities, key=lambda x: x.bwf_id):

        wu_actions.age_water_utility(
            utility,
            year,
            settings,
            national_context.nrw_model_db
        )

    return

def age_national_context_assets(
        year: int,
        national_context: NationalContext,
        water_utilities: Set[WaterUtility],
        settings: Settings
    )-> None:

    nat_actions.age_connections(
        national_context,
        year,
        settings
    )

    return

def update_financial_balances(
        year: int,
        national_context: NationalContext,
        water_utilities: Set[WaterUtility],
        settings: Settings
    ) -> None:

    for water_utility in sorted(water_utilities, key= lambda wu: wu.bwf_id):
        
        water_utility_yv = get_snapshot(water_utility, year=year)
        balance = water_utility_yv.balance

        nib_alpha = water_utility_yv.investment_budget # NIV(y) \cdot \alpha_w(y)

        revenue = wu_actions.collect_revenue(
            water_utility=water_utility,
            year=year
        )

        capex = water_utility_yv.capex

        opex = water_utility_yv.opex

        wlr = water_utility_yv.nrw_mitigation_budget

        wic = wu_actions.pay_water_imports(
            water_utility=water_utility,
            year=year
        )

        fin = water_utility_yv.gw_permit_fine

        int_pri = water_utility.get_debt_service(year=year)

        # Eq 21.a 
        provisional_balance = (
            balance + nib_alpha + revenue
            - capex - opex
            - wlr - wic - fin
            - int_pri
            - settings._cost_normalization(year, water_utility.bwf_id)
        )
        provisional_balance = round(provisional_balance, 2)

        # Eq 21.b
        debt = -provisional_balance if provisional_balance < 0.0 else 0.0

        if settings._is_simulating_historical_period:
            debt = 0.0 # we said no debt in historical period

        water_utility.track_debt(when=year, value=debt)

        if debt:
            ba2d_ratio = water_utility_yv.bond_ratio

            pro, bonds = raise_amount(
                economy_data=(
                    national_context.bonds_settings,
                    national_context.economy
                ),
                value=debt * ba2d_ratio,
                year=year,
                water_utility=water_utility
            )

            water_utility.m_bonds.add(bonds)
        else:
            pro = 0.0

        # Eq 21.c
        updated_balance = provisional_balance + pro
        updated_balance = round(updated_balance, 2)
        if settings._is_simulating_historical_period:
            updated_balance = 0.0 # we said participants will start from 0.0 balance

        water_utility.set_balance(when=year+1, value=updated_balance)

    return