from dataclasses import dataclass
import math
from typing import Tuple

import pandas as pd

from ..base_model import DynamicProperties, bwf_database, bwf_results
from .enums import SourceSize

@dataclass(frozen=True)
class _SourceVariableCostTable:
    """
    The costs per type of source (e.g. volumetric, fixed etc for groundwater)
    will be between two bounds and vary based on size.
    """
    _lookup_dict: dict[SourceSize, Tuple[float, float]]

    @classmethod
    def from_row(cls, row_data, entity_name: str):
        """
        Takes a pandas dataframe row or a dictionary written like class-min class-max
        and builds an instance of this type.
        """
        lookup: dict[SourceSize, Tuple[float, float]] = {}
        for source_class in SourceSize:
            columns = (f"{entity_name}-{source_class.name}-min", f"{entity_name}-{source_class.name}-max")
            lookup[source_class] = (row_data[columns[0]], row_data[columns[1]])
            min_val = row_data[columns[0]]
            max_val = row_data[columns[1]]
            # Check for None or NaN
            def fix_nans_none(min_val: float, max_val: float) -> Tuple[float, float]:
                if min_val is None or max_val is None:
                    return (float('inf'), float('inf'))
                if isinstance(min_val, float) and math.isnan(min_val):
                    return (float('inf'), float('inf'))
                if isinstance(max_val, float) and math.isnan(max_val):
                    return (float('inf'), float('inf'))
                return (min_val, max_val)
            min_val, max_val = fix_nans_none(min_val, max_val)
            lookup[source_class] = (min_val, max_val)

        return cls(lookup)

    def __post_init__(self):
        for a_class, values in self._lookup_dict.items():
            if values[0] < 0 or values[1] < 0:
                raise RuntimeError(f"Cost for source size {a_class.name} must be non-negative, got {values}.")
            if values[0] > values[1]:
                raise RuntimeError(f"Minimum cost for source size {a_class.name} must be smaller than its corresponding maximum.")
            
    def __getitem__(self, key: SourceSize):
        return self._lookup_dict[key]
    

class SourcesDB(DynamicProperties):
    UNIT_COST = 'new_source-unit_cost'
    OPEX_FIXED = 'opex-fixed' # [€/year] Labour, scheduled maintenance, overhead.
    OPEX_VOLUM_OTHER = 'opex-volum-other' # [€/m$^3$] Chemicals, filters, consumables.

    
    EXOGENOUS_VARIABLES = []
    ENDOGENOUS_VARIABLES = [
        UNIT_COST,
        OPEX_FIXED,
        OPEX_VOLUM_OTHER
    ]

    
    def variables_validation_checks(self) -> None:
        for property, property_type in zip(
            [self.OPEX_FIXED, self.OPEX_VOLUM_OTHER],
            [_SourceVariableCostTable, _SourceVariableCostTable]):

            # Get all the columns, so that we can undertand the first dimension (should be the source_id or similar)
            all_cols = self.dataframes[property].columns
            all_cols_firstdim = [col.split('-')[0] for col in all_cols]
            unique_dims = list(set(all_cols_firstdim))

            df = pd.DataFrame(index=self.dataframes[property].index, columns=unique_dims, dtype=object)
            for ts, row in self.dataframes[property].iterrows():
                for col in unique_dims:
                    selected_columns = [c for c in all_cols if c.startswith(col)]
                    df.loc[ts, col] = property_type.from_row(
                        row_data=row[selected_columns],
                        entity_name=col
                    )
            self.dataframes[property] = df
        
        return
    
        
@bwf_results
class SourcesResults(DynamicProperties):
    NAME = 'sources-results'

@bwf_database
class GroundWaterDB(SourcesDB):
    NAME = 'groundwater-dynamic_properties'

@bwf_database
class SurfaceWaterDB(SourcesDB):
    NAME = 'surface_water-dynamic_properties'

@bwf_database
class DesalinationDB(SourcesDB):
    NAME = 'desalination-dynamic_properties'

