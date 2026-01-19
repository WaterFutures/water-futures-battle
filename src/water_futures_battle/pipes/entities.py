from dataclasses import dataclass
from typing import Dict, Self, Tuple

import pandas as pd

from ..base_model import bwf_entity

from .dynamic_properties import PipeOptionsDB, PipesResults

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
    
@bwf_entity(db_type=None, results_type=PipesResults)
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

    decommission_date: pd.Timestamp

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Pipe):
            return NotImplemented
        return self.bwf_id == value.bwf_id
    
    def __hash__(self) -> int:
        return hash(self.bwf_id)
    
OrderedPipesCollection = Dict[int, Pipe]