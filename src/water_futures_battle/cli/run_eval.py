import warnings
from pandas.errors import PerformanceWarning
warnings.simplefilter(action="ignore", category=PerformanceWarning)

import typer

from ..io import run_eval_from_file

app = typer.Typer()
app.command()(run_eval_from_file)


if __name__ == "__main__":
    app()
