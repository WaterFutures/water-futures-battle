import os
from pathlib import Path
from typing import Any, Dict, Set, Tuple

import numpy as np
import pandas as pd
import pvlib

from ..core import Settings
from ..core.base_model import StaticProperties
from ..core.utility import timestampify
from ..jurisdictions.entities import State
from ..sources.entities import SourcesContainer
from ..pumping_stations.entities import PumpingStation

from .dynamic_properties import EnergySysDB, SolarFarmsResults
from .entities import SolarFarm, ElectricityPricePattern

def configure_energy_system(
        config: dict,
        sources: SourcesContainer,
        pumping_stations: Set[PumpingStation],
        data_path: str,
        settings: Settings
    ) -> Tuple[EnergySysDB, Set[SolarFarm]]:
    
    energysys_db = EnergySysDB.load_from_file(os.path.join(data_path, config[EnergySysDB.NAME]))

    solar_farms_res = SolarFarmsResults() 

    SolarFarm.set_dynamic_properties(energysys_db)
    SolarFarm.set_results(solar_farms_res)

    solar_farms_descriptions = pd.read_excel(
        Path(data_path) / config['solar_farms-static_properties'],
        sheet_name='entities'
    )
    
    solar_farms: Set[SolarFarm] = set()
    for _, solar_farm_data in solar_farms_descriptions.iterrows():

        solar_farms.add(
            SolarFarm.from_row(
                row_data=solar_farm_data,
                sources=sources,
                pumping_stations=pumping_stations
            
            )
        )

    return energysys_db, solar_farms

def dump_energy_system(
        energy_db: EnergySysDB,
        all_solar_farms: Set[SolarFarm],
        output_dir: Path
    ) -> Dict[str, Any]:

    full_out_dir = output_dir / "energy"
    def as_rel_path(a_path: Path) -> str:
        return os.path.relpath(a_path, output_dir)
    
    if len(all_solar_farms) > 0:
        entities_df = pd.DataFrame(
            data=[sf.to_dict() for sf in sorted(all_solar_farms, key= lambda x: x.bwf_id)]
        )
    else:
        entities_df = pd.DataFrame(columns=SolarFarm.file_columns())

    dfs  = {
        'entities': entities_df
    }

    sproperties = StaticProperties(
        name="solar_farms-static_properties",
        dataframes=dfs
    )
    
    sp_path = sproperties.dump(full_out_dir)
    dp_path = energy_db.dump(full_out_dir)

    return {
        sproperties.name: as_rel_path(sp_path),
        energy_db.NAME: as_rel_path(dp_path)
    }

SOLAR_PANEL_NL_OPTIMAL_TILT = 35.0
SOLAR_PANEL_NL_AZIMUTH_ANGLE = 180.0

def get_solar_radiation_of_year(
        year: int,
        state: State,
        observed_avg_solar_radiation: pd.Series,
        settings: Settings
    ) -> np.ndarray:

    times = pd.date_range(
        start=f'{year}-01-01',
        end=f'{year}-12-31 23:00',
        freq='1h',
        tz=state.time_zone
    )
    times = times[~((times.month == 2) & (times.day == 29))]
    
    # get full clearsky output (GHI, DNI, DHI)
    # value in W/m^2
    state_pvlib_location = state.location.to_pvlib()
    clearsky = state_pvlib_location.get_clearsky(times, model='ineichen')
    ghi_clearsky = clearsky['ghi']

    # moments of the year that we check from the observed avg solar radiation
    # at the beginning of each season (March, June, September plus twice for the winter)
    # once in the previous year (value as of January 1st) and once in this year winter start 
    anchors = [f"{year}-{month}-01" for month in [1, 3, 6, 9, 12]]+[f"{year}-12-31"]
    anchors = [pd.to_datetime(d).tz_localize(state.time_zone) for d in anchors]
    windows = list(zip(anchors, anchors[1:] + [times[-1]]))  # pair up [start, end)

    ghi_synthetic = ghi_clearsky.copy()

    for start, end in windows:
        mask = (times >= start) & (times < end)
        
        # Get the observed target for this window via asof
        target_avg = float(observed_avg_solar_radiation.asof(start))
        current_avg = ghi_clearsky[mask].mean()
    
        # and correct accordingly
        ghi_synthetic[mask] = ghi_clearsky[mask] * target_avg / current_avg

    # Scale dni and hic with the same scaling
    ghi_clearsky_np = ghi_clearsky.to_numpy()
    ghi_synthetic_np = ghi_synthetic.to_numpy()
    safe_clearsky = np.where(ghi_clearsky_np > 0, ghi_clearsky_np, 1)
    ghi_scale = np.where(ghi_clearsky_np > 0, ghi_synthetic_np / safe_clearsky, 0.0)

    dni_synthetic = (clearsky['dni'] * ghi_scale)
    dhi_synthetic = (clearsky['dhi'] * ghi_scale)

    solar_position = state_pvlib_location.get_solarposition(times)

    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=SOLAR_PANEL_NL_OPTIMAL_TILT,
        surface_azimuth=SOLAR_PANEL_NL_AZIMUTH_ANGLE,
        solar_zenith=solar_position['apparent_zenith'],
        solar_azimuth=solar_position['azimuth'],
        dni=dni_synthetic,
        ghi=ghi_synthetic,
        dhi=dhi_synthetic,
    )

    # return adapted numpy array of irradiation in kW/m^2
    return poa['poa_global'].to_numpy() * 1e-3
    
DEFAULT_SOLAR_YIELD_EFFICIENCY = 0.75
IRRADIANCE_AT_STC = 1.0 # kWh/M^2 : irradiance at standard conditions when rating solar panels capacity
def get_solar_yield(
        solar_farm: SolarFarm,
        solar_radiation: np.ndarray,
        settings: Settings
    ) -> np.ndarray:

    return solar_radiation * solar_farm.capacity / IRRADIANCE_AT_STC * DEFAULT_SOLAR_YIELD_EFFICIENCY


def get_hourly_electricity_price_of_year(
        scope: str,
        energy_sys_db: EnergySysDB,
        year: int
) -> np.ndarray:
    """
    Return a year of data combining the electricicty price and electricity price pattern
    in a given year.
    """
    ele_ucs = energy_sys_db[EnergySysDB.EPRICE_UNIT]
    ele_patterns = energy_sys_db[EnergySysDB.EPRICE_PATT]

    # we create the array by merging the first day (holiday, thus like a sunday)
    # with 53 weeks, i.e, 53 times a pattern, we then remove the extra days
    sub_patterns = []

    # First dya of the year: Take a sunday price and data as of 1st January
    ts = timestampify(year)
    ele_uc = ele_ucs.asof(ts)[scope]
    ele_pattern = ele_patterns.asof(ts).to_numpy()
    sub_patterns.append(
        ele_uc * ele_pattern[-24:]
    )

    ts += pd.DateOffset(hours=24)
    for i in range(53):
        curr_ts = ts + pd.DateOffset(weeks=i)

        ele_uc = ele_ucs.asof(curr_ts)[scope]
        ele_pattern = ele_patterns.asof(curr_ts).to_numpy()
        sub_patterns.append(
            ele_uc * ele_pattern
        )

    full_pattern = np.concat(sub_patterns, axis=0)[:24*365]
    
    return full_pattern
