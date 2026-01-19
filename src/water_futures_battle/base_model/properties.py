import os
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd

class PropertiesContainer:
    """Base container for a collection of related DataFrames."""
    def __init__(self, name: str, dataframes: Optional[Dict[str, pd.DataFrame]] = None):
        self.name = name
        if dataframes is None:
            dataframes = {}
        self.dataframes = dataframes

    def __getitem__(self, key: str) -> pd.DataFrame:
        return self.dataframes[key]

    def __setitem__(self, key: str, value: pd.DataFrame) -> None:
        self.dataframes[key] = value

    def __getattr__(self, attr):
        # Delegate to the dataframes dict if attribute not found on self
        if hasattr(self.dataframes, attr):
            return getattr(self.dataframes, attr)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{attr}'")
    
    def dump(self,
             path: Optional[Path] = None,
             alternative_name: Optional[str] = None,
             f__index: bool = False,
             presave_task = None
            ) -> Path:
        base_path = Path(path) if path else os.getcwd()
        base_name = alternative_name if alternative_name else self.name
        extension = '.xlsx'
        full_filepath = base_path/Path(base_name+extension)
        with pd.ExcelWriter(full_filepath) as writer:
            for sheet, sheet_df in self.dataframes.items():
                if presave_task:
                    sheet_df = presave_task(sheet_df)
                sheet_df.to_excel(writer, sheet_name=sheet, index=f__index)

        return full_filepath


class StaticProperties(PropertiesContainer):
    pass

class DynamicProperties(PropertiesContainer):
    
    def dump(self,
             path: Optional[Path] = None,
             alternative_name: Optional[str] = None
            ) -> Path:
        def _fix_index_dates(df: pd.DataFrame) -> pd.DataFrame:
            df.index = pd.to_datetime(df.index)
            df.index = df.index.strftime('%Y-%m-%d')
            return df

        return super().dump(
            path=path,
            alternative_name=alternative_name,
            f__index=True,
            presave_task=_fix_index_dates
        )
    
def bwf_database(cls):
    """
    Decorator for the Battle of the Water Futures object that would contain
    independent or dependent dynamic properties and results.
    This decorator automatically looks for the definition of the:
    EXOGENOUS_VARIABLES
    ENDOGENOUS_VARIABLES
    RESULTS
    and creates a load from file method where it checks that all of those
    are there.
    It also injects a validate_data method and calls it at the end of __init__.
    """
    if not issubclass(cls, DynamicProperties):
        raise TypeError(f"{cls.__name__} must inherit from DynamicProperties")
    if not hasattr(cls, 'NAME'):
        raise TypeError(f"{cls.__name__} must define a class attribute 'NAME'")
    
    def must_contain_variables_named() -> List[str]:
        vars: List[str] = []
        for attr in ['EXOGENOUS_VARIABLES', 'ENDOGENOUS_VARIABLES']:
            vars += getattr(cls, attr, [])
        return vars
    
    @classmethod
    def load_from_file(cls_, full_filepath: Path):
        vars = must_contain_variables_named()
        dfs = pd.read_excel(
            full_filepath,
            sheet_name=vars,
            index_col='timestamp', # we said this decorator is only for dynamic properties
            parse_dates=True
        )
        return cls_(dataframes=dfs)
    
    def _must_contain_variables_check(self) -> None:
        missing = [k for k in must_contain_variables_named() if k not in self.dataframes]
        if missing:
            raise ValueError(f"Missing required dataframes: {missing}")
        
    def variables_validation_checks(self) -> None:
        """Ovverride this method if you need to perform any check on the data"""
        return
    
    def __init__(self, dataframes: Dict[str, pd.DataFrame]):
        super(cls, self).__init__(
            name=self.NAME,
            dataframes=dataframes
        )

        self._must_contain_variables_check()
        self.variables_validation_checks()

    cls.load_from_file = load_from_file
    cls._must_contain_variables_check = _must_contain_variables_check
    if not hasattr(cls, 'variables_validation_checks'):
        cls.variables_validation_checks = variables_validation_checks
    cls.__init__ = __init__
    return cls

def bwf_results(cls):
    """
    Decorator for BWF results classes.
    Ensures the class inherits from DynamicProperties.
    """

    if not issubclass(cls, DynamicProperties):
        raise TypeError(f"{cls.__name__} must inherit from DynamicProperties")
    if not hasattr(cls, 'NAME'):
        raise TypeError(f"{cls.__name__} must define a class attribute 'NAME'")

    def __init__(self):
        dataframes: Dict[str, pd.DataFrame] = {}
        results = getattr(cls, 'TRACKED_VARIABLES', [])

        for result in results:
            dataframes[result] = pd.DataFrame(index=pd.DatetimeIndex([], name="timestamp"))

        super(cls, self).__init__(
            name=self.NAME,
            dataframes=dataframes
        )

    cls.__init__ = __init__
    return cls