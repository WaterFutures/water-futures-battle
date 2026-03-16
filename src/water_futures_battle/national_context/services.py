from typing import Any, Dict, Set, List

import pandas as pd

from water_futures_battle.core.settings import Settings

from ..core.utility import timestampify
from ..pipes import PipeOption
from ..water_utilities import WaterUtility
from ..water_utilities.dynamic_properties import WaterUtilityResults

from .entities import NationalContext
from .policies import BudgetAllocation
from .interventions import InstallPipe


def share_yearly_budget(
        budget: float,
        national_context: NationalContext,
        year: int,
        policy_desc: Dict[str, Any]
    ) -> Dict[str, float]:

    if policy_desc["policy"] == BudgetAllocation.BY_POPULATION:
        budget_allocation_plan = BudgetAllocation.distribute_budget_population(
            budget,
            national_context.water_utilities,
            year
        )

    elif policy_desc["policy"] == BudgetAllocation.BY_INVERSE_POPULATION:
        budget_allocation_plan = BudgetAllocation.distribute_inverse_budget_population(
            budget,
            national_context.water_utilities,
            year
        )

    elif policy_desc["policy"] == BudgetAllocation.BY_INCOME:
        budget_allocation_plan = BudgetAllocation.distribute_budget_income(
            budget,
            national_context.water_utilities,
            year
        )
    
    elif policy_desc["policy"] == BudgetAllocation.BY_INVERSE_INCOME:
        budget_allocation_plan = BudgetAllocation.distribute_reverse_budget_income(
            budget,
            national_context.water_utilities,
            year
        )
    
    elif policy_desc["policy"] == BudgetAllocation.CUSTOM:
        budget_allocation_plan = BudgetAllocation.distribute_custom(
            budget,
            national_context.water_utilities,
            policy_desc['policy_args']
        )
    
    else:
        raise ValueError(f"Unknown policy for budget allocation {policy_desc['policy']} in year {year}")
    
    # Bulk update of the budgets
    WaterUtility._results.commit(
        a_property=WaterUtilityResults.WUIB,
        timestamps=pd.date_range(
            start=timestampify(year),
            periods=1,
            freq='YS'
        ),
        data=budget_allocation_plan
    )
    
    return budget_allocation_plan

def work_on_connections(
        national_context: NationalContext,
        year: int,
        intervention_desc: List[Dict[str, Any]],
        pipe_options: Set[PipeOption],
        settings: Settings
    ) -> Dict[str, float]:
    
    # See work on connections of water_utilities to understand this funciton.
    # First we installed the requested inteventions, after we check for failing pipes
    # Differently. from wate ruitlity works on connections, here costs and emission
    # are divided equally between the two utilities

    capexes =  {
        wu.bwf_id: 0.0
        for wu in sorted(national_context.water_utilities, key=lambda x: x.bwf_id)
    }

    for intervention in intervention_desc:
        cost, (wu_from, wu_to) = InstallPipe.execute(
            national_context=national_context,
            year=year,
            intervention_desc=intervention,
            pipe_options=pipe_options,
            settings=settings
        )
        
        capexes[wu_from.bwf_id] += cost/2
        capexes[wu_to.bwf_id] += cost/2

    for connection in sorted(national_context.cross_utility_connections, key=lambda c: c.bwf_id):
        
        if connection.replaced_by_cnn_id == "":
            # the connection doesn't get replaced, if it fails we re-install a pipe here
            cost = connection.inspect_and_replace(
                year=year,
                lifetime_rng=settings.pipes_lifetime_rng
            )
        else:
            # the connection does get replaced, if it fails we install a new one on the new connection
            failed_pipe = connection.inspect(when=year)
            if failed_pipe is not None:
                # status is good, no need to do anything
                cost = 0.0
            else:
                # status is not ok, the pipe failed and the connection is not active anymore.
                # get the current connection (recurisvely in case the new connection also got replaced)
                new_connection = resolve_current_cnn(connection, year, national_context.cross_utility_connections)

                # if everything goes to plan, new connection is another connection bu not yet used.
                # however if one connection replaces more than one, it could be that the first one failing
                # installs the new pipe. we don't want that, when a connection replaces more than one, we need 
                # to deal with all of them at the same time... 
                assert len(new_connection.replaces) < 2, "A pipe that gets replaced by a connection replacing more than one failed."

                new_pipe = new_connection.install_pipe(
                    pipe_option=failed_pipe._pipe_option,
                    installation_date=failed_pipe.decommission_date,
                    lifetime_rng=settings.pipes_lifetime_rng
                )

                pipe_unit_cost = new_pipe._pipe_option.unit_cost.loc[new_pipe.installation_date]

                cost = pipe_unit_cost * new_connection.distance

        # Let's get in which water utilities this cost should be applied, if any, otherwise save the burden
        if cost ==  0.0:
            continue

        wu_from = next((wu
                         for wu in national_context.water_utilities
                         if connection.from_node in wu.municipalities
        ))
    
        wu_to = next((wu
                    for wu in national_context.water_utilities
                    if connection.to_node in wu.municipalities
        ))

        capexes[wu_from.bwf_id] += cost/2
        capexes[wu_to.bwf_id] += cost/2

    return capexes
