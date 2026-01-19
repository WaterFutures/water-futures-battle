from dataclasses import dataclass
from typing import Self

import pandas as pd

from ..base_model import bwf_entity

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
    min_lifetime: int
    MIN_LIFETIME = 'lifetime-min'

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
            min_lifetime=row_data[PumpOption.MIN_LIFETIME],
            _curves=curves
        )

        return instance

    @property
    def head_curve(self) -> pd.Series:
        return self._curves[PumpOption.H]
    
    @property
    def eff_curve(self) -> pd.Series:
        return self._curves[PumpOption.E]
    

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

    decommission_date: pd.Timestamp

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pump):
            return NotImplemented
        return self.bwf_id == other.bwf_id
    
    def __hash__(self) -> int:
        return hash(self.bwf_id)
