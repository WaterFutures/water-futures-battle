import pandas as pd
from typing import List, TypeAlias

BWFTimeLike: TypeAlias = int | str | pd.Timestamp

def timestampify(a_value: BWFTimeLike, **kwargs) -> pd.Timestamp:
    """
    Convert input to pd.Timestamp.
    If input is int, treat it as a year (January 1st of that year).
    Otherwise, use pd.to_datetime with any extra kwargs.
    """
    if isinstance(a_value, int):
        return pd.Timestamp(year=a_value, month=1, day=1)
    return pd.to_datetime(a_value, **kwargs)

def keyify(text: str) -> str:
    """Normalize text for use as keys (preserves dashes)."""
    return text.lower().replace("'", "").replace(" ", "_")

def filter_columns(df: pd.DataFrame, logical_part: str) -> List[str]:
    """
    Returns the columns of a given property following the BWF conventions.
    The bWF convention is that the dash separator ('-') is used to seprate logical 
    parts, e.g., state-size-min, the underscore separator ('_') is to replace spaces
    in words. 
    So a column state-municipality_class-min has a counterpart ... 
    
    :param df: Description
    :type df: pd.DataFrame
    :param filter: Description
    :type filter: str
    :return: Description
    :rtype: List[str]
    """
    return [c for c in df.columns if logical_part in c.split('-')]
    