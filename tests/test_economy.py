import pandas as pd
from numpy.random import default_rng
RNG = default_rng(128)

from water_futures_battle.economy.services import raise_amount
from water_futures_battle.economy.dynamic_properties import EconomyDB
from water_futures_battle.economy.entities import BondsSettings

def test_issue():

    # Hardoced value for settings
    bsett = BondsSettings(
        amount_debt_ratio=1.5,
        risk_free_rate=1.0,
        spread_sensitivity=1.0,
        maturity=25
    )

    time_range = pd.date_range(start='2000-01-01', end='2004-01-01', freq='YS')
    edb = EconomyDB(
        dataframes={
            "inflation": pd.DataFrame(
            ),
            "inflation-expect": pd.DataFrame(
                [1, 2, 3, 2.3, 1.2],
                index=time_range,
                columns=['NL0000']
            ),
            "investor_demand": pd.DataFrame(
                [0.6, 0.7, 1, 1.2, 1.4],
                index=time_range,
                columns=['NL0000']
            )
        }
    )
    yields = [2.4, 3.3, 4, 3.1, 1.8]
    coupons = [2,    3, 4, 3.3, 2.2]
    values = [92.5, 95, 100, 103, 108]

    for i, year in enumerate(time_range):
        v, bonds = raise_amount(
            economy_data=(bsett,edb),
            value=100,
            year=year.year,
            wutility_name="WU00"
        )
        assert ((v/bonds.n_bonds)-values[i]) < 1, f"Nope, {v}, {values[i]}"
    