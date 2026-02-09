from typing import Any, Dict, Set

from ..pipes import PipeOption

from .entities import NationalContext

def share_yearly_budget(
        budget: float,
        national_context: NationalContext,
        year: int,
        policy_desc: Dict[str, Any]
    ) -> Dict[str, float]:
    return {
        wu.bwf_id: 0.0
        for wu in sorted(national_context.water_utilities, key=lambda x: x.bwf_id)
    }

def work_on_connections(
        national_context: NationalContext,
        year: int,
        intervention_desc: Dict[str, Any],
        pipe_options: Set[PipeOption]
    ) -> Dict[str, float]:

    return {
        wu.bwf_id: 0.0
        for wu in sorted(national_context.water_utilities, key=lambda x: x.bwf_id)
    }
