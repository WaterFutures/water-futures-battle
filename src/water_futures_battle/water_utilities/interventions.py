from typing import Any, Dict, Set

import pandas as pd

from ..core import Settings
from ..core.utility import timestampify

from ..sources import WaterSource
from ..pumps import PumpOption
from ..pipes import PipeOption
from ..energy.entities import SolarFarm

from .entities import WaterUtility

class OpenSource:
    NAME = 'open_source'

    @classmethod
    def execute(
        cls, 
        water_utility: WaterUtility,
        year: int,
        intervention_desc: Dict[str, Any],
        pipe_options: Set[PipeOption],
        pump_options: Set[PumpOption],
        settings: Settings
    ) -> float:
        
        # Let's get the mandatory arguements
        source_id = intervention_desc[WaterSource.ID]
        source_capacity = intervention_desc['source_capacity']
        pump_option_id = intervention_desc[PumpOption.ID]
        n_pumps = intervention_desc['n_pumps']
        pipe_option_id = intervention_desc[PipeOption.ID]
        
        for source, (pumping_station, connection) in water_utility.m_supplies.items():

            if source.bwf_id != source_id:
                continue

            # We have found the source that we need to open.
            # However, it makes sense to open a source if it is closed and it was not 
            # never open before. 
            if source.is_active(when=year):
                raise ValueError(
                    f"Error applying the intervention 'OpenSource' for source {source_id} in water utility {water_utility.bwf_id} on year {year}",
                    f"Reason: the source is already active in this year."
                )
            
            # Source is not active, but it may have been closed already
            if pd.notna(source.closure_date):
                raise ValueError(
                    f"Error applying the intervention 'OpenSource' for source {source_id} in water utility {water_utility.bwf_id} on year {year}",
                    f"Reason: you can not re-open a closed source."
                )
            
            # We check that the source capacity is ok when we open it for production,
            # but here we search for the pipe option and pump option to install

            pump_option = next((po for po in pump_options if po.bwf_id == pump_option_id), None)
            if pump_option is None:
                raise ValueError(
                    f"Error applying the intervention 'OpenSource' for source {source_id} in water utility {water_utility.bwf_id} on year {year}",
                    f"No pump option found for ID {pump_option_id}."
                )
            
            if n_pumps <= 0:
                raise ValueError(
                    f"Error applying the intervention 'OpenSource' for source {source_id} in water utility {water_utility.bwf_id} on year {year}",
                    f"You need to install at least one pump."
                )
            
            pipe_option = next((po for po in pipe_options if po.bwf_id == pipe_option_id), None)
            if pipe_option is None:
                raise ValueError(
                    f"Error applying the intervention 'OpenSource' for source {source_id} in water utility {water_utility.bwf_id} on year {year}",
                    f"No pipe option found for ID {pipe_option_id}."
                )
            
            # At this point, we have validated all the inputs and it is time to 
            # do the intervention and track the cost
            # However, sources take some random time to be built, so we apply and 
            # return the costs to be paid upfront now, but everything is set in 
            # place to start working in the future.
            constr_start_date = timestampify(year)

            construction_time_rng = settings.get_random_generator('new_sources-construction_time')
            construction_time_bounds = source.construction_years_bounds

            constr_end_date = timestampify(year + int(construction_time_rng.integers(*construction_time_bounds)))
            
            source.open_production(
                when=constr_end_date,
                capacity=source_capacity,
                opex_vol_ene_factor_rng=settings.get_random_generator('new_sources-opex_vol_ene_factor')
            )

            table_unit_costs = source.construction_unit_costs.loc[constr_start_date]
            unit_cost = table_unit_costs[source.source_size_class]

            cost = source.nominal_capacity * unit_cost

            for _ in range(n_pumps):
                new_pump = pumping_station.install_pump(
                    pump_option=pump_option,
                    installation_date=constr_end_date,
                    decommission_date=None,
                    lifetime_rng=settings.get_random_generator('pumps-lifetime')
                )

                cost += new_pump._pump_option.unit_cost.loc[constr_start_date]
        
            
            new_pipe = connection.install_pipe(
                pipe_option=pipe_option,
                installation_date=constr_end_date,
                decommission_date=None,
                lifetime_rng=settings.get_random_generator('pipes-lifetime')
            )

            pipe_unit_cost = new_pipe._pipe_option.unit_cost.loc[constr_start_date]
            cost += pipe_unit_cost + connection.distance

            return cost

        # If we are here, it means we could not find the source. let's raise an error
        raise ValueError(f"Impossible to find source with ID '{source_id}' in water utility {water_utility.bwf_id} for opening it.")
            
class CloseSource:
    NAME = 'close_source'

    @classmethod
    def execute(
        cls, 
        water_utility: WaterUtility,
        year: int,
        intervention_desc: Dict[str, Any],
        settings: Settings
    ) -> float:
        
        # Let's get the mandatory arguements
        source_id = intervention_desc[WaterSource.ID]
        
        for source, (pumping_station, connection) in water_utility.m_supplies.items():

            if source.bwf_id != source_id:
                continue

            # We have found the source that we need to close, let's close the
            # connection, the pumping station and the source.
            if not source.is_active(when=year):
                raise ValueError(
                    f"Error applying the intervention 'CloseSource' for source {source_id} in water utility {water_utility.bwf_id} on year {year}",
                    f"Reason: the source is not active in this year."
                )
            
            # Since the source is active, the connection should have a pipe and 
            # the pumping stations at least a pump
            assert (
                connection.active_pipe(when=year) is not None and 
                pumping_station.active_pumps(when=year)
            ), "Error, closing a source that is active but is not connected (missing pipe in connection or pumps in pumping station)"

            connection.active_pipe(when=year).decommission(when=year)
            
            for pump in pumping_station.active_pumps(when=year).values():
                pump.decommission(when=year)

            source.close_production(when=year)

            # Done, no cost associated with closing a source
            return 0.0

        # If we are here, it means we could not find the source. let's raise an error
        raise ValueError(f"Impossible to find source with ID '{source_id}' in water utility {water_utility.bwf_id} for closing it.")

from .entities import Connection

class InstallPipe:
    NAME = 'install_pipe'

    @classmethod
    def execute(
        cls,
        water_utility: WaterUtility,
        year: int, 
        intervention_desc: Dict[str, Any],
        pipe_options: Set[PipeOption],
        settings: Settings
    ) -> float:
        
        cnn_id = intervention_desc[Connection.ID]
        pipe_option_id = intervention_desc[PipeOption.ID]
        pipe_inst_date = timestampify(year)

        connection = next((c for c in water_utility.connections if c.bwf_id == cnn_id), None)
        if connection is None:
            raise ValueError(f"Connection with id '{cnn_id}' not found in water utility {water_utility.bwf_id}.")

        if connection.replaced_by_cnn_id != '':
            raise ValueError(
                f"Impossible to install a pipe on connection {cnn_id}: This connection has been replaced by {connection.replaced_by_cnn_id}"
            )

        pipe_option = next((p for p in pipe_options if p.bwf_id == pipe_option_id), None)
        if pipe_option is None:
            raise ValueError(f"PipeOption with id '{pipe_option_id}' not found.")

        # before installing, if this connection replaces others, lets' decommision the pipes in the others first
        # we check only the first time 
        if not connection.has_active_pipe(when=year):
            for replaced_cnn_id in connection.replaces_cnn_ids:
                replaced_cnn = next(c for c in water_utility.connections if c.bwf_id == replaced_cnn_id)

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
        pipe_unit_cost = pipe_option.unit_cost.loc[pipe_inst_date]
        
        cost = pipe_unit_cost * connection.distance
        
        return cost

from ..sources import WaterSource
from ..pumps import PumpOption

class InstallPumps:
    NAME = 'install_pumps'

    _RNG_NAME = 'pumps-lifetime'

    @classmethod
    def execute(
        cls,
        water_utility: WaterUtility,
        year: int,
        intervention_desc: Dict[str, Any],
        pump_options: Set[PumpOption],
        settings: Settings
        ) -> float:

        source_id = intervention_desc[WaterSource.ID]
        pump_option_id = intervention_desc[PumpOption.ID]
        pump_inst_date = timestampify(year)

        pump_station = next((ps for ps in water_utility.pumping_stations if ps.source.bwf_id == source_id), None)
        if pump_station is None:
            raise ValueError(f"No pumping station found for source ID {source_id} in water utility {water_utility.bwf_id}")
        
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
    
from ..pumping_stations import PumpingStation

class InstallSolarFarm:
    NAME = 'install_solar'

    @classmethod
    def execute(
        cls,
        water_utility: WaterUtility,
        year: int,
        intervention_desc: Dict[str, Any],
        settings: Settings
        ) -> float:
            
            entity = None
            # Option 1, solar farm is connected to a Source
            if WaterSource.ID in intervention_desc:
                source_id = intervention_desc[WaterSource.ID]
                #check if the source id exists in the water utility, if not raise an error
                source = next((s for s in water_utility.sources if s.bwf_id == source_id), None)
                if source is None:
                    raise ValueError(f"No source found for ID {source_id} in water utility {water_utility.bwf_id}")
                
                entity = source
            
            # Option b, solar farm is connected to a pumping station
            elif PumpingStation.ID in intervention_desc:
                pumpst_id = intervention_desc[PumpingStation.ID]
                # Find the pumping station
                pumpst = next((ps for ps in water_utility.pumping_stations if ps.bwf_id == pumpst_id), None)
                if pumpst is None:
                    raise ValueError(f"No pumping station found for ID {pumpst_id} in water utility {water_utility.bwf_id}")
                
                entity = pumpst
                
            if entity is None: 
                raise ValueError(f"Error installing solar farm."
                                 f"No property '{WaterSource.ID}' or '{PumpingStation.ID}' found in the intervention description"
                )

            capacity = intervention_desc[SolarFarm.CAPACITY]
            
            #check if source capacity is not zero
            if capacity <= 0:
                raise ValueError(f"Invalid capacity {capacity} for solar farm. Must be a positive number.")

            solar_inst_date = timestampify(year)

            solar_farm = water_utility.install_solar_farm(
                capacity=capacity,
                installation_date=solar_inst_date,
                decommission_date= solar_inst_date + pd.DateOffset(years=25),
                connected_entity=entity
            )

            cost = solar_farm.capacity * solar_farm.construction_unit_costs.loc[solar_inst_date]

            return cost 
    

