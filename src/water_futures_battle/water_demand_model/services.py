import os
from typing import Any, Dict, Tuple
from pathlib import Path

import numpy as np
import pandas as pd

from ..core import Settings
from ..core.base_model import StaticProperties

from .properties import WaterDemandModelDB
from .entities import WaterDemandModelPattern, WaterDemandModelPatterns, WaterDemandModelData

def configure_water_demand_model(
        config: dict,
        data_path: str,
        settings: Settings
    ) -> WaterDemandModelData:
    """
    Use the config dicitonary to setup all the variables that the water demand model
    relies on and are not in the municipality domain

    :param config: configuration dictionary
    :type config: dict
    :return: Tuple with static and dynamic properties for the water demand model
    :rtype: tuple[Any, Any]
    """
    wdm_sheets = pd.read_excel(
        os.path.join(data_path, config['water_demand_model-static_properties']),
        sheet_name=None
    )

    patterns: WaterDemandModelPatterns = {}
    for ptype in ['residential', 'business']:
        for idx, row in wdm_sheets[ptype].iterrows():
            p_id = row[WaterDemandModelPattern.ID]

            patterns[p_id] = WaterDemandModelPattern(
                bwf_id=p_id,
                category=ptype,
                values=row[WaterDemandModelPattern.VALUES].to_numpy()
            )

    # Get the deynamic properties, e.g., per capita demand
    wdm_dps = WaterDemandModelDB.load_from_file(os.path.join(data_path, Path(config[WaterDemandModelDB.NAME])))

    return (patterns, wdm_dps)

N_HARMONICS = 3
REFERENCE_T_MAX = 20.6
T_MAX_RATIO_EXPONENT = 5
HARMONIC_VAR_MIN, HARMONICS_VAR_MAX = 0.5, 1.5
DAY_VAR_MIN, DAY_VAR_MAX = 0.95, 1.05
HOUR_VAR_MIN, HOUR_VAR_MAX = 0.95, 1.05

def modulate_house_pattern(
        pattern: np.ndarray,
        max_yearly_temp: float,
        RNG: np.random.Generator
        ) -> np.ndarray:
    """
    Modulate a base house water demand pattern with temperature and random harmonics.

    Args:
        pattern: Flattened array of hourly demand for a year (24*365).
        max_yearly_temp: Maximum yearly temperature for modulation.

    Returns:
        Flattened array of modulated hourly demand for 1 year.
    """
    HOURS_PER_DAY = 24
    DAYS_PER_YEAR = 365

    # Reshape and normalize pattern
    hourly_matrix = pattern.reshape((HOURS_PER_DAY, DAYS_PER_YEAR))
    daily_mean = np.mean(hourly_matrix, axis=0)
    hourly_adim = hourly_matrix / daily_mean

    # Generate synthetic daily mean profiles using harmonics
    days = np.arange(1, DAYS_PER_YEAR + 1)
    base = np.mean(daily_mean)
    a_coeffs = []
    b_coeffs = []
    for k in range(1, N_HARMONICS+1):
        a = (2 / DAYS_PER_YEAR) * np.sum(daily_mean * np.cos(k * 2 * np.pi * days / DAYS_PER_YEAR))
        b = (2 / DAYS_PER_YEAR) * np.sum(daily_mean * np.sin(k * 2 * np.pi * days / DAYS_PER_YEAR))
        a_coeffs.append(a)
        b_coeffs.append(b)
    a_coeffs = np.array(a_coeffs)
    b_coeffs = np.array(b_coeffs)


    # Modulate harmonics with random scaling
    
    synthetic_profiles = np.zeros((1, DAYS_PER_YEAR))
    a_rand = a_coeffs * (HARMONIC_VAR_MIN + (HARMONICS_VAR_MAX - HARMONIC_VAR_MIN) * RNG.random(N_HARMONICS))
    b_rand = b_coeffs * (HARMONIC_VAR_MIN + (HARMONICS_VAR_MAX - HARMONIC_VAR_MIN) * RNG.random(N_HARMONICS))
    profile = np.ones(DAYS_PER_YEAR) * base
    for k in range(N_HARMONICS):
        profile += a_rand[k] * np.cos((k + 1) * 2 * np.pi * days / DAYS_PER_YEAR)
        profile += b_rand[k] * np.sin((k + 1) * 2 * np.pi * days / DAYS_PER_YEAR)
    synthetic_profiles[0, :] = profile

    # Apply temperature exponent
    temp_exp = (max_yearly_temp/REFERENCE_T_MAX)**T_MAX_RATIO_EXPONENT
    synthetic_profiles = synthetic_profiles ** temp_exp

    # Apply random daily scaling
    synthetic_profiles *= DAY_VAR_MIN + (DAY_VAR_MAX - DAY_VAR_MIN) * RNG.random((1, DAYS_PER_YEAR))

    # Apply random hourly scaling and reconstruct full pattern
    modulated_pattern = np.zeros((HOURS_PER_DAY * DAYS_PER_YEAR, 1))
    
    hourly_scaling = HOUR_VAR_MIN + (HOUR_VAR_MAX - HOUR_VAR_MIN) * RNG.random((HOURS_PER_DAY, DAYS_PER_YEAR))
    modulated_hourly = hourly_adim * hourly_scaling * synthetic_profiles[0, :]
    modulated_pattern[:, 0] = modulated_hourly.flatten()

    return modulated_pattern.flatten()

def modulate_business_pattern(
        pattern: np.ndarray,
        RNG: np.random.Generator
        ) -> np.ndarray:
    return modulate_house_pattern(
        pattern=pattern,
        max_yearly_temp=REFERENCE_T_MAX,
        RNG=RNG
    )

def dump_water_demand_model(
        wdpatterns: WaterDemandModelPatterns,
        wdm_db: WaterDemandModelDB,
        output_dir: Path
    )-> Dict[str, Any]:

    full_out_dir = output_dir / "water_demand_model"
    def as_rel_path(a_path: Path) -> str:
        return os.path.relpath(a_path, output_dir)


    residential_df = pd.DataFrame(
        data=[r.to_dict() for r in wdpatterns.values() if r.category == 'residential']
    )

    business_df = pd.DataFrame(
        data=[b.to_dict() for b in wdpatterns.values() if b.category == 'business']
    )

    dfs = {
        'residential': residential_df,
        'business': business_df
    }

    sproperties = StaticProperties(
        name="water_demand_model-static_properties",
        dataframes=dfs
    )

    sp_path = sproperties.dump(full_out_dir)
    dp_path = wdm_db.dump(full_out_dir)

    return {
        sproperties.name: as_rel_path(sp_path),
        wdm_db.NAME: as_rel_path(dp_path)
    }
