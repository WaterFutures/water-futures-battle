from dataclasses import dataclass
from functools import cached_property
from typing import Self, ClassVar, Union, Optional
import warnings

import numpy as np
import pandas as pd

from .dynamic_properties import MunicipalitiesDB, MunicipalitiesResults
from .enums import MunicipalitySize

from ..base_model.entities import bwf_entity, Location
from ..nrw_model.enums import NRWClass
from ..utility.utility import keyify, timestampify

# Common properties names that are retrieved from the input files
NAME = 'name'
CBS_ID = 'cbs_id'

def keyify_jurisdiction(text: str) -> str:
    """Normalize Jurisdiction names for use as keys (converts dashes to underscores)."""
    return keyify(text).replace("-", "_")

NameLike = Union[str]  # Accepts display_name or cbs_id

@dataclass(frozen=True)
class Jurisdiction:
    """Base class for geographic entities with CBS code and normalized name."""
    _base_name: str
    cbs_id: str
    
    @cached_property
    def display_name(self) -> str:
        """Format the name for use in messages"""
        return f"{self._base_name} ({self.cbs_id})"
    
    def matches(self, other) -> bool:
        """
        Returns True if:
        - other is the same type and __eq__ is True
        - other is a str and matches cbs_id or display_name
        """
        if isinstance(other, type(self)):
            return self == other
        if isinstance(other, str):
            return (
                other == self.cbs_id
                or other == self.display_name
                or other.lower() == self._base_name.lower()
                # Name is not enough because the same name could be for a province or a municipality
            )
        return False

@dataclass(frozen=True)
class State(Jurisdiction):
    """State / national level"""
    
    def __eq__(self, other):
        if not isinstance(other, Jurisdiction):
            return NotImplemented
        # Define equality based on the unique identifier
        return self.cbs_id == other.cbs_id

    def __hash__(self):
        # Base the hash only on the unique identifier (cbs_code)
        return hash(self.cbs_id)

    _global_regions: ClassVar[dict[str,set['Region']]] = {}

    @classmethod
    def register_region(cls, a_region: 'Region') -> None:
        """Common set method to register Regions to a state"""
        # Make sure there is a set for this state
        if a_region.state.cbs_id not in cls._global_regions:
            cls._global_regions[a_region.state.cbs_id] = set()

        cls._global_regions[a_region.state.cbs_id].add(a_region)
    
    @property
    def regions(self) -> set['Region']:
        """Returns a list of all Region entities belonging to this State."""
        return self._global_regions.get(self.cbs_id, set())
    
    def region(self, identifier: NameLike) -> 'Region':
        for region in self.regions:
            if region.matches(other=identifier):
                return region
        
        raise KeyError(f"No region found with name: {identifier} in state {self.display_name}")
    
    @property
    def provinces(self) -> set['Province']:
        """
        Returns a set containing all Province instances belonging to this State (merged from all regions).
        """
        all_provinces = set()
        for region in self.regions:
            all_provinces.update(region.provinces)
        return all_provinces

    def province(self, identifier: NameLike) -> 'Province':
        """
        Retrieve a Province instance by display_name or cbs_id.
        """
        for province in self.provinces:
            if province.matches(identifier):
                return province
        raise KeyError(f"No province found for identifier: {identifier} in state {self.display_name}")
    
    @property
    def municipalities(self) -> set['Municipality']:
        """
        Returns a set containing all Municipality instances belonging to this State (merged from all provinces of all regions).
        """
        all_municipalities = set()
        for region in self.regions:
            all_municipalities.update(region.municipalities)
        return all_municipalities

    def municipality(self, identifier: NameLike) -> 'Municipality':
        """
        Retrieve a Municipality instance by display_name or cbs_id.
        """
        for municipality in self.municipalities:
            if municipality.matches(other=identifier):
                return municipality
        raise KeyError(f"No municipality found for identifier: {identifier} in state {self.display_name}")

@dataclass(frozen=True)
class Region(Jurisdiction):
    """Dutch region (landsdeel)."""
    ID_PREFIX = 'LD' # Landsdeel (region in Dutch)
    
    state: State

    def __post_init__(self):
        self.state.register_region(self)

    def __eq__(self, other):
        if not isinstance(other, Jurisdiction):
            return NotImplemented
        # Define equality based on the unique identifier
        return self.cbs_id == other.cbs_id

    def __hash__(self):
        # Base the hash only on the unique identifier (cbs_code)
        return hash(self.cbs_id)

    @classmethod
    def from_row(cls, row_data: dict, **kwargs) -> Self:
        """Primary static constructor from row data."""
 
        instance = cls(
            _base_name=row_data[NAME],
            cbs_id=row_data[CBS_ID],
            **kwargs
        )
            
        return instance
    
    # property self.state

    _global_provinces: ClassVar[dict[str,dict[str, set['Province']]]] = {}

    @classmethod
    def register_province(cls, a_province: 'Province') -> None:
        a_region = a_province.region
        a_state = a_region.state
        if a_state.cbs_id not in cls._global_provinces:
            cls._global_provinces[a_state.cbs_id] = {}

        if a_region.cbs_id not in cls._global_provinces[a_state.cbs_id]:
            cls._global_provinces[a_state.cbs_id][a_region.cbs_id] = set()

        cls._global_provinces[a_state.cbs_id][a_region.cbs_id].add(a_province)

    @property
    def provinces(self) -> set['Province']:
        state_key = self.state.cbs_id
        return (
            self._global_provinces.get(state_key, {})
            .get(self.cbs_id, set())
        )
    
    def province(self, identifier: NameLike) -> 'Province':
        for province in self.provinces:
            if province.matches(identifier):
                return province
        raise KeyError(f"No province found for identifier: {identifier} in region {self.display_name}")
    
    @property
    def municipalities(self) -> set['Municipality']:
        munis = set()
        for province in self.provinces:
            munis.update(province.municipalities)
        return munis
    
    def municipality(self, identifier: NameLike) -> 'Municipality':
        for municipality in self.municipalities:
            if municipality.matches(other=identifier):
                return municipality
        raise KeyError(f"No municipality found for identifier: {identifier} in region {self.display_name}")

@dataclass(frozen=True)
class Province(Jurisdiction):
    """Dutch province."""
    ID_PREFIX = 'PV' # Province

    region: Region

    @property
    def outfiles_name(self) -> str:
        """Name to be used in output files to not use the cbs_id"""
        return keyify_jurisdiction(self._base_name)

    def __post_init__(self):
        self.region.register_province(self)

    def __eq__(self, other):
        if not isinstance(other, Jurisdiction):
            return NotImplemented
        # Define equality based on the unique identifier
        return self.cbs_id == other.cbs_id

    def __hash__(self):
        # Base the hash only on the unique identifier (cbs_code)
        return hash(self.cbs_id)

    @classmethod
    def from_row(cls, row_data: dict, **kwargs) -> Self:
        """Primary static constructor from row data."""
        
        instance = cls(
            _base_name=row_data[NAME],
            cbs_id=row_data[CBS_ID],
            **kwargs
        )
            
        return instance

    @property
    def state(self) -> State:
        return self.region.state
    
    # property self.region

    _global_municipalities: ClassVar[dict[str, dict[str, dict[str, set['Municipality']]]]] = {}    

    @classmethod
    def register_municipality(cls, a_municipality: 'Municipality') -> None:
        a_province = a_municipality.province
        a_region = a_province.region
        a_state = a_region.state
        if a_state.cbs_id not in cls._global_municipalities:
            cls._global_municipalities[a_state.cbs_id] = {}
        if a_region.cbs_id not in cls._global_municipalities[a_state.cbs_id]:
            cls._global_municipalities[a_state.cbs_id][a_region.cbs_id] = {}
        if a_province.cbs_id not in cls._global_municipalities[a_state.cbs_id][a_region.cbs_id]:
            cls._global_municipalities[a_state.cbs_id][a_region.cbs_id][a_province.cbs_id] = set()

        cls._global_municipalities[a_state.cbs_id][a_region.cbs_id][a_province.cbs_id].add(a_municipality)

    @property
    def municipalities(self) -> set['Municipality']:
        state_key = self.region.state.cbs_id
        region_key = self.region.cbs_id
        province_key = self.cbs_id
        return (
            self._global_municipalities.get(state_key, {})
            .get(region_key, {})
            .get(province_key, set())
        )
    
    def active_municipalities(self, when: int | str | pd.Timestamp) -> set['Municipality']:
        """
        """
        return set([muni for muni in self.municipalities if muni.is_active(when=when)])
    
    def municipality(self, identifier: NameLike) -> 'Municipality':
        """
        Retrieve a Municipality instance by display_name or cbs_id.
        """
        for municipality in self.municipalities:
            if municipality.matches(other=identifier):
                return municipality
        raise KeyError(f"No municipality found for identifier: {identifier} in province {self.display_name}")

@bwf_entity(db_type=MunicipalitiesDB, results_type=MunicipalitiesResults)
@dataclass(frozen=True)
class Municipality(Jurisdiction, Location):
    """Dutch municipality (gemeente)."""
    ID_PREFIX = 'GM' # Gemeente (Municipality in Dutch)
    
    begin_date: pd.Timestamp
    BEGIN_DATE = 'begin_date'
    end_date: pd.Timestamp
    END_DATE = 'end_date'
    end_reason: str | None
    END_REASON = 'end_reason'
    destination_cbs_ids: set[str]
    END_CBSIDS = 'destination_cbs_ids'
    province: Province

    _res_p_weight: np.float64
    # assigned randomly from the service

    def __post_init__(self):
        assert self._dynamic_properties is not None
        # Register this municipality in its province
        self.province.register_municipality(self)

    def __eq__(self, other):
        if not isinstance(other, Jurisdiction):
            return NotImplemented
        # Define equality based on the unique identifier
        return self.cbs_id == other.cbs_id

    def __hash__(self):
        # Base the hash only on the unique identifier (cbs_code)
        return hash(self.cbs_id)
    
    @classmethod
    def from_row(cls, row_data: dict, **kwargs) -> Self:
        """Primary static constructor from row data."""
        raw_ids = row_data.get(Municipality.END_CBSIDS)
        end_cbs_ids = set()
        if raw_ids is not None and str(raw_ids).strip().lower() not in ('', 'none', 'nan'):
            end_cbs_ids = set(str(raw_ids).split(';'))
        instance = cls(
            _base_name=row_data[NAME],
            cbs_id=row_data[CBS_ID],
            latitude=row_data[Municipality.LATITUDE],
            longitude=row_data[Municipality.LONGITUDE],
            elevation=row_data[Municipality.ELEVATION],
            begin_date=pd.to_datetime(row_data[Municipality.BEGIN_DATE], errors='raise'),
            end_date=pd.to_datetime(row_data[Municipality.END_DATE], errors='raise'),
            end_reason=row_data[Municipality.END_REASON],
            destination_cbs_ids=end_cbs_ids,
            **kwargs # For parent instances like Province, Region
        )
        return instance
    
    # Declaration of dynamic properties, i.e., those that have some type of time dependency
    # and how the yearlyView object will handle them
    # If they return a pd.Series, we declare the casting type (e.g., population)
    # If they have a time-agnostic method and a corresponding time-aware one, we map them
    DYNAMIC_PROPERTIES = {
        'population': int,
        'size_class': MunicipalitySize,
        'nrw_class': NRWClass,
        'dist_network_avg_age': float,
        'dist_network_length': float,
        "n_houses": int,
        "n_businesses": int,
        'disp_income_avg': float,
        "assigned_demand_patterns": tuple
    }

    @property
    def state(self) -> State:
        return self.province.region.state

    @property
    def region(self) -> Region:
        return self.province.region

    # property self.province

    @property
    def n_houses(self) -> pd.Series:
        return self._dynamic_properties[MunicipalitiesDB.N_HOUSES][self.cbs_id]

    @property
    def n_businesses(self) -> pd.Series:
        return self._dynamic_properties[MunicipalitiesDB.N_BUSINESSES][self.cbs_id]

    @property
    def population(self) -> pd.Series:
        return self._dynamic_properties[MunicipalitiesDB.POPULATION][self.cbs_id]
    
    @property
    def assigned_demand_patterns(self) -> pd.Series:
        # result is a pd.Series of tuples: ((col1, col2), col3)

        #  Extract each relevant Series for this municipality
        r1 = self._dynamic_properties[MunicipalitiesDB.ASSOC_DM_R1][self.cbs_id]
        r2 = self._dynamic_properties[MunicipalitiesDB.ASSOC_DM_R2][self.cbs_id]
        b = self._dynamic_properties[MunicipalitiesDB.ASSOC_DM_B][self.cbs_id]

        # Align indexes and combine into a Series of tuples
        return pd.Series(
            data=[((v1, v2), v3) for v1, v2, v3 in zip(r1, r2, b)],
            index=r1.index
        )
    
    @property
    def assigned_res_patterns_weights(self) -> tuple[float, float]:
        return self._res_p_weight, 1.0-self._res_p_weight

    @property
    def size_class(self) -> pd.Series:
        # Ideally: self.population.apply(MunicipalitySize.determine_class
        # But it fails on nans, so apply the method only on NON-NaNs
        pop = self.population.copy()
        mask = pop.notna()
        pop[mask] = pop[mask].apply(MunicipalitySize.determine_class)
        return pop
    
    @property
    def nrw_class(self) -> pd.Series:
        # Ideally: self.dist_network_avg_age.apply(NRWClass.determine_class)
        # But it fails on nans, so apply the method only on NON-NaNs
        ages = self.dist_network_avg_age.copy()
        mask = ages.notna()
        ages[mask] = ages[mask].apply(NRWClass.determine_class)
        return ages

    @property
    def dist_network_avg_age(self) -> pd.Series:
        return self._dynamic_properties[MunicipalitiesDB.DISTNET_AVG_AGE][self.cbs_id]
    
    POPULATION_TO_PIPES = 57.7/10_000
    @property
    def dist_network_length(self) -> pd.Series:
        return self.population * self.POPULATION_TO_PIPES

    @property
    def disp_income_avg(self) -> pd.Series:
        return self._dynamic_properties[MunicipalitiesDB.ADI][self.cbs_id]

    def is_active(self, when: int | str | pd.Timestamp) -> bool:
        """
        Returns True if the municipality is active at the given year/date/timestamp.
        Accepts year (int or str), date string, or pd.Timestamp.
        """
        ts = timestampify(when, errors='raise')
        if pd.isna(self.begin_date) or ts < self.begin_date:
            return False
        if pd.notna(self.end_date) and ts >= self.end_date:
            return False
        return True

    def effective_cbs_id(self, when: int | str | pd.Timestamp) -> str:
        """
        Returns the effective CBS ID(s) for the municipality at the given date.
        If the municipality is active, returns its own cbs_id.
        If not active and yet to be opened, raises an error.
        If not active and closed (lifted or renamed), it resolves to the 
        municipality's CBS id to which it belongs at that time.
        If the municipality has been lifted and there is one municipality opening
         in that year between the destination municipalities, that municipality 
         is the destination municipality.
        Otherwise, it is simply the most populous one.
        If the destination municipality is in another province, it will print a
        warning requireing immediate action.
        """
        ts = timestampify(when, errors='raise')
        if pd.isna(self.begin_date) or ts < self.begin_date:
            raise RuntimeError(f"Requested the effective cbs id of a municipality that will open in the future: {self.display_name}")
        
        if pd.isna(self.end_date) or ts < self.end_date:
            # Still open,
            return self.cbs_id
        
        # It has indeed close, we should have the destination municipalities
        assert len(self.destination_cbs_ids) > 0

        # If it has close and one of the destination municipalities is a new one
        # opening that year, that is the destination municipality.
        # It has close, but became part of an already existing municipality,
        # we find the most popoulos in-province municipality between those and
        # return its cbs id.
        dest_munis: list[Municipality] = []
        dest_newidxs: list[int] = []
        dest_populations: list[float] = []
        for i, dest_id in enumerate(self.destination_cbs_ids):
            dest_muni = self.state.municipality(dest_id)
            dest_pop = dest_muni.population.asof(ts)

            dest_munis.append(dest_muni)
            dest_populations.append(dest_pop)
            if dest_muni.begin_date == self.end_date:
                dest_newidxs.append(i)

        # Decision making point, by default they can all be destination municipality
        # if there is a new one, we restrict the search.
        candidates = dest_munis
        candidates_pops = dest_populations
        if len(dest_newidxs):
            candidates = [dest_munis[i] for i in dest_newidxs]
            candidates_pops = [dest_populations[i] for i in dest_newidxs]

        candidate_idx = int(np.argmax(candidates_pops))

        if candidates[candidate_idx].province != self.province:
            warnings.warn(
                f"Municipality {self.display_name} closes to {candidates[candidate_idx].display_name}, "
                f"which is in a different province ({candidates[candidate_idx].province.display_name}) "
                f"than the original ({self.province.display_name})"
            )
            
        return candidates[candidate_idx].effective_cbs_id(when=ts)
    
    def effective_entity(self, when: int | str | pd.Timestamp) -> 'Municipality':
        """
        Returns the Municipality object for the municipality at the given date 
        taking advantage of the effective_cbs_id. See behaviour of effective_cbs_id.
        """
        return self.province.municipality(self.effective_cbs_id(when=when))

    # Setters for endogenous variables
    def update_dist_net_age(
            self,
            when: int | str | pd.Timestamp,
            by: float = 1,
            override_age: bool = False
        ) -> Self:

        ts = timestampify(when, errors='raise')
        db = self._dynamic_properties[MunicipalitiesDB.DISTNET_AVG_AGE]

        if override_age is True:
            if by < 0:
                raise ValueError("Age can not be negative!")
            db.loc[ts, self.cbs_id] = by
        elif ts >= self.begin_date and (pd.isna(self.end_date) or ts < self.end_date):
            current_age = self.dist_network_avg_age.asof(ts)
            if current_age+by < 0:
                raise ValueError("New age can not be negative!")
            db.loc[ts, self.cbs_id] = current_age+by
        else:
            db.loc[ts, self.cbs_id] = np.nan

        return self

    # Setters for results
    def _track(
            self,
            property: str,
            frequency: str,
            when: int | str | pd.Timestamp,
            values: np.ndarray
        ) -> Self:
        res_df = self._results[property]

        time_index = pd.date_range(
            start=timestampify(when),
            periods=len(values),
            freq=frequency
        )

        # let's make space for them in case indexes and columns are not there
        res_df = res_df.reindex(res_df.index.union(time_index))
        if self.cbs_id not in res_df.columns:
            res_df[self.cbs_id] = np.nan

        res_df.loc[time_index, self.cbs_id] = values

        # We modified only the local instance so assign it back
        self._results[property] = res_df

        return self

    # def track_nrw_demand(self, when: int | str | pd.Timestamp, values: np.ndarray) -> Self:
    #     """
    #     Expect one value per day of nrw demand with unit CMH
    #     """
    #     return self._track(
    #         property=MunicipalitiesResults.NRW_DEMAND,
    #         frequency='D',
    #         when=when,
    #         values=values
    #     )
    
    def track_demand(self, when: int | str | pd.Timestamp, values: np.ndarray) -> Self:
        """
        Expect one value per day of nrw demand with unit CMH
        """
        return self._track(
            property=MunicipalitiesResults.DEMAND,
            frequency='h',
            when=when,
            values=values
        )