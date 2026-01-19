from typing import Dict, Set, Tuple

import pandas as pd

from ..sources.entities import SourcesContainer
from ..sources import WaterSource
from ..pumps.dynamic_properties import PumpOptionsDB, PumpsResults
from ..pumps.entities import Pump, PumpOption

from .dynamic_properties import PumpingStationResults
from .entities import PumpingStation

def build_pumping_infrastructure(desc: Dict[str, str], sources: SourcesContainer) -> Tuple[Set[PumpOption], Set[PumpingStation]]:
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
    pump_options_db = PumpOptionsDB.load_from_file(desc[PumpOptionsDB.NAME])
    PumpOption.set_dynamic_properties(pump_options_db)

    pump_options_data = pd.read_excel(desc['pump_options-static_properties'],
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
        desc['pumping_stations-static_properties'],
        sheet_name='entities'
    )

    pumping_stations: Set[PumpingStation] = set()
    for idx, ps_data in pumping_stations_data.iterrows():
        pumping_stations.add(
            PumpingStation.from_row(
                row_data=ps_data,
                pump_options_map=pump_options_map,
                sources=sources
            )
        )

    pump_options = set(pump_options_map.values())

    return pump_options, pumping_stations