from typing import Dict, Set, Tuple

import pandas as pd
from rich.progress import Progress

from ..core import Settings
from ..core.utility import timestampify
from ..water_utilities import WaterUtility
from ..national_context import NationalContext
from ..masterplan import Masterplan

from ..water_utilities import services as wu_actions
from ..national_context import services as nat_actions

from .metrics import MetricsT, compute_metrics

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
    # We use a progress bar to track the evaluation across years
    with Progress() as progress:
        task_years = progress.add_task("[green]Years", total=settings.n_years_to_simulate)

        for year in settings.years_to_simulate:

            # We add a second progress bar for the application of interventions, 
            # we consider one extra utility for the interventions at national level
            task_utilities = progress.add_task("[cyan]Applying intervention to the utilities", total=len(water_utilities)+1)

            # Retrieve and apply the national policies:
            # - budget allocation
            national_policies = masterplan.national_policies(year=year)

            nat_inv_budget = 0
            nat_actions.share_yearly_budget(
                budget=nat_inv_budget,
                national_context=national_context,
                year=year,
                policy_desc=national_policies['budget_allocation']
            )

            # Retrieve and apply the national interventions:
            # - pipe installation
            national_interventions = masterplan.national_interventions(year=year)

            wus_national_capex = nat_actions.work_on_connections(
                national_context=national_context,
                year=year,
                intervention_desc=national_interventions['install_pipe'],
                pipe_options=national_context.pipe_options
            )

            # We completed national interventions, we can move to by utility actions
            progress.update(task_utilities, advance=1)
            


            # Extract this year mean max temperature. As we get it by season, 
            # let's take the maximum over the year.
            # The mean max temperature (and not the max max) captures both the 
            # durationand severity of the extreme.
            mean_tempmax = national_context.average__maximum_temperature
            maxtemp_year = mean_tempmax.loc[mean_tempmax.index.year == year].max()

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

                sources_capex = wu_actions.work_on_sources(
                    water_utility=water_utility,
                    year=year,
                    interventions_open_desc=wutil_interven['open_source'],
                    interventions_close_desc=wutil_interven['close_source'],
                    pump_options=national_context.pump_options,
                    pipe_options=national_context.pipe_options,
                    settings=settings
                )

                pipes_capex = wu_actions.work_on_connections(
                    water_utility=water_utility,
                    year=year,
                    interventions_desc=wutil_interven['install_pipe'],
                    pipe_options=national_context.pipe_options,
                    settings=settings
                )

                pumps_capex = wu_actions.work_on_pumps(
                    water_utility=water_utility,
                    year=year,
                    interventions_desc=wutil_interven['install_pumps'],
                    pump_options=national_context.pump_options,
                    settings=settings
                )

                solar_capex = wu_actions.work_on_solar_farms(
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
                #water_utility.track_capex(when=year, value=wu_capex)
                
                # compute the missing dependent dynamic properties (demand)
                wu_actions.realise_demands(
                    water_utility=water_utility,
                    year=year,
                    water_demand_model_data=national_context.water_demand_model_data,
                    nrw_model_data=national_context.nrw_model_data,
                    temperature=maxtemp_year,
                    settings=settings
                )

                # end water utilities for loop
                progress.update(task_utilities, advance=1)

            run_hydraulic_simulation(
                year=year,
                national_context=national_context,
                water_utilities=water_utilities,
                settings=settings
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

def run_hydraulic_simulation(
        year: int,
        national_context: NationalContext,
        water_utilities: Set[WaterUtility],
        settings: Settings
    )-> None:
    # Get how many disconnected water utilities are there, we will run one simulation for each indepdent network
    wutilities_groups = {}
    wutilities_groups_epanes = {}
    # Use the shared national resources to understand which are indepdent and which are not
    #task_simu = progress.add_task("[cyan]Simulating the networks", total=len(wutilities_groups))
    for idx, wutilities_group in wutilities_groups:
        # Build the network
        wutilities_groups_epanes[idx] = EpaneObject()

        # Run the simulation 
        run(wutilities_groups_epanes[idx])

    # Wait for all simulations to end
    
    # Save the results!
    for idx, wutilities_group in wutilities_groups:
        for water_utility in wutilities_group:
            water_utility.track_results(when=year, epyt_instance=wutilities_groups_epanes[idx])

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

def update_financial_balances(
        year: int,
        national_context: NationalContext,
        water_utilities: Set[WaterUtility],
        settings: Settings
    ) -> None:

    for water_utility in sorted(water_utilities, key= lambda wu: wu.bwf_id):
        
        # TODO: magical calculations

        water_utility.set_balance(when=year, value=0.0)

    return