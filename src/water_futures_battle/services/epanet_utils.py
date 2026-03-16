from typing import Dict, Optional, Set, Tuple

import itertools
from epanet_plus import EPyT, EpanetConstants
from geographiclib.geodesic import Geodesic as Geo
from epyt_flow.simulation import ScenarioSimulator, EPyT, CustomControlModule, ScadaData
from epyt_flow.utils import to_seconds
import numpy as np
import pandas as pd

from ..core.utility import timestampify
from ..water_utilities import WaterUtility
from ..sources import WaterSource
from ..connections.entities import PeerConnection, SupplyConnection
from ..pumping_stations.entities import PumpingStation, PumpOption


class FlowControlValve(CustomControlModule):
    def __init__(self, nominal_capacity: float, valve_id: str, valve_idx: int,
                 reporting_time_step: int = to_seconds(hours=1), **kwds):
        self.__valve_id = valve_id
        self.__valve_idx = valve_idx
        self.__nominal_capacity = nominal_capacity
        self.__reporting_time_step = reporting_time_step

        self.__t_idx = 0
        self.__productions = [0 for _ in range(23)]

        super().__init__(**kwds)

    def step(self, scada_data: ScadaData) -> None:
        if scada_data.sensor_readings_time[0] % self.__reporting_time_step == 0:
            cur_flow = scada_data.get_data_flows([self.__valve_id])[0][0]  # m^3/h
            if self.__t_idx >= 23:
                cap = self.__nominal_capacity - sum(self.__productions)
                self._epanet_api.setlinkvalue(self.__valve_idx, EpanetConstants.EN_SETTING, cap)

            self.__productions[self.__t_idx % 23] = cur_flow
            self.__t_idx += 1


def run_sim(
        f_inp_in,
        cluster_sources: Set[WaterSource],
        cross_utility_pipes_id: list[str],
        date_range: pd.DatetimeIndex,
        pumping_station_representation: str
    ) -> Dict[str, pd.DataFrame]:

    with ScenarioSimulator(f_inp_in=f_inp_in) as sim:
        pumps_id = sim.epanet_api.get_all_pumps_id()
        juncs_id = [j for j in sim.epanet_api.get_all_junctions_id() if j.startswith('GM')]

        sim.place_demand_sensors_everywhere()
        sim.place_flow_sensors_everywhere()
        if pumping_station_representation != "single_gpv":
            sim.place_pump_sensors_everywhere()
        else:
            pumps_id = sim.epanet_api.get_all_reservoirs_id() # Dummy pump (placeholder) for each reservoir

        if pumping_station_representation == "chocked_parallel_pumps":
            # Add flow control valve
            for source_id in sim.epanet_api.get_all_reservoirs_id():
                valve_id = f'{source_id}-cap'
                valve_idx = sim.epanet_api.get_link_idx(valve_id)

                # Temp to subsitute what was there before (the dict) but it is not done
                # just like this. Is more complicated... 
                source = next(s for s in cluster_sources if s.bwf_id == source_id)

                # The source has a nominal capacity, this is reduced by the
                # TODO: discuss with Dennis the detailed implementation including availability
                # factor.
                # Can we pass directly a reference to the source object?

                sim.add_custom_control(FlowControlValve(source.nominal_capacity, valve_id, valve_idx))

        # Setup the results that we need to return before running
        df_juncs_demands = pd.DataFrame(
            np.full((len(date_range), len(juncs_id)), np.nan),
            columns=juncs_id,
            index=date_range
        )
        df_pumps_energyconsumption = pd.DataFrame(
            np.full((len(date_range), len(pumps_id)), np.nan),
            columns=pumps_id,
            index=date_range
        )
        df_cross_utilities_flows = pd.DataFrame(
            np.full((len(date_range), len(cross_utility_pipes_id)), np.nan),
            columns=cross_utility_pipes_id,
            index=date_range
        )
        MEASUREMENTS_KEYS = [
            "juncs_demands",
            "pumps_energyconsumption",
            "cross_utilities_flows"
        ]

        scada_data = sim.run_simulation()
        if len(scada_data.warnings_code) <= 1: # Smth. went wrong when running the simulation (e.g., Error 233: network has unconnected nodes)
            return dict(zip(MEASUREMENTS_KEYS, [
                df_juncs_demands,
                df_pumps_energyconsumption,
                df_cross_utilities_flows
            ]))

        junc_demands = scada_data.get_data_demands(juncs_id)
        n_sim_steps = len(junc_demands)

        if n_sim_steps > 0:
            df_juncs_demands.iloc[:n_sim_steps, :] = junc_demands

            if pumping_station_representation != "single_gpv":
                df_pumps_energyconsumption.iloc[:n_sim_steps, :] = scada_data.get_data_pumps_energyconsumption(pumps_id)    # kwatt - hours
            else:
                df_pumps_energyconsumption.iloc[:n_sim_steps, :] = None

            df_cross_utilities_flows.iloc[:n_sim_steps, :] = scada_data.get_data_flows(cross_utility_pipes_id)

        return dict(zip(MEASUREMENTS_KEYS, [
                df_juncs_demands,
                df_pumps_energyconsumption,
                df_cross_utilities_flows
            ]))


def apply_demand_patterns(
        net: EPyT,
        demands: pd.DataFrame,
    ) -> EPyT:
    all_patterns = net.get_all_patterns_id()

    num_hours = len(demands) - 1
    net.set_simulation_duration(num_hours * 60 * 60)

    for junc_id in net.get_all_junctions_id():
        junc_idx = net.get_node_idx(junc_id)

        if junc_id in demands:

            demand_pattern_id = f"{junc_id}-demands"

            if demand_pattern_id in all_patterns:
                pattern_idx = net.get_node_pattern_idx(junc_idx)
                net.deletepattern(pattern_idx)

            node_demands = demands[junc_id].to_list()
            net.add_pattern(demand_pattern_id, node_demands)
            elev = net.get_node_elevation(junc_idx)
            net.setjuncdata(junc_idx, elev, 1, demand_pattern_id)

    return net


def apply_electricity_info(
        net: EPyT,
        electricity_price: float,
        electricity_pattern: pd.Series,
    ) -> EPyT:

    #TODO: set globale price and pattern

    return net


def build_epanet_network(
    year: int,
    water_utilities: Set[WaterUtility],
    cross_utility_connections: Set[PeerConnection],
    pumping_station_representation: str,
    epyt_kwargs: Optional[Dict] = None,
) -> EPyT:

    if epyt_kwargs is None:
        epyt_kwargs = {}

    ts = timestampify(year, errors='raise')

    net = EPyT(use_project=True, **epyt_kwargs)

    net.setflowunits(EpanetConstants.EN_CMH)
    net.setoption(EpanetConstants.EN_HEADLOSSFORM, EpanetConstants.EN_DW)
    #net.set_simulation_duration(365*24*60*60)
    net.set_hydraulic_time_step(60*60)
    net.settimeparam(EpanetConstants.EN_PATTERNSTEP, 60*60)

    net.set_demand_model(model_type=EpanetConstants.EN_PDA, pmin=15, preq=30, pexp=0.5)

    # Find the municipalities in that year
    municipalities = set().union(*[itertools.chain(utility.active_municipalities(year)) for utility in water_utilities])

    # Find all the peer connections
    peer_connections: Set[PeerConnection] = set()
    for wu in water_utilities:
        for con in wu.m_peer_connections:
            if con.is_active(when=year):
                peer_connections.add(con)
    peer_connections = peer_connections.union(cross_utility_connections)

    # Find the sources in that year
    sources: Set[WaterSource] = set()
    pump_options: Set[PumpOption] = set()
    pumping_stations_map: Dict[WaterSource, Tuple[PumpingStation, SupplyConnection]] = {}
    for utility in water_utilities:
        for ws, (ps, con) in utility.m_supplies.items():
            if ws.is_active(year):
                sources.add(ws)
                if ps.has_active_pumps(year):
                    pumping_stations_map[ws] = (ps, con)

                    for p in ps.active_pumps(year).values():
                        pump_options.add(p._pump_option)

    # Build network
    for m in municipalities:
        elem_name = m.cbs_id

        #demands = m._results["demand"][elem_name]
        #demands = demands.loc[demands.index.year == year]
        #node_demands = demands.to_numpy().flatten().tolist()

        elem_idx = net.addnode(elem_name, EpanetConstants.EN_JUNCTION)
        net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION, m.elevation)
        net.setcoord(elem_idx, x=m.longitude, y=m.latitude)

        #demand_pattern_id = f"{elem_name}-demands"
        #net.add_pattern(demand_pattern_id, node_demands)
        #pattern_idx = net.get_node_pattern_idx(elem_idx)
        #net.setjuncdata(elem_idx, m.elevation, 1, demand_pattern_id)

    for p_option in pump_options:
        #---- Pump curve
        pumpcurve_name = f"{p_option.bwf_id}-hc"

        net.addcurve(pumpcurve_name)
        elem_idx = net.getcurveindex(pumpcurve_name)

        net.setcurvetype(elem_idx, EpanetConstants.EN_PUMP_CURVE)
        net.setcurve(
            elem_idx,
            list(p_option.head_curve.index),
            list(p_option.head_curve.values),
            len(p_option.head_curve)
        )

        #---- Effic curve
        efficcurve_name = f"{p_option.bwf_id}-ec"

        net.addcurve(efficcurve_name)
        elem_idx = net.getcurveindex(efficcurve_name)

        net.setcurvetype(elem_idx, EpanetConstants.EN_EFFIC_CURVE)
        net.setcurve(
            elem_idx,
            list(p_option.eff_curve.index),
            list(p_option.eff_curve.values),
            len(p_option.eff_curve)
        )

        #---- Patterns for pumps
        pattern_name = f"{p_option.bwf_id}-pa"
        net.add_pattern(pattern_id=pattern_name, pattern_values=[1.0])
        elem_idx = net.getpatternindex(pattern_name)

    double_element_ps = (pumping_station_representation == "chocked_parallel_pumps")
    gpv_as_ps = (pumping_station_representation == "single_gpv")

    for source, (pumping_station, con) in pumping_stations_map.items():
        if not source.is_active(year):
            continue

        source_id = source.bwf_id

        pipe = con.active_pipe(year)
        assert pipe is not None
        municipality = con.to_node.effective_entity(year)

        pumps = pumping_station.active_pumps(when=year)

        elem_idx = net.addnode(source_id, EpanetConstants.EN_RESERVOIR)
        net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION, value=source.elevation)
        net.setcoord(elem_idx, x=source.longitude, y=source.latitude)

        source_cv_id = source_id+'-CV'
        source_buffer_id = source_id+"-buffer"
        source_fcv_id = source_id+"-cap"
        ps_inlet_id = pumping_station.bwf_id+'-inlet'
        # pumps have their id already pumps.bwf_id :)
        ps_outlet_id = pumping_station.bwf_id+'-outlet'
        # connections have their own id already, too
        # municipality was already built

        # Let's get the coordinate of the points
        #calculate the line that connect the source and the node
        geodesic_line = Geo.WGS84.InverseLine(
            source.coordinates[0], source.coordinates[1],
            municipality.coordinates[0],  municipality.coordinates[1])

        source_buffer_coord = geodesic_line.Position(0.01 * geodesic_line.s13)
        ps_inlet_coord = geodesic_line.Position(0.10 * geodesic_line.s13)
        ps_outlet_coord = geodesic_line.Position(0.25 * geodesic_line.s13)

        if double_element_ps:
            elem_idx = net.addnode(source_buffer_id, EpanetConstants.EN_JUNCTION)
            net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION, value=source.elevation)
            net.setcoord(elem_idx, x=source_buffer_coord["lon2"], y=source_buffer_coord["lat2"])

        elem_idx = net.addnode(ps_inlet_id, EpanetConstants.EN_JUNCTION)
        net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION, value=source.elevation)
        net.setcoord(elem_idx, x=ps_inlet_coord["lon2"], y=ps_inlet_coord["lat2"])

        elem_idx = net.addnode(ps_outlet_id, EpanetConstants.EN_JUNCTION)
        net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION, value=source.elevation)
        net.setcoord(elem_idx, x=ps_outlet_coord["lon2"], y=ps_outlet_coord["lat2"])

        # A Check valve
        elem_idx = net.addlink(source_cv_id, EpanetConstants.EN_CVPIPE,
                                from_node=source.bwf_id,
                                to_node=source_buffer_id if double_element_ps else ps_inlet_id)
        net.setpipedata(
            index=elem_idx,
            length=1, # m, should not be very long
            diam=pipe._pipe_option.diameter, # same diameter for visualization purposes
            rough=0.0001, # NOTE: Smallest I can, zero is not possible.
            mloss=0
        )

        if double_element_ps:
            # B Flow control valve
            # this should be capped at available capacity minus the 23 previous hours
            # for simplicity we put it 
            # We also track the maximum flowrate that we would like to see here
            total_max_flowrate = 0
            for _, pump in pumps.items():
                total_max_flowrate += pump._pump_option.head_curve.index.max()

            elem_idx = net.addlink(source_fcv_id, EpanetConstants.EN_FCV,
                                   from_node=source_buffer_id,
                                   to_node=ps_inlet_id)
            net.setlinkvalue(elem_idx, EpanetConstants.EN_INITSETTING,
                             value=total_max_flowrate
                            ) # Nominal capacity is in m^3/day, we use peak factor to size the system
            net.setlinkvalue(elem_idx, EpanetConstants.EN_DIAMETER,
                             value=pipe._pipe_option.diameter)


        # C Pumps or GPV
        if gpv_as_ps:
            EN_GPV_CURVE = 24

            # Create the curve of the parallel pumps system
            a_pump = next(iter(pumps.values()))
            # Take the opposite of the pump curve as we use it as valve curve
            pumping_station_curve = -a_pump._pump_option.head_curve.copy()
            pumping_station_curve.index = pumping_station_curve.index * len(pumps)
            # Add extra point with high head to cutoff big flow
            pumping_station_curve.loc[pumping_station_curve.index.max()*1.1] = 100_000

            net.addcurve(pumping_station.bwf_id+'-hc')
            ps_curve_idx: int = net.getcurveindex(pumping_station.bwf_id+'-hc')

            net.setcurvetype(ps_curve_idx, EpanetConstants.EN_HLOSS_CURVE)
            net.setcurve(
                ps_curve_idx,
                pumping_station_curve.index.to_list(),
                pumping_station_curve.to_list(),
                len(pumping_station_curve)
            )

            elem_idx = net.addlink(pumping_station.bwf_id, EpanetConstants.EN_GPV,
                                   from_node=ps_inlet_id,
                                   to_node=ps_outlet_id)
            net.setlinkvalue(elem_idx, EN_GPV_CURVE,
                value=ps_curve_idx
            )
        else:
            for pump in pumps.values():
                elem_idx = net.addlink(pump.bwf_id, EpanetConstants.EN_PUMP,
                                       from_node=ps_inlet_id,
                                       to_node=ps_outlet_id)

                curve_idx = net.getcurveindex(f"{pump._pump_option.bwf_id}-hc")
                net.setlinkvalue(elem_idx, EpanetConstants.EN_PUMP_HCURVE, value=curve_idx)

                curve_idx = net.getcurveindex(f"{pump._pump_option.bwf_id}-ec")
                net.setlinkvalue(elem_idx, EpanetConstants.EN_PUMP_ECURVE, value=curve_idx)

                #pattern_idx = net.getpatternindex(f"{pump._pump_option.bwf_id}-pa")
                #net.setlinkvalue(elem_idx, EpanetConstants.EN_LINKPATTERN, value=pattern_idx)

        # D Supply pipe connection
        elem_idx = net.addlink(pipe.bwf_id, EpanetConstants.EN_PIPE,
                               from_node=ps_outlet_id,
                               to_node=municipality.cbs_id)
        net.setpipedata(
            index=elem_idx,
            length=con.distance, # m
            diam=pipe._pipe_option.diameter,
            rough=pipe.friction_factor.loc[ts],
            mloss=con.minor_loss_coeff
        )

    for con in peer_connections:
        assert isinstance(con, PeerConnection)

        if not con.has_active_pipe(year):
            continue

        pipe = con.active_pipe(year)
        assert pipe is not None

        elem_idx = net.addlink(pipe.bwf_id, EpanetConstants.EN_PIPE,
                               from_node=con.from_node.effective_cbs_id(year),
                               to_node=con.to_node.effective_cbs_id(year))

        net.setpipedata(
            index=elem_idx,
            length=con.distance,
            diam=pipe._pipe_option.diameter,
            rough=pipe.friction_factor.loc[ts],
            mloss=con.minor_loss_coeff
        )

    return net
