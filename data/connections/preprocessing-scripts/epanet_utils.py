import math
import os

from typing import Dict, Optional, Set

from epanet_plus import EPyT, EpanetConstants
from geographiclib.geodesic import Geodesic as Geo
import numpy as np
import pandas as pd

from water_futures_battle.jurisdictions.entities import Province
from water_futures_battle.sources import WaterSource
from water_futures_battle.sources.entities import SourcesContainer
from water_futures_battle.pumps.entities import PumpOption, Pump
from water_futures_battle.pumping_stations.entities import PumpingStation

DEST_FOLDER = '../../epanet-networks/.debug/'

DIAM_OPTIONS_MAP = {
    200: "PI01",
    400: "PI02",
    600: "PI03",
    800: "PI06",
    1000: "PI07",
    1250: "PI08",
    1500: "PI09",
    2000: "PI10"
}

DIAM_OPTIONS_DECAY_BOUNDS_MAP: Dict[str, tuple[float, float]] = {
    "PI01": (0, 0.00007),
    "PI02": (0, 0.00007),
    "PI03": (0, 0.00007),
    "PI06": (0.000259, 0.002523),
    "PI07": (0.000259, 0.002523),
    "PI08": (0.000259, 0.002523),
    "PI09": (0.000259, 0.002523),
    "PI10": (0.000259, 0.002523)
}

DIAM_OPTIONS_NFF_MAP = {
    "PI01": 0.0015,
    "PI02": 0.0015,
    "PI03": 0.0015,
    "PI06": 0.045,
    "PI07": 0.045,
    "PI08": 0.045,
    "PI09": 0.045,
    "PI10": 0.045
}

def _select_option_diam(a_diameter: float) -> str:
    for d, code in DIAM_OPTIONS_MAP.items():
        if d >= a_diameter:
            return code
    # Default, return 2000 mm
    return DIAM_OPTIONS_MAP[2000]

def get_pipe_option_id(pipe_flow__m3ps: float, design_vel__mps: float):
    design_diam = np.sqrt(4/math.pi *pipe_flow__m3ps / design_vel__mps) * 1000 # mm
    return _select_option_diam(a_diameter=design_diam)

def _calculate_roughness(
        connection: pd.Series,
        a_year: int,
        pipe_options: pd.DataFrame,
        pipes_roughnesses_history: Optional[pd.DataFrame]
    ) -> float:

    # None means you are just plotting for visualization of the topology,
    if pipes_roughnesses_history is None:
        return 128.0

    THIS_YEAR = pd.Timestamp(year=a_year, month=1, day=1)

    pipe_option_id = connection['pipes-option_ids'].split(';')[0]

    # Pipe option id "UNDECIDED", it measn you are just plotting for visualization of the topology
    if pipe_option_id == "UNDECIDED":
        return 128.0

    pipe_install_dates = connection['pipes-installation_dates']
    if isinstance(pipe_install_dates, pd.Timestamp):
        pipe_install_date = pipe_install_dates
        pipe_id = f"{connection.name}-00"
    else:
        assert isinstance(pipe_install_dates, str)
        pipe_install_dates = [pd.to_datetime(d) for d in pipe_install_dates.split(';')]
        pipe_install_dates = [d for d in pipe_install_dates if d <= THIS_YEAR]
        pipe_install_date = max(pipe_install_dates)
        pipe_id = f"{connection.name}-{(len(pipe_install_dates)-1):02d}"

    if pipe_id in pipes_roughnesses_history.columns:
        pipe_rhg_history = pipes_roughnesses_history[pipe_id].dropna()

        if THIS_YEAR in pipe_rhg_history.index:
            return pipe_rhg_history.loc[THIS_YEAR]

        assert all(THIS_YEAR > pipe_rhg_history.index)
        pipe_age = int((THIS_YEAR - pipe_rhg_history.index.max()).days/365.25)
        rgh = pipe_rhg_history.iloc[-1]

    else:
        pipe_age = int((THIS_YEAR - pipe_install_date).days/365.25)
        rgh = pipe_options.loc[pipe_option_id, 'darcy_friction_factor-new_pipe'].astype(float)


    rgh += pipe_age * pipe_options.loc[pipe_option_id, 'darcy_friction_factor-decay_rate-max'].astype(float)
            
    return rgh

def build_epyt(
    province: Province,
    munic_demands: Dict[str, float],
    all_sources: SourcesContainer,
    pump_options: Set[PumpOption],
    all_pumping_stations: Set[PumpingStation],
    year: int,
    connections_df: pd.DataFrame,
    dates_as_str: bool,
    pipe_options_df: pd.DataFrame,
    pipes_roughnesses_history: Optional[pd.DataFrame],
    situation_name: Optional[str],
    pda=False,
    future_sources=False,
    pumping_station_representation: str = "free_parallel_pumps",
    pumping_stations_speeds: Optional[Dict[str, float]] = None,
    epyt_kwargs: Optional[Dict] = None
) -> EPyT:
    
    if epyt_kwargs is None:
        epyt_kwargs = {}

    net = EPyT(use_project=True, **epyt_kwargs)
    net.setflowunits(EpanetConstants.EN_CMH)
    net.setoption(EpanetConstants.EN_HEADLOSSFORM, EpanetConstants.EN_DW)
    net.setoption(EpanetConstants.EN_ACCURACY, 0.1)

    if pda:
        net.set_demand_model(
            model_type=EpanetConstants.EN_PDA,
            pmin=15,
            preq=30,
            pexp=0.5
            )

    # Find the municipalities in that year and add them
    municipalities = province.active_municipalities(year)
    
    # Find the sources in that year and add them
    sources: Set[WaterSource] = set()
    for source in all_sources:
        if source.province == province and source.is_active(when=year):
            sources.add(source)
        elif future_sources and pd.isna(source.activation_date) and source.province == province:
            sources.add(source)

    # Keep the pumping stations in this province, that have active pumps
    assert pumping_station_representation in [
        "free_parallel_pumps",
        "chocked_parallel_pumps",
        "single_gpv"
    ]
    if pumping_stations_speeds is None:
        pumping_stations_speeds = {}

    pumping_stations_map: Dict[WaterSource, PumpingStation] = {}
    for ps in all_pumping_stations:
        if ps.province != province:
            continue

        if ps.source.is_active(when=year) or (
            future_sources and pd.isna(ps.source.activation_date)
        ):
            pumping_stations_map[ps.source] = ps

    # Detach this variable and add what is the effective cbs id in that year for each connection
    connections_df = connections_df.copy()
    def get_name_in_this_year(x: str) -> str:
        # Sources stay as they are
        if x.startswith('S'):
            return x
        
        # It's a municipality...
        conn_municipality = province.state.municipality(x)
        
        if conn_municipality.begin_date <= pd.to_datetime(f"{year}"):
            return conn_municipality.effective_cbs_id(when=year)
        
        # if the municipality will open in the future we do not update it because
        # it will be discared later automatically.
        return x
            
    connections_df['from_node-real'] = connections_df['from_node'].apply(get_name_in_this_year)
    connections_df['to_node-real'] = connections_df['to_node'].apply(get_name_in_this_year)

    # Now keep only the rows that have both the from_node and to_node to sources
    # or municipalities that exist in this province and year.
    municipalities_ids: set[str] = set([m.cbs_id for m in municipalities])
    sources_ids: set[str] = set([s.bwf_id for s in sources])
    nodes_ids = municipalities_ids.union(sources_ids)
    MASK_CONNECTIONS = (
        connections_df['from_node-real'].apply(lambda x: True if x in nodes_ids else False) & 
        connections_df['to_node-real'].apply(lambda x: True if x in nodes_ids else False) & 
        (connections_df['from_node-real'] != connections_df['to_node-real']) # check self loops after municipality closes
    )
    if not dates_as_str:
        MASK_ACTIVE_CONNECTIONS = MASK_CONNECTIONS & connections_df['pipes-installation_dates'].notna()
    else:
        MASK_ACTIVE_CONNECTIONS = MASK_CONNECTIONS & (connections_df['pipes-installation_dates'] != '')
    
    # Let's actually build it:
    def build_info():
        for pump_option in sorted(pump_options, key=lambda po: po.bwf_id):
            
            #---- Pump curve 
            pumpcurve_name = f"{pump_option.bwf_id}-hc"

            net.addcurve(pumpcurve_name)
            elem_idx = net.getcurveindex(pumpcurve_name)

            net.setcurvetype(elem_idx, EpanetConstants.EN_PUMP_CURVE)
            net.setcurve(
                elem_idx,
                list(pump_option.head_curve.index),
                list(pump_option.head_curve.values),
                len(pump_option.head_curve)
            )

            #---- Effic curve
            efficcurve_name = f"{pump_option.bwf_id}-ec"

            net.addcurve(efficcurve_name)
            elem_idx = net.getcurveindex(efficcurve_name)

            net.setcurvetype(elem_idx, EpanetConstants.EN_EFFIC_CURVE)
            net.setcurve(
                elem_idx,
                list(pump_option.eff_curve.index),
                list(pump_option.eff_curve.values),
                len(pump_option.eff_curve)
            )

        #---- Patterns for pumps
        if pumping_station_representation != 'single_gpv':
            elem_idx = net.add_pattern(
                pattern_id="PUMP_OFF",
                pattern_values=[0.0]
            )

        return

    def build_municipalities():
        for m in sorted(municipalities, key= lambda m: m.cbs_id):
            elem_name = m.cbs_id

            elem_idx = net.addnode(elem_name, EpanetConstants.EN_JUNCTION)
            net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION,
                            value=m.elevation)
            net.setcoord(elem_idx, x=m.longitude, y=m.latitude)

            net.setnodevalue(elem_idx, EpanetConstants.EN_BASEDEMAND,
                            value=munic_demands[elem_name])
        return
    
    def build_sources():
        # Chocked parallel pumps use a flow control valve and pumps, so we model it with two distinct elements
        double_element_ps = (pumping_station_representation == "chocked_parallel_pumps")

        # Use a GPV as a pumping station
        gpv_as_ps = (pumping_station_representation == "single_gpv")

        for source in sorted(sources, key= lambda s: s.bwf_id):
            # Get the source other components: pumping station, connection, and municipality
            pumping_station = pumping_stations_map[source]
            pumps = pumping_station.active_pumps(when=year)

            mask = MASK_ACTIVE_CONNECTIONS & (
                connections_df['from_node-real'] == source.bwf_id
            )
            assert sum(mask) < 2, "More than one connection to this source has been found"
            # We accpet also zero because this function may be called even before we define sources connections
            
            if any(mask):
                connection = connections_df.loc[mask].iloc[0]
                pipe_option_id = connection['pipes-option_ids'].split(';')[0]

                if pipe_option_id != "UNDECIDED":
                    diameter = pipe_options_df.loc[pipe_option_id, 'diameter']
                else:
                    diameter = 0.001

                municipality_id = connection['to_node-real']
                municipality = province.municipality(municipality_id)
            else:
                connection = pd.Series()
            
            # The structure is as follow:
            # - reservoir (source itself)
            # - pipe check valve (to not allow backflow)
            #  - (chocked approach) junction (helper node to connect the FCV)
            #  - (chocked approach) flow control valve (to limit the capacity)
            # - junction (helper node for connection to the pumps)
            # - pumps (free approach) or gpv (gpv approach)
            # - junction (helper node for connection to the pumps)
            # - pipe (connection to the municipality)

            source_id = source.bwf_id

            elem_idx = net.addnode(source_id, EpanetConstants.EN_RESERVOIR)
            net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION,
                             value=source.elevation)
            net.setcoord(elem_idx, x=source.longitude, y=source.latitude)

            # We add the other points and connections, only if the connection has been defined already
            if len(connection) == 0:
                continue

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
            ps_outlet_coord= geodesic_line.Position(0.25 * geodesic_line.s13)

            if double_element_ps:
                elem_idx = net.addnode(source_buffer_id, EpanetConstants.EN_JUNCTION)
                net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION,     
                                value=source.elevation)
                net.setcoord(elem_idx, x=source_buffer_coord["lon2"], y=source_buffer_coord["lat2"])

            elem_idx = net.addnode(ps_inlet_id, EpanetConstants.EN_JUNCTION)
            net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION,     
                             value=source.elevation)
            net.setcoord(elem_idx, x=ps_inlet_coord["lon2"], y=ps_inlet_coord["lat2"])

            elem_idx = net.addnode(ps_outlet_id, EpanetConstants.EN_JUNCTION)
            net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION,     
                             value=source.elevation)
            net.setcoord(elem_idx, x=ps_outlet_coord["lon2"], y=ps_outlet_coord["lat2"])

            # A Check valve
            elem_idx = net.addlink(source_cv_id, EpanetConstants.EN_CVPIPE,
                from_node=source.bwf_id,
                to_node=source_buffer_id if double_element_ps else ps_inlet_id
            )
            net.setpipedata(
                index=elem_idx,
                length=1, # m, should not be very long
                diam=diameter, # same diameter for visualization purposes
                rough=0.0001, # NOTE: Smallest I can, zero is not possible.
                mloss=0
            )

            if double_element_ps:
                # B Flow control valve
                # this should be capped at available capacity minus the 23 previous hours
                # for simplicity we put it 
                # We also track the maximum flowrate that we would like to see here
                total_max_flowrate = 0
                for idx, pump in pumps.items():
                    total_max_flowrate += pump._pump_option.head_curve.index.max()

                elem_idx = net.addlink(source_fcv_id, EpanetConstants.EN_FCV,
                                    from_node=source_buffer_id,
                                    to_node=ps_inlet_id)
                net.setlinkvalue(elem_idx, EpanetConstants.EN_INITSETTING,
                                value=total_max_flowrate
                                ) # Nominal capacity is in m^3/day, we use peak factor to size the system
                net.setlinkvalue(elem_idx, EpanetConstants.EN_DIAMETER,
                                            value=diameter)
            
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

                if pumping_station.bwf_id not in pumping_stations_speeds:
                    n_running_pumps = len(pumps)
                    pump_speed = 1.0
                else:
                    ps_speed = pumping_stations_speeds[pumping_station.bwf_id]
                    n_running_pumps = math.ceil(ps_speed)-1
                    pump_speed = ps_speed - n_running_pumps

                pattern_idx = net.add_pattern(
                    pattern_id=pumping_station.bwf_id,
                    pattern_values=[pump_speed]
                )
                
                for j, pump in enumerate(pumps.values(), start=1):
                    elem_idx = net.addlink(pump.bwf_id, EpanetConstants.EN_PUMP,
                                    from_node=ps_inlet_id,
                                    to_node=ps_outlet_id)
                    
                    curve_idx = net.getcurveindex(f"{pump._pump_option.bwf_id}-hc")
                    net.setlinkvalue(elem_idx, EpanetConstants.EN_PUMP_HCURVE, value=curve_idx)

                    curve_idx = net.getcurveindex(f"{pump._pump_option.bwf_id}-ec")
                    net.setlinkvalue(elem_idx, EpanetConstants.EN_PUMP_ECURVE, value=curve_idx)

                    if j <= n_running_pumps:
                        pattern_idx = net.getpatternindex(pumping_station.bwf_id)
                    else:
                        pattern_idx = net.getpatternindex("PUMP_OFF")
                    net.setlinkvalue(elem_idx, EpanetConstants.EN_LINKPATTERN, value=pattern_idx)
            
            # D the pipe connecting the municipality
            elem_idx = net.addlink(connection.name, EpanetConstants.EN_PIPE,
                                   from_node=ps_outlet_id,
                                   to_node=municipality.cbs_id)
            net.setpipedata(
                index=elem_idx,
                length=connection['distance'],
                diam=diameter,
                rough=_calculate_roughness(
                    connection,
                    year,
                    pipe_options_df,
                    pipes_roughnesses_history
                ),
                mloss=connection['minor_loss_coefficient']
            )
        return
            
    def build_gm2gm_connections():
        mask = MASK_ACTIVE_CONNECTIONS & (
            connections_df[['from_node-real', 'to_node-real']].apply(
                # they are both a municipality (gementee GM)
                lambda row: str(row['from_node-real']).startswith('GM') and str(row['to_node-real']).startswith('GM'),
                axis=1
            )
        )

        for elem_name, connection in connections_df[mask].iterrows():
            from_node = province.municipality(connection['from_node-real'])
            to_node = province.municipality(connection['to_node-real'])

            pipe_install_dates = connection['pipes-installation_dates']
            if isinstance(pipe_install_dates, str):
                # let's make sure we don't have a future pipe only in this connection
                pipe_install_dates = [pd.to_datetime(d) for d in pipe_install_dates.split(';')]
                pipe_install_dates = [d for d in pipe_install_dates if d.year <= year]
                if len(pipe_install_dates) == 0:
                    # we discovered that the pipes installed here are not active yet
                    continue

            if (
                pd.notna(connection['last_pipe_decom_date']) and 
                connection['last_pipe_decom_date'].year <= year
            ):
                # no pipe remaining in the connection
                continue

            elem_idx = net.addlink(elem_name, EpanetConstants.EN_PIPE,
                        from_node=from_node.cbs_id,
                        to_node=to_node.cbs_id)

            # Lenght
            net.setlinkvalue(elem_idx, EpanetConstants.EN_LENGTH,
                                        value=connection['distance'])

            # Diameter
            pipe_option_id = connection['pipes-option_ids'].split(';')[0]
            if pipe_option_id != "UNDECIDED":
                diameter = float(pipe_options_df.loc[pipe_option_id, 'diameter'])
                status = EpanetConstants.EN_OPEN
            else:
                diameter = 0.001
                status = EpanetConstants.EN_CLOSED
            net.setlinkvalue(elem_idx, EpanetConstants.EN_DIAMETER,
                                        value=diameter)

            # Roughness
            net.setlinkvalue(elem_idx, EpanetConstants.EN_ROUGHNESS,
                                        value=_calculate_roughness(
                                            connection,
                                            year,
                                            pipe_options_df,
                                            pipes_roughnesses_history
                                        )
            )

            # Minorloss from input file
            net.setlinkvalue(elem_idx, EpanetConstants.EN_MINORLOSS,
                                        value=connection['minor_loss_coefficient'])

            # Status, just in case..
            net.setlinkvalue(elem_idx, EpanetConstants.EN_STATUS,
                                        value=status)

        return
        
    build_info()
    build_municipalities()
    build_sources()
    build_gm2gm_connections()

    if situation_name:
        full_dest_folder = f"{DEST_FOLDER}/{province.outfiles_name}/{situation_name}"
        os.makedirs(full_dest_folder, exist_ok=True)

        net_inp_filename =f'{province.outfiles_name}-{year}-{situation_name}.inp'
        
        with open(f'{full_dest_folder}/{net_inp_filename}', 'w'):
            pass
        net.saveinpfile(f'{full_dest_folder}/{net_inp_filename}')

    return net

def get_total_undelivered_demand(
    net: EPyT
) -> float:
    """
    Simulate a network at peak demand and extracts its undelivered demand.
    Assumptions: network is at peak demand, duration etc already set and 
    PDA already set.
    """
    try:
        # Run sim
        net.openH()
        net.initH(EpanetConstants.EN_INITFLOW)
        
        #tstep = 1
        #while tstep > 0:
        t = net.runH()

        u = np.round(np.array(net.getnodevalues(EpanetConstants.EN_DEMANDDEFICIT)), 2)
        # tstep = self.net.nextH()
        
        net.closeH()

        return sum(u)
    except Exception as e:
        net.closeH()
        
        return sum([
            float(net.getnodevalue(m_idx, EpanetConstants.EN_BASEDEMAND))
            for m_idx in net.get_all_junctions_idx()
        ])