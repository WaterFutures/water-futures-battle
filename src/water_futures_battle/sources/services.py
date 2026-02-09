"""
Here we will have the sources:
- Groundwater
- Surface water (river)
- Desalination (brackish water)
"""
import os
from typing import Any, Dict, Set, Tuple
from pathlib import Path

import pandas as pd

from ..core import Settings
from ..core.base_model import StaticProperties
from ..jurisdictions.entities import State

from .properties import SourcesResults, GroundWaterDB, SurfaceWaterDB, DesalinationDB
from .entities import WaterSource, GroundWater, SurfaceWater, Desalination, SourcesContainer, SourcesSettings

def build_sources(
        properties_desc: Dict[str, str | float],
        a_state: State,
        data_path: str,
        settings: Settings
        ) -> Tuple[SourcesContainer, SourcesSettings]:
    """
    Build all the sources specified startign from a config dictionary.
    """

    # Each water source type has its own database, but they have a common results object
    sources_results = SourcesResults()
    for ws_type, db_type in zip([GroundWater, SurfaceWater, Desalination],
                                [GroundWaterDB, SurfaceWaterDB, DesalinationDB]):
        sources_db = db_type.load_from_file(os.path.join(data_path, Path(properties_desc.get(db_type.NAME, ""))))
        ws_type.set_dynamic_properties(sources_db)

    
    # Now we can start building for each type
    all_sources: Dict[str, Set[WaterSource]] = {
        GroundWater.NAME: set(),
        SurfaceWater.NAME: set(),
        Desalination.NAME: set()
    }
    dfs = pd.read_excel(
        Path(data_path)/Path(properties_desc.get('sources-static_properties', "")),
        sheet_name=SourcesContainer.types_names
    )
    for ws_type in [GroundWater, SurfaceWater, Desalination]:
        for _, a_source_data in dfs[ws_type.NAME].iterrows():
            source_s_province = a_state.province(a_source_data['province'])
            a_source = ws_type.from_row(
                row_data=a_source_data.to_dict(),
                a_province=source_s_province
            )
            all_sources[ws_type.NAME].add(a_source)

    global_options_df = pd.read_excel(
        Path(data_path)/Path(properties_desc.get('sources-static_properties', "")),
        sheet_name='global',
        index_col='source_type'
    )

    # Create the sources' settings
    src_settings = SourcesSettings.from_configs(
        config=properties_desc,
        global_options=global_options_df
    )

    return SourcesContainer(all_sources), src_settings

def dump_sources(
        all_sources: SourcesContainer,
        sources_settings: SourcesSettings,
        output_dir: Path
    ) -> Dict[str, Any]:

    full_out_dir = output_dir / "sources"
    def as_rel_path(a_path: Path) -> str:
        return os.path.relpath(a_path, output_dir)

    desalination_df = pd.DataFrame(data=[r.to_dict() for r in all_sources.desalination])

    groundwater_df = pd.DataFrame(data=[r.to_dict() for r in all_sources.groundwater])

    surface_water_df = pd.DataFrame(data=[r.to_dict() for r in all_sources.surface_water])

    src_set_config, src_set_global_df = sources_settings.to_configs()

    dfs = {
        'desalination': desalination_df,
        'groundwater': groundwater_df,
        'surface_water': surface_water_df,
        'global': src_set_global_df
    }

    sproperties = StaticProperties(
        name="sources-static_properties",
        dataframes=dfs
    )

    sp_path = sproperties.dump(full_out_dir)

    dp_path_gw = GroundWater._dynamic_properties.dump(full_out_dir)
    dp_path_sw = SurfaceWater._dynamic_properties.dump(full_out_dir)
    dp_path_des = Desalination._dynamic_properties.dump(full_out_dir)

    return {
        sproperties.name: as_rel_path(sp_path),
        GroundWaterDB.NAME: as_rel_path(dp_path_gw),
        SurfaceWaterDB.NAME: as_rel_path(dp_path_sw),
        DesalinationDB.NAME: as_rel_path(dp_path_des),
        **src_set_config
    }
