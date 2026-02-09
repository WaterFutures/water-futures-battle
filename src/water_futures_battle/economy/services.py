import os
from pathlib import Path
from typing import Any, Dict, Set, Tuple

import numpy as np
import pandas as pd

from ..core.utility import timestampify
from ..core.base_model import StaticProperties
from ..core import Settings

from .dynamic_properties import EconomyDB
from .entities import BondIssuance, BondsSettings

def configure_economy(
        config: dict,
        data_path: str,
        settings: Settings
    ) -> Tuple[BondsSettings, EconomyDB, Dict[str, Set[BondIssuance]]]:

    bonds_config = config['bonds']

    bnd_settings = BondsSettings(
        risk_free_rate=bonds_config[BondsSettings.RISKFREE_RATE],
        spread_sensitivity=bonds_config[BondsSettings.SPREAD_SENS],
        maturity=bonds_config[BondsSettings.MATURITY]
    )

    economy_db = EconomyDB.load_from_file(os.path.join(data_path, config[EconomyDB.NAME]))

    # For each water utility, create the bond that were already existing
    bonds = {}

    return bnd_settings, economy_db, bonds

def bond_price(
        face_value: float,
        coupon_rate: float,
        yield_rate: float,
        horizon: int
) -> float:
    """
    Calculates the present value (price) of a bond.
    
    :param face_value: The bond's face/par value (principal)
    :param coupon_rate: Annual coupon rate as a decimal (e.g., 0.05 for 5%)
    :param yield_rate: Market yield/discount rate as a decimal
    :param horizon: Number of years until maturity
    :return: Current bond price
    """
    # Annual coupon payment
    c = coupon_rate * face_value
    
    # Calculate the discount factor for each future period
    periods = np.arange(1, horizon + 1)
    disc = 1.0 / (1.0 + yield_rate) ** periods

    pv_coupons = (c * disc).sum() 
    pv_face = face_value * disc[-1]

    return float(pv_coupons + pv_face)

def raise_amount(
        economy_data: Tuple[BondsSettings, EconomyDB],
        value: float,
        year: int,
        wutility_name: str
    ) -> Tuple[float, BondIssuance]:

    ts = timestampify(year, errors='raise')

    # Inflation expectation
    cs = economy_data[1][EconomyDB.INFEXPECT]['NL0000'].asof(ts)

    # Coupon = r + cs
    c = economy_data[0].risk_free_rate + cs

    a = economy_data[0].spread_sensitivity
    d = economy_data[1][EconomyDB.INVDEMAND]['NL0000'].asof(ts)

    # Yield rate 
    y = c + a * (1-d) 

    bp = bond_price(
        face_value=100,
        coupon_rate=c/100,
        yield_rate=y/100,
        horizon=economy_data[0].maturity
    )

    num_bonds = int(np.ceil(value / bp))

    actual_amount_raised = num_bonds * bp  # Might be slightly more than needed because of ceil operation

    bonds = BondIssuance(
        bwf_id="-".join([BondIssuance.ID_PREFIX, wutility_name, str(year)]),
        n_bonds=num_bonds,
        issue_date=ts,
        maturity_year=ts+pd.DateOffset(years=economy_data[0].maturity),
        coupon_rate=c
    )

    return actual_amount_raised, bonds

def adjust_for_inflation(
    values: pd.Series, 
    base_year: pd.Timestamp, 
    inflation: pd.Series
) -> pd.DataFrame:
    """
    Adjust values from base_year to all other years using inflation rates.
    
    Returns a DataFrame where:
    - Rows before base_year: inflated values (real → nominal)
    - Row at base_year: original values (unchanged)
    - Rows after base_year: deflated values (nominal → real)
    
    Args:
        values: Values at base_year
        base_year: Reference year for the values
        inflation: Series of inflation rates
    
    Returns:
        DataFrame with values adjusted to each year's purchasing power
    """
    # Assert that inflation has one value per year with no gaps
    years = inflation.index.year
    year_diffs = years[1:] - years[:-1]
    assert (year_diffs == 1).all(), (
        f"Inflation series must have exactly one value per year with no gaps. "
        f"Found year differences: {set(year_diffs)}"
    )
    
    cum_inflation = (1 + inflation / 100).cumprod()
    base_index = cum_inflation.loc[base_year]
    
    adjusted_values = values.values * (cum_inflation.values[:, None] / base_index)
    
    return pd.DataFrame(
        data=adjusted_values,
        columns=values.index,
        index=cum_inflation.index
    )

def dump_economy(
        bonds_settings: BondsSettings,
        economy_db: EconomyDB,
        all_wu_bonds: Dict[str, Set[BondIssuance]],
        output_dir: Path
    ) -> Dict[str, Any]:

    full_out_dir = output_dir / "economy"
    def as_rel_path(a_path: Path) -> str:
        return os.path.relpath(a_path, output_dir)

    bonds_desc = bonds_settings.to_dict()

    bonds_data = []
    for w_id, bonds_issuances in all_wu_bonds.items():
        for b in bonds_issuances:
            bonds_data.append(b.to_dict() | {'water_utility_id': w_id})

    if len(bonds_data) > 0:
        bonds_df = pd.DataFrame(bonds_data)
    else:
        bonds_df = pd.DataFrame(columns=BondIssuance.file_columns())

    bonds_properties = StaticProperties(
        name="bonds-static_properties",
        dataframes={'entities': bonds_df}
    )

    sp_path = bonds_properties.dump(full_out_dir)

    bonds_desc['static_properties'] = as_rel_path(sp_path)

    dp_path = economy_db.dump(full_out_dir)

    return {
        economy_db.NAME: as_rel_path(dp_path),
        bonds_properties.name: as_rel_path(sp_path),
        "bonds": bonds_desc
    }
