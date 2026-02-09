from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Self, Set, Optional

import numpy as np
import pandas as pd

from ..core import Settings
from ..core.base_model import bwf_entity
from ..core.utility import BWFTimeLike
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
    def from_row(
        cls,
        row_data: pd.Series,
        pump_options_map: Dict[str, PumpOption],
        sources: SourcesContainer,
        settings: Settings
    ) -> Self:
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
                bwf_id_prefix=pumping_station_id,
                settings=settings
            )
        )

        return instance
    
    def __post_init__(self):
        
        # Register this pumping station to the assigned source
        self.source.register_pumping_station(self)

    @property
    def province(self):
        return self.source.province

    def active_pumps(self, when: BWFTimeLike) -> OrderedPumpsCollection:
        return {
            pidx: pump
            for pidx, pump in self.pumps.items()
            if pump.is_active(when=when)
        }
    
    def has_active_pumps(self, when: BWFTimeLike) -> bool:
        return len(self.active_pumps(when=when)) > 0
    
    def install_pump(
            self,
            pump_option: PumpOption,
            installation_date: pd.Timestamp,
            decommission_date: Optional[pd.Timestamp] = None,
            lifetime_rng: Optional[np.random.Generator] = None
    ) -> Pump:
        
        #We are installing a new pump, this has name {my_id}-{counter:02d}
        ## we start countign from 0 so let's just use len(installed)
        n_current_installed_pumps = len(self.pumps)
        pump_id = f"{self.bwf_id}-{n_current_installed_pumps:02d}"

        # The user must either pass a decommision date (historical information)
        # or a random generator:
        # if none of the two is passed raise error 
        # if both are passed the second is ignored

        if decommission_date is None and lifetime_rng is None:
            raise ValueError(f"Impossible to install a pump on pumping station {self.bwf_id}.",
                             "You need to pass either a decommision date or a random generator argument.")


        if decommission_date is not None and pd.notna(decommission_date):
            deco_date = decommission_date
            lifetime = -1 # like nan but the property is an int
        else:
            assert lifetime_rng is not None
            deco_date = pd.NaT
            lifetime = lifetime_rng.integers(*pump_option.lifetime)

        #### heck if the install pump is the same time as the pumping station 
        #check if the are pumps installed or the old active pumps pumps are a different type 
        if (len(self.pumps) > 0 and
            any(pump._pump_option != pump_option
                for pump in self.active_pumps(installation_date).values())
        ): 
            
            raise ValueError(
                f"Impossible to install a pump of type {pump_option.bwf_id} on pumping station {self.bwf_id} at timestep {installation_date}",
                "You need to install a pump of the same type as it was already installed or decommission all the active pumps before."
            )
    
        new_pump = Pump(
            bwf_id=pump_id,
            _pump_option=pump_option,
            installation_date=installation_date,
            _decommission_date=deco_date,
            _sampled_lifetime=lifetime
        )

        #actually install the pump
        self.pumps[len(self.pumps)] = new_pump

        return new_pump
    
    def inspect_and_replace(
            self,
            year: int,
            lifetime_rng: np.random.Generator
    ) -> float:

        if not self.has_active_pumps(when=year):
            return 0.0
        
        active_pumps = self.active_pumps(when=year)
        assert active_pumps is not None

        cost = 0.0
        for active_pump in active_pumps.values():
            if not active_pump._is_failing_this_year(when=year):
                continue

            # It is failing, so decommission it and open a new one
            active_pump._fail()
            failed_pump = active_pump

        
            new_pump = self.install_pump(
                pump_option=failed_pump._pump_option,
                installation_date=failed_pump.decommission_date,
                lifetime_rng=lifetime_rng)

            pump_unit_cost = new_pump._pump_option.unit_cost.loc[failed_pump.decommission_date]
            cost += pump_unit_cost

        return cost
        
    def to_dict(self) -> Dict[str, Any]:
        install_dates = [
            p.installation_date.strftime('%Y-%m-%d')
            for p in self.pumps.values()
        ]
        deco_dates = [
            p.decommission_date.strftime('%Y-%m-%d') if pd.notna(p.decommission_date) else ''
            for p in self.pumps.values()
        ]
        
        # Remove trailing None in deco_dates to avoid ;;;; at the end
        while deco_dates and deco_dates[-1] == '':
            deco_dates.pop()

        return {
            self.ID: self.bwf_id,
            self.SOURCE: self.source.bwf_id,
            self.P_OPTION: ';'.join([p._pump_option.bwf_id for p in self.pumps.values()]),
            self.P_INSTDATE: ';'.join(install_dates),
            self.P_DECODATE: ';'.join(deco_dates)
        }


def get_pumps_collection(
    option_ids_desc: str,
    instal_dates_desc: str,
    decomm_dates_desc: str,
    pump_options_map: Dict[str, PumpOption],
    bwf_id_prefix: str,
    settings: Settings
) -> OrderedPumpsCollection:
    
    pumps: OrderedPumpsCollection = {}
    
    if len(option_ids_desc) == 0 or option_ids_desc == 'nan':
        return pumps
    
    # get how many pumps are there, whene they were installed and decomissioned (as pd.timestamp)

    pump_options = [pump_options_map[oid] for oid in option_ids_desc.split(";")]
    pumps_instdates = [pd.to_datetime(d, errors='raise') for d in instal_dates_desc.split(";")]
    pumps_decodates_strs = decomm_dates_desc.split(";")

    assert len(pump_options) == len(pumps_instdates), f"Lengths for pipe collecion don't match: option_ids {len(pump_options)}, install_dates={len(pumps_instdates)}"

    # Create the immutable pump obects with the characteristics we defined
    for i, (poption, pinstdate) in enumerate(zip(pump_options, pumps_instdates)):
        # All decommisioned pumps get that date and -1 as sampled lifetime
        # otherwise if the decommision date is nan or in general the pumps has not closed
        if i < len(pumps_decodates_strs) and pumps_decodates_strs[i] != "":
            deco_date = pd.to_datetime(pumps_decodates_strs[i], errors='coerce')
            lifetime = -1
        else:
            deco_date = pd.NaT
            lifetime = settings.get_random_generator('pumps-lifetime').integers(
                *poption.lifetime
            )

        pumps[i] = Pump(
            bwf_id=f"{bwf_id_prefix}-{i:02d}",
            _pump_option=poption,
            installation_date=pinstdate,
            _decommission_date=deco_date,
            _sampled_lifetime=lifetime
            )

    return pumps