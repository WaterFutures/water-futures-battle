import os
from pathlib import Path
from typing import Any, Dict

from ..core import Settings

from .dynamic_properties import ClimateDB

def configure_climate(
        config: dict,
        data_path: str,
        settings: Settings
    ) -> ClimateDB:

    return ClimateDB.load_from_file(os.path.join(data_path, config[ClimateDB.NAME]))

def dump_climate(
        climate_db: ClimateDB,
        output_dir: Path
    )-> Dict[str, Any]:

    full_out_dir = output_dir / "climate"
    def as_rel_path(a_path: Path) -> str:
        return os.path.relpath(a_path, output_dir)
    
    dp_path = climate_db.dump(full_out_dir)

    return {
        climate_db.NAME: as_rel_path(dp_path)
    }