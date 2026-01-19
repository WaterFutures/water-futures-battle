from typing import Tuple
from pathlib import Path

from numpy.random import default_rng
RNG= default_rng(128)
import pandas as pd

from .properties import WaterDemandModelDB
from .entities import WaterDemandModelPattern, WaterDemandModelPatterns

def configure_water_demand_model(config: dict) -> Tuple[WaterDemandModelPatterns, WaterDemandModelDB]:
    """
    Use the config dicitonary to setup all the variables that the water demand model
    relies on and are not in the municipality domain

    :param config: configuration dictionary
    :type config: dict
    :return: Tuple with static and dynamic properties for the water demand model
    :rtype: tuple[Any, Any]
    """
    wdm_sheets = pd.read_excel(config['water_demand_model-static_properties'], sheet_name=None)

    patterns: WaterDemandModelPatterns = {}
    for ptype in ['residential', 'business']:
        for idx, row in wdm_sheets[ptype].iterrows():
            p_id = row[WaterDemandModelPattern.ID]

            patterns[p_id] = WaterDemandModelPattern(
                bwf_id=p_id,
                category=ptype,
                values=row[WaterDemandModelPattern.VALUES].to_numpy()
            )

    # Get the deynamic properties, e.g., per capita demand
    wdm_dps = WaterDemandModelDB.load_from_file(Path(config[WaterDemandModelDB.NAME]))

    return (patterns, wdm_dps)
