import os 
from pathlib import Path

import pandas as pd
import yaml

FILE_EXTENSION_MAP = {
    "climate/climate-dynamic_properties.xlsx": [],
    "economy/economy-dynamic_properties.xlsx": [],
    "energy/energy_system-dynamic_properties.xlsx": ['electricity_price-unit_cost', 'electricity_price-pattern'],
    "jurisdictions/municipalities-dynamic_properties.xlsx": ['dist_network-age-avg'],
}

def repeat_last_year(
        df: pd.DataFrame,
        REF_YEAR: int,
        N_YEARS: int
    ) -> pd.DataFrame:

    MASK = df.index.year == REF_YEAR
    base = df[MASK]

    # Repeat the base DataFrame N_YEARS times, updating the index for each year
    frames = [
        base.set_index(base.index + pd.DateOffset(years=y+1))
        for y in range(N_YEARS)
    ]
    extended = pd.concat(frames)

    result = pd.concat([df, extended])
    result = result[~result.index.duplicated(keep='last')]
    result = result.sort_index()
    return result

def main(
        folder: Path
    ) -> None:
    
    # config file stays as is, but let's use to get which years we need to extend
    configuration_filename = folder / "configuration.yaml"

    if not os.path.exists(configuration_filename) or not os.path.isfile(configuration_filename):
        raise ValueError("Configuration file not found")
    
    with open(configuration_filename, 'r') as f_yaml:
        config = yaml.safe_load(f_yaml)
    
    YEARS = list(range(config['settings']['start_year'], config['settings']['end_year']+1))
    LAST_YEAR = YEARS[0]-1

    for filename, sheets_to_skip in FILE_EXTENSION_MAP.items():
        
        # open, extend all dictionaries, save

        dfs = pd.read_excel(
            folder / filename,
            sheet_name=None,
            index_col='timestamp',
            parse_dates=True
        )

        for sheet, df in dfs.items():

            if sheet in sheets_to_skip:
                continue

            dfs[sheet] = repeat_last_year(
                df=df,
                REF_YEAR=LAST_YEAR,
                N_YEARS=len(YEARS)
            )

        with pd.ExcelWriter(folder/filename) as writer:
            for sheet, df in dfs.items():
                
                df.index = df.index.strftime('%Y-%m-%d')

                df.to_excel(writer, sheet_name=sheet, index=True)

    print(
        "Extended the folder with exogenous dynamic properties required by the BWF evaluator.",
        "You can overwrite them manually or with your preferred tool.",
        "",
        "The following dynamic exogenous variables can also be changed to modify the scenario:",
        "  - Energy system: electricity price (unit cost and pattern)",
        "  - Surface water sources: availability factor",
        "  - Groundwater sources: permit violation fine",
        "  - Pipe options: emission factor",
        "  - Water demand model: per household and per business demand",
    )

    return
        
if __name__ == "__main__":
    # This script is intended to modify a results file as a basic input file
    # for the new stage and team.

    # DISCLAIMER: This function will override files in the specified directory.
    # Did you create a backup? Are you sure you want to continue?
    proceed = input("WARNING: This script will overwrite files in the specified directory. Did you create a backup? Are you sure you want to continue? (yes/[no]): ").strip().lower()
    if proceed != "yes":
        print("Operation cancelled by user.")
        exit(1)

    import argparse
    parser = argparse.ArgumentParser(
        description="Update a BWF results directory to be able to handle a test for the next stage."
    )
    parser.add_argument(
        "results_dir",
        type=Path,
        help="Path to the BWF results folder to update"
    )
    
    args = parser.parse_args()

    next_stage_inputs = args.results_dir
    if not next_stage_inputs.is_absolute():
        next_stage_inputs = Path(os.getcwd()) / next_stage_inputs

    main(next_stage_inputs)