import os
from pathlib import Path
from typing import Any, Dict, Set, Tuple

import pandas as pd

from ..core import Settings
from ..core.base_model import StaticProperties
from ..sources.entities import SourcesContainer, WaterSource
from ..pumps.dynamic_properties import PumpOptionsDB, PumpsResults
from ..pumps.entities import Pump, PumpOption

from .dynamic_properties import PumpingStationResults
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

    pumping_stations_results = PumpingStationResults()
    PumpingStation.set_results(pumping_stations_results)

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
        pump_options_dfs[p.bwf_id] = p.get_curves().reset_index()

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
