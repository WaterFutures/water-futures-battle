from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Self, Set, Tuple, Union

import pandas as pd

from ..jurisdictions.entities import Province
from ..core.base_model import bwf_entity, Location
from .properties import SourcesDB, SourcesResults
from ..core.utility import timestampify, BWFTimeLike

@dataclass(frozen=True)
class WaterSource(Location):
    """
    Base class for representing a water source.
    """
    # Unique identifier of the BWF, is used also for hashing and equality purposes
    bwf_id: str
    ID = "source_id"
    # ID prefix, equality and hashing are defined by derived type because they get
    # overwritten automatically by frozen dataclass

    # Plus from Location:
    # latitude
    # longitude
    # elevation

    # province: we passed the object itself
    province: Province
    PROVINCE = "province"
    
    # Optional name:
    display_name: str
    DISPLAY_NAME = 'name'

    # Closest municipality
    _closest_municipality_id: str
    CLOS_M_ID = 'closest_municipality'
    
    nominal_capacity: float
    NOMINAL_CAPACITY = 'capacity-nominal'
    
    activation_date: pd.Timestamp
    ACT_DATE = 'activation_date'
    closure_date: pd.Timestamp
    CLOS_DATE = 'closure_date'
    
    opex_vol_enfactor: float
    OPEX_VOLUM_ENERGY = 'opex-volum-energy_factor' # [kWh/m$^3$] Covers pumping, treatment, etc.

    # Class Variable to store all the Pumping stations associated to the sources.
    _global_pumping_stations: ClassVar[Dict[str, 'PumpingStation']] = {}

    @classmethod
    def register_pumping_station(cls, a_pumping_station: 'PumpingStation') -> None:
        # I could do fancy checks to make sure this pumping stations has not been
        # associated already somewhere or that I am not overwriting the association
        # for now keep it simple
        cls._global_pumping_stations[a_pumping_station.source.bwf_id] = a_pumping_station
        return

    # Class Variable to store all the Solar Farms and how they are (if they are) associated 
    # to each source.
    _global_solar_farms: ClassVar[Dict[str, Set['SolarFarm']]] = {}

    @classmethod
    def register_solar_farm(cls, a_solar_farm: 'SolarFarm') -> None:
        # Multiple solar farms can be associated to one element, but at each moment
        # in time only one will be active.
        if cls.bwf_id not in cls._global_solar_farms:
            cls._global_solar_farms[a_solar_farm.source.bwf_id] = set()

        cls._global_solar_farms[a_solar_farm.source.bwf_id].add(a_solar_farm)
        return

    # Constructor ("class method from row") is defined by the derived type because
    # it gets overwritten automatically by frozen class dataclass
    
    def is_active(self, when: BWFTimeLike) -> bool:
        """
        Returns True if the source is active at the given year/date/timestamp.
        Accepts year (int or str), date string, or pd.Timestamp.
        """
        ts = timestampify(when, errors='raise')
        if pd.isna(self.activation_date) or ts < self.activation_date:
            return False
        if pd.notna(self.closure_date) and ts >= self.closure_date:
            return False
        return True

    def volumetric_opex_rate(self) -> pd.Series:
        return self._dynamic_properties[SourcesDB.UNIT_COST][self.bwf_id]

    """
    REDO like above...
    def fixed_opex_rate(self) -> pd.Series:

        return self._dynamic_properties[self.self_type][self.bwf_id]

    def unit_cost(self) -> pd.Series:
        return self._dynamic_properties[self.self_type][self.province.region.cbs_id]
    """
    
    # TODO: functions to save the results in the self._results dictionary

    def to_dict(self) -> Dict[str, Any]:
        activ_date = self.activation_date.strftime('%Y-%m-%d') if pd.notna(self.activation_date) else ''
        clos_date = self.closure_date.strftime('%Y-%m-%d') if pd.notna(self.closure_date) else ''
        return {
            self.ID: self.bwf_id,
            self.LATITUDE: self.latitude,
            self.LONGITUDE: self.longitude,
            self.ELEVATION: self.elevation,
            self.DISPLAY_NAME: self.display_name,
            self.PROVINCE: self.province.cbs_id,
            self.CLOS_M_ID: self._closest_municipality_id,
            self.ACT_DATE: activ_date,
            self.CLOS_DATE: clos_date,
            self.NOMINAL_CAPACITY: self.nominal_capacity,
            self.OPEX_VOLUM_ENERGY: self.opex_vol_enfactor,
        }


@bwf_entity(db_type=SourcesDB, results_type=SourcesResults)
@dataclass(frozen=True)
class GroundWater(WaterSource):
    """
    Class representing a ground water source.
    """
    NAME = 'groundwater'
    ID_PREFIX = 'SG' # Source Groundwater

    def __eq__(self, other):
        if not isinstance(other, WaterSource):
            return NotImplemented
        # Define equality based on the unique identifier
        return self.bwf_id == other.bwf_id

    def __hash__(self):
        # Base the hash only on the unique identifier
        return hash(self.bwf_id)

    permit: float
    PERMIT = 'permit'

    @classmethod
    def from_row(cls, row_data: dict, a_province: Province, **kwargs) -> Self:
        """
        Primary static constructor from row data.
        """
        return cls(
            bwf_id=row_data[WaterSource.ID],
            province=a_province,
            latitude=row_data[WaterSource.LATITUDE],
            longitude=row_data[WaterSource.LONGITUDE],
            elevation=row_data[WaterSource.ELEVATION],
            display_name=row_data[WaterSource.DISPLAY_NAME],
            _closest_municipality_id=row_data[WaterSource.CLOS_M_ID],
            nominal_capacity=row_data[WaterSource.NOMINAL_CAPACITY],
            activation_date=pd.to_datetime(row_data[WaterSource.ACT_DATE], errors='coerce'),
            closure_date=pd.to_datetime(row_data[WaterSource.CLOS_DATE], errors='coerce'),
            opex_vol_enfactor=row_data[WaterSource.OPEX_VOLUM_ENERGY],
            permit=row_data[GroundWater.PERMIT],
            **kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict() | {self.PERMIT: self.permit}

@bwf_entity(db_type=SourcesDB, results_type=SourcesResults)
@dataclass(frozen=True)
class SurfaceWater(WaterSource):
    """
    Class representing a surface water source.
    """
    NAME = 'surface_water'
    ID_PREFIX = 'SS' # Source Surface water
    
    def __eq__(self, other):
        if not isinstance(other, WaterSource):
            return NotImplemented
        # Define equality based on the unique identifier
        return self.bwf_id == other.bwf_id

    def __hash__(self):
        # Base the hash only on the unique identifier
        return hash(self.bwf_id)
    
    basin: str
    BASIN = 'basin'
    
    @classmethod
    def from_row(cls, row_data: dict, a_province: Province, **kwargs) -> Self:
        """
        Primary static constructor from row data.
        """
        return cls(
            bwf_id=row_data[WaterSource.ID],
            province=a_province,
            latitude=row_data[WaterSource.LATITUDE],
            longitude=row_data[WaterSource.LONGITUDE],
            elevation=row_data[WaterSource.ELEVATION],
            display_name=row_data[WaterSource.DISPLAY_NAME],
            _closest_municipality_id=row_data[WaterSource.CLOS_M_ID],
            nominal_capacity=row_data[WaterSource.NOMINAL_CAPACITY],
            activation_date=pd.to_datetime(row_data[WaterSource.ACT_DATE], errors='coerce'),
            closure_date=pd.to_datetime(row_data[WaterSource.CLOS_DATE], errors='coerce'),
            opex_vol_enfactor=row_data[WaterSource.OPEX_VOLUM_ENERGY],
            basin=row_data[SurfaceWater.BASIN],
            **kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict() | {self.BASIN: self.basin}

@bwf_entity(db_type=SourcesDB, results_type=SourcesResults)
@dataclass(frozen=True)
class Desalination(WaterSource):
    """
    Class representing a desalination water source.
    """
    NAME = 'desalination'
    ID_PREFIX = 'SD' # Source Desalination

    def __eq__(self, other):
        if not isinstance(other, WaterSource):
            return NotImplemented
        # Define equality based on the unique identifier
        return self.bwf_id == other.bwf_id

    def __hash__(self):
        # Base the hash only on the unique identifier
        return hash(self.bwf_id)

    @classmethod
    def from_row(cls, row_data: dict, a_province: Province, **kwargs) -> Self:
        """
        Primary static constructor from row data.
        """
        return cls(
            bwf_id=row_data[WaterSource.ID],
            province=a_province,
            latitude=row_data[WaterSource.LATITUDE],
            longitude=row_data[WaterSource.LONGITUDE],
            elevation=row_data[WaterSource.ELEVATION],
            display_name=row_data[WaterSource.DISPLAY_NAME],
            _closest_municipality_id=row_data[WaterSource.CLOS_M_ID],
            nominal_capacity=row_data[WaterSource.NOMINAL_CAPACITY],
            activation_date=pd.to_datetime(row_data[WaterSource.ACT_DATE], errors='coerce'),
            closure_date=pd.to_datetime(row_data[WaterSource.CLOS_DATE], errors='coerce'),
            opex_vol_enfactor=row_data[WaterSource.OPEX_VOLUM_ENERGY],
            **kwargs
        )

ValidWaterSources = Union[GroundWater, SurfaceWater, Desalination]
GroundWaterSources = Set[GroundWater]
SurfaceWaterSources = Set[SurfaceWater]
DesalinationSources = Set[Desalination]
WaterSourcesTypes: list[type] = [GroundWater, SurfaceWater, Desalination]

class SourcesContainer:

    types = WaterSourcesTypes
    types_names = [t.NAME for t in WaterSourcesTypes]

    def __init__(self, sources: dict[str, Union[GroundWaterSources, SurfaceWaterSources, DesalinationSources]]):
        self.m_sources = sources

    @property
    def groundwater(self) -> GroundWaterSources:
        return self.m_sources[GroundWater.NAME]
    
    @property
    def surface_water(self) -> SurfaceWaterSources:
        return self.m_sources[SurfaceWater.NAME]
    
    @property
    def desalination(self) -> DesalinationSources:
        return self.m_sources[Desalination.NAME]
    
    def active_sources(self,year: int | str | pd.Timestamp) -> Set[WaterSource]:
        active_set: Set[WaterSource] = set()
        for source_set in self.m_sources.values():
            for source in source_set:
                if source.is_active(year):
                    active_set.add(source)
        return active_set
    
    def source_by_province(self, a_province: Province) -> Set[WaterSource]:
        province_set: Set[WaterSource] = set()
        for source_set in self.m_sources.values():
            for source in source_set:
                if source.province == a_province:
                    province_set.add(source)
        return province_set

    def __iter__(self):
        """Iterate through all sources across all source types."""
        for source_set in self.m_sources.values():
            for source in source_set:
                yield source

    def __len__(self):
        """Return total number of sources."""
        return sum(len(source_set) for source_set in self.m_sources.values())

    def items(self):
        """Return items view of source types and their sets."""
        return self.m_sources.items()

    def keys(self):
        """Return keys view of source types."""
        return self.m_sources.keys()

    def values(self):
        """Return values view of source sets."""
        return self.m_sources.values()
    
    @property
    def ordered_entities(self) -> list[WaterSource]:
        return sorted(self, key=lambda s: s.bwf_id)
    
    def entity(self, bwf_id: str) -> WaterSource:
        """
        Return the WaterSource object whose bwf_id matches the given string.
        Raises KeyError if not found.
        """
        for source in self:
            if source.bwf_id == bwf_id:
                return source
        raise KeyError(f"No WaterSource with bwf_id '{bwf_id}' found.")
        
@dataclass(frozen=True)
class SourcesSettings:

    # From configuration.yaml file a few special settings
    gw_construction_size_surplus: float
    GW_CONSTR_SIZE_SUR = 'groundwater-construction_size-max_permit_surplus'
    sw_construction_size_bounds: Tuple[float, float]
    SW_CONSTR_SIZE = 'surface_water-construction_size'
    des_construction_size_bounds: Tuple[float, float]
    DES_CONSTR_SIZE = 'desalination-construction_size'

    # From gloabl settings dataframe, a few common settings with values by source type
    # If deterministic just the value, i.e. Dict[str, float]
    # If uncertain, the bounds: Dict[str, Tuple[float, float]]
    # 
    capacity_target_factor: Dict[str, float]
    CAP_TARGET_FACT = 'capacity-target_factor'

    opex_volum_other_multip: Dict[str, float]
    OPEX_VOL_MULT = 'opex-volum-other-multiplier'

    construction_time_bounds: Dict[str, Tuple[float, float]]
    CONSTR_TIME = 'construction_time'

    new_source_opex_energyf_bounds: Dict[str, Tuple[float, float]]
    NEWSRC_ENERGYFACT = 'opex-volum-energy_factor' 

    @classmethod
    def from_configs(cls, config: Dict[str, float], global_options: pd.DataFrame) -> Self:
        return cls(
            gw_construction_size_surplus=config[cls.GW_CONSTR_SIZE_SUR],
            sw_construction_size_bounds=(
                config[cls.SW_CONSTR_SIZE+'-min'],
                config[cls.SW_CONSTR_SIZE+'-max']
            ),
            des_construction_size_bounds=(
                config[cls.DES_CONSTR_SIZE+'-min'],
                config[cls.DES_CONSTR_SIZE+'-max']
            ),
            capacity_target_factor={
                st: global_options.loc[st, cls.CAP_TARGET_FACT].astype(float)
                for st in SourcesContainer.types_names
            },
            opex_volum_other_multip={
                st: global_options.loc[st, cls.OPEX_VOL_MULT].astype(float)
                for st in SourcesContainer.types_names
            },
            construction_time_bounds={
                st: (
                    global_options.loc[st, cls.CONSTR_TIME+'-min'].astype(float),
                    global_options.loc[st, cls.CONSTR_TIME+'-max'].astype(float)
                )
                for st in SourcesContainer.types_names
            },
            new_source_opex_energyf_bounds={
                st: (
                    global_options.loc[st, cls.NEWSRC_ENERGYFACT+'-min'].astype(float),
                    global_options.loc[st, cls.NEWSRC_ENERGYFACT+'-max'].astype(float)
                )
                for st in SourcesContainer.types_names
            },
        )

    def to_configs(self) -> Tuple[Dict[str, float], pd.DataFrame]:
        config = {
            self.GW_CONSTR_SIZE_SUR: self.gw_construction_size_surplus,
            self.SW_CONSTR_SIZE+'-min': self.sw_construction_size_bounds[0],
            self.SW_CONSTR_SIZE+'-max': self.sw_construction_size_bounds[1],
            self.DES_CONSTR_SIZE+'-min': self.des_construction_size_bounds[0],
            self.DES_CONSTR_SIZE+'-max': self.des_construction_size_bounds[1],
        }

        global_options = []
        for source_type in SourcesContainer.types_names:
            global_options.append({
                'source_type': source_type,
                self.CAP_TARGET_FACT: self.capacity_target_factor[source_type],
                self.OPEX_VOL_MULT: self.opex_volum_other_multip[source_type],
                self.CONSTR_TIME+'-min': self.construction_time_bounds[source_type][0],
                self.CONSTR_TIME+'-max': self.construction_time_bounds[source_type][1],
                self.NEWSRC_ENERGYFACT+'-min': self.new_source_opex_energyf_bounds[source_type][0],
                self.NEWSRC_ENERGYFACT+'-max': self.new_source_opex_energyf_bounds[source_type][1],
            })

        global_options_df = pd.DataFrame(global_options)

        return config, global_options_df
