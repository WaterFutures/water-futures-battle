import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from geopy.distance import geodesic
import numpy as np
import pandas as pd
import yaml

from water_futures_battle.core.base_model import StaticProperties
from water_futures_battle.jurisdictions.entities import Municipality
from water_futures_battle.connections.entities import PeerConnection, SelfLoopConnection

STAGE_YEARS = [
    ("2025-01-01", "2049-01-01"),
    ("2050-01-01", "2074-01-01"),
    ("2075-01-01", "2099-01-01"),
]
STAGE_INDEX_SHIFT = [4000, 5000, 6000] # here we have 4, 5, and 6 because 
# municipalities already arrive up to 19xx in the cbs id and connections use 3xxx
# for those new in 2025.

def append_date_if_needed(row: pd.Series, event_date: pd.Timestamp) -> str:
    """
    Helper function to transfrom a connection's pipe decommission date field.
    If a pipe is still active in the connection, it closes it at event date
    and returns the field formatted as a string.
    """
    p_installation_dates = [ pd.to_datetime(d)
        for d in str(row[PeerConnection.P_INSTDATE]).split(';')
        if d != 'nan' and d != ""
    ]
    p_decom_dates = [ pd.to_datetime(d)
        for d in str(row[PeerConnection.P_DECODATE]).split(';')
        if d != 'nan' and d != ""
    ]

    if len(p_installation_dates) == len(p_decom_dates):
        # nothing to do if they have the same length
        if pd.isna(row[PeerConnection.P_DECODATE]):
            return ""
        else:
            return str(row[PeerConnection.P_DECODATE])
    
    assert len(p_installation_dates) == len(p_decom_dates)+1

    p_decom_dates.append(event_date)

    return ';'.join([d.strftime('%Y-%m-%d') for d in p_decom_dates])

def get_stage_events(
        new_municipalities_events: Dict[str, Any],
        stage_idx: int
    ) -> Dict[str, Any]:
    """
    Given a dictionary of events (new_municipalities_events file content), filter
    by keeping only this stage's events.
    """
    # Get the date range for this stage
    start_date = pd.to_datetime(STAGE_YEARS[stage_idx][0])
    end_date = pd.to_datetime(STAGE_YEARS[stage_idx][1])

    def in_stage(a_date):
        return start_date <= pd.to_datetime(a_date) < end_date

    filtered = {}
    for event_type, events in new_municipalities_events.items():
        filtered_events = []
        for event in events:
            # Each event must have a 'date' field
            if 'date' in event and in_stage(event['date']):
                filtered_events.append(event)
        if filtered_events:
            filtered[event_type] = filtered_events
    return filtered

def update_municipalities(
        all_juris_dict: Dict[str, pd.DataFrame],
        stage_municipalities_event: Dict[str, Any],
        stage_idx: int
    ) -> Dict[str, pd.DataFrame]:
    """
    Append the new municipalities to the bottom and add the end dates for 
    the closing ones.
    """

    # Mergers
    def update_with_merger(df: pd.DataFrame, event_desc: Dict[str, Any], cbs_id: str) -> pd.DataFrame:
        """
        Update the municipalities dataframe with the info of a merger
        """
        df.loc[len(df)] = {
            'name': event_desc['name'],
            'cbs_id': cbs_id,
            Municipality.PROVINCE: event_desc[Municipality.PROVINCE],
            Municipality.BEGIN_DATE: event_desc['date'].strftime("%Y-%m-%d"),
            Municipality.LATITUDE: event_desc[Municipality.LATITUDE],
            Municipality.LONGITUDE: event_desc[Municipality.LONGITUDE],
            Municipality.ELEVATION: event_desc[Municipality.ELEVATION],
        }

        for closing_muni_id in event_desc['closing']:
            assert isinstance(closing_muni_id, str) and closing_muni_id.startswith('GM'), "Write the closing municipalities ID as a list of str"

            df.loc[
                df['cbs_id'] == closing_muni_id,
                [Municipality.END_DATE, Municipality.END_CBS_ID]
            ] = [event_desc['date'].strftime("%Y-%m-%d"), cbs_id]

        return df
    
    def update_with_absorption(df: pd.DataFrame, event_desc: Dict[str, Any]) -> pd.DataFrame:
        """
        Update the municipalities dataframe with the info of an absorption
        """
        for closing_muni_id in event_desc['closing']:
            assert isinstance(closing_muni_id, str) and closing_muni_id.startswith('GM'), "Write the closing municipalities ID as a list of str"

            df.loc[
                df['cbs_id'] == closing_muni_id,
                [Municipality.END_DATE, Municipality.END_CBS_ID]
            ] = [event_desc['date'].strftime("%Y-%m-%d"), event_desc['receiving_id']]

        return df
    
    municipalities_df = all_juris_dict['municipalities']
    
    for cbs_idx, event in enumerate(
        stage_municipalities_event.get('mergers', []),
        start=STAGE_INDEX_SHIFT[stage_idx]+1
    ):
        update_with_merger(
            df=municipalities_df,
            event_desc=event,
            cbs_id=f"{Municipality.ID_PREFIX}{cbs_idx:04d}"
        )

    for event in stage_municipalities_event.get('absorptions', []):
        update_with_absorption(
            df=municipalities_df,
            event_desc=event
        )

    all_juris_dict['municipalities'] = municipalities_df

    return all_juris_dict

def update_peer_connections(
        all_cnns_dict: Dict[str, pd.DataFrame],
        stage_municipalities_event: Dict[str, Any],
        municipalities_lookp_df: pd.DataFrame,
        stage_idx: int
    ) -> Dict[str, pd.DataFrame]:

    # Mergers
    def update_with_merger(
            df: pd.DataFrame,
            event_desc: Dict[str, Any],
            cbs_id: str,
            cnns_idx_shift: int
        ) -> Tuple[pd.DataFrame, int]:
        """
        Update the provicial connections dataframe with the info of a merger.
        Each closing municipality has a set of existing connections to other external municipalities 
        not involved in the merger.
        We create one new connection to the new municipality from each of these.
        """

        closing_municipalities_id = event_desc['closing']
        
        mask = (
            df[PeerConnection.FROM_NODE].isin(closing_municipalities_id) |
            df[PeerConnection.TO_NODE].isin(closing_municipalities_id) 
        ) & (
            pd.isna(df[PeerConnection.REPLACED_BY]) |
            (df[PeerConnection.REPLACED_BY] == "")
        )

        # get the list of municipalities involved with this merger
        # (untouched but connected to closing together with the closing ones)
        municipalities_involved = set(df.loc[mask, PeerConnection.FROM_NODE]).union(set(df.loc[mask, PeerConnection.TO_NODE]))
        # once we remove the closing municipalities, we are left with only the 
        # municipalities surrounding the merger
        extern_municipalities = municipalities_involved - set(closing_municipalities_id)

        # for each of these extern municipalities we need one new connection to 
        # the new municipality and close/update the old ones that are being modified
        for ext_m in sorted(extern_municipalities):
            # new one:
            new_cnn_id = f"CG{cnns_idx_shift:04d}"
            
            disappearing_cnns_mask = (
                (
                    (df[PeerConnection.FROM_NODE] == ext_m) &
                    df[PeerConnection.TO_NODE].isin(closing_municipalities_id)
                ) | (
                    (df[PeerConnection.TO_NODE] == ext_m) &
                    df[PeerConnection.FROM_NODE].isin(closing_municipalities_id)
                )
            )

            disappearing_cnns_id = df.loc[disappearing_cnns_mask, PeerConnection.ID].to_list()

            df.loc[disappearing_cnns_mask, PeerConnection.REPLACED_BY] = new_cnn_id
            df.loc[disappearing_cnns_mask, PeerConnection.P_DECODATE] = df.loc[
                disappearing_cnns_mask, 
                [PeerConnection.P_INSTDATE, PeerConnection.P_DECODATE]].apply(
                lambda row: append_date_if_needed(row, pd.to_datetime(event_desc['date'])),
                axis=1
            )

            df.loc[len(df)] = {
                PeerConnection.ID: new_cnn_id,
                PeerConnection.FROM_NODE: ext_m,
                PeerConnection.TO_NODE: cbs_id,
                PeerConnection.DISTANCE: geodesic(
                    tuple(municipalities_lookp_df.loc[ext_m, [Municipality.LATITUDE, Municipality.LONGITUDE]]),
                    tuple(municipalities_lookp_df.loc[cbs_id, [Municipality.LATITUDE, Municipality.LONGITUDE]])
                ).m,
                PeerConnection.MINORLOSSC: 0.0,
                PeerConnection.REPLACES: ';'.join(disappearing_cnns_id)
            }

            cnns_idx_shift += 1
        
        return df, cnns_idx_shift
    
    def update_with_absorption(df: pd.DataFrame, event_desc: Dict[str, Any]) -> pd.DataFrame:
        """
        Update the provincial connections dataframe with the info of an absorption.
        When a municipality gets absorbed, all the connections between the receiving
        and the closing municipality, or between the closing municipality itself, 
        become hidden, aka SELF_LOOP.
        """
        involved_municipalities_id = event_desc['closing'] + [event_desc['receiving_id']]

        # Create a mask where both nodes are in the involved_ids list
        mask = df[PeerConnection.FROM_NODE].isin(involved_municipalities_id) & df[PeerConnection.TO_NODE].isin(involved_municipalities_id)

        df.loc[mask, PeerConnection.REPLACED_BY] = SelfLoopConnection.LABEL
        df.loc[mask, PeerConnection.P_DECODATE] = df.loc[
            mask, 
            [PeerConnection.P_INSTDATE, PeerConnection.P_DECODATE]].apply(
            lambda row: append_date_if_needed(row, pd.to_datetime(event_desc['date'])),
            axis=1
        )

        return df
    
    cnns_df = all_cnns_dict['provincial']

    new_cnns_index_shift = STAGE_INDEX_SHIFT[stage_idx]+1
    for cbs_idx, event in enumerate(
        stage_municipalities_event.get('mergers', []),
        start=STAGE_INDEX_SHIFT[stage_idx]+1
    ):
        cnns_df, new_cnns_index_shift = update_with_merger(
            df=cnns_df,
            event_desc=event,
            cbs_id=f"{Municipality.ID_PREFIX}{cbs_idx:04d}",
            cnns_idx_shift=new_cnns_index_shift
        )

    for event in stage_municipalities_event.get('absorptions', []):
        update_with_absorption(
            df=cnns_df,
            event_desc=event
        )

    all_cnns_dict['provincial'] = cnns_df

    return all_cnns_dict

def main(previous_stage_results: Path, next_stage_inputs: Path, stage_number: int):
    
    prev_stage_file =  previous_stage_results / 'jurisdictions' / 'jurisdictions-static_properties.xlsx'
    all_juris_dict = pd.read_excel(prev_stage_file, sheet_name=None)

    prev_stage_file =  previous_stage_results / 'connections' / 'connections-static_properties.xlsx'
    all_cnns_dict = pd.read_excel(prev_stage_file, sheet_name=None)

    # Relative path to this script for the new municipalities file
    with open('../jurisdictions/raw-data/new_municipalities_events.yaml', 'r') as f:
        new_municipalities_events = yaml.safe_load(f)

    stage_municipalities_event = get_stage_events(new_municipalities_events, stage_number-1)

    all_juris_dict = update_municipalities(
        all_juris_dict=all_juris_dict,
        stage_municipalities_event=stage_municipalities_event,
        stage_idx=stage_number-1
    )

    all_cnns_dict = update_peer_connections(
        all_cnns_dict=all_cnns_dict,
        stage_municipalities_event=stage_municipalities_event,
        municipalities_lookp_df=all_juris_dict['municipalities'].set_index('cbs_id'),
        stage_idx=stage_number-1
    )

    StaticProperties(
        name=f"jurisdictions-static_properties-stage_{stage_number}",
        dataframes=all_juris_dict
    ).dump(
        path=next_stage_inputs/'jurisdictions'
    )

    StaticProperties(
        name=f"connections-static_properties-temp",
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
