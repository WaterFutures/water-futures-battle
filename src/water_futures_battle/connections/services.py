import os
from pathlib import Path
from typing import Any, Dict, Set, Tuple

import numpy as np
import pandas as pd

from ..core import Settings
from ..core.base_model import StaticProperties
from ..jurisdictions.entities import State
from ..sources.entities import SourcesContainer
from ..pipes.dynamic_properties import PipeOptionsDB, PipesDB, PipesResults
from ..pipes.entities import Pipe, PipeOption
from .entities import Connection, SupplyConnection, PeerConnection

def build_piping_infrastructure(
        desc: Dict[str, str],
        a_state: State, sources:
        SourcesContainer,
        data_path: str,
        settings: Settings
        ) -> Tuple[Set[PipeOption], Set[Connection]]:

    # PIPE OPTIONS
    # open the dynamic properties, set the DB to be accessible from all the instances
    # then create the instances

    pipe_options_db = PipeOptionsDB.load_from_file(os.path.join(data_path, desc[PipeOptionsDB.NAME]))
    PipeOption.set_dynamic_properties(pipe_options_db)

    pipe_options_data = pd.read_excel(
        os.path.join(data_path, desc['pipe_options-static_properties']),
        sheet_name=None
    )

    pipe_options_map: Dict[str, PipeOption] = {}
    for idx, option in pipe_options_data['options'].iterrows():
        pipe_option = PipeOption.from_row(row_data=option)

        pipe_options_map[pipe_option.bwf_id] = pipe_option

    # PIPES (objects) and CONNECTIONS (container of pipes)
    pipes_db = PipesDB.load_from_file(os.path.join(data_path, desc[PipesDB.NAME]))
    Pipe.set_dynamic_properties(pipes_db)

    pipes_results = PipesResults()
    Pipe.set_results(pipes_results)

    connections_data = pd.read_excel(
        os.path.join(data_path, desc['connections-static_properties']),
        sheet_name=['provincial', 'sources', 'cross-provincial']
    )

    connections: Set[Connection] = set()
    for idx, conn_data in connections_data['sources'].iterrows():
        connections.add(
            SupplyConnection.from_row(
                row_data=conn_data,
                pipe_options_map=pipe_options_map,
                a_state=a_state,
                sources=sources,
                settings=settings
            )
        )

    for type_label in ['provincial', 'cross-provincial']:
        for idx, conn_data in connections_data[type_label].iterrows():
            connections.add(
                PeerConnection.from_row(
                    row_data=conn_data,
                    pipe_options_map=pipe_options_map,
                    a_state=a_state,
                    settings=settings
                )
            )

    # Sort the friction factors of the new installed pipes
    Pipe._dynamic_properties[PipesDB.FRICTIONF].sort_index(inplace=True)

    pipe_options = set(pipe_options_map.values())

    return pipe_options, connections

def age_pipes(
        connections: Set[Connection],
        year: int,
        pipe_ageing_rng: np.random.Generator
    )-> None:
    """
    Age by one year all active pipes in the passed connections.
    
    :param connections: Description
    :type connections: Set[Connection]
    :param year: Description
    :type year: int
    :param pipe_options_db: Description
    :type pipe_options_db: PipeOptionsDB
    """

    # Track a few properties to vectorize the set operation
    pipe_ids = []
    pipe_dec_rate_lb = []
    pipe_dec_rate_ub = []
    
    for connection in sorted(connections, key= lambda c: c.bwf_id):

        pipe = connection.active_pipe(when=year)

        # If connection doesn't have installed pipes, nothing to do
        if pipe is None:
            continue

        # If pipe is changing next year, this is the last year so we ignore it
        if connection.active_pipe(when=year+1) != pipe:
            continue

        # Else, we know next year is still there and we are ageing it.
        pipe_ids.append(pipe.bwf_id)
        pipe_dec_rate_lb.append(pipe._pipe_option.dff_decay_rate[0])
        pipe_dec_rate_ub.append(pipe._pipe_option.dff_decay_rate[1])

    # complete the ageing process in a vectorized fashion
    rnd_sample = pipe_ageing_rng.uniform(low=0, high=1, size=len(pipe_ids))
    decay_low = np.array(pipe_dec_rate_lb)
    decay_high = np.array(pipe_dec_rate_ub)
    
    decay = decay_low + (decay_high-decay_low)*rnd_sample

    ff_df = Pipe._dynamic_properties[PipesDB.FRICTIONF]

    ts = pd.Timestamp(year=year, month=1, day=1)
    base_values = ff_df.loc[ts, pipe_ids]

    Nts = pd.Timestamp(year=year+1, month=1, day=1)
    updated_values = base_values.values + decay
    ff_df.loc[Nts, pipe_ids] = updated_values

    return

def dump_piping_infrastructure(
        all_connections: Set[Connection],
        pipe_options: Set[PipeOption],
        output_dir: Path
    )-> Dict[str, Any]:

    full_out_dir_cnns = output_dir / "connections"
    full_out_dir_pipe = output_dir / "pipes"
    def as_rel_path(a_path: Path) -> str:
        return os.path.relpath(a_path, output_dir)

    provincial_df = pd.DataFrame(data=[c.to_dict() for c in all_connections
                                       if isinstance(c, PeerConnection) and c.is_provincial() is True])

    sources_df = pd.DataFrame(data=[c.to_dict() for c in all_connections if isinstance(c, SupplyConnection)])

    cross_provincial_df = pd.DataFrame(data=[c.to_dict() for c in all_connections
                                       if isinstance(c, PeerConnection) and c.is_cross_provincial() is True])

    def reordered(df: pd.DataFrame):
        new_order = [df.columns[0], df.columns[-1]]+list(df.columns[1:-1])
        df = df[new_order]

        df = df.sort_values(by=Connection.ID)
        return df

    connections_df = {
        'provincial': reordered(provincial_df),
        'sources': reordered(sources_df),
        'cross-provincial': reordered(cross_provincial_df)
    }

    connections_properties = StaticProperties(
        name="connections-static_properties",
        dataframes=connections_df
    )

    pipe_options_df = pd.DataFrame(data=[p.to_dict() for p in pipe_options]).sort_values(PipeOption.ID)

    pipe_options_properties = StaticProperties(
        name="pipe_options-static_properties",
        dataframes={'options': pipe_options_df}
    )

    sp_path_cnns = connections_properties.dump(full_out_dir_cnns)
    sp_path_po = pipe_options_properties.dump(full_out_dir_pipe)

    dp_path_pi = Pipe._dynamic_properties.dump(full_out_dir_pipe)
    dp_path_po = PipeOption._dynamic_properties.dump(full_out_dir_pipe)

    return {
        connections_properties.name: as_rel_path(sp_path_cnns),
        PipesDB.NAME: as_rel_path(dp_path_pi),
        pipe_options_properties.name: as_rel_path(sp_path_po),
        PipeOptionsDB.NAME: as_rel_path(dp_path_po)
    }
