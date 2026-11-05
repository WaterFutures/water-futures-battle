import copy
import datetime
import math
import sys
from typing import Any, Dict, List, Optional, Self, Set, Tuple, NamedTuple

from epanet_plus import EpanetConstants
import numpy as np
import pandas as pd
try:
    import pygmo
    HAS_PYGMO = True
except ImportError:
    HAS_PYGMO = False

from water_futures_battle.jurisdictions.entities import Province
from water_futures_battle.sources.entities import SourcesContainer
from water_futures_battle.pumps.entities import PumpOption
from water_futures_battle.pumping_stations.entities import PumpingStation

import epanet_utils
import file_utils

# Define the pygmo compatible problem
MIN_VEL = 0.5
MAX_VEL = 2.5
MIN_PRESSURE = 30
PIPE_DECIDER_KWARGS = {
    "no_pipe_option": False
}
NO_PIPE_OPTION_DIAM = 0.0001

class PipeDiamDecider():

    # ******************
    
    MetricsT = Tuple[float, float, float, float, float, float]

    # ******************
    # Constructors and co:
    # init
    # enter, exit, delete
    # deepcopy (to bypass pygmo default deepcopy)
    # close (to release/close the EPANET network)
    # ******************

    def __init__(
            self,
            a_province: Province,
            build_epyt_args: Dict[str, Any],
            optimise_cnns_ages: Dict[str, int],
            optimise_cnns_rel_decay: Dict[str, float],
            no_pipe_option = False
            ):
        
        self.pv_name = a_province.outfiles_name
        
        build_epyt_args['epyt_kwargs'] = {}
        build_epyt_args['epyt_kwargs']['ignore_error_codes'] = [4, 5, 6]
        self.net = epanet_utils.build_epyt(**build_epyt_args)
        self._owns_net = True

        # ----------------------------------------------------------------------
        # Setup helpers for Decision variables
        # ----------------------------------------------------------------------
        # pipe diameters for the peer connections (connection id starts with 'CG')
        # or for the requested links (no check to see if it makes sense)
        # The pipe options is between 1 and 10, with the 0 reserved for the no pipe option.
        # When applying it we will shift down by 1

        # get the EPANET idx of the pipes to optimise
        assert list(optimise_cnns_ages.keys()) == list(optimise_cnns_rel_decay.keys())
        optimise_cnns_ids = list(optimise_cnns_ages.keys())
        pipes_idxs_map = dict(zip(
            self.net.get_all_pipes_id(),
            self.net.get_all_pipes_idx()
        ))
        self.ENidx_opt_pipes = [pipes_idxs_map[c_id] for c_id in optimise_cnns_ids]
        self.idx_opt_pipes = [p_idx-1 for p_idx in self.ENidx_opt_pipes]
        self.ages_opt_pipes = list(optimise_cnns_rel_decay.values())
        self.rel_dec_opt_pipes = list(optimise_cnns_rel_decay.values())
        
        # pygmo requires the number of integer decision variables (all of
        # them here) and the lower and upper bounds. 
        # We set here the variables so that the methods can return these values
        # instead of computing them at runtime every time.        

        # Num. integer decision variables = total number of links to optimise
        self.nidvs = len(self.ENidx_opt_pipes)

        # Lower and upper bounds definition (same for all pipes)
        if no_pipe_option:
            lb = 0
        else:
            lb=1
        ub = len(self.possible_diams)
        self.lb = np.array([lb]*self.nidvs)
        self.ub = np.array([ub]*self.nidvs)

        # ----------------------------------------------------------------------
        # Setup helpers for Fitness functions (Objectives and Constraints):
        # ----------------------------------------------------------------------
        # We use the compute function to calculate a series of metrics.
        # We set a callable object that receives this set of metrics and arrange
        # them into a fitness vector. 

        # 1.------------
        # First metric is the network volume, which is a proxy for cost.
        # 2.------------
        # Second one is the network length, which it doesn't change if the
        # "no pipe option" is disabled
        
        net_volume_min = 0.0
        net_volume_max = 0.0
        net_length_min = 0.0
        net_lenght_max = 0.0
        length_opt_pipes = []
        for pipe_idx in self.ENidx_opt_pipes:
            length:float = self.net.getlinkvalue(pipe_idx, EpanetConstants.EN_LENGTH)

            net_length_min += 0.0 if no_pipe_option else length
            net_lenght_max += length

            length_opt_pipes.append(length)

            min_diameter = 0.0 if no_pipe_option else self.possible_diams[0]
            max_diameter = self.possible_diams[-1]
            
            net_volume_min += length*min_diameter*min_diameter*3.14/4
            net_volume_max += length*max_diameter*max_diameter*3.14/4

        self.net_volume_min = net_volume_min
        self.net_volume_max = net_volume_max   
        self.net_length_min = net_length_min
        self.net_length_max = net_lenght_max
        self.length_opt_pipes = np.array(length_opt_pipes)

        # 3.------------
        # Third metric is the min velocity deviation (towards slower velocities)
        # NOTE: We don't implent an upper bound because on such networks it
        # would create huge frictions, so if it is there is because it is necessary
        # We calculate it only on pipes that we optimise, because on the ones
        # we don't control we have little power over. Also shortens the loop
        self.min_velocity_threshold=0.5 # m/s
        self.total_vel_dev_min = 0.0
        self.total_vel_dev_max = self.min_velocity_threshold * len(self.ENidx_opt_pipes)

        # 4. ------------
        # Fourth metric is the pressure deficit in the municipalities
        # 5. ------------
        # Fifth metric is the undelivered demand.
        # The optimisation should use the pressure deficit if in DDA, the 
        # undelivered demand in PDA.

        # Get the municipalities where we will look for pressure requirements
        junctions_map = zip(self.net.get_all_junctions_idx(), self.net.get_all_junctions_id())
        self.ENidx_municipalities = [m_idx for m_idx, m_id in junctions_map if m_id.startswith('GM')]
        self.idx_municipalities = [m_idx-1 for m_idx in self.ENidx_municipalities]

        self.min_pressure_threshold = 30 # m
        self.total_press_def_min = 0.0
        self.total_press_def_max = self.min_pressure_threshold*len(self.ENidx_municipalities)

        self.total_und_dem_min = 0.0
        self.total_und_dem_max = sum([
            float(self.net.getnodevalue(m_idx, EpanetConstants.EN_BASEDEMAND))
            for m_idx in self.ENidx_municipalities
        ])

        # 6. ------------
        # Sixth metric is the pumps relative use. We care that no pumps breaks
        # this constraint, so, never mind which one or by how much
        self.share_pumps_over_min = 0.0
        self.share_pumps_over_max = 1.0 # 100%
        
        # Track each pump max flowrate to compute this metric
        pumps_max_q = []
        self.pumps_ENidx = []
        self.pumps_idx = []
        for pump_ENidx, pump_id in zip(
            self.net.get_all_pumps_idx(),
            self.net.get_all_pumps_id()
        ):
            curve_idx = int(self.net.getlinkvalue(pump_ENidx, EpanetConstants.EN_PUMP_HCURVE))
            curve_id = self.net.getcurveid(curve_idx)
            curve = self.net.get_curve(curve_id=curve_id)

            max_flow = curve[-1][0]
            pumps_max_q.append(max_flow)
            self.pumps_ENidx.append(pump_ENidx)
            self.pumps_idx.append(pump_ENidx-1)
        self.pumps_max_q = np.array(pumps_max_q)

        # ------------
        # Metrics combiner:
        def make_metrics_combiner(no_pipe_option: bool, pda: bool):
            def metrics_combiner(
                net_volume: float,
                net_length: float,
                total_vel_dev: float,
                total_press_def: float,
                total_und_dem: float,
                share_pumps_over: float
            ) -> Tuple[float, float, float]:
                if no_pipe_option:
                    # If no pipe option is enabled, focus on network length first
                    # and volume after.
                    obj1 = round(net_length, 2) + 0.001 * round(net_volume, 3)
                else:
                    # Otherwise, focus only on network volume
                    obj1 = net_volume

                if pda:
                    # If PDA, use undelivered demand as second objective
                    obj2 = round(total_und_dem, 2) + 0.001 * round(share_pumps_over, 3)
                else:
                    # Otherwise, use pressure deficit
                    obj2 = round(total_press_def, 2) + 0.001 * round(share_pumps_over, 3)

                obj3 = total_vel_dev
                return (obj1, obj2, obj3)
            return metrics_combiner

        # The optimisation uses a different objective if in simulations are run in 
        # PDA or DDA (undelivered demand for the former, DDA for the latter).
        self.pda = build_epyt_args.get('pda', False)

        self.metrics_combiner = make_metrics_combiner(no_pipe_option, self.pda)

        return # end __init__

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
    
    def __deepcopy__(self, memo):
        # Create a shallow copy, but do not copy .net
        copied = type(self).__new__(type(self))
        memo[id(self)] = copied

        for k, v in self.__dict__.items():
            if k == "net":
                setattr(copied, k, self.net) # Share reference, we don't access it from multiple threads
            elif k == "_owns_net":
                setattr(copied, k, False)  # Copies don't own it
            else:
                setattr(copied, k, copy.deepcopy(v, memo))
        return copied
    
    def __del__(self):
        self.close()
        return
    
    def close(self) -> None:
        if self._owns_net and hasattr(self, "net") and self.net is not None:
            self.net.close()
            self.net = None
        return

    # ******************
    # Pygmo mandatory functions
    # get_bounds
    # get_nobj
    # get_fitness
    # to complete the formulation
    # get_nix (number of integer dvs)
    # ******************
    
    def get_bounds(self) -> tuple[np.ndarray, np.ndarray]:
        return (self.lb, self.ub)
    
    def get_nix(self) -> int: 
        return self.nidvs
    
    def get_nobj(self) -> int:
        return 3 # Same number of elements return in the combine
    
    def fitness(self, x: np.ndarray) -> np.ndarray:
        assert self.net is not None, "Calling fitness on copied object. Network has been released from this object."
        
        metrics = self.apply(x).compute(verbose=False)
        
        return np.array(self.metrics_combiner(*metrics))

    # ******************
    # Helper properties and functions
    # possible diams (fix instead of input)
    # metrics best and worst values, nadir and ideal_point for normalisation
    # apply and reset o modify the object with the dvs
    # compute to run calculate the metrics on the applied dv
    # ******************
    @property
    def possible_diams(self) -> list[int]:
        return list(epanet_utils.DIAM_OPTIONS_MAP.keys())

    @property
    def possible_decay_bounds(self) -> list[tuple[float, float]]:
        return list(epanet_utils.DIAM_OPTIONS_DECAY_BOUNDS_MAP.values())

    @property
    def possible_start_ff(self) -> list[float]:
        return list(epanet_utils.DIAM_OPTIONS_NFF_MAP.values())
    
    @property
    def metrics_best_values(self) -> MetricsT:
        return (
            self.net_volume_min,
            self.net_length_min,
            self.total_vel_dev_min,
            self.total_press_def_min,
            self.total_und_dem_min,
            self.share_pumps_over_min
        )
    
    @property
    def metrics_worst_values(self) -> MetricsT:
        return (
            self.net_volume_max,
            self.net_length_max,
            self.total_vel_dev_max,
            self.total_press_def_max,
            self.total_und_dem_max,
            self.share_pumps_over_max
        )
    
    def target(self) -> np.ndarray:
        return np.array(self.metrics_combiner(*self.metrics_best_values))

    def nadir(self) -> np.ndarray:
        return np.array(self.metrics_combiner(*self.metrics_worst_values))

    def apply(self, x: np.ndarray) -> Self:
        assert self.net is not None
        dvs = x.astype(int)
        for i, dv in enumerate(dvs):

            if dv > 0:
                diam = self.possible_diams[dv-1]
                status = EpanetConstants.EN_OPEN

                start_dff = self.possible_start_ff[dv-1]
                decay_bounds_dff = self.possible_decay_bounds[dv-1]
                rel_ub_dff = decay_bounds_dff[1]-decay_bounds_dff[0]
                age = self.ages_opt_pipes[i]
                rel_decay = self.rel_dec_opt_pipes[i]
                dff = (
                    start_dff + # base value
                    age*decay_bounds_dff[0] + # minimum amount due to age
                    rel_decay * rel_ub_dff # relative amount 
                )
            else:
                diam = NO_PIPE_OPTION_DIAM
                status = EpanetConstants.EN_CLOSED
                dff = 128.0
            
            self.net.setlinkvalue(self.ENidx_opt_pipes[i], EpanetConstants.EN_DIAMETER,
                                  value=diam)
            self.net.setlinkvalue(self.ENidx_opt_pipes[i], EpanetConstants.EN_ROUGHNESS,
                                  value=dff)
            self.net.setlinkvalue(self.ENidx_opt_pipes[i], EpanetConstants.EN_STATUS,
                                  value=status)

        return self

    def reset(self, x: np.ndarray) -> Self:
        assert self.net is not None
        return self

    def compute(self, verbose=False) -> MetricsT:
        assert self.net is not None
        try:
            # Run sim
            self.net.openH()
            self.net.initH(EpanetConstants.EN_INITFLOW)
            
            #tstep = 1
            #while tstep > 0:
            t = self.net.runH()
                
            r = np.round(np.array(self.net.getnodevalues(EpanetConstants.EN_PRESSURE)), 2)
            r[r<0] = 0.0 # adjust engative pressure in DDA
            u = np.round(np.array(self.net.getnodevalues(EpanetConstants.EN_DEMANDDEFICIT)), 2)
            v = np.round(np.array(self.net.getlinkvalues(EpanetConstants.EN_VELOCITY)), 2)
            q = np.round(np.abs(np.array(self.net.getlinkvalues(EpanetConstants.EN_FLOW))), 2)
            # tstep = self.net.nextH()
            
            self.net.closeH()
        except Exception as e:
            self.net.closeH()
            
            return self.metrics_worst_values

        # Metric 1: network volume (of optimised pipes)
        diameters = np.array(self.net.getlinkvalues(EpanetConstants.EN_DIAMETER))
        diameters = diameters[self.idx_opt_pipes]

        installed_pipes_mask = diameters < 1
        diameters[installed_pipes_mask] = 0.0
        total_vol = float(np.sum(self.length_opt_pipes * diameters * diameters * 3.14/4))

        # Metric 2: network length (of optimised pipes)
        total_lengths = float(np.sum(self.length_opt_pipes[installed_pipes_mask]))

        # Metric 3: Velocity deviation (of optimised pipes)
        total_vel_dev = float(np.sum(
            np.maximum(self.min_velocity_threshold - v[self.idx_opt_pipes], 0)
        ))

        # Metric 4: Pressure deficit 
        deficit = self.min_pressure_threshold - r
        deficit[deficit < 0] = 0 # Remove the nodes where we actually have surplus 
        total_deficit = float(np.sum(deficit[self.idx_municipalities]))

        total_ud = float(np.sum(u[self.idx_municipalities]))
        
        # Metric 6: Relative source use
        if len(self.pumps_idx) > 0:
            pumps_q = q[self.pumps_idx]
            pumps_over_q = float(np.sum(pumps_q > self.pumps_max_q))/len(self.pumps_idx)
        else:
            pumps_over_q = 0.0

        return (
            total_vol,
            total_lengths,
            total_vel_dev,
            total_deficit,
            total_ud,
            pumps_over_q
        )

class PipeDiamPumpSpeedDecider():

    # ******************
    
    class Metrics(NamedTuple):
        net_volume: float
        net_length: float
        total_velocity_deviation: float
        total_pressure_deficit: float
        total_undelivered_demand: float
        sources_contribution_var: float
        n_shutoff_pumps: int

    # ******************
    # Constructors and co:
    # init
    # enter, exit, delete
    # deepcopy (to bypass pygmo default deepcopy)
    # close (to release/close the EPANET network)
    # ******************

    def __init__(
            self,
            a_province: Province,
            build_epyt_args: Dict[str, Any],
            optimise_cnns_ages: Dict[str, int],
            optimise_cnns_rel_decay: Dict[str, float],
            no_pipe_option = False
            ):
        
        self.pv_name = a_province.outfiles_name
        
        build_epyt_args['epyt_kwargs'] = {}
        build_epyt_args['epyt_kwargs']['ignore_error_codes'] = [4, 5, 6]
        self.net = epanet_utils.build_epyt(**build_epyt_args)
        self._owns_net = True

        # ----------------------------------------------------------------------
        # Setup helpers for Decision variables
        # ----------------------------------------------------------------------
        # pipe diameters for the peer connections (connection id starts with 'CG')
        # or for the requested links (no check to see if it makes sense)
        # The pipe options is between 1 and 10, with the 0 reserved for the no pipe option.
        # When applying it we will shift down by 1

        # get the EPANET idx of the pipes to optimise
        assert list(optimise_cnns_ages.keys()) == list(optimise_cnns_rel_decay.keys())
        optimise_cnns_ids = list(optimise_cnns_ages.keys())
        pipes_idxs_map = dict(zip(
            self.net.get_all_pipes_id(),
            self.net.get_all_pipes_idx()
        ))
        self.ENidx_opt_pipes = [pipes_idxs_map[c_id] for c_id in optimise_cnns_ids]
        self.idx_opt_pipes = [p_idx-1 for p_idx in self.ENidx_opt_pipes]
        self.ages_opt_pipes = list(optimise_cnns_rel_decay.values())
        self.rel_dec_opt_pipes = list(optimise_cnns_rel_decay.values())
        self.opt_pipes_ids = optimise_cnns_ids

        # Pumps speed for the pumping stations, (each pumping stations has a pattern
        # named PSxxx) and its pumps are named PSxxxx-yy. So, we get how many 
        # pumping stations are there counting the patterns with this name, 
        # and assign the pumps to each of them accordingly.
        # We also get what is the source capacity for each pumping station.
        pstat_pumps_map: dict[str, list[int]] = {}
        for pu_id, pu_ENidx in zip(
            self.net.get_all_pumps_id(),
            self.net.get_all_pumps_idx()
        ):
            # Pumping station name is the first 6 chars
            ps_name = pu_id[:6]

            if ps_name not in pstat_pumps_map:
                pstat_pumps_map[ps_name] = []

            pstat_pumps_map[ps_name].append(pu_ENidx)

        pumping_stations: Set[PumpingStation] =  build_epyt_args["all_pumping_stations"]

        self.pstat_ids: list[str] = []
        self.pstat_ENidxs: list[int] = []
        self.pump_off_ENidx = 0
        self.pstat_pumps_ENidxs: list[list[int]] = []
        self.pstat_capacities: list[float] = []
        for pa_id in self.net.get_all_patterns_id():
            
            pa_ENidx = int(self.net.getpatternindex(pattern_id=pa_id))

            if pa_id == 'PUMP_OFF':
                # special pattern for pumps off, save and continue
                self.pump_off_ENidx = pa_ENidx
                continue
            
            if not pa_id.startswith('PS'):
                # Non interesting pattern, just move on and skip the loop
                continue

            if pa_id not in pstat_pumps_map:
                # Pumping station pattern for a non installed pumping station, skip
                continue
            
            self.pstat_ids.append(pa_id)

            # pa_id is a pumping station pattern
            self.pstat_ENidxs.append(pa_ENidx)

            self.pstat_pumps_ENidxs.append(
                pstat_pumps_map[pa_id]
            )   

            # Go in the epyt args and find out this pumping station.
            pumping_station = next((ps for ps in pumping_stations if ps.bwf_id == pa_id), None)
            assert pumping_station is not None

            self.pstat_capacities.append(
                pumping_station.source.nominal_capacity / 24 # m^3/hour
            )
        
        self.pstat_pumps_idxs = [[i-1 for i in sublist] for sublist in self.pstat_pumps_ENidxs]

        # pygmo requires the number of integer decision variables (all of
        # them here) and the lower and upper bounds. 
        # We set here the variables so that the methods can return these values
        # instead of computing them at runtime every time.        
        lb = []
        ub = []
        nidvs = 0
        
        # Pumps speed are continuous, the lower bound is 1 (pumping station not off)
        # the upper bound is n_pumps +1. The integer part indicates the number of 
        # pumps running, the decimal part their speed.
        nidvs_pumpspeeds = 0
        for i, ps_ENidx in enumerate(self.pstat_ENidxs):
            lb.append(1)
            ub.append(len(self.pstat_pumps_ENidxs[i])+1)        
        nidvs += nidvs_pumpspeeds

        # Pipes (discrete and always the same)
        nidvs_pipediam = len(self.ENidx_opt_pipes)
        lb_pipediam = 0 if no_pipe_option else 1
        ub_pipediam = len(self.possible_diams)

        lb += [lb_pipediam]*nidvs_pipediam
        ub += [ub_pipediam]*nidvs_pipediam
        nidvs += nidvs_pipediam
        
        # Convert and store the dv bounds as np array
        self.nidvs = nidvs
        self.lb = np.array(lb)
        self.ub = np.array(ub)

        # ----------------------------------------------------------------------
        # Setup helpers for Fitness functions (Objectives and Constraints):
        # ----------------------------------------------------------------------
        # We use the compute function to calculate a series of metrics.
        # We set a callable object that receives this set of metrics and arrange
        # them into a fitness vector. 

        # 1.------------
        # First metric is the network volume, which is a proxy for cost.
        # 2.------------
        # Second one is the network length, which it doesn't change if the
        # "no pipe option" is disabled
        
        net_volume_min = 0.0
        net_volume_max = 0.0
        net_length_min = 0.0
        net_lenght_max = 0.0
        length_opt_pipes = []
        for pipe_idx in self.ENidx_opt_pipes:
            length:float = self.net.getlinkvalue(pipe_idx, EpanetConstants.EN_LENGTH)

            net_length_min += 0.0 if no_pipe_option else length
            net_lenght_max += length

            length_opt_pipes.append(length)

            min_diameter = 0.0 if no_pipe_option else self.possible_diams[0]
            max_diameter = self.possible_diams[-1]
            
            net_volume_min += length*min_diameter*min_diameter*3.14/4
            net_volume_max += length*max_diameter*max_diameter*3.14/4

        self.net_volume_min = net_volume_min
        self.net_volume_max = net_volume_max   
        self.net_length_min = net_length_min
        self.net_length_max = net_lenght_max
        self.length_opt_pipes = np.array(length_opt_pipes)

        # 3.------------
        # Third metric is the min velocity deviation (towards slower velocities)
        # NOTE: We don't implent an upper bound because on such networks it
        # would create huge frictions, so if it is there is because it is necessary
        # We calculate it only on pipes that we optimise, because on the ones
        # we don't control we have little power over. Also shortens the loop
        self.min_velocity_threshold=0.5 # m/s
        self.total_vel_dev_min = 0.0
        self.total_vel_dev_max = self.min_velocity_threshold * len(self.ENidx_opt_pipes)

        # 4. ------------
        # Fourth metric is the pressure deficit in the municipalities
        # 5. ------------
        # Fifth metric is the undelivered demand.
        # The optimisation should use the pressure deficit if in DDA, the 
        # undelivered demand in PDA.

        # Get the municipalities where we will look for pressure requirements
        junctions_map = zip(self.net.get_all_junctions_idx(), self.net.get_all_junctions_id())
        self.ENidx_municipalities = [m_idx for m_idx, m_id in junctions_map if m_id.startswith('GM')]
        self.idx_municipalities = [m_idx-1 for m_idx in self.ENidx_municipalities]

        self.min_pressure_threshold = 30 # m
        self.total_press_def_min = 0.0
        self.total_press_def_max = self.min_pressure_threshold*len(self.ENidx_municipalities)

        self.total_und_dem_min = 0.0
        self.total_und_dem_max = sum([
            float(self.net.getnodevalue(m_idx, EpanetConstants.EN_BASEDEMAND))
            for m_idx in self.ENidx_municipalities
        ])

        # 6. ------------
        # Sixth metric is the variance between the sources relative use. 
        # Each source has a nominal capacity and we want that each source 
        # contributes more or less the same in proportion to their size.
        # We cap the ratio at 2, so the realtive use goes from 0 to 2.
        # Therefore the variance goes from 0 (all the same ratio) to 1 (half of them
        # on 0 and half of them on 1)
        self.sources_contr_var_min = 0.0
        self.sources_contr_var_max = 1.0

        # 7. ------------
        # Share of pumps that after simulation are in "Pump is closed because it can't
        # deliver head". Those pumps should be off because of the decision variable,
        # not forced by EPANET.
        self.n_shutoff_pumps_min = 0
        self.n_shutoff_pumps_max = int(self.net.get_num_pumps())

        # The optimisation uses a different objective if in simulations are run in 
        # PDA or DDA (undelivered demand for the former, DDA for the latter).
        self.pda = build_epyt_args.get('pda', False)
        # same for the no pipe option
        self.no_pipe_option = no_pipe_option

        return # end __init__

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
    
    def __deepcopy__(self, memo):
        # Create a shallow copy, but do not copy .net
        copied = type(self).__new__(type(self))
        memo[id(self)] = copied

        for k, v in self.__dict__.items():
            if k == "net":
                setattr(copied, k, self.net) # Share reference, we don't access it from multiple threads
            elif k == "_owns_net":
                setattr(copied, k, False)  # Copies don't own it
            else:
                setattr(copied, k, copy.deepcopy(v, memo))
        return copied
    
    def __del__(self):
        self.close()
        return
    
    def close(self) -> None:
        if hasattr(self, "_owns_net") and self._owns_net and hasattr(self, "net") and self.net is not None:
            self.net.close()
            self.net = None
        return

    # ******************
    # Pygmo mandatory functions
    # get_bounds
    # get_nobj
    # get_fitness
    # to complete the formulation
    # get_nix (number of integer dvs)
    # ******************
    
    def get_bounds(self) -> tuple[np.ndarray, np.ndarray]:
        return (self.lb, self.ub)
    
    def get_nix(self) -> int: 
        return self.nidvs
    
    def get_nobj(self) -> int:
        return 3 # Same number of elements return in the combine
    
    def fitness(self, x: np.ndarray) -> np.ndarray:
        assert self.net is not None, "Calling fitness on copied object. Network has been released from this object."
        
        metrics = self.apply(x).compute(verbose=False)
        
        return np.array(self._metrics_to_fitness(metrics))

    # ******************
    # Helper properties and functions
    # possible diams (fix instead of input)
    # metrics best and worst values, nadir and ideal_point for normalisation
    # apply and reset o modify the object with the dvs
    # compute to run calculate the metrics on the applied dv
    # ******************
    @property
    def possible_diams(self) -> list[int]:
        return list(epanet_utils.DIAM_OPTIONS_MAP.keys())[:-1]

    @property
    def possible_decay_bounds(self) -> list[tuple[float, float]]:
        return list(epanet_utils.DIAM_OPTIONS_DECAY_BOUNDS_MAP.values())

    @property
    def possible_start_ff(self) -> list[float]:
        return list(epanet_utils.DIAM_OPTIONS_NFF_MAP.values())
    
    @property
    def n_pumping_stations(self) -> int:
        return len(self.pstat_ENidxs)
    
    @property
    def metrics_best_values(self) -> Metrics:
        return self.Metrics(
            self.net_volume_min,
            self.net_length_min,
            self.total_vel_dev_min,
            self.total_press_def_min,
            self.total_und_dem_min,
            self.sources_contr_var_min,
            self.n_shutoff_pumps_min
        )
    
    @property
    def metrics_worst_values(self) -> Metrics:
        return self.Metrics(
            self.net_volume_max,
            self.net_length_max,
            self.total_vel_dev_max,
            self.total_press_def_max,
            self.total_und_dem_max,
            self.sources_contr_var_max,
            self.n_shutoff_pumps_max
        )
    
    def target(self) -> np.ndarray:
        return np.array(self._metrics_to_fitness(self.metrics_best_values))

    def nadir(self) -> np.ndarray:
        return np.array(self._metrics_to_fitness(self.metrics_worst_values))

    def apply(self, x: np.ndarray) -> Self:
        assert self.net is not None

        n_pstat = self.n_pumping_stations
        pump_speeds = x[:n_pstat]
        pipe_diams = x[n_pstat:]

        self.apply_pump_speeds(pump_speeds)
        self.apply_pipe_diams(pipe_diams)

        return self

    def apply_pump_speeds(self, x: np.ndarray) -> Self:
        assert self.net is not None

        dvs = x.astype(float)
        for i, dv in enumerate(dvs):

            # get the pumps in pstation
            pstat_pumps_ENidxs = self.pstat_pumps_ENidxs[i]

            # integer part: number of pumps on in the pumping station,
            # decimal part: pumps' speed (of those on)
            n_pumps_on = math.ceil(dv)-1
            pumps_speed = dv-n_pumps_on

            # fix the pumping station velocity in the pattern
            pstat_ENidx = self.pstat_ENidxs[i]
            self.net.setpatternvalue(
                pstat_ENidx,
                period=1,
                value=pumps_speed
            )
            
            # Assign which pumps follow the pumping station pattern, and which one 
            # are off.
            for j, pump_ENidx in enumerate(pstat_pumps_ENidxs, start=1):

                if j <= n_pumps_on:
                    # Pump is on, 
                    self.net.set_pump_pattern(
                        pump_idx=pump_ENidx,
                        pattern_idx=pstat_ENidx
                    )

                else:
                    # Pump is off (common pattern)
                    self.net.set_pump_pattern(
                        pump_idx=pump_ENidx,
                        pattern_idx=self.pump_off_ENidx
                    )

        return self
        
    def apply_pipe_diams(self, x: np.ndarray) -> Self:
        assert self.net is not None

        dvs = x.astype(int)
        for i, dv in enumerate(dvs):

            if dv > 0:
                diam = self.possible_diams[dv-1]
                status = EpanetConstants.EN_OPEN

                start_dff = self.possible_start_ff[dv-1]
                decay_bounds_dff = self.possible_decay_bounds[dv-1]
                rel_ub_dff = decay_bounds_dff[1]-decay_bounds_dff[0]
                age = self.ages_opt_pipes[i]
                rel_decay = self.rel_dec_opt_pipes[i]
                dff = (
                    start_dff + # base value
                    age*decay_bounds_dff[0] + # minimum amount due to age
                    rel_decay * rel_ub_dff # relative amount 
                )
            else:
                diam = NO_PIPE_OPTION_DIAM
                status = EpanetConstants.EN_CLOSED
                dff = 128.0
            
            self.net.setlinkvalue(self.ENidx_opt_pipes[i], EpanetConstants.EN_DIAMETER,
                                  value=diam)
            self.net.setlinkvalue(self.ENidx_opt_pipes[i], EpanetConstants.EN_ROUGHNESS,
                                  value=dff)
            self.net.setlinkvalue(self.ENidx_opt_pipes[i], EpanetConstants.EN_STATUS,
                                  value=status)

        return self

    def reset(self, x: np.ndarray) -> Self:
        assert self.net is not None
        return self

    def compute(self, verbose=False) -> Metrics:
        assert self.net is not None
        try:
            # Run sim
            self.net.openH()
            self.net.initH(EpanetConstants.EN_INITFLOW)
            
            #tstep = 1
            #while tstep > 0:
            t = self.net.runH()
                
            r = np.round(np.array(self.net.getnodevalues(EpanetConstants.EN_PRESSURE)), 2)
            r[r<0] = 0.0 # adjust engative pressure in DDA
            u = np.round(np.array(self.net.getnodevalues(EpanetConstants.EN_DEMANDDEFICIT)), 2)
            v = np.round(np.array(self.net.getlinkvalues(EpanetConstants.EN_VELOCITY)), 2)
            q = np.round(np.abs(np.array(self.net.getlinkvalues(EpanetConstants.EN_FLOW))), 2)
            s = np.array(self.net.getlinkvalues(EpanetConstants.EN_PUMP_STATE)).astype(int)
            # tstep = self.net.nextH()
            
            self.net.closeH()
        except Exception as e:
            self.net.closeH()
            
            return self.metrics_worst_values

        # Metric 1: network volume (of optimised pipes)
        diameters = np.array(self.net.getlinkvalues(EpanetConstants.EN_DIAMETER))
        diameters = diameters[self.idx_opt_pipes]

        installed_pipes_mask = diameters < 1
        diameters[installed_pipes_mask] = 0.0
        total_vol = float(np.sum(self.length_opt_pipes * diameters * diameters * 3.14/4))

        # Metric 2: network length (of optimised pipes)
        total_lengths = float(np.sum(self.length_opt_pipes[installed_pipes_mask]))

        # Metric 3: Velocity deviation (of optimised pipes)
        total_vel_dev = float(np.sum(
            np.maximum(self.min_velocity_threshold - v[self.idx_opt_pipes], 0)
        ))

        # Metric 4: Pressure deficit 
        deficit = self.min_pressure_threshold - r
        deficit[deficit < 0] = 0 # Remove the nodes where we actually have surplus 
        total_deficit = float(np.sum(deficit[self.idx_municipalities]))

        total_ud = float(np.sum(u[self.idx_municipalities]))
        
        # Metric 6: Variance of the sources relative contribution,
        # plus, adjust for pumps delivering too much flow (consider that as ud)
        sources_contributions = []
        shutoff_pumps_counter = 0
        for pstat_pumps_idxs, pstat_capacity in zip(
            self.pstat_pumps_idxs,
            self.pstat_capacities
        ):
            pstat_actual_flow = float(np.sum(q[pstat_pumps_idxs]))

            pstat_rel_contr = pstat_actual_flow/pstat_capacity

            # cap at 2, so that alos we bound the max variance
            pstat_rel_contr = min(pstat_rel_contr, 2.0)

            sources_contributions.append(pstat_rel_contr)

            # Consider the flow out of pumps that are exceeding their maximum flow
            # as undelivered demand to promote a proper use.
            pumps_overflowing = np.array(pstat_pumps_idxs)[
                s[pstat_pumps_idxs] == EpanetConstants.EN_PUMP_XFLOW
            ]
            overdelivered_water = float(np.sum(q[pumps_overflowing]))

            # Count how many pumps are being shutoff (the dv could have shut them 
            # off instead of EPANET)
            shutoff_pumps_counter += sum(s[pstat_pumps_idxs] == EpanetConstants.EN_PUMP_XHEAD)

            total_ud += overdelivered_water

        sources_contributions = np.array(sources_contributions)
        sources_contributions_var = float(np.var(sources_contributions))

        return self.Metrics(
            total_vol,
            total_lengths,
            total_vel_dev,
            total_deficit,
            total_ud,
            sources_contributions_var,
            shutoff_pumps_counter
        )
    
    def _metrics_to_fitness(self, metrics: Metrics) -> tuple[float, float, float]:
        return (
            self._make_obj1(
                net_volume=metrics.net_volume,
                total_vel_dev=metrics.total_velocity_deviation,
                net_length=metrics.net_length
            ),
            self._make_obj2(
                total_press_def=metrics.total_pressure_deficit,
                total_und_dem=metrics.total_undelivered_demand
            ),
            self._make_obj3(
                sources_contr_var=metrics.sources_contribution_var,
                n_shutoff_pumps=metrics.n_shutoff_pumps
            )
        )

    def _make_obj1(
            self,
            net_volume: float,
            total_vel_dev: float,
            net_length: float
        ) -> float:

        norm_net_volume = (net_volume - self.net_volume_min) / (
            self.net_volume_max - self.net_volume_min
        )
        return np.clip(norm_net_volume, 0.0, 1.0)
    
        norm_total_vel_dev = (total_vel_dev - self.total_vel_dev_min) / (
            self.total_vel_dev_max - self.total_vel_dev_min
        )

        if not self.no_pipe_option:
            return round(norm_net_volume, 6) + 1e-7 * norm_total_vel_dev
        
        # we have the no pipe option, so we want to have the longest possible net
        # (min pipes deactivated) possible before cons

        norm_net_length = (net_length - self.net_length_min) / (
            self.net_length_max - self.net_length_min
        )

        raise NotImplementedError            

    def _make_obj2(
            self,
            total_press_def: float,
            total_und_dem: float
        ) -> float:

        if self.pda:
            norm_total_und_dem = (total_und_dem - self.total_und_dem_min) / (
                self.total_und_dem_max - self.total_und_dem_min
            )
            return np.clip(norm_total_und_dem, 0.0, 1.0)
        else:
            norm_total_press_def = (total_press_def - self.total_press_def_min) / (
                self.total_press_def_max - self.total_press_def_min
            )
            return np.clip(norm_total_press_def, 0.0, 1.0)
        
    def _make_obj3(
            self,
            sources_contr_var: float,
            n_shutoff_pumps: float,
        ) -> float:
        norm_sources_contr_var = (sources_contr_var - self.sources_contr_var_min) / (
            self.sources_contr_var_max - self.sources_contr_var_min
        )

        norm_n_shutoff_pumps = (n_shutoff_pumps - self.n_shutoff_pumps_min) / (
            self.n_shutoff_pumps_max - self.n_shutoff_pumps_min
        )

        return np.clip(
            round(norm_sources_contr_var, 3) + 1e-4*norm_n_shutoff_pumps,
            0.0,
            1.0
        )

