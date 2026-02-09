from pathlib import Path
import os

from typing import Any, Dict, Tuple

from ..core import Settings

from .dynamic_properties import NRWModelDB
from .entities import NRWModelSettings

DEFAULT_SUCCESS_PROB_BOUND_MIN = 0.95
DEFAULT_SUCCESS_PROB_BOUND_MAX = 1

def configure_nrw_model(
        config: dict,
        data_path: str,
        settings: Settings
    ) -> Tuple[NRWModelSettings, NRWModelDB]:
    
    nrw_model_settings = NRWModelSettings(
        success_proba_bounds=(
            config.get(f"{NRWModelSettings.SUCCESS_PROBA}-min", DEFAULT_SUCCESS_PROB_BOUND_MIN),
            config.get(f"{NRWModelSettings.SUCCESS_PROBA}-max", DEFAULT_SUCCESS_PROB_BOUND_MAX)
        )
    )

    nrw_model_db = NRWModelDB.load_from_file(os.path.join(data_path, config[NRWModelDB.NAME]))

    return nrw_model_settings, nrw_model_db

def dump_nrw_model(
        nrw_settings: NRWModelSettings,
        nrw_db: NRWModelDB,
        output_dir: Path
    )-> Dict[str, Any]:

    full_out_dir = output_dir / "nrw_model"
    def as_rel_path(a_path: Path) -> str:
        return os.path.relpath(a_path, output_dir)
    
    desc = nrw_settings.to_dict()

    dp_path = nrw_db.dump(full_out_dir)

    desc[nrw_db.NAME] = as_rel_path(dp_path)

    return desc