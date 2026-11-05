import os
from pathlib import Path
import numpy as np
import pandas as pd
from water_futures_battle.core.base_model import DynamicProperties
from water_futures_battle.sources.properties import SurfaceWaterDB, GroundWaterDB
from water_futures_battle.climate.dynamic_properties import ClimateDB

RNG = np.random.default_rng(seed=12890)

STAGE_SEEDS = RNG.spawn(n_children=3)
STAGE_YEARS = [
    ("2025-01-01", "2049-01-01"),
    ("2050-01-01", "2074-01-01"),
    ("2075-01-01", "2099-01-01"),
]

def append_availability_data(
        avail_df: pd.DataFrame,
        spei_df: pd.DataFrame,
        stage_idx: int
    )-> pd.DataFrame:
    
    rng = STAGE_SEEDS[stage_idx]

    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")

    for year in YEARS:
        spei_spring = float(spei_df.loc[year + pd.DateOffset(months=2), "NL0000"]) # March
        spei_summer = float(spei_df.loc[year + pd.DateOffset(months=5), "NL0000"]) # June

        # ── No restriction if spring is not dry enough ───────────────────
        if spei_spring >= -1.0:
            continue

        # restrictions are on
        for basin in ['Rhine', 'Meuse']:
            
            # ── AF magnitude (linear -1 → 1.0, -2 → 0.0) ───────────────────
            noise = rng.uniform(-0.2, 0.2)
            af_spring = float(np.clip(2.0 + spei_spring + noise, 0.0, 1.0))

            # ── Start date: random within spring ────────────────────────────
            t_start = rng.choice(pd.date_range(
                f'{year.year}-03-01', f'{year.year}-05-31'
            ))

            # ── End date and final AF: depend on summer SPEI ─────────────────
            if spei_summer >= -1.0:
                # Recovery: ends early summer
                n_days = rng.integers(15, 90)
            else:
                # Drought persists: ends late summer / early autumn
                n_days = rng.integers(90, 110)

            t_end = t_start + pd.DateOffset(days=n_days)

            avail_df.loc[t_start, basin] = af_spring
            avail_df.loc[t_end,   basin] = 1.0

    return avail_df.sort_index().ffill()

def append_sw_data(
        avail_df: pd.DataFrame,
        spei_df: pd.DataFrame,
        stage_idx: int
    )-> tuple[pd.DataFrame]:

    avail_df = append_availability_data(avail_df, spei_df, stage_idx)

    return (avail_df,)

def append_fine_data(
        fine_df: pd.DataFrame,
        stage_idx: int
    )-> pd.DataFrame:

    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")

    if pd.to_datetime("2030-01-01") in YEARS:
        fine_df.loc[pd.to_datetime("2030-01-01")] = [1e6, 25e6, 2e8]

    if pd.to_datetime("2060-01-01") in YEARS:
        fine_df.loc[pd.to_datetime("2060-01-01")] = [1.5e6, 30e6, 2e8]

    if pd.to_datetime("2081-01-01") in YEARS:
        fine_df.loc[pd.to_datetime("2081-01-01")] = [2e6, 40e6, 2e8]

    return fine_df

def append_gw_data(
        fine_df: pd.DataFrame,
        stage_idx: int
) -> tuple[pd.DataFrame]:
    
    fine_df = append_fine_data(fine_df, stage_idx)

    return (fine_df,)


def main(previous_stage_results: Path, next_stage_inputs: Path, stage_number: int):
    
    filename = 'surface_water-dynamic_properties.xlsx'

    input_path =  previous_stage_results / 'sources' / filename
    
    swsources_db = SurfaceWaterDB.load_from_file(input_path)
    avail_df = swsources_db[SurfaceWaterDB.AVAILABILITY_FACTOR]

    # Availability factor of surface water sources depends on climate
    climate_inputpath = next_stage_inputs / 'climate' / f'climate-dynamic_properties-stage_{stage_number}.xlsx'
    climate_db = ClimateDB.load_from_file(climate_inputpath)
    spei_df = climate_db[ClimateDB.SPEI]

    (avail_df,) = append_sw_data(
        avail_df,
        spei_df,
        stage_number-1
    )

    swsources_db[SurfaceWaterDB.AVAILABILITY_FACTOR] = avail_df
    #assign back and save 
    swsources_dps = DynamicProperties(
        name =f"surface_water-dynamic_properties-stage_{stage_number}",
        dataframes= swsources_db
    )

    swsources_dps.dump(path = next_stage_inputs / "sources")

    # Groundwater
    filename = 'groundwater-dynamic_properties.xlsx'
    input_path =  previous_stage_results / 'sources' / filename
    
    gwsources_db = GroundWaterDB.load_from_file(input_path)
    fines_df = gwsources_db[GroundWaterDB.FINE_AMOUNT]

    (fines_df,) = append_gw_data(
        fines_df,
        stage_number-1
    )

    gwsources_db[GroundWaterDB.FINE_AMOUNT] = fines_df
    #assign back and save 
    gwsources_dps = DynamicProperties(
        name =f"groundwater-dynamic_properties-stage_{stage_number}",
        dataframes= gwsources_db
    )

    gwsources_dps.dump(path = next_stage_inputs / "sources")

    # Desalination is unchanged

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
