from dataclasses import dataclass
from typing import Any, Dict, Tuple

import numpy as np

from .properties import WaterDemandModelDB

# Entites are the patterns, which have, identifier, type/category and values (the 8760-value pattern)

@dataclass(frozen=True)
class WaterDemandModelPattern:
        
    bwf_id: str
    ID = "demand_pattern_id"

    category: str
    # this is identified by the sheet

    values: np.ndarray
    VALUES = [f'year_hour-{i}' for i in range(8760)]

    def __eq__(self, other):
        if not isinstance(other, WaterDemandModelPattern):
            return NotImplemented
        return self.bwf_id == other.bwf_id

    def __hash__(self):
        return hash(self.bwf_id)

    def to_dict(self) -> Dict[str, Any]:
        r = {
            self.ID: self.bwf_id,
        }

        for val_desc, val in zip(self.VALUES, self.values):
            r[val_desc] = val

        return r

WaterDemandModelPatterns = Dict[str, WaterDemandModelPattern]

WaterDemandModelData = Tuple[WaterDemandModelPatterns, WaterDemandModelDB]