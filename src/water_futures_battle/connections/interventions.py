from typing import Any, Dict, Set

from ..core import Settings
from ..core.utility import timestampify
from ..pipes import Pipe, PipeOption
from ..pipes.dynamic_properties import PipeOptionsDB
from .entities import Connection

class InstallPipe:
    NAME = 'install_pipe'

    _RNG_NAME = 'pipes-lifetime'

    @classmethod
    def execute(
        cls,
        intervention_desc: Dict[str, Any],
        year: int, 
        connections: Set[Connection],
        pipe_options: Set[PipeOption],
        settings: Settings
    ) -> float:
        
        cnn_id = intervention_desc[Connection.ID]
        pipe_option_id = intervention_desc[PipeOption.ID]
        pipe_inst_date = timestampify(year)

        connection = next((c for c in connections if c.bwf_id == cnn_id), None)
        if connection is None:
            raise ValueError(f"Connection with id '{cnn_id}' not found.")

        pipe_option = next((p for p in pipe_options if p.bwf_id == pipe_option_id), None)
        if pipe_option is None:
            raise ValueError(f"PipeOption with id '{pipe_option_id}' not found.")

        new_pipe = connection.install_pipe(
            pipe_option=pipe_option,
            installation_date=pipe_inst_date,
            lifetime_rng=settings.get_random_generator(cls._RNG_NAME)
        )

        # Calculate this new pipe cost because it will immediately influence the 
        # w. utility balance, while emission are calculated at the end of simulation
        # because they are independent
        pipe_unit_cost = pipe_option.unit_cost.loc[pipe_inst_date]
        
        cost = pipe_unit_cost * connection.distance
        
        return cost