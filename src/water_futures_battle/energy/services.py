import os
from pathlib import Path
from typing import Any, Dict, Set, Tuple

import pandas as pd

from ..core import Settings
from ..core.base_model import StaticProperties
from ..sources.entities import SourcesContainer
from ..pumping_stations.entities import PumpingStation

from .dynamic_properties import EnergySysDB
from .entities import SolarFarm

def configure_energy_system(
        config: dict,
        sources: SourcesContainer,
        pumping_stations: Set[PumpingStation],
        data_path: str,
        settings: Settings
    ) -> Tuple[EnergySysDB, Set[SolarFarm]]:
    
    energysys_db = EnergySysDB.load_from_file(os.path.join(data_path, config[EnergySysDB.NAME]))

    solar_farms = set()

    return energysys_db, solar_farms

def dump_energy_system(
        energy_db: EnergySysDB,
        all_solar_farms: Set[SolarFarm],
        output_dir: Path
    ) -> Dict[str, Any]:

    full_out_dir = output_dir / "energy"
    def as_rel_path(a_path: Path) -> str:
        return os.path.relpath(a_path, output_dir)
    
    if len(all_solar_farms) > 0:
        entities_df = pd.DataFrame(
            data=[sf.to_dict() for sf in sorted(all_solar_farms, key= lambda x: x.bwf_id)]
        )
    else:
        entities_df = pd.DataFrame(columns=SolarFarm.file_columns())

    dfs  = {
        'entities': entities_df
    }

    sproperties = StaticProperties(
        name="solar_farms-static_properties",
        dataframes=dfs
    )
    
    sp_path = sproperties.dump(full_out_dir)
    dp_path = energy_db.dump(full_out_dir)

    return {
        sproperties.name: as_rel_path(sp_path),
        energy_db.NAME: as_rel_path(dp_path)
    }