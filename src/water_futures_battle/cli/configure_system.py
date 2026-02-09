import warnings
from pandas.errors import PerformanceWarning
warnings.simplefilter(action="ignore", category=PerformanceWarning)

import typer

from ..io import configure_system

app = typer.Typer()
app.command()(configure_system)


if __name__ == "__main__":
    app()
