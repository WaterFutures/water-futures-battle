import pandas as pd

def timestampify(a_value: int | str | pd.Timestamp, **kwargs) -> pd.Timestamp:
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
