from collections import deque
from enum import IntEnum
import os
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

import itertools
from epanet_plus import EPyT, EpanetConstants
from geographiclib.geodesic import Geodesic as Geo
import numpy as np
import pandas as pd

from ..core import Settings
from ..core.utility import timestampify
from ..jurisdictions.entities import Municipality
from ..sources import WaterSource
from ..connections.entities import PeerConnection, SupplyConnection
from ..pumps.entities import Pump, PumpOption
from ..pumping_stations.entities import PumpingStation
from ..pumping_stations.services import get_lowest_energy_pumping_station_setup, NoValidPumpConfigurationError
from ..energy.entities import ElectricityPricePattern
from ..water_utilities import WaterUtility
from ..national_context import NationalContext
from ..national_context.entities import WaterUtilitiesCluster

class PumpingStationRepresentation(IntEnum):
    FREE_PARALLEL_PUMPS = 1
    CHOCKED_PARALLEL_PUMPS = 2
    SINGLE_GPV = 3
    FIXED_HEAD = 4
    CHOCKED_FIXED_HEAD = 5

PUMPCURVE_SUFFIX = 'hc'
EFFICURVE_SUFFIX = 'ec'
BUFFER_SUFFIX = 'buffer'
INLET_SUFFIX = 'inlet'
OUTLET_SUFFIX = 'outlet'
CV_SUFFIX = 'CV'
FCV_SUFFIX = 'cap'

from importlib.resources import files

def load_target_heads() -> pd.DataFrame:
    path = files("water_futures_battle.services").joinpath("target_heads.csv")
    with path.open("r") as f:
        return pd.read_csv(f, index_col='year')
pstations_target_heads = load_target_heads()
    
def get_source_head(pstations_target_heads: pd.DataFrame, source: WaterSource, year: int) -> float:
    """
    Look up the target head for a source at a given year.
    - If source_id not in columns: return 50 (fallback offset).
    - If year is present and not NaN: return that value.
    - Otherwise: return the latest non-NaN value before (or at) that year.
    """
    closest_m = source.closest_municipality

    if closest_m.begin_date.year > year:
        raise ValueError("Should not happen that a source opens before its municipality does")

    closest_m = closest_m.effective_entity(when=year)

    if closest_m.cbs_id not in pstations_target_heads.columns:
        return 50.0

    col = pstations_target_heads[closest_m.cbs_id].dropna()

    if year in col.index:
        return col.loc[year]

    earlier = col[col.index <= year]
    if earlier.empty:
        return 50.0
    return earlier.iloc[-1]

def build_epanet_network(
    year: int,
    water_utilities: Set[WaterUtility],
    cross_utility_connections: Set[PeerConnection],
    pumping_station_representation: int,
    epyt_kwargs: Optional[Dict] = None,
) -> EPyT:

    if epyt_kwargs is None:
        epyt_kwargs = {}

    assert pumping_station_representation in PumpingStationRepresentation

    ts = timestampify(year, errors='raise')

    net = EPyT(use_project=True, **epyt_kwargs)

    net.setflowunits(EpanetConstants.EN_CMH)
    net.setoption(EpanetConstants.EN_HEADLOSSFORM, EpanetConstants.EN_DW)
    net.set_hydraulic_time_step(60*60)
    net.settimeparam(EpanetConstants.EN_PATTERNSTEP, 60*60)
    net.setoption(EpanetConstants.EN_ACCURACY, value=0.01)
    net.setoption(EpanetConstants.EN_DAMPLIMIT, value=0.5)
    net.setoption(EpanetConstants.EN_CHECKFREQ, value=10)
    net.setoption(EpanetConstants.EN_TRIALS, value=300)
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
    pumps: Set[Pump] = set()
    for utility in water_utilities:
        for ws, (ps, con) in utility.m_supplies.items():
            if ws.is_active(year):
                sources.add(ws)
                if ps.has_active_pumps(year):
                    pumping_stations_map[ws] = (ps, con)

                    for p in ps.active_pumps(year).values():
                        pumps.add(p)
                        pump_options.add(p._pump_option)

    # We start adding the helpers to the network
    # ---- Curves
    # -------- Pumps in model (free or chocked)
    #          one pump curve and one efficiency curve per pump option
    if pumping_station_representation in [
        PumpingStationRepresentation.FREE_PARALLEL_PUMPS,
        PumpingStationRepresentation.CHOCKED_PARALLEL_PUMPS
    ]:
        for p_option in sorted(pump_options, key= lambda po: po.bwf_id):
            #---- Pump curve
            pumpcurve_name = p_option.bwf_id+'-'+PUMPCURVE_SUFFIX

            net.addcurve(pumpcurve_name)
            elem_idx = net.getcurveindex(pumpcurve_name)
            assert isinstance(elem_idx, int)

            net.setcurvetype(elem_idx, EpanetConstants.EN_PUMP_CURVE)
            net.setcurve(
                elem_idx,
                list(p_option.head_curve.index),
                list(p_option.head_curve.values),
                len(p_option.head_curve)
            )

            #---- Effic curve
            efficcurve_name = p_option.bwf_id+'-'+EFFICURVE_SUFFIX

            net.addcurve(efficcurve_name)
            elem_idx = net.getcurveindex(efficcurve_name)
            assert isinstance(elem_idx, int)

            net.setcurvetype(elem_idx, EpanetConstants.EN_EFFIC_CURVE)
            net.setcurve(
                elem_idx,
                list(p_option.eff_curve.index),
                list(p_option.eff_curve.values),
                len(p_option.eff_curve)
            )
    
    # ---- Curves
    # -------- Pumping station as GPV
    #          one flow-head curve per pumping station (source)
    if pumping_station_representation == PumpingStationRepresentation.SINGLE_GPV:
        for pstat, _ in sorted(
            pumping_stations_map.values(),
            key= lambda t: t[0].bwf_id
        ):
            a_pump = next(iter(pstat.active_pumps(when=year).values()))
            # Take the opposite of the pump curve as we use it as valve curve
            pumping_station_curve = -a_pump._pump_option.head_curve.copy()
            pumping_station_curve.index = pumping_station_curve.index * len(pumps)
            # Add extra point with high head to cutoff big flow 
            pumping_station_curve.loc[pumping_station_curve.index.max()*1.1] = 100_000

            net.addcurve(pstat.bwf_id+'-'+PUMPCURVE_SUFFIX)
            ps_curve_idx = net.getcurveindex(pstat.bwf_id+'-'+PUMPCURVE_SUFFIX)
            assert isinstance(ps_curve_idx, int)
            
            net.setcurvetype(ps_curve_idx, EpanetConstants.EN_HLOSS_CURVE)
            net.setcurve(
                ps_curve_idx,
                pumping_station_curve.index.to_list(),
                pumping_station_curve.to_list(),
                len(pumping_station_curve)
            )

    # ---- Curves
    # -------- Fixed head
    #          no curves
    if pumping_station_representation == PumpingStationRepresentation.FIXED_HEAD:
        pass

    # ---- Patterns
    # -------- Pumps in model (free or chocked)
    #          one per pump
    if pumping_station_representation in [
        PumpingStationRepresentation.FREE_PARALLEL_PUMPS,
        PumpingStationRepresentation.CHOCKED_PARALLEL_PUMPS
    ]:
        for p in sorted(pumps, key= lambda p: p.bwf_id):
            net.add_pattern(
                pattern_id=p.bwf_id,
                pattern_values=[0.0]
            )

    # ---- Patterns
    # -------- No pump in model (GPV or fixed head)
    #          no patterns
    else:
        pass

    # ---- Patterns
    #      one pattern per municipality for its demand
    for m in sorted(municipalities, key= lambda m: m.cbs_id):
        net.add_pattern(
            pattern_id=m.cbs_id,
            pattern_values=[0.0]
        )

    # 2. ---- We add the nodes to the network
    #    2.1 -- We add the demand nodes, i.e., the municipalities
    for m in sorted(municipalities, key= lambda m: m.cbs_id):
        elem_name = m.cbs_id

        elem_idx = net.addnode(elem_name, EpanetConstants.EN_JUNCTION)
        assert isinstance(elem_idx, int)

        net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION, m.elevation)
        net.setcoord(elem_idx, x=m.longitude, y=m.latitude)

        pattern_idx = net.getpatternindex(pattern_id=m.cbs_id)
        assert isinstance(pattern_idx, int)

        net.setnodevalue(elem_idx, EpanetConstants.EN_BASEDEMAND,
            value=1.0
        )
        net.setnodevalue(elem_idx, EpanetConstants.EN_PATTERN,
            value=pattern_idx
        )

    #    2.2 -- We add the reservoirs and helper nodes, i.e., the water source
    #           The structure is as follow:
    #            - FREE PARALLEL PUMPS
    #              Reservoir -> CV -> ps inlet -> pumps -> ps outlet -> pipe -> net
    #            - CHOCKED PARALLEL PUMPS
    #              Reservoir -> CV -> buffer -> FCV -> ps inlest -> pumps -> 
    #                -> ps outlet -> pipe -> net
    #            - SINGLE GPV
    #              Reservoir -> CV -> ps inlet -> GPV -> ps outlet -> pipe -> net
    #            - FIXED HEAD
    #              Reservoir (elevated) -> CV -> ps outlet -> pipe -> net
    #            - FIXED HEAD
    #              Reservoir (elevated) -> CV -> buffer -> FCV -> ps outlet -> pipe -> net

    HAS_BUFFER = (
        pumping_station_representation == PumpingStationRepresentation.CHOCKED_PARALLEL_PUMPS or 
        pumping_station_representation == PumpingStationRepresentation.CHOCKED_FIXED_HEAD
    )
    HAS_INLET = (
        pumping_station_representation == PumpingStationRepresentation.CHOCKED_PARALLEL_PUMPS or
        pumping_station_representation == PumpingStationRepresentation.FREE_PARALLEL_PUMPS or
        pumping_station_representation == PumpingStationRepresentation.SINGLE_GPV
    )
    
    for source, (pumping_station, con) in sorted(pumping_stations_map.items(), key= lambda x: x[0].bwf_id):
        if not source.is_active(year):
            continue

        # ---- First point: Reservoir
        source_id = source.bwf_id

        elem_idx = net.addnode(source_id, EpanetConstants.EN_RESERVOIR)
        assert isinstance(elem_idx, int)

        if (
            pumping_station_representation == PumpingStationRepresentation.FIXED_HEAD or 
            pumping_station_representation == PumpingStationRepresentation.CHOCKED_FIXED_HEAD
        ):
           source_elevation = source.elevation + get_source_head(pstations_target_heads, source, year)
        else:
            source_elevation = source.elevation

        net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION, value=source_elevation)
        net.setcoord(elem_idx, x=source.longitude, y=source.latitude)

        # ---- Helper points: buffer, inlet, outlet
        #   depending on the representation, we don't have coordinates for these
        #   so we lay them along the line connecting the source to the municipality
        
        municipality = con.to_node.effective_entity(year)
        geodesic_line = Geo.WGS84.InverseLine(
            source.coordinates[0],       source.coordinates[1],
            municipality.coordinates[0], municipality.coordinates[1]
        )

        if HAS_BUFFER:
            source_buffer_id = source_id+'-'+BUFFER_SUFFIX
            source_buffer_coord = geodesic_line.Position(0.01 * geodesic_line.s13)

            elem_idx = net.addnode(source_buffer_id, EpanetConstants.EN_JUNCTION)
            assert isinstance(elem_idx, int)

            net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION, value=source_elevation)
            net.setcoord(elem_idx, x=source_buffer_coord["lon2"], y=source_buffer_coord["lat2"])

        if HAS_INLET:
            ps_inlet_id = pumping_station.bwf_id+'-'+INLET_SUFFIX
            ps_inlet_coord = geodesic_line.Position(0.10 * geodesic_line.s13)

            elem_idx = net.addnode(ps_inlet_id, EpanetConstants.EN_JUNCTION)
            assert isinstance(elem_idx, int)

            net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION, value=source.elevation)
            net.setcoord(elem_idx, x=ps_inlet_coord["lon2"], y=ps_inlet_coord["lat2"])

        # always has outlet
        ps_outlet_id = pumping_station.bwf_id+'-'+OUTLET_SUFFIX
        ps_outlet_coord = geodesic_line.Position(0.25 * geodesic_line.s13)

        elem_idx = net.addnode(ps_outlet_id, EpanetConstants.EN_JUNCTION)
        assert isinstance(elem_idx, int)

        net.setnodevalue(elem_idx, EpanetConstants.EN_ELEVATION, value=source.elevation)
        net.setcoord(elem_idx, x=ps_outlet_coord["lon2"], y=ps_outlet_coord["lat2"])

        # ---- Source connecting elements
        pipe = con.active_pipe(year)
        assert pipe is not None
        # -------- Check valve
        #          to the first helper node available
        source_cv_id = source_id+'-'+CV_SUFFIX

        if HAS_BUFFER:
            source_cv_2node_id = source_buffer_id
        elif HAS_INLET:
            source_cv_2node_id = ps_inlet_id
        else:
            source_cv_2node_id = ps_outlet_id

        elem_idx = net.addlink(source_cv_id, EpanetConstants.EN_CVPIPE,
            from_node=source.bwf_id,
            to_node=source_cv_2node_id
        )
        assert isinstance(elem_idx, int)

        net.setpipedata(
            index=elem_idx,
            length=1, # m, # Smallest possible to reduce impact
            diam=pipe._pipe_option.diameter, # same diameter for visualization purposes
            rough=0.0001, # Smallest possible to reduce impact
            mloss=0
        )
        
        # -------- FCV (optional)
        if (
            pumping_station_representation == PumpingStationRepresentation.CHOCKED_PARALLEL_PUMPS or 
            pumping_station_representation == PumpingStationRepresentation.CHOCKED_FIXED_HEAD
        ):
            source_fcv_id = source_id+'-'+FCV_SUFFIX
            
            if HAS_INLET:
                source_fcv_2node_id = ps_inlet_id
            else:
                source_fcv_2node_id = ps_outlet_id

            total_max_flowrate = 0
            for pump in pumping_station.active_pumps(year).values():
                total_max_flowrate += pump._pump_option.head_curve.index.max()

            elem_idx = net.addlink(source_fcv_id, EpanetConstants.EN_FCV,
                from_node=source_buffer_id,
                to_node=source_fcv_2node_id
            )
            assert isinstance(elem_idx, int)

            net.setlinkvalue(elem_idx, EpanetConstants.EN_INITSETTING,
                value=total_max_flowrate
            ) # Nominal capacity is in m^3/day, we use peak factor to size the system
            net.setlinkvalue(elem_idx, EpanetConstants.EN_DIAMETER,
                value=pipe._pipe_option.diameter # Same diameter for visualization purposes
            )

        # -------- Pumps (optional)
        if pumping_station_representation in [
            PumpingStationRepresentation.CHOCKED_PARALLEL_PUMPS,
            PumpingStationRepresentation.FREE_PARALLEL_PUMPS
        ]:
            for pump in pumping_station.active_pumps(when=year).values():
                elem_idx = net.addlink(pump.bwf_id, EpanetConstants.EN_PUMP,
                    from_node=ps_inlet_id,
                    to_node=ps_outlet_id
                )
                assert isinstance(elem_idx, int)

                curve_idx = net.getcurveindex(pump._pump_option.bwf_id+'-'+PUMPCURVE_SUFFIX)
                assert isinstance(curve_idx, int)
                net.setlinkvalue(elem_idx, EpanetConstants.EN_PUMP_HCURVE, value=curve_idx)

                curve_idx = net.getcurveindex(pump._pump_option.bwf_id+'-'+EFFICURVE_SUFFIX)
                assert isinstance(curve_idx, int)
                net.setlinkvalue(elem_idx, EpanetConstants.EN_PUMP_ECURVE, value=curve_idx)

                pattern_idx = net.getpatternindex(pump.bwf_id)
                assert isinstance(pattern_idx, int)
                net.setlinkvalue(elem_idx, EpanetConstants.EN_LINKPATTERN, value=pattern_idx)
        
        # -------- GPV (optional)
        if pumping_station_representation == PumpingStationRepresentation.SINGLE_GPV:

            ps_curve_idx = net.getcurveindex(pumping_station.bwf_id+'-'+PUMPCURVE_SUFFIX)
            assert isinstance(ps_curve_idx, int)

            elem_idx = net.addlink(pumping_station.bwf_id, EpanetConstants.EN_GPV,
                from_node=ps_inlet_id,
                to_node=ps_outlet_id
            )
            assert isinstance(elem_idx, int)
            net.setlinkvalue(elem_idx, EpanetConstants.EN_GPV_CURVE,
                value=ps_curve_idx
            )

        # -------- Pipe
        elem_idx = net.addlink(pipe.bwf_id, EpanetConstants.EN_PIPE,
            from_node=ps_outlet_id,
            to_node=municipality.cbs_id
        )
        assert isinstance(elem_idx, int)
        
        net.setpipedata(
            index=elem_idx,
            length=con.distance, # m
            diam=pipe._pipe_option.diameter,
            rough=pipe.friction_factor.loc[ts],
            mloss=con.minor_loss_coeff
        )

    # 3. -- We connect the network nodes between each other
    for con in sorted(peer_connections, key= lambda c: c.bwf_id):
        assert isinstance(con, PeerConnection)

        if not con.has_active_pipe(year):
            continue

        pipe = con.active_pipe(year)
        assert pipe is not None

        elem_idx = net.addlink(pipe.bwf_id, EpanetConstants.EN_PIPE,
            from_node=con.from_node.effective_cbs_id(year),
            to_node=con.to_node.effective_cbs_id(year)
        )
        assert isinstance(elem_idx, int)
        net.setpipedata(
            index=elem_idx,
            length=con.distance,
            diam=pipe._pipe_option.diameter,
            rough=pipe.friction_factor.loc[ts],
            mloss=con.minor_loss_coeff
        )

    return net

def apply_demand_patterns(
        net: EPyT,
        demands: pd.DataFrame,
    ) -> EPyT:
    
    num_hours = len(demands) - 1
    net.set_simulation_duration(num_hours * 60 * 60)

    for junc_id, junc_idx in zip(
        net.get_all_junctions_id(),
        net.get_all_junctions_idx()
    ):
        if not junc_id.startswith(Municipality.ID_PREFIX):
            # not a demand node (aka municipality), we don't care
            continue
        
        assert junc_id in demands.columns, f"Municipality {junc_id} in network doesn't have demand in dataframe"

        pattern_idx = net.getpatternindex(pattern_id=junc_id)
        assert isinstance(pattern_idx, int) and pattern_idx > 0, f"Could not locate municipality {junc_id}'s demand pattern"

        node_demands = demands[junc_id].to_list()
        net.setpattern(pattern_idx, values=node_demands, len=len(node_demands))
    
    return net

ELECTRICITY_PATTERN_ID = "ELECTRICITY"
def apply_electricity_info(
        net: EPyT,
        electricity_price: float,
        electricity_pattern: ElectricityPricePattern
    ) -> EPyT:

    net.setoption(EpanetConstants.EN_GLOBALPRICE, value=electricity_price)

    try:
        pattern_idx = net.getpatternindex(pattern_id=ELECTRICITY_PATTERN_ID)
    except Exception:
        # the pattern has not been created yet
        net.addpattern(id=ELECTRICITY_PATTERN_ID)
        pattern_idx = net.getpatternindex(pattern_id=ELECTRICITY_PATTERN_ID)
    assert isinstance(pattern_idx, int)

    net.setpattern(pattern_idx,
        values=list(electricity_pattern.values),
        len=len(electricity_pattern.values)
    )

    net.setoption(EpanetConstants.EN_GLOBALPATTERN, value=pattern_idx)

    return net

def apply_pumping_stations_patterns(
    net: EPyT,
    patterns: pd.DataFrame,
    mapping: Dict[str, list[int]]
) -> EPyT:
    """
    Apply pumping station patterns to a network, setting individual pump speed patterns.

    Each pumping station pattern value encodes both the number of active pumps and their
    speed as a single float, using the convention: value in (n, n+1] means n pumps running.

        n_running_pumps = ceil(value) - 1
        pump_speed      = value - n_running_pumps  ∈ (0, 1]

    Examples:
        3.8  → 3 pumps at 80%
        4.0  → 3 pumps at 100%  (NOT 4 — integers map to n-1 pumps at 100%)
        1.0  → 0 pumps running  (all off)
        0.x  → 0 pumps running  (all off, speed irrelevant)

    Within each station, pumps are ranked by index. Pump i is active if i <= n_running_pumps,
    otherwise its speed is set to 0. All active pumps share the same speed.

    Args:
        net:      EPANET network object to modify in place.
        patterns: DataFrame where each column is a pumping station ID and each row is a
                  timestep value following the encoding above.
        mapping:  Dict mapping each pumping station ID to an ordered list of EPANET pattern
                  indices (1-based), one per pump in that station.

    Returns:
        The modified network object.
    """
    for pstat_id in patterns.columns:
        pstat_pattern = patterns[pstat_id].to_numpy()

        n_running_pumps = np.ceil(pstat_pattern) -1
        pumps_speed = pstat_pattern - n_running_pumps

        for i, patt_ENidx in enumerate(mapping[pstat_id], start=1):
            pump_speed = pumps_speed.copy()

            # where i is greater than n_running_pumps, this pump needs to be off
            pump_speed[n_running_pumps < i] = 0.0

            net.setpattern(
                index=patt_ENidx,
                values=list(pump_speed),
                len=pump_speed.shape[0]
            )

    return net

def apply_pumping_stations_pattern_at(
    net: EPyT,
    pattern_row: pd.Series | Dict[str, float],
    mapping: Dict[str, list[int]],
    pattern_step: int,
) -> EPyT:
    """
    Same as apply_pumping_stations_pattern but for a single point of the pattern
    """
    for pstat_id in pattern_row:
        value = pattern_row[pstat_id]
        n_running_pumps = np.ceil(value) - 1
        pump_speed = value - n_running_pumps

        for i, patt_ENidx in enumerate(mapping[pstat_id], start=1):
            speed = pump_speed if i <= n_running_pumps else 0.0
            net.setpatternvalue(
                index=patt_ENidx,
                period=pattern_step+1,
                value=speed,
            )

    return net

def apply_sources_remaining_capacity_to_fcvs(
        net: EPyT,
        sources_capacity: np.ndarray,
        sources_fcv_ENidx: list[int]
) -> EPyT:
    
    for i, fcv_idx in enumerate(sources_fcv_ENidx):

        net.setlinkvalue(
            index=fcv_idx,
            property=EpanetConstants.EN_SETTING,
            value=sources_capacity[i]
        )
    
    return net

class BWFHydraulicSimReults(NamedTuple):
    undelivered_demands: pd.DataFrame
    pumps_energy_consumption: pd.DataFrame
    cross_utilities_flows: pd.DataFrame
    sources_production: pd.DataFrame

import logging

def setup_cluster_logger(network_id):
    logger = logging.getLogger(f"{network_id}")
    
    # If the logger doesn't have a handler yet, add one
    if not logger.handlers:
        Path("bwf_logs").mkdir(exist_ok=True)

        handler = logging.FileHandler(f"bwf_logs/{network_id}.log")
        formatter = logging.Formatter('%(asctime)s | %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

def run_cluster_hydraulics(
        national_context: NationalContext,
        cluster: WaterUtilitiesCluster, 
        year: int,
        settings: Settings
    ) -> BWFHydraulicSimReults:

    PUMPING_STATION_REPRESENTATION = PumpingStationRepresentation.FREE_PARALLEL_PUMPS
    cluster.network = build_epanet_network(
        year=year,
        water_utilities=cluster.water_utilities,
        cross_utility_connections=cluster.cross_utility_connections,
        pumping_station_representation=PUMPING_STATION_REPRESENTATION,
        epyt_kwargs={
            # see EPANET warning codes
            "ignore_error_codes": [2,4,5,6]
        }
    )

    # Setup helper variables and "dimensions" of the simulation
    year_timesteps = pd.date_range(
        start=f"{year}-01-01 00:00:00",
        periods=365 * 24,
        freq="h"
    )
    
    # ---- MUNICIPALITIES
    municipalities_id = [ j
        for j in cluster.network.get_all_junctions_id()
        if j.startswith(Municipality.ID_PREFIX)
    ]
    municipalities_ENidx = [ i
        for j, i in zip(
            cluster.network.get_all_junctions_id(),
            cluster.network.get_all_junctions_idx()
        )
        if j.startswith(Municipality.ID_PREFIX)
    ]
    municipalities_idx = [i-1 for i in municipalities_ENidx]

    municipalities_dem = national_context.municipalities_total_demands.loc[
        year_timesteps,
        municipalities_id
    ].to_numpy(dtype=np.float32)

    # Here we store the results
    municipalities_consumptions = np.full(
        shape=(len(year_timesteps), len(municipalities_id)),
        fill_value=np.float32(np.nan),
        dtype=np.float32
    )

    # ---- SOURCES (and helper elements)

    sources_id = cluster.network.get_all_reservoirs_id()
    sources_ENidx = cluster.network.get_all_reservoirs_idx()
    sources_idx = [i-1 for i in sources_ENidx]

    fcv_id_to_ENidx = {
        v: i
        for v, i in zip(
            cluster.network.get_all_valves_id(),
            cluster.network.get_all_valves_idx()
        )
        if v.endswith(FCV_SUFFIX)
    }
    sources_fcv_id: list[str] = []
    sources_fcv_ENidx: list[int] = []
    for sid in sources_id:
        fcv_id = sid + '-' + FCV_SUFFIX
        if fcv_id in fcv_id_to_ENidx:
            sources_fcv_id.append(fcv_id)
            sources_fcv_ENidx.append(fcv_id_to_ENidx[fcv_id])

    # Cache sources' pumping station target head
    sources_map_target_head = {
        source.bwf_id: get_source_head(pstations_target_heads, source, year)
        for source in cluster.water_sources
    }
    sources_target_head = np.array([ sources_map_target_head[s]
        for s in sources_id                                
    ])

    # Cache sources' pumps to help 
    sources_map_active_pumps = {
        source.bwf_id: source.pumping_station.active_pumps(when=year)
        for source in cluster.water_sources
    }

    # Cache sources's pumping stations number of pumps
    sources_n_avail_pumps = np.array([
        len(sources_map_active_pumps[s])
        for s in sources_id
    ])

    # Cache sources' pumping stations pump curve coefficients (since they are all 
    # identical, we take those of the first active pump)
    sources_pump_options: List[PumpOption] = [ 
        next(iter(sources_map_active_pumps[s].values()))._pump_option
        for s in sources_id
    ]
    sources_pc_coeff = np.array([ 
        po.pump_curve_coeffs
        for po in sources_pump_options
    ])

    sources_map_pstat_id = {
        source.bwf_id: source.pumping_station.bwf_id
        for source in cluster.water_sources
    }
    pstations_id = [ sources_map_pstat_id[s]
        for s in sources_id
    ]

    if PUMPING_STATION_REPRESENTATION in [
        PumpingStationRepresentation.CHOCKED_PARALLEL_PUMPS, 
        PumpingStationRepresentation.FREE_PARALLEL_PUMPS
    ]:
        pumps_id = cluster.network.get_all_pumps_id()
        pumps_ENidx = cluster.network.get_all_pumps_idx()
        pumps_idx = [i-1 for i in pumps_ENidx]

        pumps_patterns_id = [pp
            for pp in cluster.network.get_all_patterns_id()
            if pp.startswith(PumpingStation.ID_PREFIX)
        ]
        pumps_patterns_ENidx = [ int(cluster.network.getpatternindex(pattern_id=pp))
            for pp in pumps_patterns_id                      
        ]

        pstations_map_pumps_ENidx: Dict[str, list[int]] = {
            p: []
            for p in pstations_id
        }
        for pump_id, pump_ENidx in zip(pumps_id, pumps_ENidx):
            pstation_id = pump_id[:6]
            assert pstation_id in pstations_id

            pstations_map_pumps_ENidx[pstation_id].append(pump_ENidx)
        
        pstations_map_pumps_patterns_ENidx: Dict[str, list[int]] = {
            p: []
            for p in pstations_id
        }
        for pump_pattern_id, pump_pattern_ENidx in zip(pumps_patterns_id, pumps_patterns_ENidx):
            pstation_id = pump_pattern_id[:6]
            assert pstation_id in pstations_id

            pstations_map_pumps_patterns_ENidx[pstation_id].append(pump_pattern_ENidx)

    else:

        pumps_id = [
            pump.bwf_id
            for s in sources_id
            for pump in sources_map_active_pumps[s].values()
        ]

    # Prepend last year's last 23 hours to get what is the effective hourly production
    # at the first hour of this year. When we don't have old results (source has 
    # just opened and it doesn't have its column or hte column is just nans), we just put 0.
    sources_eopy_np = np.array([
        np.zeros(23, dtype=np.float32)
        if sid not in national_context.sources_production or len(national_context.sources_production[sid].dropna())==0
        else national_context.sources_production[sid].dropna().iloc[-23:].to_numpy(dtype=np.float32)
        for sid in sources_id
    ]).T  # (23, S)
    daily_prod_history = deque(sources_eopy_np, maxlen=23)  # stores one (S,) array per hour

    # What is the daily production in the last 23 hours
    daily_productions = sources_eopy_np.sum(axis=0).copy()  # shape (S,)

    # Cache all sources available capacities.
    sources_available_capacities = pd.DataFrame({
        s.bwf_id: s.available_capacity
        for s in cluster.water_sources
    })
    # When we concat groundwater sources with surface water, the latter have more
    # data points, thus the former have nan on those dates.
    sources_available_capacities.ffill(inplace=True)

    # this dataframe has values only when the value changes, so we need to use 
    # asof(timestamp) to get a value at a given moment in time.
    # we reduce the dataframe to this year for faster lookups with asof
    sources_available_capacities = sources_available_capacities.loc[
        sources_available_capacities.index.year == year
    ]

    # if now is empty, it means there were no reduction in that year, so we just
    # fill it at first of january with each source nominal capacity
    if sources_available_capacities.empty:
        sources_available_capacities = pd.DataFrame({
            s.bwf_id: [s.nominal_capacity]
            for s in cluster.water_sources
        }, index=[year_timesteps[0]])

    # Just convert to numpy for faster lookups
    sources_avcap_timestamps = sources_available_capacities.index
    sources_available_capacities = sources_available_capacities[sources_id].to_numpy(dtype=np.float32)
    avcap_ptr = 0 # at which index of this df we are

    # Cache all sources's pumping station peak discharge
    sources_map_peakq = {
        s.bwf_id: s.pumping_station.peak_discharge(when=year)
        for s in cluster.water_sources
    }
    sources_peak_discharge = np.array([ sources_map_peakq[s]
        for s in sources_id
    ])

    sources_peak_head = np.array([
        po.head_curve.max()
        for po in sources_pump_options
    ])
    sources_target_head_max_speed = np.sqrt(
        sources_target_head / sources_peak_head
    )
    sources_target_head_peak_discharge = sources_peak_discharge * sources_target_head_max_speed
   
    # Create a weeks "full on" pumping station pattern for each pumping station
    pstations_pattern = pd.DataFrame({
        pstation.bwf_id: np.full(
            shape=(24*7,),
            fill_value=len(pstation.active_pumps(when=year)) + 1.0
        )
        for pstation in cluster.pumping_stations
    }).astype(np.float32)

    # Results will be stored here
    sources_productions = np.full(
        shape=(len(year_timesteps), len(sources_id)),
        fill_value=np.float32(np.nan),
        dtype=np.float32
    )
    pumps_energy_usage = np.full(
        shape=(len(year_timesteps), len(pumps_id)),
        fill_value=np.float32(np.nan),
        dtype=np.float32
    )

    # ---- CROSS UTILITIES PIPES
    cross_wu_conn_id = [ c.bwf_id
        for c in cluster.cross_utility_connections
        if c.is_active(year)
    ]
    cross_wu_pipes_id = [ p
        for p in cluster.network.get_all_pipes_id()
        if p[:6] in cross_wu_conn_id
    ]
    cross_wu_pipes_ENidx = [ i
        for p, i in zip(
            cluster.network.get_all_pipes_id(),
            cluster.network.get_all_pipes_idx()
        )
        if p[:6] in cross_wu_conn_id
    ]
    cross_wu_pipes_idx = [i-1 for i in cross_wu_pipes_ENidx]

    cross_wu_pipes_flows = np.full(
        shape=(len(year_timesteps), len(cross_wu_pipes_id)),
        fill_value=np.float32(np.nan),
        dtype=np.float32
    )

    last_working_tidx = -1
    def advance_sim(sidx, eidx):

        net = cluster.network
        assert net is not None
        nonlocal daily_productions, avcap_ptr, last_working_tidx

        apply_demand_patterns(
            net=net,
            demands=national_context.municipalities_total_demands.loc[
                year_timesteps[sidx:eidx]
            ]
        )

        if PUMPING_STATION_REPRESENTATION in [
            PumpingStationRepresentation.FREE_PARALLEL_PUMPS,
            PumpingStationRepresentation.CHOCKED_PARALLEL_PUMPS
        ]:
            hours_2_sim = eidx-sidx
            assert hours_2_sim > 0
            apply_pumping_stations_patterns(
                net=net,
                patterns=pstations_pattern.iloc[-hours_2_sim:, :],
                mapping=pstations_map_pumps_patterns_ENidx
            )

        elif PUMPING_STATION_REPRESENTATION == PumpingStationRepresentation.SINGLE_GPV:
            print("Not implement custom controls on GPVs")

        else:
            # Fixed head variations
            pass # we don't need to change any control
        
        net.openH()
        net.initH(EpanetConstants.EN_INITFLOW)
        for tidx in range(sidx, eidx):
            ts = year_timesteps[tidx]

            # Limit the sources outflow based on the rules:
            # availabile capacity (cap_values) is nominal capacity accounting for the availability factor
            # remove the previous 23 hours production from it to keep the 24-hours below the capacity
            # account for the maximum peak discharge of the pumping station
            while avcap_ptr + 1 < len(sources_avcap_timestamps) and sources_avcap_timestamps[avcap_ptr + 1 ]<= ts:
                avcap_ptr += 1

            sources_current_capacity = np.clip(
                sources_available_capacities[avcap_ptr] - daily_productions,
                a_min=0.0,
                a_max=None
            )
            # Correct for the pumping stations peak_discharge
            sources_current_capacity = np.minimum(
                sources_current_capacity,
                sources_target_head_peak_discharge
            )
            try:

                # todo: handle when capacity is 0...

                if (
                    PUMPING_STATION_REPRESENTATION == PumpingStationRepresentation.CHOCKED_PARALLEL_PUMPS or
                    PUMPING_STATION_REPRESENTATION == PumpingStationRepresentation.CHOCKED_FIXED_HEAD
                ):
                    apply_sources_remaining_capacity_to_fcvs(
                        net=net,
                        sources_capacity=sources_current_capacity,
                        sources_fcv_ENidx=sources_fcv_ENidx
                    )

                if (
                    PUMPING_STATION_REPRESENTATION == PumpingStationRepresentation.CHOCKED_PARALLEL_PUMPS or
                    PUMPING_STATION_REPRESENTATION == PumpingStationRepresentation.FREE_PARALLEL_PUMPS or 
                    PUMPING_STATION_REPRESENTATION == PumpingStationRepresentation.SINGLE_GPV
                ):
                    
                    # Approx with perfect control: we know the exact demands
                    # Get how much is this hour demand with respect to this hour capacity

                    dem_to_cap = municipalities_dem[tidx, :].sum() / sources_peak_discharge.sum()
                    sources_target_flow = sources_current_capacity * dem_to_cap

                    pstation_current_setup = {}
                    for i, source in enumerate(sources_id):
                        n_avail = sources_n_avail_pumps[i]

                        try:
                            n_pumps, pspeed, penergy, peff = get_lowest_energy_pumping_station_setup(
                                target_head=sources_target_head[i],
                                target_flow=sources_target_flow[i],
                                n_available_pumps=sources_n_avail_pumps[i],
                                pump_option=sources_pump_options[i],
                                speed_ratio_bounds=(0.5,1.00),
                                pump_curve_coeffs=tuple(sources_pc_coeff[i, :])
                            )
                        except Exception:
                            # try maxing out
                            n_pumps = n_avail
                            pspeed = 1.0

                        pstation_current_setup[pstations_id[i]] = n_pumps + pspeed

                    apply_pumping_stations_pattern_at(
                        net=net,
                        pattern_row=pstation_current_setup,
                        mapping=pstations_map_pumps_patterns_ENidx,
                        pattern_step=(tidx-sidx)
                    )

                # Run
                net.runH()

                d = np.array(net.getnodevalues(EpanetConstants.EN_DEMAND), dtype=np.float32)
                f = np.array(net.getlinkvalues(EpanetConstants.EN_FLOW), dtype=np.float32)

                # Extract the results
                consumptions_h = d[municipalities_idx]
                productions_h = -d[sources_idx]
                exchanges_h = f[cross_wu_pipes_idx]

                if PUMPING_STATION_REPRESENTATION in [
                    PumpingStationRepresentation.FREE_PARALLEL_PUMPS,
                    PumpingStationRepresentation.CHOCKED_PARALLEL_PUMPS
                ]:
                    e = np.array(net.getlinkvalues(EpanetConstants.EN_ENERGY), dtype=np.float32)

                    energies_h = e[pumps_idx]

                else:
                    energies_h = np.full((len(pumps_id),), fill_value=np.nan, dtype=np.float32)
                    pump_offset = 0

                    for i, source in enumerate(sources_id):
                        n_avail = sources_n_avail_pumps[i]

                        try:
                            n_pumps, pspeed, penergy, peff = get_lowest_energy_pumping_station_setup(
                                target_head=sources_target_head[i],
                                target_flow=productions_h[i],
                                n_available_pumps=sources_n_avail_pumps[i],
                                pump_option=sources_pump_options[i],
                                speed_ratio_bounds=(0.5,1.05),
                                pump_curve_coeffs=tuple(sources_pc_coeff[i, :])
                            )
                            # first n_pumps are running
                            energies_h[pump_offset : pump_offset + n_pumps] = penergy
                            # remaining are off
                            energies_h[pump_offset + n_pumps : pump_offset + n_avail] = 0.0

                        except NoValidPumpConfigurationError:
                            # whole source is off / infeasible: max_energy (we assume you are compensating somehow)
                            energies_h[pump_offset : pump_offset + n_avail] = sources_pump_options[i].break_power_curve.max()

                        pump_offset += n_avail

                # We managed to get to the end of this timestep simulation, results are valid
                last_working_tidx = tidx
            
            except Exception as e:
                # Something din't work out. 
                net_logger = setup_cluster_logger(cluster.filename)

                # If it is the first hour of the sim or it has been failing for 
                # some hours in a row (>2), we just fail the whole network
                if last_working_tidx == -1 or ((tidx-last_working_tidx)>2):
                    productions_h = np.zeros(shape=(len(sources_id),), dtype=np.float32)
                    consumptions_h = np.zeros(shape=(len(municipalities_id),), dtype=np.float32)
                    exchanges_h = np.zeros(shape=(len(cross_wu_pipes_id),), dtype=np.float32)
                    energies_h = np.zeros(shape=(len(pumps_id),), dtype=np.float32)
                    net_logger.error(f"BWF Simulation hour: {ts} | FULL_ERROR | {e}")
                
                else:
                    # it failed on for one hour, probably suboptimal controls in the pumps
                    # we use the "same results" as the previous hours

                    # same share of delivered demand as the last working hour
                    share_deliv = municipalities_consumptions[last_working_tidx, :] / municipalities_dem[last_working_tidx, :]
                    consumptions_h = share_deliv * municipalities_dem[last_working_tidx, :]

                    # Share the demand proportionally between the sources based on their availability
                    productions_h = (consumptions_h.sum()/sources_current_capacity.sum()) * sources_current_capacity

                    # Exchanges are tricky, just use the previous hour result assuming flows are not changing much
                    exchanges_h = cross_wu_pipes_flows[last_working_tidx, :].copy()

                    # Recalculate the energies proportionally to the demand variation
                    demand_ratio = consumptions_h.sum() / municipalities_consumptions[last_working_tidx, :].sum()
                    energies_h = demand_ratio * pumps_energy_usage[last_working_tidx, :] 

                    # Log again but not a full error
                    net_logger.error(f"BWF Simulation hour: {ts} | APPROXIMATED HYDRAULICS because: {e}")

            # Assign the results
            municipalities_consumptions[tidx, :] = consumptions_h
            sources_productions[tidx, :] = productions_h
            cross_wu_pipes_flows[tidx, :] = exchanges_h
            pumps_energy_usage[tidx, :] = energies_h
            # Next
            t = net.nextH()
            # assign back 23 hours ago production, and remove this hour production
            # to mantain the rolling average
            daily_productions -= daily_prod_history[0]
            daily_productions += productions_h
            daily_prod_history.append(productions_h)
        
        net.closeH()
        return
        # End of sim

    # First day of the year, is a holiday, we take the sunday pattern for pumps
    start_idx = 0
    end_idx = 24
    advance_sim(start_idx, end_idx)

    # All other weeks, contigously
    for w in range(0, 52):
        start_idx = 24 + w*7*24
        end_idx = 24 + (w+1)*7*24
        advance_sim(start_idx, end_idx)

    # Done with the simulations
    cluster.network.close()

    # Fix where we don't have values
    municipalities_consumptions = np.nan_to_num(
        municipalities_consumptions,
        nan=0.0
    )
    sources_productions = np.nan_to_num(
        sources_productions,
        nan=0.0
    )
    pumps_energy_usage = np.nan_to_num(
        pumps_energy_usage,
        nan=0.0
    )
    cross_wu_pipes_flows = np.nan_to_num(
        cross_wu_pipes_flows,
        nan=0.0
    )
    
    # Compute undelivered demand
    municipalities_udem = municipalities_dem - municipalities_consumptions
    municipalities_udem = np.clip(
        municipalities_udem,
        a_min=0.0,
        a_max=None
    )

    return BWFHydraulicSimReults(
        undelivered_demands=pd.DataFrame(
            data=municipalities_udem,
            index=year_timesteps,
            columns=municipalities_id
        ),
        pumps_energy_consumption=pd.DataFrame(
            data=pumps_energy_usage,
            index=year_timesteps,
            columns=pumps_id
        ),
        cross_utilities_flows=pd.DataFrame(
            data=cross_wu_pipes_flows,
            index=year_timesteps,
            columns=cross_wu_pipes_id
        ),
        sources_production=pd.DataFrame(
            data=sources_productions,
            index=year_timesteps,
            columns=sources_id
        )
    )
