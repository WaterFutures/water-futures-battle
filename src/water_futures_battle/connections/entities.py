from dataclasses import dataclass
from typing import Dict, Self, Set

import pandas as pd

from ..base_model import bwf_entity
from ..jurisdictions import Municipality, State
from ..sources.entities import SourcesContainer
from ..sources import WaterSource
from ..pipes import Pipe, PipeOption
from ..pipes.entities import OrderedPipesCollection

@dataclass(frozen=True)
class Connection:
    """
    Represents a connections between two nodes. 
    It can be both between municipalities and between a municipality and a source.
    It can be both intra-provincial and inter-provincial.
    """
    # Unique identifier of the BWF, is used also for hashing and equality purposes
    bwf_id: str
    ID = 'connection_id'
    # ID Prefix depends on type

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Connection):
            return NotImplemented
        return self.bwf_id == value.bwf_id
    
    def __hash__(self) -> int:
        return hash(self.bwf_id)
    
    # To node is always a municipality, but the from node type depends
    FROM_NODE = 'from_node'
    to_node: Municipality
    TO_NODE = 'to_node'

    distance: float
    DISTANCE = 'distance'

    minor_loss_coeff: float
    MINORLOSSC = 'minor_loss_coefficient'

    # Collection of pipes installed on this connection over time
    pipes: OrderedPipesCollection
    # Completely described by 2 properties: option, installation.
    # decommission date is the new pipe installation date
    P_OPTION = 'pipes-option_ids'
    P_INSTDATE = 'pipes-installation_dates'

def get_pipe_collection(
    installation_dates_desc: str,
    option_ids_desc: str,
    pipe_options_map: Dict[str, PipeOption],
    bwf_id_prefix: str
) -> OrderedPipesCollection:
    
    if len(installation_dates_desc) == 0 or installation_dates_desc == 'nan':
        return {}

    pipe_options = [pipe_options_map[oid] for oid in option_ids_desc.split(';')]

    # Since only one pipe can be installed on each connection, every pipe replaces the previoys one 
    install_dates = [pd.to_datetime(d, errors='raise') for d in installation_dates_desc.split(';')]
    decomis_dates = install_dates[1:] + [pd.NaT]  # Add extra NaT at the end
    
    assert len(pipe_options) == len(install_dates) == len(decomis_dates), (
        f"Lengths for pipe collecion don't match: option_ids={len(pipe_options)}, install_dates={len(install_dates)}, decomis_dates={len(decomis_dates)}"
    )

    pipes: Dict[int, Pipe] = {}
    for i, pipe_option in enumerate(pipe_options):
        pipes[i] = Pipe(
            bwf_id=f"{bwf_id_prefix}-{i:02d}",
            _pipe_option=pipe_option,
            installation_date=install_dates[i],
            decommission_date=decomis_dates[i]
        )

    return pipes

@dataclass(frozen=True, eq=False, unsafe_hash=False)
class SupplyConnection(Connection):
    """
    Represents a connection from a source to a municipality.
    It is intraprovince by definition.
    """
    NAME = 'supply_connection'
    ID_PREFIX = 'CS'

    from_node: WaterSource
    
    @classmethod
    def from_row(cls, row_data: pd.Series, pipe_options_map: Dict[str, PipeOption], a_state: State, sources: SourcesContainer) -> Self:
        """
        Primary static constructor from row data.
        """
        connection_id = str(row_data[Connection.ID])

        from_source = sources.entity(str(row_data[Connection.FROM_NODE]))
        to_municipality = a_state.municipality(str(row_data[Connection.TO_NODE]))
        assert from_source.province == to_municipality.province

        return cls(
            bwf_id=connection_id,
            to_node=to_municipality,
            distance=float(row_data[Connection.DISTANCE]),
            minor_loss_coeff=float(row_data[Connection.MINORLOSSC]),
            pipes=get_pipe_collection(
                str(row_data[Connection.P_INSTDATE]),
                str(row_data[Connection.P_OPTION]),
                pipe_options_map=pipe_options_map,
                bwf_id_prefix=connection_id
            ),
            from_node=from_source
        )
    
@dataclass(frozen=True, eq=False, unsafe_hash=False)  
class PeerConnection(Connection):
    """
    Represents a connection between municipalities.
    It can be either interprovince or intraprovince.
    """
    from_node: Municipality

    @property
    def ID_PREFIX(self) -> str:
        if self.is_provincial():
            return 'CG'
        else:
            return 'CP'

    @classmethod
    def from_row(cls, row_data: pd.Series, pipe_options_map: Dict[str, PipeOption], a_state: State) -> Self:
        connection_id = str(row_data[Connection.ID])

        from_municipality = a_state.municipality(str(row_data[Connection.TO_NODE]))
        to_municipality = a_state.municipality(str(row_data[Connection.FROM_NODE]))

        return cls(
            bwf_id=connection_id,
            to_node=to_municipality,
            distance=float(row_data[Connection.DISTANCE]),
            minor_loss_coeff=float(row_data[Connection.MINORLOSSC]),
            pipes=get_pipe_collection(
                str(row_data[Connection.P_INSTDATE]),
                str(row_data[Connection.P_OPTION]),
                pipe_options_map=pipe_options_map,
                bwf_id_prefix=connection_id
            ),
            from_node=from_municipality
        )
    
    def is_provincial(self) -> bool:
        return self.from_node.province == self.to_node.province
    
    def is_cross_provincial(self) -> bool:
        return not self.is_provincial()