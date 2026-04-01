import os
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

import numpy as np
import pandas as pd

from ..core import Settings
from ..core.base_model import StaticProperties
from ..sources.entities import SourcesContainer, WaterSource
from ..pumps.dynamic_properties import PumpOptionsDB, PumpsResults
from ..pumps.entities import Pump, PumpOption

from .entities import PumpingStation

def build_pumping_infrastructure(
        desc: Dict[str, str],
        sources: SourcesContainer,
        data_path: str,
        settings: Settings
        ) -> Tuple[Set[PumpOption], Set[PumpingStation]]:
    """
    Build all the pumping stations and the elements they rely on (pumps and pump options)
    
    :param desc: Description
    :type desc: dict[str, str]
    :param sources: Description
    :type sources: dict[str, WaterSource]
    :return: Description
    :rtype: Any
    """

    # Pumping stations depends on Pump, which depend on Pump Options, so let's start from the latter

    # PUMP OPTIONS
    # open the dynamic properties, set the DB to be accessible from all the instances
    # then create the instances
    pump_options_db = PumpOptionsDB.load_from_file(os.path.join(data_path, desc[PumpOptionsDB.NAME]))
    PumpOption.set_dynamic_properties(pump_options_db)

    pump_options_data = pd.read_excel(os.path.join(data_path, desc['pump_options-static_properties']),
                                      sheet_name=None)
    
    pump_options_map: Dict[str, PumpOption] = {}
    for idx, option in pump_options_data['options'].iterrows():
        pump_option = PumpOption.from_row(
            row_data=option,
            other_data=pump_options_data
        )

        pump_options_map[pump_option.bwf_id] = pump_option
    
    # Once we created the database of pump options we can start building the Pumps and Pumping Stations
    pumps_results = PumpsResults()
    Pump.set_results(pumps_results)

    pumping_stations_data = pd.read_excel(
        os.path.join(data_path, desc['pumping_stations-static_properties']),
        sheet_name='entities'
    )

    pumping_stations: Set[PumpingStation] = set()
    for idx, ps_data in pumping_stations_data.iterrows():
        pumping_stations.add(
            PumpingStation.from_row(
                row_data=ps_data,
                pump_options_map=pump_options_map,
                sources=sources,
                settings=settings
            )
        )

    pump_options = set(pump_options_map.values())

    return pump_options, pumping_stations

def dump_pumping_infrastructure(
        all_pumping_stations: Set[PumpingStation],
        pump_options: Set[PumpOption],
        output_dir: Path
    )-> Dict[str, Any]:

    full_out_dir_ps = output_dir / "pumping_stations"
    full_out_dir_pump = output_dir / "pumps"
    def as_rel_path(a_path: Path) -> str:
        return os.path.relpath(a_path, output_dir)

    entities_df = pd.DataFrame(data=[
        r.to_dict()
        for r in all_pumping_stations
    ]).sort_values(PumpingStation.ID)

    pumping_stations_properties = StaticProperties(
        name="pumping_stations-static_properties",
        dataframes={'entities': entities_df}
    )

    options_df = pd.DataFrame(data=[
        p.to_dict()
        for p in pump_options
    ]).sort_values(PumpOption.ID)
    
    pump_options_dfs = {
        'options': options_df
    }
    for p in sorted(pump_options, key= lambda p: p.bwf_id):
        pump_options_dfs[p.bwf_id] = p.get_curves().reset_index().iloc[1:, :] # drop the first row that we artificially added in the init

    pump_option_properties = StaticProperties(
        name="pump_options-static_properties",
        dataframes=pump_options_dfs
    )

    sp_path_ps = pumping_stations_properties.dump(full_out_dir_ps)
    sp_path_po = pump_option_properties.dump(full_out_dir_pump)
    dp_path = PumpOption._dynamic_properties.dump(full_out_dir_pump)

    return {
        pumping_stations_properties.name: as_rel_path(sp_path_ps),
        pump_option_properties.name: as_rel_path(sp_path_po),
        PumpOptionsDB.NAME: as_rel_path(dp_path)
    }

class NoValidPumpConfigurationError(Exception):
    pass

def fit_pump_speed(
    head: float,
    flow: float,
    pump_curve_coeffs: Tuple[float, float, float]
) -> float:
    """
    Solves A·α² + B·Q·α + (C·Q² - H) = 0 for speed ratio α.
    
    pump_curve_coeffs: (A, B, C) from quadratic fit to H-Q curve
                       H_nominal = A + B·Q + C·Q²
    """
    A, B, C = pump_curve_coeffs
    Q = flow
    H = head

    # quadratic coefficients in α
    a_q = A
    b_q = B * Q
    c_q = C * Q**2 - H

    discriminant = b_q**2 - 4 * a_q * c_q

    if discriminant < 0:
        raise NoValidPumpConfigurationError(
            f"No real speed solution exists for Q={Q}, H={H} — "
            "operating point may be outside the pump's capability"
        )

    sqrt_disc = np.sqrt(discriminant)

    # two candidate roots
    alpha1 = (-b_q + sqrt_disc) / (2 * a_q)
    alpha2 = (-b_q - sqrt_disc) / (2 * a_q)

    # pick the physically meaningful one: positive, prefer the larger
    # (smaller root often corresponds to an unstable operating point)
    candidates = [a for a in (alpha1, alpha2) if a > 0]

    if not candidates:
        raise NoValidPumpConfigurationError(
            f"No positive speed ratio solution for Q={Q}, H={H}"
        )

    return min(candidates, key=lambda a: abs(a - 1.0))

def get_lowest_energy_pumping_station_setup(
    target_head: float,
    target_flow: float,
    n_available_pumps: int,
    pump_option: PumpOption,
    speed_ratio_bounds: Tuple[float, float],
    pump_curve_coeffs: Optional[Tuple[float, float, float]] = None
) -> Tuple[int, float, float, float]:
    """
    Given some info on the ps returns best n of pumps running, speed, energy 
    consumption, and efficiency of a single pump.
    """
    
    if target_flow < -10.0:
        # We check for <1.0 because sometimes EPANET return tiny negative flows
        raise ValueError("Negative flow should not happen for a pumping station")
    
    if target_flow < 10.0:
        # pumping station is off
        return 0, 0.0, 0.0, 0.0
    
    if pump_curve_coeffs is None:
        pump_curve_coeffs = pump_option.pump_curve_coeffs

    speeds = np.full(
        shape=(n_available_pumps,),
        fill_value=np.nan
    )
    efficiencies = np.full(
        shape=(n_available_pumps,),
        fill_value=np.nan
    )
    single_pump_energies = np.full(
        shape=(n_available_pumps,),
        fill_value=np.nan
    )
    pumping_station_energies = np.full(
        shape=(n_available_pumps,),
        fill_value=np.nan
    )

    for n_pumps in range(1, n_available_pumps+1):

        try:
            speed = fit_pump_speed(
                head=target_head,
                flow=target_flow/n_pumps,
                pump_curve_coeffs=pump_curve_coeffs
            )
        except NoValidPumpConfigurationError:
            # Could not find a solution, we set to inf as 
            speeds[n_pumps-1] = np.inf  # it will be filtered by bounds check
            continue

        speeds[n_pumps-1] = speed

        efficiency = pump_option.efficiency_at_flow_and_speedr(
            flow=target_flow/n_pumps,
            speed_ratio=speed
        )
        efficiencies[n_pumps-1] = efficiency

        energy = pump_option.break_power_at_flow_and_speedr(
            flow=target_flow/n_pumps,
            speed_ratio=speed
        ) # it is ok because our unit is kW and energy in kWh
        single_pump_energies[n_pumps-1] = energy
        pumping_station_energies[n_pumps-1] = energy * n_pumps

    # now I can select the best combo

    # filter by speed bounds
    lo, hi = speed_ratio_bounds
    valid_mask = (speeds >= lo) & (speeds <= hi) & np.isfinite(single_pump_energies)

    if not np.any(valid_mask):
        raise NoValidPumpConfigurationError(
            f"No valid configuration found for target_flow={target_flow}, "
            f"target_head={target_head} within speed bounds {speed_ratio_bounds}"
            f"and {n_available_pumps} pumps of type pump_option={pump_option.bwf_id}."
        )

    # best = lowest total energy among valid configs
    valid_indices = np.where(valid_mask)[0]
    best_idx = int(valid_indices[np.argmin(pumping_station_energies[valid_indices])])

    best_n      = best_idx + 1
    best_speed  = float(speeds[best_idx])
    best_energy = float(single_pump_energies[best_idx])
    best_eff    = float(efficiencies[best_idx])

    return best_n, best_speed, best_energy, best_eff
