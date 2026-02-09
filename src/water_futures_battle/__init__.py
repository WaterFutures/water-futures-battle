import os

from .services import run_eval, compute_metrics
from .io import get_package_version, configure_system, run_eval_from_file
from .masterplan import parse_masterplan

__version__ = get_package_version()
VERSION = __version__