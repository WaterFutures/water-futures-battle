import os
from pathlib import Path
import numpy as np
import pandas as pd
from water_futures_battle.core.base_model import DynamicProperties
from water_futures_battle.pipes.dynamic_properties import PipeOptionsDB

PVC_PIPES = [f'PI{str(i).zfill(2)}' for i in range(1, 6)]
STEEL_PIPES = [f'PI{str(i).zfill(2)}' for i in range(6, 11)]
# Define reduction factors and years
STAGE_PVC_FACTORS = [
    np.array([1.00, 0.96, 0.92, 0.88, 0.85]),
    np.array([0.80, 0.58, 0.36, 0.32, 0.28]),
    np.array([0.23, 0.17, 0.11, 0.05, 0.01])
]
STAGE_STEEL_FACTORS = [
    np.array([1.00, 0.95, 0.90, 0.72, 0.53]),
    np.array([0.35, 0.31, 0.27, 0.24, 0.22]),
    np.array([0.20, 0.16, 0.07, 0.00, 0.00])
]
STAGE_YEARS = [
    pd.date_range(start="2025-01-01", end="2049-01-01", freq='5YS'),
    pd.date_range(start="2050-01-01", end="2074-01-01", freq='5YS'),
    pd.date_range(start="2075-01-01", end="2099-01-01", freq='5YS')
]

def append_data(
        emission_df: pd.DataFrame,
        stage_idx: int
    ) -> tuple[pd.DataFrame]:

    years = STAGE_YEARS[stage_idx]
    pvc_factors= STAGE_PVC_FACTORS[stage_idx].reshape(-1, 1)
    steel_factors = STAGE_STEEL_FACTORS[stage_idx].reshape(-1, 1)

    base_values_pvc = emission_df.loc[pd.to_datetime("2020-01-01"), PVC_PIPES].to_numpy()
    base_values_steel = emission_df.loc[pd.to_datetime("2020-01-01"), STEEL_PIPES].to_numpy()

    emission_df = emission_df.reindex(emission_df.index.union(years))
    emission_df.index.name = 'timestamp'

    emission_df.loc[years, PVC_PIPES] = np.tile(base_values_pvc, (5,1)) * pvc_factors
    emission_df.loc[years, STEEL_PIPES] = np.tile(base_values_steel, (5,1)) * steel_factors

    return (emission_df,)

def main(previous_stage_results: Path, next_stage_inputs: Path, stage_number: int):
    # Load the pipe options database

    filename = 'pipe_options-dynamic_properties.xlsx'


    input_path = previous_stage_results / 'pipes' / filename
    pipe_options_db = PipeOptionsDB.load_from_file(input_path)
    emission_df = pipe_options_db[PipeOptionsDB.EMISSION]

    (emission_df,) = append_data(
        emission_df=emission_df,
        stage_idx=stage_number-1
    )
    
    # Assign back and save
    pipe_options_db[PipeOptionsDB.EMISSION] = emission_df
    pipe_options_dps = DynamicProperties(
        name=f'pipe_options-dynamic_properties-stage_{stage_number}',
        dataframes=pipe_options_db.dataframes
    )
    pipe_options_dps.dump(path=next_stage_inputs / 'pipes')

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
