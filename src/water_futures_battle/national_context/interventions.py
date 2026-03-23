
from typing import Any, Dict, Set, Tuple


from ..core import Settings
from ..core.utility import timestampify
from ..pipes import PipeOption
from ..connections.entities import Connection 
from ..water_utilities import WaterUtility
from .entities import NationalContext 
class InstallPipe:
    NAME = 'install_pipe'

    @classmethod
    def execute(
        cls,
        national_context: NationalContext,
        year: int, 
        intervention_desc: Dict[str, Any],
        pipe_options: Set[PipeOption],
        settings: Settings
    ) -> Tuple[float, float, Tuple[WaterUtility, WaterUtility]]:
        
        cnn_id = intervention_desc[Connection.ID]
        pipe_option_id = intervention_desc[PipeOption.ID]
        pipe_inst_date = timestampify(year)

        connection = next((c for c in national_context.cross_utility_connections if c.bwf_id == cnn_id), None)
        if connection is None:
            raise ValueError(f"Connection with id '{cnn_id}' not found in national context.")
        pipe_option = next((p for p in pipe_options if p.bwf_id == pipe_option_id), None)
        if pipe_option is None:
            raise ValueError(f"PipeOption with id '{pipe_option_id}' not found.")

        # before installing, if this connection replaces others, lets' decommision the pipes in the others first
        # we check only the first time 
        if not connection.has_active_pipe(when=year):
            for replaced_cnn_id in connection.replaces_cnn_ids:
                replaced_cnn = next(c for c in national_context.cross_utility_connections if c.bwf_id == replaced_cnn_id)

                repl_cnn_active_pipe = replaced_cnn.active_pipe(when=year)
                if repl_cnn_active_pipe is not None:
                    repl_cnn_active_pipe.decommission(when=year)

        new_pipe = connection.install_pipe(
            pipe_option=pipe_option,
            installation_date=pipe_inst_date,
            lifetime_rng=settings.pipes_lifetime_rng
        )

        # Calculate this new pipe cost because it will immediately influence the 
        # w. utility balance, while emission are calculated at the end of simulation
        # because they are independent
        pipe_unit_cost = float(pipe_option.unit_cost.loc[pipe_inst_date])
        pipe_emb_ghg = float(pipe_option.embodied_emssions.asof(pipe_inst_date))
        
        cost = pipe_unit_cost * connection.distance
        emiss = pipe_emb_ghg * connection.distance

        #find which water utilities are connected 
        wu_from = next((wu
                         for wu in national_context.water_utilities
                         if connection.from_node in wu.municipalities
        ))
    
        wu_to = next((wu
                    for wu in national_context.water_utilities
                    if connection.to_node in wu.municipalities
        ))

        return cost, emiss, (wu_from, wu_to)
