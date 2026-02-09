from typing import Dict, Set

import pandas as pd
import numpy as np

from ..core import Settings, get_snapshot
from ..core.utility import timestampify
from ..jurisdictions import Municipality
from ..water_utilities import WaterUtility
from ..national_context import NationalContext

MetricsT = Dict[str, pd.DataFrame]

def end_of_horizon_debt_npv(a_water_utility: WaterUtility) -> float:
    return 0.0

def ghg_emissions(a_water_utility: WaterUtility) -> pd.Series:
    return pd.Series()

def service_reliability_metric(a_municipality: Municipality) -> pd.Series:
    return pd.Series()

def affordability_metric(a_water_utility: WaterUtility, Dlife: float) -> pd.Series:
    
    avg_disposable_incomes = pd.concat([
        m.disp_income_avg for m in a_water_utility.municipalities
    ], axis=1)

    return (
        (a_water_utility.price_fix_comp + a_water_utility.price_var_comp * Dlife) / 
        avg_disposable_incomes.quantile(0.2, axis=1)
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
    for wu in sorted(water_utilities, key=lambda x: x.bwf_id):

        pi_1_dfs[wu.bwf_id] = end_of_horizon_debt_npv(wu)

        pi_2_dfs[wu.bwf_id] = ghg_emissions(wu)

        # PI3 is the only one that works by municipality and not by water utility,
        # thus we iterate for each water utility's municipality
        for m in sorted(wu.municipalities, key= lambda x: x.cbs_id):
            pi_3_dfs[m.cbs_id] = service_reliability_metric(m)

        pi_4_dfs[wu.bwf_id] = affordability_metric(wu, settings.lifeline_volume)
    
    y2s = [timestampify(y) for y in settings.years_to_simulate]
    npv_debt_df = pd.DataFrame(pi_1_dfs, index=[f"{settings.end_year+1}-01-01"])
    npv_debt_df.index.name = "timestamp"

    ghg_emissions_df = pd.DataFrame(pi_2_dfs)
    ghg_emissions_df.index.name = "timestamp"
    ghg_emissions_df = ghg_emissions_df.loc[ghg_emissions_df.index.isin(y2s)]
    
    service_rel_df = pd.DataFrame(pi_3_dfs)
    service_rel_df.index.name = "timestamp"
    service_rel_df = service_rel_df.loc[service_rel_df.index.isin(y2s)]

    affordability_df = pd.DataFrame(pi_4_dfs)
    affordability_df.index.name = "timestamp"
    affordability_df = affordability_df.loc[affordability_df.index.isin(y2s)]

    return {
        "financial_sustainability": npv_debt_df,
        "GHG_emissions": ghg_emissions_df,
        "service_reliability": service_rel_df,
        "affordability": affordability_df
    }

    