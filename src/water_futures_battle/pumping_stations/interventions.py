from typing import Any, Dict, Set

from ..core import Settings
from ..core.utility import timestampify
from ..sources import WaterSource
from ..pumps import PumpOption
from ..pumping_stations import PumpingStation

class InstallPumps:
    NAME = 'install_pumps'

    _RNG_NAME = 'pumps-lifetime'

    @classmethod
    def execute(
        cls,
        intervention_desc: Dict[str, Any],
        year: int,
        pumping_stations: Set[PumpingStation],
        pump_options: Set[PumpOption],
        settings: Settings
        ) -> float:

        source_id = intervention_desc[WaterSource.ID]
        pump_option_id = intervention_desc[PumpOption.ID]
        pump_inst_date = timestampify(year)

        pump_station = next((ps for ps in pumping_stations if ps.source.bwf_id == source_id), None)

        if pump_station is None:
            raise ValueError(f"No pumping station found for source ID {source_id}")
        
        pump_option = next((po for po in pump_options if po.bwf_id == pump_option_id), None)
        if pump_option is None:
            raise ValueError(f"No pump option found for ID {pump_option_id}")
        
        if intervention_desc["behaviour"] not in ["replace","new"]:
             raise ValueError(f"Invalid behaviour {intervention_desc['behaviour']}. Must be 'replace' or 'new'.")

        if intervention_desc["behaviour"] == "replace":
            for pump in pump_station.active_pumps(year).values():
                pump.decommission(pump_option_id)
                
        cost = 0.0
        for _ in range(intervention_desc["n_pumps"]):
            
            pump = pump_station.install_pump(
                pump_option=pump_option,
                installation_date=pump_inst_date,
                lifetime_rng=settings.get_random_generator(cls._RNG_NAME)
            )
            
            cost += pump._pump_option.unit_cost.loc[pump_inst_date]
        
        return cost