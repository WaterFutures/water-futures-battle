from dataclasses import dataclass
from typing import Any, Dict, Self, Set, Optional

import numpy as np
import pandas as pd

from ..core import Settings
from ..core.base_model import bwf_entity
from ..core.utility import BWFTimeLike, timestampify
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

    def is_active(self, when: BWFTimeLike) -> bool:
        """
        Returns True if the connection is active at the given time.
        Must be implemented by subclasses.
        """
        raise NotImplementedError(f"Subclass {self} must implement is_active()")

    def active_pipe(self, when: BWFTimeLike) -> Optional[Pipe]:
        """
        Returns the first pipe that is active at the given time.
        A pipe is active if:
        - installation_date <= when
        - (decommission_date is NaT or decommission_date > when)
        """
        ts = timestampify(when)

        for pipe in self.pipes.values():
            install = pipe.installation_date
            decomm = pipe.decommission_date
            if install <= ts and (pd.isna(decomm) or decomm > ts):
                return pipe
        return None

    def has_active_pipe(self, when: BWFTimeLike) -> bool:
        return self.active_pipe(when=when) != None
    
    def install_pipe(
            self,
            pipe_option: PipeOption, 
            installation_date: pd.Timestamp,
            decommission_date: Optional[pd.Timestamp] = None,
            lifetime_rng: Optional[np.random.Generator] = None
        ) -> Pipe:

        # We are installing a new pipe, this has name {my_id}-{counter:02d}
        # we start countign from 0 so let's just use len(installed)
        n_currently_installed_pipes = len(self.pipes)
        pipe_id = f"{self.bwf_id}-{n_currently_installed_pipes:02d}"

        # The user must either pass a decommision date (historical information)
        # or a random generator:
        # if none of the two is passed raise error 
        # if both are passed the second is ignored

        if decommission_date is None and lifetime_rng is None:
            raise ValueError(f"Impossible to install a pipe on connection {self.bwf_id}.",
                             "You need to pass either a decommision date or a random generator argument.")
        
        if decommission_date is not None and pd.notna(decommission_date):
            deco_date = decommission_date
            lifetime = -1 # like nan but the property is an int
        else:
            assert lifetime_rng is not None
            deco_date = pd.NaT
            lifetime = lifetime_rng.integers(*pipe_option.lifetime)

        # Before installing, let's see if the previously installed pipe needs to
        # be decommissioned (active pipe and with no date)
        if (self.has_active_pipe(installation_date) and 
            pd.isna(self.active_pipe(installation_date).decommission_date)):
            
            self.active_pipe(installation_date).decommission(when=installation_date)

        # "Order the pipe to the manufacturer"
        new_pipe = Pipe(
            bwf_id=pipe_id,
            _pipe_option=pipe_option,
            installation_date=installation_date,
            _decommission_date=deco_date,
            _sampled_lifetime=lifetime
        )

        # Actually install it
        self.pipes[len(self.pipes)] = new_pipe

        return new_pipe
    
    def inspect_and_replace(
            self,
            year: int,
            lifetime_rng: np.random.Generator
        ) -> float:

        # Nothing to do if there is no active pipe installed
        if not self.has_active_pipe(when=year):
            return 0.0
        
        # If there is a pipe, we get it and see if is failing this year
        active_pipe = self.active_pipe(when=year)
        assert active_pipe is not None

        if not active_pipe._is_failing_this_year(when=year):
            return 0.0

        # It is failing, so decommision it and open a new one
        active_pipe._fail()
        failed_pipe = active_pipe

        new_pipe = self.install_pipe(
            pipe_option=failed_pipe._pipe_option,
            installation_date=failed_pipe.decommission_date,
            lifetime_rng=lifetime_rng
        )

        pipe_unit_cost = new_pipe._pipe_option.unit_cost.loc[failed_pipe.decommission_date]
        
        cost = pipe_unit_cost * self.distance

        return cost


    def to_dict(self) -> Dict[str, Any]:
        install_dates = [
            p.installation_date.strftime('%Y-%m-%d')
            for p in self.pipes.values()
        ]

        r = {
            self.ID: self.bwf_id,
            self.TO_NODE: self.to_node.cbs_id,
            self.DISTANCE: self.distance,
            self.MINORLOSSC: self.minor_loss_coeff,
            self.P_INSTDATE: ';'.join(install_dates),
            self.P_OPTION: ';'.join([p._pipe_option.bwf_id for p in self.pipes.values()]),
        }

        return r


def get_pipe_collection(
    installation_dates_desc: str,
    option_ids_desc: str,
    pipe_options_map: Dict[str, PipeOption],
    bwf_id_prefix: str,
    settings:Settings
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
        # All pipes, except the last one are decommisioned, thus we put -1 (like we do in pipe_install)
        if i != len(pipe_options)-1:
            lifetime = -1
        else:
            lifetime = settings.get_random_generator('pipes-lifetime').integers(
                *pipe_option.lifetime
            )

        pipes[i] = Pipe(
            bwf_id=f"{bwf_id_prefix}-{i:02d}",
            _pipe_option=pipe_option,
            installation_date=install_dates[i],
            _decommission_date=decomis_dates[i],
            _sampled_lifetime=lifetime
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
    def from_row(
        cls,
        row_data: pd.Series,
        pipe_options_map: Dict[str, PipeOption],
        a_state: State,
        sources: SourcesContainer,
        settings: Settings
    ) -> Self:
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
                bwf_id_prefix=connection_id,
                settings=settings
            ),
            from_node=from_source
        )
    
    def is_active(self, when: BWFTimeLike) -> bool:
        """
        Supply connections gets deactivate the moment when the source gets deactivated
        because their to node is always passed along to the new one.
        
        :param self: Description
        :param when: Description
        :type when: BWFTimeLike
        :return: Description
        :rtype: bool
        """
        return self.from_node.is_active(when=when)

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict() | {self.FROM_NODE: self.from_node.bwf_id}

    
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
    def from_row(
        cls,
        row_data: pd.Series,
        pipe_options_map: Dict[str, PipeOption],
        a_state: State,
        settings: Settings
    ) -> Self:
        connection_id = str(row_data[Connection.ID])

        from_municipality = a_state.municipality(str(row_data[Connection.FROM_NODE]))
        to_municipality = a_state.municipality(str(row_data[Connection.TO_NODE]))

        return cls(
            bwf_id=connection_id,
            to_node=to_municipality,
            distance=float(row_data[Connection.DISTANCE]),
            minor_loss_coeff=float(row_data[Connection.MINORLOSSC]),
            pipes=get_pipe_collection(
                str(row_data[Connection.P_INSTDATE]),
                str(row_data[Connection.P_OPTION]),
                pipe_options_map=pipe_options_map,
                bwf_id_prefix=connection_id,
                settings=settings
            ),
            from_node=from_municipality
        )
    
    def is_provincial(self) -> bool:
        return self.from_node.province == self.to_node.province
    
    def is_cross_provincial(self) -> bool:
        return not self.is_provincial()
    
    def is_active(self, when: BWFTimeLike) -> bool:
        """
        Peer connections gets deactivate the moment when the both nodes gets merged 
        together.
        
        :param self: Description
        :param when: Description
        :type when: BWFTimeLike
        :return: Description
        :rtype: bool
        """
        if not self.from_node.has_open(when=when) or not self.to_node.has_open(when=when):
            return False
        
        # Confirmed that they have been at least opened, we can ask the effective
        # entity (otherwise it would raise an error)
        effective_from_n = self.from_node.effective_entity(when=when)
        effective_to_n = self.to_node.effective_entity(when=when)
        return effective_from_n != effective_to_n
    
    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict() | {self.FROM_NODE: self.from_node.cbs_id}
