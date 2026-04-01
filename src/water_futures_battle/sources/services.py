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
from ..core.utility import timestampify
from ..jurisdictions.entities import State

from .enums import GroundwaterPermitDeviation
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
    # Each water source type has its own database, but they have a common results
    # object.
    # They also have a common settings object.
    # Let's allocate the result object and the dictionary to hold the sources by type
    sources_results = SourcesResults()
    
    global_options_df = pd.read_excel(
        Path(data_path) / Path(properties_desc.get('sources-static_properties', "")),
        sheet_name='global',
        index_col='source_type'
    )

    # Create the sources' settings
    src_settings = SourcesSettings.from_configs(
        config=properties_desc,
        global_options=global_options_df
    )
    WaterSource._sources_settings = src_settings

    all_sources: Dict[str, Set[WaterSource]] = {}
    for ws_type, db_type in zip(
        [GroundWater, SurfaceWater, Desalination],
        [GroundWaterDB, SurfaceWaterDB, DesalinationDB]
        ):
        
        sources_db = db_type.load_from_file(
            Path(data_path) / Path(properties_desc.get(db_type.NAME, ""))
        )
        
        ws_type.set_dynamic_properties(sources_db)
        ws_type.set_results(sources_results)

        entities_df = pd.read_excel(
            Path(data_path) / Path(properties_desc.get('sources-static_properties', "")),
            sheet_name=ws_type.NAME
        )

        sources = []
        for _, a_source_data in entities_df.iterrows():

            source_s_province = a_state.province(a_source_data['province'])
            
            sources.append(
                ws_type.from_row(
                    row_data=a_source_data.to_dict(),
                    a_province=source_s_province
                )
            )

        all_sources[ws_type.NAME] = set(sources)
    
    

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

def check_groundwater_permits(
        gw_sources: Set[GroundWater],
        sources_year_production: pd.DataFrame,
        year: int
) -> float:
    
    total_fines_amount = 0.0

    gw_sources_permits = {
        s.bwf_id: s.permit
        for s in gw_sources
    }
    gw_sources_id = list(gw_sources_permits.keys())

    gw_sources_cum_year_production = sources_year_production[
        gw_sources_id
    ].sum(axis=0)

    gw_permits_deviation = (gw_sources_cum_year_production - pd.Series(gw_sources_permits)).clip(lower=0)

    gw_permit_dev_classes = gw_permits_deviation.apply(GroundwaterPermitDeviation.determine_class)

    ts = timestampify(year)
    all_fine_schema = GroundWater._dynamic_properties[GroundWaterDB.FINE_AMOUNT].asof(ts)

    for dev_class in gw_permit_dev_classes:
        # of course, no cost associated with compliant sources
        if dev_class == GroundwaterPermitDeviation.COMPLIANT:
            continue

        # non compliant source, we need the fine_schema_for this specific source
        # simplify
        fine_schema_col = '-'.join([
            'NL0000', # this should the highest available "source level"
            GroundwaterPermitDeviation(dev_class).name
        ])

        total_fines_amount += float(all_fine_schema[fine_schema_col])

    return total_fines_amount