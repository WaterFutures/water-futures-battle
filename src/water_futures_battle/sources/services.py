"""
Here we will have the sources:
- Groundwater
- Surface water (river)
- Desalination (brackish water)
"""
from typing import Dict, Set
from pathlib import Path

import pandas as pd

from .properties import SourcesResults, GroundWaterDB, SurfaceWaterDB, DesalinationDB
from .entities import WaterSource, GroundWater, SurfaceWater, Desalination, SourcesContainer

from ..jurisdictions.entities import State


def build_sources(properties_desc: dict[str,str], a_state: State) -> SourcesContainer:
    """
    Build all the sources specified startign from a config dictionary.
    """

    # Each water source type has its own database, but they have a common results object
    sources_results = SourcesResults()
    for ws_type, db_type in zip([GroundWater, SurfaceWater, Desalination],
                                [GroundWaterDB, SurfaceWaterDB, DesalinationDB]):
        sources_db = db_type.load_from_file(Path(properties_desc.get(db_type.NAME, "")))
        ws_type.set_dynamic_properties(sources_db)

    
    # Now we can start building for each type
    sources: Dict[str, Set[WaterSource]] = {
        GroundWater.NAME: set(),
        SurfaceWater.NAME: set(),
        Desalination.NAME: set()
    }
    dfs = pd.read_excel(Path(properties_desc.get('sources-static_properties', "")),
                        sheet_name=None)
    for ws_type in [GroundWater, SurfaceWater, Desalination]:
        for _, a_source_data in dfs[ws_type.NAME].iterrows():
            source_s_province = a_state.province(a_source_data['province'])
            a_source = ws_type.from_row(
                row_data=a_source_data.to_dict(),
                a_province=source_s_province
            )
            sources[ws_type.NAME].add(a_source)

    return SourcesContainer(sources)