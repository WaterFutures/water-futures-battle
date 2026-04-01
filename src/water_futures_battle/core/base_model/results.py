from pathlib import Path
from typing import Any, Dict, List, Self, Optional, Union

import numpy as np
import pandas as pd

from .properties import DynamicProperties, PropertiesContainer

class BWFResult(DynamicProperties):
    NAME: str # For type hints, must be defined in derived class, we check in the init

    TRACKED_VARIABLES: List[str] = [ ] # Default for results, just in case you use them as a placeholder (you would not need this class if you don't use this)

    def __init__(self):

        # Enforce check on NAME
        if not hasattr(self, 'NAME') or self.NAME is None:
            raise TypeError(f"{self.__class__.__name__} must define a class attribute 'NAME'")
        
        dataframes = {
            var: pd.DataFrame(
                index=pd.DatetimeIndex(
                    [],
                    name="timestamp"
                ),
                dtype=np.float32
            )
            for var in self.TRACKED_VARIABLES
        }
        super().__init__(name=self.NAME, dataframes=dataframes)

    def commit(
        self,
        a_property: str,
        timestamps: pd.DatetimeIndex,
        data: Optional[Union[pd.DataFrame, pd.Series, Dict[str, Union[float, np.ndarray]]]] = None,
        entity: Optional[str] = None,
        values: Optional[Union[float, np.ndarray]] = None
    ) -> Self:
        """
        Commit results to the dataframe for a specific property.

        Results are stored as float64 values indexed by timestamp. Two modes are supported:

        **Bulk mode** (using `data`):
            Commit multiple entities at once using a dictionary mapping entity names to arrays.

        **Single entity mode** (using `entity` + `values`):
            Commit data for one specific entity/column.

        Args:
            a_property: Name of the tracked variable (must be in TRACKED_VARIABLES)
            timestamps: Timestamp(s) for the data. Single timestamp or multiple.
            data: Dictionary mapping entity names to numpy arrays of values. 
                    Each array must match the length of `timestamps`.
                    Mutually exclusive with `entity`/`values`.
            entity: Name of a single entity/column to update.
                    Mutually exclusive with `data`.
            values: Value(s) for the entity. Can be a single float or array matching
                    the length of `timestamps`. Only used with `entity`.

        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If both `data` and `entity`/`values` are provided, or if neither is provided
            ValueError: If array lengths don't match `timestamps` length
            
        Examples:
            # Single timestamp, single entity
            results.commit("temperature", pd.DatetimeIndex([now]), entity="sensor_1", values=23.5)
            
            # Multiple timestamps, single entity
            results.commit("temperature", timestamps, entity="sensor_1", values=temp_array)
            
            # Multiple timestamps, multiple entities (bulk)
            results.commit("temperature", timestamps, data={
                "sensor_1": temp_array_1,
                "sensor_2": temp_array_2
            })
        """
        # Check that property exists
        if a_property not in self.TRACKED_VARIABLES:
            raise KeyError(f"Property '{a_property}' not in TRACKED_VARIABLES: {self.TRACKED_VARIABLES}")
        
        # Check mutually exclusive parameters
        if data is not None and (entity is not None or values is not None):
            raise ValueError("Cannot specify both 'data' and 'entity'/'values'")
        
        if data is None and entity is None:
            raise ValueError("Must specify either 'data' or 'entity'/'values'")
        
        # Convert single-entity mode to bulk format, for single interface
        if entity is not None:
            if values is None:
                raise ValueError("Must provide 'values' when using 'entity'")
            data = {entity: values}
    
        # Convert to arrays if values are scalar 
        if isinstance(data, dict):
            for key, x in data.items():
                if np.ndim(x) == 0:
                    data[key] = np.full(len(timestamps), x)
            
            data_df = pd.DataFrame.from_dict(data=data, orient='columns')

        elif isinstance(data, pd.Series):
            if len(timestamps) == 1:
                # If there is only one measurement, we interpret the series as a row
                data_df = pd.DataFrame([data.values], index=timestamps, columns=data.index)
            else:
                # otherwise, if more timestamps are there, we use it as a column
                if len(timestamps) != len(data):
                    raise ValueError(
                        f"timestamps length ({len(timestamps)}) must match "
                        f"data length ({len(data)}) when timestamps has more than 1 entry."
                    )
                data_df = pd.DataFrame(data.values, index=timestamps, columns=[data.name])

        else:
            assert data is not None
            data_df = data.astype(np.float64)

        res_df = self.dataframes[a_property]
        
        # let's make space for them in case indexes and columns are not there
        new_timestamps = timestamps.difference(res_df.index)
        if len(new_timestamps) > 0:
            res_df = res_df.reindex(res_df.index.union(timestamps))
            res_df.index.name = 'timestamp'
            res_df = res_df.astype(np.float32)  # reindex fills NaNs as float64

        new_cols = data_df.columns.difference(res_df.columns)
        if len(new_cols) > 0:
            res_df[new_cols] = np.float32(np.nan)  # typed from the start, no cast needed

        res_df.loc[timestamps, data_df.columns] = data_df.values.astype(np.float32)
        
        assert (res_df.dtypes == np.float32).all(), \
            f"dtype drift detected: {res_df.dtypes[res_df.dtypes != np.float32].to_dict()}"

        # We modified only the local instance so assign it back
        self.dataframes[a_property] = res_df

        return self

    def dump(
            self,
            path: Optional[Path] = None,
            alternative_name: Optional[str] = None,
            subset: Optional[List[str]] = None,
            format: str = 'xlsx'
        ) -> Union[Path, List[Path]]:

        if not subset:
            # If the user doesn't specifiy a subset of fields, it means it wants all
            
            return super().dump(
                path=path,
                alternative_name=alternative_name,
                format=format
            )
         
        # otherwise, we filter the requested field, making sure they exist
        # a typo in the field doens't throw, but it doesn't get print
        requested_fields = [f
            for f in subset
            if f in self.TRACKED_VARIABLES
        ]
        # we then create a temp DynamicProperties object with the requested fields
        return DynamicProperties(
            name=self.NAME,
            dataframes={
                f: self[f]
                for f in requested_fields
            }
        ).dump(
            path=path,
            alternative_name=alternative_name,
            format=format
        )
        