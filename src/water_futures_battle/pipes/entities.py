from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Self, Tuple

import numpy as np
import pandas as pd

from ..core.base_model import bwf_entity
from ..core.utility import BWFTimeLike, timestampify

from .dynamic_properties import PipeOptionsDB, PipesDB, PipesResults

@bwf_entity(db_type=PipeOptionsDB, results_type=None)
@dataclass(frozen=True)
class PipeOption:
    """
    Represents a **pipe option** in the water futures battle
    """
    bwf_id: str
    ID = 'option_id'
    ID_PREFIX = 'PI'

    diameter: float
    DIAMETER = 'diameter'

    material: str
    MATERIAL = 'material'

    # Darcy friction factor properties
    dff_new: float
    DFF_NEW = 'darcy_friction_factor-new_pipe'
    dff_decay_rate: Tuple[float, float]
    DFF_DECAYRATE = 'darcy_friction_factor-decay_rate'

    lifetime: Tuple[int, int]
    LIFETIME = 'lifetime'

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, PipeOption):
            return NotImplemented
        return self.bwf_id == value.bwf_id

    def __hash__(self) -> int:
        return hash(self.bwf_id)

    @classmethod
    def from_row(cls, row_data: pd.Series) -> Self:
        return cls(
            bwf_id=row_data[PipeOption.ID],
            diameter=row_data[PipeOption.DIAMETER],
            material=row_data[PipeOption.MATERIAL],
            dff_new=row_data[PipeOption.DFF_NEW],
            dff_decay_rate=(
                row_data[PipeOption.DFF_DECAYRATE+'-min'],
                row_data[PipeOption.DFF_DECAYRATE+'-max']
            ),
            lifetime=(
                row_data[PipeOption.LIFETIME+'-min'],
                row_data[PipeOption.LIFETIME+'-max']
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            self.ID: self.bwf_id,
            self.DIAMETER: self.diameter,
            self.MATERIAL: self.material,
            self.DFF_NEW: self.dff_new,
            self.DFF_DECAYRATE+'-min': self.dff_decay_rate[0],
            self.DFF_DECAYRATE+'-max': self.dff_decay_rate[0],
            self.LIFETIME+'-min': self.lifetime[0],
            self.LIFETIME+'-max': self.lifetime[1]
        }

    @property
    def unit_cost(self) -> pd.Series:
        return self._dynamic_properties[PipeOptionsDB.COST][self.bwf_id]
    
@bwf_entity(db_type=PipesDB, results_type=PipesResults)
@dataclass(frozen=True)
class Pipe:
    """
    Represents a pipe object (actual physical element installed, not option) in
    the BWF.
    """
    # Unique identifier of the BWF (will be something like connection_id-xx)
    bwf_id: str

    _pipe_option: PipeOption

    installation_date: pd.Timestamp

    # Decommission date is a mixture of a few options and methods
    # - '_decommission_date' which takes precedence over everything else.
    #   this is set from the input files and is frozen as per class immutability
    # - '_DECOMMISSION_REGISTRY' external registry shared between instances where 
    #   they can lookup their effective date of decomission if decided by the user
    #   or if the pipe arrives at failure
    # - '_sampled_lifetime' set at creation time, tells what is the lifetime if
    #   the element doesn't get replaced first, otherwise ignored
    _decommission_date: pd.Timestamp
    _DECOMMISSION_REGISTRY: ClassVar[Dict[str, pd.Timestamp]] = {}
    _sampled_lifetime: int

    @property
    def decommission_date(self) -> pd.Timestamp:
        if pd.notna(self._decommission_date):
            return self._decommission_date
        
        return self._DECOMMISSION_REGISTRY.get(self.bwf_id, pd.NaT)
    
    def __post_init__(self):
        assert self._dynamic_properties is not None
        assert self._results is not None

        #--- Register this pipe in the databases

        # his pipe has a starting friction factor that depend on the pipe option
        if self.bwf_id not in self._dynamic_properties[PipesDB.FRICTIONF].columns:

            self._dynamic_properties[PipesDB.FRICTIONF][self.bwf_id] = np.nan

            self._dynamic_properties[PipesDB.FRICTIONF].loc[
                self.installation_date,
                self.bwf_id
            ] = self._pipe_option.dff_new

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Pipe):
            return NotImplemented
        return self.bwf_id == value.bwf_id

    def __hash__(self) -> int:
        return hash(self.bwf_id)

    def get_option_id(self) -> str:
        return self._pipe_option.bwf_id
    
    def decommission(self, when: BWFTimeLike) -> Self:
        ts = timestampify(when, errors='raise')

        if (ts <= self.installation_date):
            raise ValueError(
                f"Decommission date {ts} must be after installation date {self.installation_date} for pipe {self.bwf_id}."
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
            raise ValueError(f"Impossible to fail pipe {self.bwf_id}.",
                             "This pipe has no sampled lifetime because it has a decommision date.")
        return self.decommission(self.installation_date.year+self._sampled_lifetime)
    
OrderedPipesCollection = Dict[int, Pipe]