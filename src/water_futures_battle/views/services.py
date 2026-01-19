from typing import TypeVar

from ._entities import YearlyView

# Define a Type Variable for the Generic
C = TypeVar('C')

def get_snapshot(c: C, year: int) -> YearlyView[C]:
    return YearlyView(c, year)