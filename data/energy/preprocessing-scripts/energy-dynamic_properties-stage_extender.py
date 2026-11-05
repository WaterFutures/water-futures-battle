import os
from pathlib import Path
import numpy as np
RNG = np.random.default_rng(seed=12870)
import pandas as pd
from water_futures_battle.core.base_model import DynamicProperties
from water_futures_battle.energy.dynamic_properties import EnergySysDB
from water_futures_battle.economy.dynamic_properties import EconomyDB

STAGE_SEEDS = RNG.spawn(n_children=3)
STAGE_YEARS = [
    ("2025-01-01", "2049-01-01"),
    ("2050-01-01", "2074-01-01"),
    ("2075-01-01", "2099-01-01"),
]
STAGE_INF_WEIGHT = [
    0.25,
    0.4,
    0.1
]
STAGE_TREND = [
    -0.015,
    0.018,
    -0.02
]
STAGE_VOLATILITY = [
    0.05,
    0.07,
    0.02
]
STAGE_P = [
    0.3,
    0.1,
    0.1
]
STAGE_SHOCK = [
    0.1,
    0.2,
    0.05
]

def append_emission_data_1(emission_df: pd.DataFrame) -> pd.DataFrame:
    YEARS = pd.date_range(start="2025-01-01", end="2045-01-01", freq="YS")
    reduction_factors = RNG.normal(loc=0.929, scale=0.065, size=len(YEARS))

    emission_df = emission_df.reindex(emission_df.index.union(YEARS))
    emission_df.index.name = "timestamp"
    for i, year in enumerate(YEARS):
        emission_df.loc[year] = emission_df.loc[year - pd.DateOffset(years=1)] * reduction_factors[i]

    YEARS = pd.date_range(start="2046-01-01", end="2049-01-01", freq="YS")
    reduction_factors = RNG.normal(loc = 0.978, scale = 0.065, size = len(YEARS))

    for i, year in enumerate(YEARS):
        emission_df.loc[year] = emission_df.loc[year - pd.DateOffset(years=1)] * reduction_factors[i]
    
    
    return emission_df

def append_emission_data_2(emission_df: pd.DataFrame) -> pd.DataFrame:
    YEARS = pd.date_range(start="2050-01-01", end="2072-01-01", freq="YS")
    reduction_factors = RNG.normal(loc=1, scale=0.065, size=len(YEARS))

    emission_df = emission_df.reindex(emission_df.index.union(YEARS))
    emission_df.index.name = "timestamp"
    for i, year in enumerate(YEARS):
        emission_df.loc[year] = emission_df.loc[year - pd.DateOffset(years=1)] * reduction_factors[i]

    reduction_diff = emission_df.loc[YEARS[-1]]/10

    YEARS = pd.date_range(start="2073-01-01", end="2074-01-01", freq="YS")

    for i, year in enumerate(YEARS):
        emission_df.loc[year] = emission_df.loc[year - pd.DateOffset(years=1)] - reduction_diff
    
    return emission_df

def append_emission_data_3(emission_df: pd.DataFrame) -> pd.DataFrame:
    YEARS = pd.date_range(start="2075-01-01", end="2099-01-01", freq="YS")
    
    emission_df = emission_df.reindex(emission_df.index.union(YEARS))
    emission_df.index.name = "timestamp"
    reduction_diff = float(emission_df.loc[YEARS[0] - pd.DateOffset(years=1), 'NL0000'])/8
    
    noise = RNG.normal(loc=1, scale=1, size=len(YEARS))

    for i, year in enumerate(YEARS):
        emission_df.loc[year] = emission_df.loc[year - pd.DateOffset(years=1)] - reduction_diff*noise[i]

    emission_df = emission_df.apply(lambda x: np.maximum(x, 0))
    
    return emission_df

def append_ele_price_data(
        ele_price_df: pd.DataFrame,
        inflation_df: pd.DataFrame,
        stage_idx: int
    ) -> pd.DataFrame:

    rng = STAGE_SEEDS[stage_idx]

    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")

    #variables
    k = STAGE_INF_WEIGHT[stage_idx]
    energy_trend = STAGE_TREND[stage_idx]
    volatility = STAGE_VOLATILITY[stage_idx]
    p = STAGE_P[stage_idx]
    shock = STAGE_SHOCK[stage_idx]

    for year in YEARS:
        current_inflation = inflation_df.loc[year, "NL0000"]/100

        z_score = rng.standard_normal()
        occurred_shock = shock if rng.random() < p else 0

        # Price = Prev * (1 + trend + k*inflation + vol*Z + shock)
        prev_price = float(ele_price_df.loc[year-pd.DateOffset(years=1), "NL0000"])
        growth_rate = (
            k * (energy_trend + current_inflation) + 
            volatility * z_score + 
            occurred_shock
        )
        
        current_price = prev_price * (1 + growth_rate)

        # Update DataFrame
        ele_price_df.loc[year, "NL0000"] = current_price
        ele_price_df.loc[year + pd.DateOffset(months=6), "NL0000"] = current_price

    return ele_price_df.sort_index()

STAGE_SOLAR_TREND = [
    0.035,
    0.015,
    0.0 # third stage grows with inflation
]
STAGE_SOLAR_VOLATILITY = [
    0.02,
    0.02,
    0.02
]

def append_solar_cost_data(
        solar_df: pd.DataFrame,
        inflation_df: pd.DataFrame,
        stage_idx: int
    ) -> pd.DataFrame:
    rng = STAGE_SEEDS[stage_idx]

    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")

    trend = STAGE_SOLAR_TREND[stage_idx]
    volatility = STAGE_SOLAR_VOLATILITY[stage_idx]

    for year in YEARS:
        prev_cost = float(solar_df.loc[year - pd.DateOffset(years=1), "NL0000"])

        if year.year < 2050:
            z_score = rng.standard_normal()

            # SolarCost = PrevCost * (1 - trend + volatility * Z)
            # Note: If (volatility * Z) is more positive than trend is negative, 
            # costs could technically go up slightly in a "bad" year.
            current_multiplier = (1 - trend + volatility * z_score)
            current_cost = prev_cost * current_multiplier
        
        else:
            current_cost = prev_cost * (1+float(inflation_df.loc[year, "NL0000"])/100)

        solar_df.loc[year, "NL0000"] = current_cost
    
    return solar_df.sort_index()

def append_ele_patter_data(
        ele_patter_df: pd.DataFrame,
        future_patterns_df: pd.DataFrame,
        stage_idx: int
    ) -> pd.DataFrame:
    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")

    for ts in YEARS:
        if not f"year-{ts.year}" in future_patterns_df.columns:
            # no change of pattern this year
            continue

        # there is a change of pattern, add it
        ele_patter_df.loc[ts] = future_patterns_df[f"year-{ts.year}"].to_numpy()
    
    return ele_patter_df.sort_index()


def append_data (
        ele_price_df: pd.DataFrame,
        ele_patter_df: pd.DataFrame,
        emission_df: pd.DataFrame,
        solar_df: pd.DataFrame,
        inflation_df: pd.DataFrame,
        future_patterns_df: pd.DataFrame,
        stage_idx: int
    )-> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    
    ele_price_df = append_ele_price_data(ele_price_df, inflation_df, stage_idx)
    if stage_idx == 0:
        emission_df = append_emission_data_1(emission_df)
    elif stage_idx == 1:
        emission_df = append_emission_data_2(emission_df)
    else:
        emission_df = append_emission_data_3(emission_df)
    solar_df = append_solar_cost_data(solar_df, inflation_df, stage_idx)
    ele_patter_df = append_ele_patter_data(ele_patter_df, future_patterns_df, stage_idx)

    return (
        ele_price_df.round(4),
        ele_patter_df.round(3),
        emission_df.round(),
        solar_df.round(2)
    )

def main(previous_stage_results: Path, next_stage_inputs: Path, stage_number: int):
    
    filename = 'energy_system-dynamic_properties.xlsx'
    
    input_path =  previous_stage_results / 'energy' / filename

    energy_db = EnergySysDB.load_from_file(input_path)
    ele_price_df = energy_db[EnergySysDB.EPRICE_UNIT]
    ele_patter_df = energy_db[EnergySysDB.EPRICE_PATT]
    emission_df = energy_db[EnergySysDB.EMISS_FACTOR]
    solar_df = energy_db[EnergySysDB.SOLAR_COST]

    # Energy behaviour depends on inflation
    inflation_inputpath = next_stage_inputs / 'economy' / f'economy-dynamic_properties-stage_{stage_number}.xlsx'
    economy_db = EconomyDB.load_from_file(inflation_inputpath)
    inflation_df = economy_db[EconomyDB.INFLATION]

    # Electricty price patterns are uploaded from a file in. the raw-data folder
    future_patterns_df = pd.read_csv("../raw-data/future_electricity_patterns.csv")

    (
        ele_price_df,
        ele_patter_df,
        emission_df,
        solar_df
    ) = append_data(
        ele_price_df,
        ele_patter_df,
        emission_df,
        solar_df,
        inflation_df,
        future_patterns_df,
        stage_number-1
    )

    #assign back and save
    energy_db[EnergySysDB.EPRICE_UNIT] = ele_price_df
    energy_db[EnergySysDB.EPRICE_PATT] = ele_patter_df
    energy_db[EnergySysDB.EMISS_FACTOR] = emission_df
    energy_db[EnergySysDB.SOLAR_COST] = solar_df
    energy_options_dps = DynamicProperties(
        name =f"energy_system-dynamic_properties-stage_{stage_number}",
        dataframes=energy_db.dataframes
    )

    energy_options_dps.dump(path = next_stage_inputs / "energy")


if __name__ == "__main__":
    # This script is intended to be run for each team to append exogenous dynamic properties
    # to the system's final status from the previous stage, producing new input files for the next stage.

    # Parse arguments: previous stage results directory and next stage input directory.
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate dynamic pipe options properties for stage 1 based on the previous stage's final status."
    )
    parser.add_argument(
        "stage_number",
        type=int,
        choices=[1,2,3],
        help="Stage of the compeition for which to generate the new data (1, 2, or 3)"
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

    # We work form this file directory to have all paths relative to this file.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main(previous_stage_results, next_stage_inputs, args.stage_number)
