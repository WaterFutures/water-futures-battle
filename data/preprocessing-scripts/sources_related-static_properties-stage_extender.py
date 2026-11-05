import os
from pathlib import Path
from typing import Dict, List, Tuple

from geopy.distance import geodesic
import numpy as np
import pandas as pd

from water_futures_battle.core.base_model import StaticProperties
from water_futures_battle.sources.entities import WaterSource, GroundWater, SurfaceWater, Desalination
from water_futures_battle.pumping_stations.entities import PumpingStation
from water_futures_battle.connections.entities import SupplyConnection

STAGE_YEARS = [
    ("2025-01-01", "2049-01-01"),
    ("2050-01-01", "2074-01-01"),
    ("2075-01-01", "2099-01-01"),
]
STAGE_INDEX_SHIFT = [1000, 2000, 3000]

def append_new_sources(
        all_sources_dict: Dict[str, pd.DataFrame],
        all_new_sources: pd.DataFrame,
        stage_idx: int
    ) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:

    stage_new_sources = all_new_sources[all_new_sources['stage'] == stage_idx+1]
    
    # Concat to the old dataframes the new one by type of source
    stage_new_sources_list = []
    for source_type in [GroundWater, SurfaceWater, Desalination]:
        new_sources_t = stage_new_sources[
            stage_new_sources['source_type'] == source_type.NAME
        ]
        new_sources_t[WaterSource.ID] = [
            f"{source_type.ID_PREFIX}{x:04d}"
            for x in range(
                STAGE_INDEX_SHIFT[stage_idx]+1,
                STAGE_INDEX_SHIFT[stage_idx]+1+ len(new_sources_t)
            )
        ]

        new_sources_t = new_sources_t.reindex(columns=all_sources_dict[source_type.NAME].columns, fill_value=np.nan)

        all_sources_dict[source_type.NAME] = pd.concat(
            [
                all_sources_dict[source_type.NAME],
                new_sources_t
            ],
            axis=0,
            ignore_index=True
        )

        stage_new_sources_list.append(new_sources_t)
    
    stage_new_sources = pd.concat(
        stage_new_sources_list,
        axis=0,
        ignore_index=True,
        join='outer'
    )
    stage_new_sources.sort_values(by=[WaterSource.ID], inplace=True)

    return all_sources_dict, stage_new_sources

def append_new_pumping_stations(
        all_pstations_dict: Dict[str, pd.DataFrame],
        stage_new_sources_id: List[str],
        stage_idx: int
    ) -> Dict[str, pd.DataFrame]:

    # Add new pumping stations starting counting again but shifted by this stage index
    new_rows = pd.DataFrame(
        [
            {
                PumpingStation.ID: f"{PumpingStation.ID_PREFIX}{x:04d}",
                PumpingStation.SOURCE: source_id
            }
            for x, source_id in enumerate(
                stage_new_sources_id,
                start=STAGE_INDEX_SHIFT[stage_idx]+1
            )
        ]
    )

    # Concatenate with join='outer' to ensure all columns are present
    all_pstations_dict['entities'] = pd.concat(
        [all_pstations_dict['entities'], new_rows],
        axis=0,
        ignore_index=True,
        join='outer'
    )

    
    return all_pstations_dict

def append_new_supply_connections(
        all_cnns_dict: Dict[str, pd.DataFrame],
        stage_new_sources: pd.DataFrame,
        municipalities_lookup_df: pd.DataFrame,
        stage_idx: int
    ) -> Dict[str, pd.DataFrame]:

    stage_new_sources = stage_new_sources.set_index(WaterSource.ID)
    stage_new_sources['cnn_id'] = [ f"{SupplyConnection.ID_PREFIX}{x:04d}"
        for x in range(STAGE_INDEX_SHIFT[stage_idx]+1, STAGE_INDEX_SHIFT[stage_idx]+1+len(stage_new_sources))          
    ] 

    # Create new rows with only ID and assigned_source filled
    new_rows = []
    for source_id, source_info in stage_new_sources.iterrows():
        new_rows.append({
            SupplyConnection.ID: source_info['cnn_id'],
            SupplyConnection.FROM_NODE: source_id,
            SupplyConnection.TO_NODE: source_info[WaterSource.CLOS_M_ID],
            SupplyConnection.DISTANCE: geodesic(
                (source_info[WaterSource.LATITUDE], source_info[WaterSource.LONGITUDE]),
                tuple(municipalities_lookup_df.loc[
                    source_info[WaterSource.CLOS_M_ID],
                    [WaterSource.LATITUDE, WaterSource.LONGITUDE]
                ])
            ).m,
            SupplyConnection.MINORLOSSC: 0.0
        })
    new_rows = pd.DataFrame(new_rows)

    # Concatenate with join='outer' to ensure all columns are present, others will be NaN
    all_cnns_dict['sources'] = pd.concat(
        [all_cnns_dict['sources'], new_rows],
        axis=0,
        ignore_index=True,
        join='outer'
    )

    return all_cnns_dict

def main(previous_stage_results: Path, next_stage_inputs: Path, stage_number: int):
    
    prev_stage_file =  previous_stage_results / 'sources' / 'sources-static_properties.xlsx'
    all_sources_dict = pd.read_excel(prev_stage_file, sheet_name=None)

    prev_stage_file =  previous_stage_results / 'pumping_stations' / 'pumping_stations-static_properties.xlsx'
    all_pstations_dict = pd.read_excel(prev_stage_file, sheet_name=None)

    # Connections is the only file that we need to take from this stage and not
    # the previous one because it is first modified by municipalities
    prev_stage_file =  next_stage_inputs / 'connections' / 'connections-static_properties-temp.xlsx'
    all_cnns_dict = pd.read_excel(prev_stage_file, sheet_name=None)

    # Relative path to this script for the new sources file
    new_sources_file = '../sources/raw-data/new_sources.csv'
    all_new_sources = pd.read_csv(new_sources_file)

    # Helper file of the jurisdictions (to help calculate distances) has been 
    # created already in the next stage inputs.
    juris_file = next_stage_inputs / 'jurisdictions' / f'jurisdictions-static_properties-stage_{stage_number}.xlsx'
    municipalities_df = pd.read_excel(juris_file, sheet_name='municipalities', index_col='cbs_id')

    all_sources_dict, stage_new_sources = append_new_sources(
        all_sources_dict=all_sources_dict,
        all_new_sources=all_new_sources,
        stage_idx=stage_number-1
    )

    all_pstations_dict = append_new_pumping_stations(
        all_pstations_dict=all_pstations_dict,
        stage_new_sources_id=stage_new_sources[WaterSource.ID].to_list(),
        stage_idx=stage_number-1    
    )

    all_cnns_dict = append_new_supply_connections(
        all_cnns_dict=all_cnns_dict,
        stage_new_sources=stage_new_sources,
        municipalities_lookup_df=municipalities_df,
        stage_idx=stage_number-1
    )
    
    StaticProperties(
        name=f"sources-static_properties-stage_{stage_number}",
        dataframes=all_sources_dict
    ).dump(
        path=next_stage_inputs/'sources'
    )

    StaticProperties(
        name=f"pumping_stations-static_properties-stage_{stage_number}",
        dataframes=all_pstations_dict
    ).dump(
        path=next_stage_inputs/'pumping_stations'
    )

    StaticProperties(
        name=f"connections-static_properties-stage_{stage_number}",
        dataframes=all_cnns_dict
    ).dump(
        path=next_stage_inputs/'connections'
    )

    return

if __name__ == "__main__":
    # This script is intended to be run for each team to append new information
    # to the system's final status from the previous stage, producing new input files for the next stage.

    # Parse arguments: previous stage results directory and next stage input directory.
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate dynamic pipe options properties for stage 1 based on the previous stage's final status."
    )
    parser.add_argument(
        "stage_number",
        type=int,
        choices=[1,2,3],
        help="Stage of the compeition for which to generate the new data (1, 2, or 3)"
    )
    parser.add_argument(
        "previous_stage_results",
        type=Path,
        help="Path to the folder containing the final status of the system in the previous stage (absolute or relative to the current working directory)."
    )
    parser.add_argument(
        "next_stage_inputs",
        type=Path,
        help="Path to the output folder where the new input files for the next stage will be saved (absolute or relative to the current working directory)."
    )
    args = parser.parse_args()

    previous_stage_results = args.previous_stage_results
    if not previous_stage_results.is_absolute():
        previous_stage_results = Path(os.getcwd()) / previous_stage_results
    next_stage_inputs = args.next_stage_inputs
    if not next_stage_inputs.is_absolute():
        next_stage_inputs = Path(os.getcwd()) / next_stage_inputs

    # We work form this file directory to have all paths relative to this file.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main(previous_stage_results, next_stage_inputs, args.stage_number)
