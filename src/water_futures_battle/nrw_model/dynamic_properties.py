# Usually the dynamic properties are simple int, float or strings.
# In this case is a table
from dataclasses import dataclass
import itertools

import pandas as pd

from ..base_model import DynamicProperties, bwf_database
from ..jurisdictions.enums import MunicipalitySize
from .enums import NRWClass

@dataclass(frozen=True)
class _NRWInterventionTable:
    """
    The intervention cost on the nrw class varies with the nrw class and the
    the municipality size class (like from small to big).
    This class models this 2 dimensional lookup.
    """
    _lookup_dict: dict[tuple[NRWClass, MunicipalitySize], float]

    @classmethod
    def from_row(cls, row_data):
        # Build the lookup dict and assign it to the instnace

        lookup: dict[tuple[NRWClass, MunicipalitySize], float] = {}
        for nrw_class, muni_size_class in itertools.product(NRWClass, MunicipalitySize):
            column = f"{nrw_class.name}-{muni_size_class.name}"
            lookup[(nrw_class, muni_size_class)] = row_data[column]

        return cls(lookup)

    def __getitem__(self, key: tuple[NRWClass, MunicipalitySize]):
        return self._lookup_dict[key]
    
    def __mul__(self, value: float):
        # Return a new instance with all values multiplied by value
        new_lookup = {
            k: v * value for k, v in self._lookup_dict.items()
        }
        return type(self)(new_lookup)

    def __rmul__(self, value: float):
        return self.__mul__(value)

    
@dataclass(frozen=True)
class NRWInterventionCostTable(_NRWInterventionTable):
    """
    Specific class for when the lookup table is for money (cost of the interventions).
    """

    def __post_init__(self):
        for (nrw_class, muni_size_class), value in self._lookup_dict.items():
            if value <= 0.0:
                raise RuntimeError(f"Intervention cost for nrw class {nrw_class} and municipality size class {muni_size_class} must be positive, got {value}.")

# Similar class for intervention probabilities
@dataclass(frozen=True)
class NRWInterventionProbabilityTable(_NRWInterventionTable):
    """
    Specific class for when the lookup table is for probabilities (effectiveness of interventions).
    """

    def __post_init__(self):
        for (nrw_class, muni_size_class), value in self._lookup_dict.items():
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"Intervention probability for nrw class {nrw_class} and municipality size class {muni_size_class} must be between 0 and 1, got {value}.")

@bwf_database
class NRWModelDB(DynamicProperties):
    """
    Loads and stores nrw intervention tables over time.
    Each sheet in the Excel file corresponds to a property (cost or probability),
    with rows indexed by timestamp (year or date).
    It will also hold other parameters set from the configuration file.
    """
    NAME = 'nrw_model-dynamic_properties'
    
    COST = 'nrw_intervention-unit_cost'
    PROBABILITY = 'nrw_intervention-probability'

    EXOGENOUS_VARIABLES = [
        COST
    ]

    def variables_validation_checks(self) -> None:

        for property, property_type in zip([self.COST], [NRWInterventionCostTable]):
            df = pd.DataFrame(index=self.dataframes[property].index, columns=['NL0000'], dtype=object)
            for ts, row in self.dataframes[property].iterrows():
                df.loc[ts, 'NL0000'] = property_type.from_row(row_data=row)
            self.dataframes[property] = df

        return
