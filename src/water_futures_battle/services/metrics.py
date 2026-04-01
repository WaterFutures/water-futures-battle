from typing import Dict, Set

import pandas as pd
import numpy as np

from ..core import Settings, get_snapshot
from ..core.utility import timestampify
from ..jurisdictions.dynamic_properties import MunicipalitiesResults
from ..jurisdictions import Municipality
from ..economy.dynamic_properties import EconomyDB
from ..economy.entities import BondsSettings
from ..water_utilities import WaterUtility
from ..national_context import NationalContext

MetricsT = Dict[str, pd.DataFrame]

def end_of_horizon_debt_npv(
        a_water_utility: WaterUtility,
        last_year: int,
        yield_rate: float
    ) -> float:

    npv = 0.0

    for bond in a_water_utility.m_bonds:
        npv += bond.net_present_value(
            year=last_year,
            yield_rate=yield_rate
        )

    return npv

def ghg_emissions(a_water_utility: WaterUtility) -> pd.Series:
    return a_water_utility.ghg_embedded_emissions + a_water_utility.ghg_operations_emissions

def service_reliability_metric(a_municipality: Municipality) -> pd.Series:
    return 1 - (a_municipality.undelivered_demand / a_municipality.billable_demand)

def affordability_metric(a_water_utility: WaterUtility, Dlife: float) -> pd.Series:
    
    # We should do a weighted quantile calculation for income, but the difference is minimal
    avg_disposable_incomes = pd.concat([
        m.disp_income_avg for m in a_water_utility.municipalities
    ], axis=1)

    # Dlife is in L/person/day -> *365*0.001 to get m^3/person/year
    # Costs are in €/household/year (or person in this case)
    # and €/m^3. Thus we get €/year.
    # Income is in k€
    return (
        (a_water_utility.price_fix_comp + a_water_utility.price_var_comp * Dlife*365*0.001) / 
        (avg_disposable_incomes.quantile(0.2, axis=1)*1000)
    )


def compute_metrics(
        settings: Settings,
        national_context: NationalContext,
        water_utilities: Set[WaterUtility]
    ) -> Dict[str, pd.DataFrame]:
    
    pi_1_dfs = {}
    pi_2_dfs = {}
    pi_3_dfs = {}
    pi_4_dfs = {}
    # To calculate the NPV of the remaining bonds we use the current yield rate
    # as discount factor, but in a neutral setup, i.e., removing investor sensitivity.
    bonds_neutral_yield_rate = (
        national_context.bonds_settings.risk_free_rate +
        float(national_context.economy[EconomyDB.INFEXPECT].loc[
            timestampify(settings.end_year),
            national_context.state.cbs_id
        ])
    )

    for wu in sorted(water_utilities, key=lambda x: x.bwf_id):

        pi_1_dfs[wu.bwf_id] = end_of_horizon_debt_npv(
            a_water_utility=wu,
            last_year=settings.end_year,
            yield_rate=bonds_neutral_yield_rate/100
        )

        pi_2_dfs[wu.bwf_id] = ghg_emissions(wu)

        # PI3 is the only one that works by municipality and not by water utility,
        # thus we iterate for each water utility's municipality
        for m in sorted(wu.municipalities, key= lambda x: x.cbs_id):

            if m.cbs_id not in Municipality._results[MunicipalitiesResults.DEMAND_BILLABLE]:
                # it means we didn't evaluate it in this stage
                continue

            pi_3_dfs[m.cbs_id] = service_reliability_metric(m)

        pi_4_dfs[wu.bwf_id] = affordability_metric(wu, settings.lifeline_volume)
    
    y2s = [timestampify(y) for y in settings.years_to_simulate]
    npv_debt_df = pd.DataFrame(pi_1_dfs, index=[f"{settings.end_year+1}-01-01"]).round(2)
    npv_debt_df.index.name = "timestamp"

    ghg_emissions_df = pd.DataFrame(pi_2_dfs)
    ghg_emissions_df.index.name = "timestamp"
    ghg_emissions_df = ghg_emissions_df.loc[ghg_emissions_df.index.isin(y2s)].round(0)
    
    service_rel_df = pd.DataFrame(pi_3_dfs)
    service_rel_df.index.name = "timestamp"
    service_rel_df = service_rel_df.loc[service_rel_df.index.isin(y2s)].round(3)

    affordability_df = pd.DataFrame(pi_4_dfs)
    affordability_df.index.name = "timestamp"
    affordability_df = affordability_df.loc[affordability_df.index.isin(y2s)].round(4)

    return {
        "financial_sustainability": npv_debt_df,
        "GHG_emissions": ghg_emissions_df,
        "service_reliability": service_rel_df,
        "affordability": affordability_df
    }

    