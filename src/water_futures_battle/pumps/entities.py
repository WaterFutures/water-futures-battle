from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Self, Tuple

import numpy as np
import pandas as pd

from ..core.base_model import bwf_entity
from ..core.utility import timestampify, BWFTimeLike, OptionalTimestamp

from .dynamic_properties import PumpOptionsDB, PumpsResults

@bwf_entity(db_type=PumpOptionsDB, results_type=None)
@dataclass(frozen=True)
class PumpOption:
    """
    Represent a **pump option** in the water futures battle.
    """
    # Unique identifier of the BWF
    bwf_id: str
    ID = 'option_id'
    ID_PREFIX = 'PU' # Pump Unit

    # Name of the pump
    name: str
    NAME = 'name'

    # Nominal/design flow rate of this pump
    nominal_flow_rate: float
    NOMINAL_FLOW_RATE = 'flow_rate-nominal'

    # Lifetime of a pump
    lifetime: Tuple[int, int]
    LIFETIME = 'lifetime'

    # Object descring the curves associated with this pump option
    _curves: pd.DataFrame
    # this is described in a sheet named with the id
    # That sheet contains a table describing all the curves (each curve a column)

    Q = 'flow_rate'
    H = 'head'
    P = 'break_power'
    E = 'efficiency'
    CURVES_COLUMNS = [Q, H, P, E]

    def __eq__(self, other):
        if not isinstance(other, PumpOption):
            return NotImplemented
        return self.bwf_id == other.bwf_id

    def __hash__(self):
        return hash(self.bwf_id)

    @classmethod
    def from_row(cls, row_data: dict, other_data: dict) -> Self:
        option_id = row_data[PumpOption.ID]
        # All pump option properites are in the columns, excpet the curves,
        # which are in the other sheets of the other_data dict
        
        curves = other_data[option_id].set_index(PumpOption.Q)

        instance = cls(
            bwf_id=option_id,
            name=row_data[PumpOption.NAME],
            nominal_flow_rate=row_data[PumpOption.NOMINAL_FLOW_RATE],
            lifetime=(
                row_data[PumpOption.LIFETIME+'-min'],
                row_data[PumpOption.LIFETIME+'-max'],
            ),
            _curves=curves
        )

        return instance

    @property
    def head_curve(self) -> pd.Series:
        return self._curves[PumpOption.H]

    @property
    def eff_curve(self) -> pd.Series:
        return self._curves[PumpOption.E]

    def to_dict(self) -> Dict[str, Any]:
        return {
            self.ID: self.bwf_id,
            self.NAME: self.name,
            self.NOMINAL_FLOW_RATE: self.nominal_flow_rate,
            self.LIFETIME+'-min': self.lifetime[0],
            self.LIFETIME+'-max': self.lifetime[1],
        }

    def get_curves(self) -> pd.DataFrame:
        return self._curves.copy()
    
    @property
    def unit_cost(self) -> pd.Series:
        return self._dynamic_properties[PumpOptionsDB.COST][self.bwf_id]
    
@bwf_entity(db_type=None, results_type=PumpsResults)
@dataclass(frozen=True)
class Pump:
    """
    Represents a pump object (actula physical element installed, not option) in
    the BWF
    """
    # Unique identifier of the BWF (will be something like pumping_station_id-xx)
    bwf_id: str

    # Specify which pump option is this pump, so that we can take all the info 
    # from this object
    _pump_option: PumpOption

    installation_date: pd.Timestamp

    # Decommision date follows the same pattern explained for pipes
    # see the class Pipe in file pipes/entities.py 
    _decommission_date: OptionalTimestamp
    _DECOMMISSION_REGISTRY: ClassVar[Dict[str, pd.Timestamp]] = {}
    _sampled_lifetime: int

    @property
    def decommission_date(self) -> OptionalTimestamp:
        if pd.notna(self._decommission_date):
            return self._decommission_date
        
        return self._DECOMMISSION_REGISTRY.get(self.bwf_id, pd.NaT)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pump):
            return NotImplemented
        return self.bwf_id == other.bwf_id
    
    def __hash__(self) -> int:
        return hash(self.bwf_id)
    
    def __post_init__(self):
        assert self._results is not None

    def is_active(self, when: BWFTimeLike) -> bool:
        ts = timestampify(when)
        return (
            ts >= self.installation_date and 
            (pd.isna(self.decommission_date) or ts < self.decommission_date)
        )
    
    def decommission(self, when: BWFTimeLike) -> Self:
        ts = timestampify(when, errors='raise')

        if pd.notna(self.decommission_date):
            raise ValueError(
                f"Error decommisioning pump {self.bwf_id} on {ts}",
                "The entity has already a decommission date."
            )

        if ts <= self.installation_date:
            raise ValueError(
                f"Error decommisioning pump {self.bwf_id} on {ts}",
                f"The decommission date can not be before the installation date ({self.installation_date})"
            )
        
        self._DECOMMISSION_REGISTRY[self.bwf_id] = ts

        return self
    
    def _is_failing_this_year(self, when: int) -> bool:
        # Never failing if sampled lifetime is not there
        if self._sampled_lifetime <= 0:
            return False
        return (self.installation_date.year + self._sampled_lifetime) == when
    
    def _fail(self) -> Self:
        if self._sampled_lifetime <= 0:
            raise ValueError(f"Impossible to fail pump {self.bwf_id}.",
                             "This pump has no sampled lifetime because it has a decommision date.")
        return self.decommission(self.installation_date.year+self._sampled_lifetime)
    
    def track_ele_energy(
            self,
            when: BWFTimeLike,
            values: np.ndarray
        ) -> Self:
        """
        This function tracks the electrical energy consumption of a pump.

        It expects an array of values at a hourly timestep
        
        :param self: Description
        :param when: Description
        :type when: BWFTimeLike
        :param values: Description
        :type values: np.ndarray
        :return: Description
        :rtype: Self
        """
        # We expect one year of values at hourly frequence
        assert len(values) == 24*365

        self._results.commit(
            a_property=PumpsResults.ELE_ENERGY,
            timestamps=pd.date_range(
                start=timestampify(when),
                periods=len(values),
                freq='h'
            ),
            entity=self.bwf_id,
            values=values
        )

        return self