from typing import TypeVar, Dict, Generic, List, Any

import pandas as pd

from ..utility.utility import timestampify

# Define a Type Variable for the Generic
C = TypeVar('C')

class YearlyView(Generic[C]):
    """"
    Yearly view is a class that acts as a view on a bwf_entity.
    """
    def __init__(self, original_instance: C, year: int):
        self._original = original_instance
        self._ts = timestampify(year, errors='raise')

    def __getattr__(self, name: str):
        
        # Get the list of dynamic properties from the *bwf entity*
        dynamic_properties: Dict[str, Any] = getattr(self._original, 'DYNAMIC_PROPERTIES', {})

        # Check if the requested attribute is one of the dynamic properties, otherwise
        # just pass it along
        if name in dynamic_properties:
            # The user requested an attribute that has been declared a dynamic property.
            # We use the declaration to handle the cases:
            # A: user declared a type. The method returns a pd.series, and we use self._ts
            #    to get the value at that point in time and we cast it to the required type.
            # B: user declared the corresponding time-aware method (a string), we get
            #    the value of that method.
            handler = dynamic_properties[name]

            if isinstance(handler, type):
                time_series_data = getattr(self._original, name)
            
                if not isinstance(time_series_data, pd.Series) and not isinstance(time_series_data, pd.DataFrame):
                    raise TypeError(
                        f"Dynamic property '{name}' of {type(self._original).__name__} is not a pandas Series or DataFrame. "
                        "Check your entity configuration."
                    )

                # Get the value in whatever format Pandas is storing it
                value = time_series_data.asof(self._ts)
                # but return it in the format we declared we want, e.g., EnumClass
                return dynamic_properties[name](value)
            
            elif isinstance(handler, str):
                method = getattr(self._original, handler)
                return method(self._ts)

        # The requeste attribute was not declared a dynamic property:
        return getattr(self._original, name)
