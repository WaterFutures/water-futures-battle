from dataclasses import dataclass
import itertools
from typing import Any, Dict, Tuple

from .enums import NRWClass

@dataclass(frozen=True)
class NRWModelSettings:

    success_proba_bounds: Tuple[float, float]
    SUCCESS_PROBA = "nrw_model-intervention_success_prob"

    def to_dict(self) -> Dict[str, Any]:
        return {
            self.SUCCESS_PROBA+'-min': self.success_proba_bounds[0],
            self.SUCCESS_PROBA+'-max': self.success_proba_bounds[1]
        }
    
@dataclass(frozen=True)
class NRWInterventionCostTable:
    """
    The intervention cost on the nrw class varies with the nrw class and the
    the municipality size class (like from small to big).
    This class models this 2 dimensional lookup.
    """
    _lookup_dict: dict[tuple[NRWClass, 'MunicipalitySize'], float]

    @classmethod
    def from_row(cls, row_data):
        # Build the lookup dict and assign it to the instnace

        lookup: dict[tuple[NRWClass, 'MunicipalitySize'], float] = {}
        for nrw_class, muni_size_class in itertools.product(NRWClass, 'MunicipalitySize'):
            column = f"{nrw_class.name}-{muni_size_class.name}"
            lookup[(nrw_class, muni_size_class)] = row_data[column]

        return cls(lookup)
    
    def __post_init__(self):
        for (nrw_class, muni_size_class), value in self._lookup_dict.items():
            if value <= 0.0:
                raise RuntimeError(f"Intervention cost for nrw class {nrw_class} and municipality size class {muni_size_class} must be positive, got {value}.")

    def __getitem__(self, key: tuple[NRWClass, 'MunicipalitySize']):
        return self._lookup_dict[key]
    
    def __mul__(self, value: float):
        # Return a new instance with all values multiplied by value
        new_lookup = {
            k: v * value for k, v in self._lookup_dict.items()
        }
        return type(self)(new_lookup)

    def __rmul__(self, value: float):
        return self.__mul__(value)
