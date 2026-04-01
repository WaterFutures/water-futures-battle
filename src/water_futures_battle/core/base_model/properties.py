import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Protocol, Type, TypeVar, Union

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
        presave_task = None,
        format: str = 'xlsx'
    ) -> Union[Path, List[Path]]:
        
        base_path = Path(path) if path else Path(os.getcwd())
        base_path.mkdir(exist_ok=True)

        base_name = alternative_name if alternative_name else self.name
        
        return _dump_to_file(
            base_path=base_path,
            base_name=base_name,
            format=format,
            a_dict=self.dataframes,
            f__index=f__index,
            presave_task=presave_task,
        )
        
def _dump_to_excel(
        base_path: Path,
        base_name: str,
        a_dict: Dict[str, pd.DataFrame],
        f__index: bool = False,
        presave_task = None
    ) -> Path:
        fp = base_path / f"{base_name}.xlsx"
        with pd.ExcelWriter(fp) as writer:
            for sheet, df in a_dict.items():
                if presave_task:
                    df = presave_task(df)
                df.to_excel(writer, sheet_name=sheet, index=f__index)
        return fp

def _dump_to_csv(
        base_path: Path,
        base_name: str,
        a_dict: Dict[str, pd.DataFrame],
        f__index: bool = False,
        presave_task = None
    ) -> List[Path]:
        # one csv per sheet  →  base_name-sheet.csv
        fps = []
        for sheet, df in a_dict.items():
            fp = base_path / f"{base_name}-{sheet}.csv"

            if presave_task:
                df = presave_task(df)

            df.to_csv(fp, index=f__index)
            fps.append(fp)
        return fps

ALLOWED_FORMATS = {'xlsx', 'csv', 'parquet'}
def _dump_to_file(
        base_path: Path,
        base_name: str,
        format: str,
        a_dict: Dict[str, pd.DataFrame],
        f__index: bool = False,
        presave_task = None
    ) -> Union[Path, List[Path]]:

        if format not in ALLOWED_FORMATS:
            raise ValueError(f"format must be one of {ALLOWED_FORMATS}, got '{format}'")
            
        if format == 'xlsx':
            return _dump_to_excel(
                base_path=base_path,
                base_name=base_name,
                a_dict=a_dict,
                f__index=f__index,
                presave_task=presave_task
            )
        
        elif format == 'csv':
            return _dump_to_csv(
                base_path=base_path,
                base_name=base_name,
                a_dict=a_dict,
                f__index=f__index,
                presave_task=presave_task
            )
        
        else:
            return _dump_to_csv(
                base_path=base_path,
                base_name=base_name,
                a_dict=a_dict,
                f__index=f__index,
                presave_task=presave_task
            )

class StaticProperties(PropertiesContainer):
    pass

class DynamicProperties(PropertiesContainer):
    
    HOURLY_YEAR_THRESHOLD = 2 * 8760  # at least 2 years of hourly data to split by year
    # because if we use one year of data, 25 years of daily values has more points

    def dump(
            self,
            path: Optional[Path] = None,
            alternative_name: Optional[str] = None,
            format: str = 'xlsx'
        ) -> Union[Path, List[Path]]:
        
            def _fix_index_dates(df: pd.DataFrame) -> pd.DataFrame:
                df = df.copy()
                df.index = pd.to_datetime(df.index)
                df.sort_index(inplace=True)

                if len(df.index) < self.HOURLY_YEAR_THRESHOLD:
                    df.index = df.index.strftime('%Y-%m-%d')
                else:
                    df.index = df.index.strftime('%Y-%m-%d %H:%M')
                    # Drop columns full of NaNs for elements that were not there in a given year
                    df.dropna(axis=1, how='all', inplace=True)  

                return df

            dump_kwargs = dict(path=path, alternative_name=alternative_name, f__index=True, presave_task=_fix_index_dates, format=format)

            flat_dfs = {k: v for k, v in self.dataframes.items() if len(v) < self.HOURLY_YEAR_THRESHOLD}
            by_year_dfs = {k: v for k, v in self.dataframes.items() if len(v) >= self.HOURLY_YEAR_THRESHOLD}

            fps = []

            # Flat sheets → single file under the original name
            if flat_dfs:
                fp = PropertiesContainer(self.name, flat_dfs).dump(**dump_kwargs)
                fps.extend([fp] if isinstance(fp, Path) else fp)

            # Long sheets → one file per year, named "<name>-<year>"
            if by_year_dfs:
                all_years = sorted({year for df in by_year_dfs.values() for year in df.index.year})
                for year in all_years:
                    year_dict = {
                        sheet: df[df.index.year == year]
                        for sheet, df in by_year_dfs.items()
                        if not df[df.index.year == year].empty
                    }
                    fp = PropertiesContainer(f"{self.name}-{year}", year_dict).dump(**dump_kwargs)
                    fps.extend([fp] if isinstance(fp, Path) else fp)

            return fps[0] if len(fps) == 1 else fps

    
T = TypeVar("T", bound="DynamicProperties")

def bwf_database(cls: Type[T]) -> Type[T]:
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
