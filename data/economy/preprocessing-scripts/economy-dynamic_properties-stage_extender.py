
import os
from pathlib import Path
import numpy as np
RNG = np.random.default_rng(seed=12860)
import pandas as pd
from water_futures_battle.core.base_model import DynamicProperties
from water_futures_battle.economy.dynamic_properties import EconomyDB

STAGE_SEEDS = RNG.spawn(n_children=3)
STAGE_YEARS = [
    ("2025-01-01", "2049-01-01"),
    ("2050-01-01", "2074-01-01"),
    ("2075-01-01", "2099-01-01"),
]
STAGE_TARGET_INFLATION = [
    2.5,
    4,
    2,
]
STAGE_K = [
    0.10,
    0.15,
    0.2,
]
STAGE_SIGMA = [
    0.4,
    0.7,
    0.4,
]
STAGE_P = [
    0.04,
    0.07,
    0.03,
]
STAGE_SHOCK = [
    4,
    6,
    2,
]


def append_inflation_data(economic_df: pd.DataFrame, stage_idx: int) -> pd.DataFrame:
    rng = STAGE_SEEDS[stage_idx]

    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")

    target_inflation = STAGE_TARGET_INFLATION[stage_idx]
    k = STAGE_K[stage_idx]
    sigma = STAGE_SIGMA[stage_idx]
    p = STAGE_P[stage_idx]
    shock = STAGE_SHOCK[stage_idx]

    for year in YEARS:
        pre_inflation = float(economic_df.loc[year - pd.DateOffset(years=1), "NL0000"])

        z_score = rng.standard_normal()
        occurred_shock = shock if rng.random() < p else 0
        current_inflation = (
            pre_inflation + k * (target_inflation - pre_inflation) + sigma * z_score + occurred_shock
        )
        economic_df.loc[year, "NL0000"] = current_inflation
        
    return economic_df.sort_index().round(2)

def append_expectation_data(
        df: pd.DataFrame,
        inflation_df: pd.DataFrame,
        stage_idx: int
) -> pd.DataFrame:

    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")
    new_expectations = inflation_df.shift(1).rolling(window=3).mean()

    df = df.reindex(df.index.union(YEARS))
    df.loc[YEARS] = new_expectations.loc[YEARS]
    df.index.name = 'timestamp'
    return df

def append_invdemand_data(
        df: pd.DataFrame,
        stage_idx: int
) -> pd.DataFrame:
    
    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")

    MIN_INVESTOR_DEMAND = 0.6
    MAX_INVESTOR_DEMAND = 1.4
    new_invdemand_df = pd.DataFrame(
        data={'NL0000': STAGE_SEEDS[stage_idx].uniform(
            low=MIN_INVESTOR_DEMAND,
            high=MAX_INVESTOR_DEMAND,
            size=(len(YEARS),)
        )},
        index=YEARS
    )

    df = pd.concat([df, new_invdemand_df], axis=0)
    df.index.name = 'timestamp'
    return df


def main(previous_stage_results: Path, next_stage_inputs: Path, stage_number: int):
    
    filename = "economy-dynamic_properties.xlsx"
    
    input_path = previous_stage_results /"economy" / filename
    economic_db = EconomyDB.load_from_file(input_path)
    inflation_df = economic_db[EconomyDB.INFLATION]
    expectation_df = economic_db[EconomyDB.INFEXPECT]
    invdemand_df = economic_db[EconomyDB.INVDEMAND]

    inflation_df = append_inflation_data(inflation_df, stage_number-1)
    expectation_df = append_expectation_data(expectation_df, inflation_df, stage_number-1)
    invdemand_df = append_invdemand_data(invdemand_df, stage_number-1)
    
    economic_db[EconomyDB.INFLATION] = inflation_df
    economic_db[EconomyDB.INFEXPECT] = expectation_df
    economic_db[EconomyDB.INVDEMAND] = invdemand_df
    economics_options_dps = DynamicProperties(
        name=f"economy-dynamic_properties-stage_{stage_number}",
        dataframes=economic_db
    )
    economics_options_dps.dump(path=next_stage_inputs / "economy")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate economy time series for a stage and append it to the previous stage's file."
    )
    parser.add_argument(
        "stage_number",
        type=int,
        choices=[1,2,3],
        help="Stage of the competition for which to generate the new data (1, 2, or 3)"
    )
    parser.add_argument(
        "previous_stage_results",
        type=Path,
        help="Path to the folder containing the final status of the system in the previous stage (absolute or relative to the current working directory)."
    )
    parser.add_argument(
        "next_stage_inputs",
        type=Path,
        help="Path to the output folder where the new input files for the next stage will be saved (absolute or relative to the current working directory)."
    )
    args = parser.parse_args()

    previous_stage_results = args.previous_stage_results
    if not previous_stage_results.is_absolute():
        previous_stage_results = Path(os.getcwd()) / previous_stage_results
    next_stage_inputs = args.next_stage_inputs
    if not next_stage_inputs.is_absolute():
        next_stage_inputs = Path(os.getcwd()) / next_stage_inputs

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main(previous_stage_results, next_stage_inputs, args.stage_number)
