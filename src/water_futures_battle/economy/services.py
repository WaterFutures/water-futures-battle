from typing import Dict, Set, Tuple

import numpy as np
import pandas as pd

from .dynamic_properties import EconomyDB
from .entities import BondIssuance, BondsSettings
from ..utility.utility import timestampify

def configure_economy(config: dict) -> Tuple[BondsSettings, EconomyDB, Dict[str, Set[BondIssuance]]]:

    bonds_config = config['bonds']

    bnd_settings = BondsSettings(
        amount_debt_ratio=bonds_config[BondsSettings.AM2DEBT_RATIO],
        risk_free_rate=bonds_config[BondsSettings.RISKFREE_RATE],
        spread_sensitivity=bonds_config[BondsSettings.SPREAD_SENS],
        maturity=bonds_config[BondsSettings.MATURITY]
    )

    economy_db = EconomyDB.load_from_file(config[EconomyDB.NAME])

    # For each water utility, create the bond that were already existing
    bonds = {}

    return bnd_settings, economy_db, bonds
