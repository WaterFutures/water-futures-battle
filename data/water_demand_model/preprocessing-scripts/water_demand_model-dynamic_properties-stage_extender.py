import os
from pathlib import Path
import numpy as np
import pandas as pd
from water_futures_battle.core.base_model import DynamicProperties
from water_futures_battle.water_demand_model.properties import WaterDemandModelDB
import csv

NL_COLS = ["NL0000-min", "NL0000-max"]

# Stage-specific parameters
STAGE_YEARS = [
    pd.date_range(start ="2025-01-01", end="2049-01-01", freq="YS"),
    pd.date_range(start ="2050-01-01", end="2074-01-01", freq="YS"),
    pd.date_range(start ="2075-01-01", end="2099-01-01", freq="YS")
]

def append_data (
        residential_demand_df: pd.DataFrame,
        industrial_demand_df: pd.DataFrame,
        future_residential_demands: pd.DataFrame,
        future_industrial_demands: pd.DataFrame,
        stage_idx: int
    )-> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Appends future demand data for the given stage index (0, 1, 2).
    """

    start_time = pd.to_datetime("2024-01-01")
    # We add a bit of slack only because we forgot to do it for the original data...
    init_consumption_residential  = residential_demand_df.loc[start_time, NL_COLS]*np.array([0.95, 1.05])
    init_consumption_industrial = industrial_demand_df.loc[start_time, NL_COLS]*np.array([0.975, 1.025])

    YEARS = STAGE_YEARS[stage_idx]
    for year in YEARS:
        for col in future_residential_demands.columns:
            if col == 'NL0000':
                residential_demand_df.loc[year, NL_COLS] = float(future_residential_demands.loc[year, col])*init_consumption_residential
                industrial_demand_df.loc[year, NL_COLS] = float(future_industrial_demands.loc[year, col])*init_consumption_industrial
            else:
                residential_demand_df.loc[year, col] = future_residential_demands.loc[year, col]*init_consumption_residential.mean()
                industrial_demand_df.loc[year, col] = future_industrial_demands.loc[year, col]*init_consumption_industrial.mean()

    return (residential_demand_df,industrial_demand_df)


def main(previous_stage_results: Path, next_stage_inputs: Path, stage_number: int):
    # Determine input file based on stage
    filename = 'water_demand_model-dynamic_properties.xlsx'
    input_path = previous_stage_results / 'water_demand_model' / filename

    water_demand_db = WaterDemandModelDB.load_from_file(input_path)
    residential_demand_df = water_demand_db[WaterDemandModelDB.PER_HOUSE_DEMAND]
    industrial_demand_df = water_demand_db[WaterDemandModelDB.PER_BUSINESS_DEMAND]

    # The future vales of per unit demand are stored in the csv files in raw-data folder
    future_residential_demands = pd.read_csv("../raw-data/future_residential_demands.csv",index_col="YEAR",parse_dates=True)
    future_industrial_demands = pd.read_csv("../raw-data/future_industrial_demands.csv",index_col="YEAR",parse_dates=True)

    residential_demand_df, industrial_demand_df = append_data(
        residential_demand_df=residential_demand_df,
        industrial_demand_df=industrial_demand_df,
        future_residential_demands=future_residential_demands,
        future_industrial_demands=future_industrial_demands,
        stage_idx=stage_number-1
    )

    water_demand_db[WaterDemandModelDB.PER_HOUSE_DEMAND] = residential_demand_df
    water_demand_db[WaterDemandModelDB.PER_BUSINESS_DEMAND] = industrial_demand_df

    # Assign back and save
    water_demand_dps = DynamicProperties(
        name = f"water_demand_model-dynamic_properties-stage_{stage_number}",
        dataframes=water_demand_db
    )
    water_demand_dps.dump(path = next_stage_inputs / "water_demand_model")


if __name__ == "__main__":
    # This script is intended to be run for each team to append exogenous dynamic properties
    # to the system's final status from the previous stage, producing new input files for the next stage.

    # Parse arguments: stage number, previous stage results directory, and next stage input directory.
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate dynamic water demand model properties for a given stage based on the previous stage's final status."
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

    # We work from this file directory to have all paths relative to this file.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main(previous_stage_results, next_stage_inputs, args.stage_number)
