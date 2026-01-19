from dataclasses import dataclass
from typing import ClassVar, Dict, List, Self, Set

import pandas as pd

from ..base_model import bwf_entity
from ..sources.entities import WaterSource, SourcesContainer
from ..pumps import Pump, PumpOption

from .dynamic_properties import PumpingStationResults

OrderedPumpsCollection = Dict[int, Pump]
@bwf_entity(db_type=None, results_type=PumpingStationResults)
@dataclass(frozen=True)
class PumpingStation:
    """
    Represents a pumping station (collection of parallel pumps associated to a
    source) in the water futures battle.
    """
    # Unique identifier of the BWF, is used also for hashing and equality purposes
    bwf_id: str
    ID = 'pumping_station_id'
    ID_PREFIX = 'PS' # Pumping Station

    def __eq__(self, other):
        if not isinstance(other, PumpingStation):
            return NotImplemented
        return self.bwf_id == other.bwf_id

    def __hash__(self):
        return hash(self.bwf_id)

    # Source from which this pumping station pushes water from (assigned source)
    source: WaterSource
    SOURCE = 'assigned_source'

    # All time collection of the pumps installed at this station (this means pumps are either open or closed)
    pumps: OrderedPumpsCollection
    # Completely described by 3 properties: option, installation and decomminsion dates
    P_OPTION = 'pumps-option_ids'
    P_INSTDATE = 'pumps-installation_dates'
    P_DECODATE = 'pumps-end_dates'

    # Class Variable to store all the Solar Farms and how they are (if they are) associated 
    # to each pumping station.
    _global_solar_farms: ClassVar[Dict[str, Set['SolarFarm']]] = {}
    
    @classmethod
    def register_solar_farm(cls, a_solar_farm: 'SolarFarm') -> None:
        # Multiple solar farms can be associated to one element, but at each moment
        # in time only one will be active.
        if cls.bwf_id not in cls._global_solar_farms:
            cls._global_solar_farms[cls.bwf_id] = set()

        cls._global_solar_farms[cls.bwf_id].add(a_solar_farm)
        return

    @classmethod
    def from_row(cls, row_data: pd.Series, pump_options_map: Dict[str, PumpOption], sources: SourcesContainer) -> Self:
        """Create a PumpingStation instance from a dictionary row data."""
        # first of all, pumping station id
        pumping_station_id = str(row_data[PumpingStation.ID])

        # Discover which source you are associated to
        source = sources.entity(str(row_data[PumpingStation.SOURCE]))

        # Finally give everything to the puping station
        instance = cls(
            bwf_id=pumping_station_id,
            source=source,
            pumps=get_pumps_collection(
                str(row_data[PumpingStation.P_OPTION]),
                str(row_data[PumpingStation.P_INSTDATE]),
                str(row_data[PumpingStation.P_DECODATE]),
                pump_options_map=pump_options_map,
                bwf_id_prefix=pumping_station_id
            )
        )

        return instance
    
    def __post_init__(self):
        
        # Register this pumping station to the assigned source
        self.source.register_pumping_station(self)

    @property
    def province(self):
        return self.source.province

def get_pumps_collection(
    option_ids_desc: str,
    instal_dates_desc: str,
    decomm_dates_desc: str,
    pump_options_map: Dict[str, PumpOption],
    bwf_id_prefix: str
) -> OrderedPumpsCollection:
    
    pumps: OrderedPumpsCollection = {}
    
    if len(option_ids_desc) == 0 or option_ids_desc == 'nan':
        return pumps
    
    # get how many pumps are there, whene they were installed and decomissioned (as pd.timestamp)

    pump_options = [pump_options_map[oid] for oid in option_ids_desc.split(";")]
    pumps_instdates = [pd.to_datetime(d, errors='raise') for d in instal_dates_desc.split(";")]
    pumps_decodates = [pd.to_datetime(d, errors='raise') for d in decomm_dates_desc.split(";")]

    assert len(pump_options) == len(pumps_instdates), f"Lengths for pipe collecion don't match: option_ids {len(pump_options)}, install_dates={len(pumps_instdates)}"

    # Create the immutable pump obects with the characteristics we defined
    for i, poption in enumerate(pump_options):
        pumps[i] = Pump(
            bwf_id=f"{bwf_id_prefix}-{i:02d}",
            _pump_option=poption,
            installation_date=pumps_instdates[i], # this should be as long as the pump options as every pump must have been installed at some point
            decommission_date=pumps_decodates[i] if i < len(pumps_decodates) else pd.NaT
            )
    
    return pumps