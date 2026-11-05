import os
from pathlib import Path
import numpy as np
RNG = np.random.default_rng(seed=12850)
import pandas as pd
from water_futures_battle.core.base_model import DynamicProperties
from water_futures_battle.climate.dynamic_properties import ClimateDB

STAGE_LENGTH_Y = 25 # YEARS
STAGE_PREV_TIMES = [
    [f"{year}-12-01", f"{year}-03-01", f"{year}-06-01", f"{year}-09-01"]
    for year in [2024, 2049, 2074]
]
STAGE_SCENARIO_TIMES = [
    [f"{year-1}-12-01", f"{year}-03-01", f"{year}-06-01", f"{year}-09-01"]
    for year in [2050, 2100, 2100]
]
STAGE_SCENARIOS = ['Hn', 'Hd', 'Hd']
STAGE_SEEDS = RNG.spawn(n_children=3)
STAGE_CLIM_VAR = [1.0, 1.2, 1.3]

def generate_noise(
        rng: np.random.Generator,
        method: str,
        target_mean: float,
        target_std: float,
        reverse: bool
    ) -> np.ndarray:

    if method == "normal":
        return rng.normal(loc=target_mean, scale=target_std, size=STAGE_LENGTH_Y)
    
    if method == "gumbel":
        # Derive native Gumbel parameters from target mean and std
        # std(Gumbel)  = π * scale / √6  →  scale = target_std * √6 / π
        # mean(Gumbel) = loc + scale * γ  →  loc   = target_mean - scale * γ
        euler_gamma = 0.57721566
        scale = target_std * (np.sqrt(6) / np.pi)
        loc   = target_mean - scale * euler_gamma
        noise = rng.gumbel(loc=loc, scale=scale, size=STAGE_LENGTH_Y)

        # Reverse flips the tail: reflects around target_mean
        # skewed-high (heatwaves) becomes skewed-low (cold snaps)
        if reverse:
            noise = 2 * target_mean - noise

        return noise
        
    if method == "gamma":
        # shape=2: raw_gamma has mean=1, std=1/√2
        # scale raw deviations so output has target_std
        # std(noise) = param/√2 = target_std  →  param = target_std * √2
        shape = 2.0
        raw_gamma = rng.gamma(shape=shape, scale=1.0 / shape, size=STAGE_LENGTH_Y)
        noise = target_mean + (raw_gamma - 1) * (target_std * np.sqrt(2))

        return noise

    raise ValueError("unknown method")

def compute_spei_seasonal(precip: pd.Series, temp: pd.Series) -> pd.Series:
    """
    Simplified SPEI calculation for each season using only a modulated temperature
    and the observed precipitation. Computed with respect to the historical values
    and a simple meand and std method.
    The goal is to have somethning that looks realistic.
    """
    pet = temp.clip(lower=0) * 0.17 # we use this to convert between ET and precipitation at the seasonal level
    D = precip - pet

    # Compute mean/std only from the historical period
    D_hist = D[D.index <= pd.to_datetime("2025-01-01")]

    spei = pd.Series(index=D.index, dtype=float)
    for month in D.index.month.unique():
        mask = D.index.month == month
        hist_mask = D_hist.index.month == month
        
        mu  = D_hist[hist_mask].mean()
        sig = D_hist[hist_mask].std()
        
        spei[mask] = (D[mask] - mu) / sig

    return spei.clip(-3, 3)

def append_climate_data(
        df: pd.DataFrame,
        last_obs_times: list[str],
        scenario_times: list[str],
        scenario: str,
        variability_factor: float,
        rng: np.random.Generator,
        method: str,
        reverse: bool,
        is_additive: bool
    ) -> pd.DataFrame:

    dest_point_rel = rng.uniform(0, 1)

    for start_time, scenario_time in zip(
        [pd.to_datetime(t) for t in last_obs_times],
        [pd.to_datetime(t) for t in scenario_times],
    ):

        # Extract what the senario predicts
        low_pt = float(df.loc[scenario_time, "NL0000-"+scenario+"-min"])
        high_pt = float(df.loc[scenario_time, "NL0000-"+scenario+"-max"])
        
        # Create the trend
        start_point = float(df.loc[start_time, "NL0000"])
        dest_point = low_pt + (high_pt - low_pt) * dest_point_rel

        trend = np.linspace(
            start=start_point,
            stop=dest_point,
            num=scenario_time.year-start_time.year
        )

        # And add the noise with the std dev suggest by the scenario, increase
        # by our variability
        scenario_sigma = (high_pt - low_pt) / (2 * 1.645)
        noise = generate_noise(
            rng=rng,
            method=method,
            target_mean=0.0 if is_additive else 1.0,
            target_std=scenario_sigma * variability_factor if is_additive 
               else (scenario_sigma / dest_point) * variability_factor,  # dimensionless
            reverse=reverse
        )

        if is_additive:
            values = trend[:STAGE_LENGTH_Y] + noise
        else:
            values = trend[:STAGE_LENGTH_Y] * noise

        target_dates = [
            pd.Timestamp(year=start_time.year + i + 1,
                        month=start_time.month,
                        day=start_time.day)
            for i in range(STAGE_LENGTH_Y)
        ]

        df = df.reindex(df.index.union(target_dates))
        df.loc[target_dates, 'NL0000'] = values

    return df.sort_index()

def append_data (
        temp_averg_df: pd.DataFrame,
        temp_min_averg_df: pd.DataFrame,
        temp_max_averg_df: pd.DataFrame,
        temp_warmest_df: pd.DataFrame,
        temp_coldest_df: pd.DataFrame,
        precipitation_df: pd.DataFrame,
        solar_radiation_df: pd.DataFrame,
        SPEI_df: pd.DataFrame,
        stage_idx: int
    )-> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    
# --- TEMPERATURES (is_additive=True) ---
    # Centered Normal - standard annual variance
    temp_averg_df = append_climate_data(
        df=temp_averg_df,
        last_obs_times=STAGE_PREV_TIMES[stage_idx],
        scenario_times=STAGE_SCENARIO_TIMES[stage_idx],
        scenario=STAGE_SCENARIOS[stage_idx],
        variability_factor=STAGE_CLIM_VAR[stage_idx],
        rng=STAGE_SEEDS[stage_idx],
        method="normal",
        reverse=False,
        is_additive=True
    )

    # Gumbel Reversed - focuses on cold spikes (Min Avg)
    temp_min_averg_df = append_climate_data(
        df=temp_min_averg_df,
        last_obs_times=STAGE_PREV_TIMES[stage_idx],
        scenario_times=STAGE_SCENARIO_TIMES[stage_idx],
        scenario=STAGE_SCENARIOS[stage_idx],
        variability_factor=STAGE_CLIM_VAR[stage_idx],
        rng=STAGE_SEEDS[stage_idx],
        method="gumbel",
        reverse=False,
        is_additive=True
    )

    # Gumbel Standard - focuses on heat spikes (Max Avg)
    temp_max_averg_df = append_climate_data(
        df=temp_max_averg_df,
        last_obs_times=STAGE_PREV_TIMES[stage_idx],
        scenario_times=STAGE_SCENARIO_TIMES[stage_idx],
        scenario=STAGE_SCENARIOS[stage_idx],
        variability_factor=STAGE_CLIM_VAR[stage_idx],
        rng=STAGE_SEEDS[stage_idx],
        method="gumbel",
        reverse=False,
        is_additive=True
    )

    # Gumbel Standard - extreme heatwaves
    temp_warmest_df = append_climate_data(
        df=temp_warmest_df,
        last_obs_times=STAGE_PREV_TIMES[stage_idx],
        scenario_times=STAGE_SCENARIO_TIMES[stage_idx],
        scenario=STAGE_SCENARIOS[stage_idx],
        variability_factor=STAGE_CLIM_VAR[stage_idx],
        rng=STAGE_SEEDS[stage_idx],
        method="gumbel",
        reverse=False,
        is_additive=True
    )

    # Gumbel Reversed - extreme deep freezes
    temp_coldest_df = append_climate_data(
        df=temp_coldest_df,
        last_obs_times=STAGE_PREV_TIMES[stage_idx],
        scenario_times=STAGE_SCENARIO_TIMES[stage_idx],
        scenario=STAGE_SCENARIOS[stage_idx],
        variability_factor=STAGE_CLIM_VAR[stage_idx],
        rng=STAGE_SEEDS[stage_idx],
        method="gumbel",
        reverse=True,
        is_additive=True
    )

    # --- VOLUMETRIC (is_additive=False) ---
    # Gamma - High variance for rainfall (vol=1.0 will create very dry vs very wet years)
    precipitation_df = append_climate_data(
        df=precipitation_df,
        last_obs_times=STAGE_PREV_TIMES[stage_idx],
        scenario_times=STAGE_SCENARIO_TIMES[stage_idx],
        scenario=STAGE_SCENARIOS[stage_idx],
        variability_factor=STAGE_CLIM_VAR[stage_idx],
        rng=STAGE_SEEDS[stage_idx],
        method="gamma",
        reverse=False,
        is_additive=False
    )
    precipitation_df['NL0000'] = precipitation_df['NL0000'].clip(lower=0)    

    # Normal - High variance for solar (Note: may need clipping to prevent >100% sunshine)
    solar_radiation_df = append_climate_data(
        df=solar_radiation_df,
        last_obs_times=STAGE_PREV_TIMES[stage_idx],
        scenario_times=STAGE_SCENARIO_TIMES[stage_idx],
        scenario=STAGE_SCENARIOS[stage_idx],
        variability_factor=STAGE_CLIM_VAR[stage_idx],
        rng=STAGE_SEEDS[stage_idx],
        method="normal",
        reverse=False,
        is_additive=True
    )

    SPEI_df = compute_spei_seasonal(
        precip=precipitation_df["NL0000"],
        temp=temp_averg_df["NL0000"]
    ).to_frame(name="NL0000")
    
    return (temp_averg_df, temp_min_averg_df, temp_max_averg_df, temp_warmest_df, temp_coldest_df, precipitation_df, solar_radiation_df, SPEI_df)

def main(previous_stage_results: Path, next_stage_inputs: Path, stage_number: int):
    
    filename = "climate-dynamic_properties.xlsx"

    input_path =  previous_stage_results / 'climate' / filename

    climate_db = ClimateDB.load_from_file(input_path)

    temp_averg_df = climate_db[ClimateDB.TEMPERATURE_AVG]
    temp_min_averg_df = climate_db[ClimateDB.TEMPERATURE_MIN_AVG]
    temp_max_averg_df = climate_db[ClimateDB.TEMPERATURE_MAX_AVG]
    temp_warmest_df = climate_db[ClimateDB.TEMPERATURE_WARMDAY]
    temp_coldest_df = climate_db[ClimateDB.TEMPERATURE_COLDDAY]
    precipitation_df = climate_db[ClimateDB.PRECIPITATION]
    solar_radiation_df = climate_db[ClimateDB.SOLARRAD]
    SPEI_df = climate_db[ClimateDB.SPEI]

    (
        temp_averg_df,
        temp_min_averg_df,
        temp_max_averg_df,
        temp_warmest_df,
        temp_coldest_df,
        precipitation_df,
        solar_radiation_df,
        SPEI_df
    ) = append_data (
        temp_averg_df,
        temp_min_averg_df,
        temp_max_averg_df,
        temp_warmest_df,
        temp_coldest_df,
        precipitation_df,
        solar_radiation_df,
        SPEI_df,
        stage_number-1
    )
    
    
    climate_db[ClimateDB.TEMPERATURE_AVG] = temp_averg_df
    climate_db[ClimateDB.TEMPERATURE_MIN_AVG] = temp_min_averg_df
    climate_db[ClimateDB.TEMPERATURE_MAX_AVG] = temp_max_averg_df
    climate_db[ClimateDB.TEMPERATURE_WARMDAY] = temp_warmest_df
    climate_db[ClimateDB.TEMPERATURE_COLDDAY] = temp_coldest_df
    climate_db[ClimateDB.PRECIPITATION] = precipitation_df
    climate_db[ClimateDB.SOLARRAD] = solar_radiation_df
    climate_db[ClimateDB.SPEI] = SPEI_df

    climate_options_dps = DynamicProperties(
        name =f'climate-dynamic_properties-stage_{stage_number}',
        dataframes=climate_db.dataframes
    )

    climate_options_dps.dump(path = next_stage_inputs / 'climate')


if __name__ == "__main__":
    # This script is intended to be run for each team to append exogenous dynamic properties
    # to the system's final status from the previous stage, producing new input files for the next stage.

    # Parse arguments: previous stage results directory and next stage input directory.
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate climate time series for a stage and append it to the previous stage's file."
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
