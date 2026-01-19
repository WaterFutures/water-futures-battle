from typing import Dict, Set, Tuple

import pandas as pd

from ..jurisdictions.entities import State
from ..sources.entities import SourcesContainer
from ..pipes.dynamic_properties import PipeOptionsDB, PipesResults
from ..pipes.entities import Pipe, PipeOption
from .entities import Connection, SupplyConnection, PeerConnection

def build_piping_infrastructure(desc: Dict[str, str], a_state: State, sources: SourcesContainer) -> Tuple[Set[PipeOption], Set[Connection]]:

    # PIPE OPTIONS
    # open the dynamic properties, set the DB to be accessible from all the instances
    # then create the instances

    pipe_options_db = PipeOptionsDB.load_from_file(desc[PipeOptionsDB.NAME])
    PipeOption.set_dynamic_properties(pipe_options_db)

    pipe_options_data = pd.read_excel(
        desc['pipe_options-static_properties'],
        sheet_name=None
    )

    pipe_options_map: Dict[str, PipeOption] = {}
    for idx, option in pipe_options_data['options'].iterrows():
        pipe_option = PipeOption.from_row(row_data=option)

        pipe_options_map[pipe_option.bwf_id] = pipe_option

    # PIPES (objects) and CONNECTIONS (container of pipes)
    pipes_results = PipesResults()
    Pipe.set_results(pipes_results)

    connections_data = pd.read_excel(
        desc['connections-static_properties'],
        sheet_name=['provincial', 'sources', 'cross-provincial']
    )

    connections: Set[Connection] = set()
    for idx, conn_data in connections_data['sources'].iterrows():
        connections.add(
            SupplyConnection.from_row(
                row_data=conn_data,
                pipe_options_map=pipe_options_map,
                a_state=a_state,
                sources=sources
            )
        )

    for type_label in ['provincial', 'cross-provincial']:
        for idx, conn_data in connections_data[type_label].iterrows():
            connections.add(
                PeerConnection.from_row(
                    row_data=conn_data,
                    pipe_options_map=pipe_options_map,
                    a_state=a_state
                )
            )

    pipe_options = set(pipe_options_map.values())

    return pipe_options, connections