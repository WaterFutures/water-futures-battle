import datetime
import sys
from typing import Dict, List, Tuple, NamedTuple

import numpy as np
import pandas as pd
try:
    import pygmo
    HAS_PYGMO = True
except ImportError:
    HAS_PYGMO = False

from water_futures_battle.jurisdictions.entities import Province

import epanet_utils
import file_utils

class OptimisationResult(NamedTuple):
    decisions: Dict[Tuple[int,int], np.ndarray]
    fitnesses: Dict[Tuple[int,int], np.ndarray]
    target: np.ndarray
    nadir: np.ndarray
    pipediam_dv_shift: int
    pumping_stations_ids: List[str]
    connection_ids: List[str]

import opt_state

def optimise_province_cnns(
        run_optimisation: bool,
        province_name: str,
        province_id: str,
        idx: int,
        algo_seed: int,
        pop_seed: int
    ) -> OptimisationResult:
        
        island_results = file_utils.upload_results(
            province_name=province_name,
            idx=idx
        )

        if island_results:
            return island_results

        if not run_optimisation or not HAS_PYGMO:
            problem = opt_state.get_problem(province_id)
            island_results = OptimisationResult(
                decisions={},
                fitnesses={},
                target=problem.target(),
                nadir=problem.nadir(),
                pipediam_dv_shift=problem.n_pumping_stations,
                pumping_stations_ids=problem.pstat_ids,
                connection_ids=problem.opt_pipes_ids
            )

        # We definitely need the optimisation, print the time
        print(datetime.datetime.now())

        problem = opt_state.get_problem(province_id)
        N_GENERATIONS = max(500, 20*len(problem.get_bounds()[0]))
        N_INDIVIDUALS = max(200, 8*len(problem.get_bounds()[0]))
        island_results = OptimisationResult(
            decisions={},
            fitnesses={},
            target=problem.target(),
            nadir=problem.nadir(),
            pipediam_dv_shift=problem.n_pumping_stations,
            pumping_stations_ids=problem.pstat_ids,
            connection_ids=problem.opt_pipes_ids
        )
        
        pgprob = pygmo.problem(problem)

        N_INTERVALS = 20
        N_INTERVAL_GEN = N_GENERATIONS // N_INTERVALS

        generation = 0
        pop = pygmo.population(
            pgprob,
            size=N_INDIVIDUALS,
            seed=pop_seed
        )
    
        algo = pygmo.algorithm(pygmo.nsga2(
            gen=N_INTERVAL_GEN,
            seed=algo_seed
        ))
    
        # Save inital population
        island_results.decisions[(idx, generation)] = pop.get_x()
        island_results.fitnesses[(idx, generation)] = pop.get_f()

        for generation in range(0, N_GENERATIONS+N_INTERVAL_GEN, N_INTERVAL_GEN):
            print(f"PV {province_name} at {generation} out of {N_GENERATIONS+N_INTERVAL_GEN}")
            
            pop = algo.evolve(pop)

            island_results.decisions[(idx, generation)] = pop.get_x()
            island_results.fitnesses[(idx, generation)] = pop.get_f()    

        print(datetime.datetime.now())

        file_utils.save_results(
            province_name=province_name,
            idx=idx,
            result=island_results
        )

        return island_results

class OptimisationMetrics(NamedTuple):
    decisions: Dict[int, np.ndarray]
    fitnesses: Dict[int, np.ndarray]
    hypervolumes: Dict[Tuple[int, int], float]
    global_hypervolumes: Dict[int, float]
    pareto_front_decisions: np.ndarray
    pareto_front_fitnesses: np.ndarray
        
if HAS_PYGMO:
    def compute_final_metrics(
        result: OptimisationResult
    ) -> OptimisationMetrics:

        normalization_range = result.nadir - result.target
        reference_point = [1.0+1e-6]*len(result.nadir)

        # --- Step 2: Set Normalized Reference Point and Prepare HV Calculator ---
        all_decisions = {}
        all_fitnesses = {}
        hvs = {}
        for (isl, gen), current_fitnesses in result.fitnesses.items():
            
            is_finite_mask_2d = np.isfinite(current_fitnesses) & (current_fitnesses != sys.float_info.max)
            mask = is_finite_mask_2d.all(axis=1)
            current_fitnesses = current_fitnesses[mask]

            if len(current_fitnesses) == 0:
                hvs[(isl, gen)] = 0.0

            else:
                normalized_fitnesses = (current_fitnesses - result.target) / normalization_range

                hv_value = pygmo.hypervolume(normalized_fitnesses).compute(reference_point)

                hvs[(isl, gen)] = hv_value

            if gen not in all_decisions:
                all_decisions[gen] = result.decisions[(isl, gen)]
            else:
                all_decisions[gen] = np.concat([all_decisions[gen], result.decisions[(isl, gen)]], axis=0)
            if gen not in all_fitnesses:
                all_fitnesses[gen] = current_fitnesses
            else:
                all_fitnesses[gen] = np.concat([all_fitnesses[gen], current_fitnesses], axis=0)

        global_hvs = {}
        for gen, current_fitnesses in all_fitnesses.items():
            ndf, dl, dc, ndr = pygmo.fast_non_dominated_sorting(points=current_fitnesses)

            pf = ndf[0]
            all_fitnesses[gen] = current_fitnesses[pf, :]
            all_decisions[gen] = all_decisions[gen][pf, :]

            global_hvs[gen] = pygmo.hypervolume(current_fitnesses[pf, :]).compute(reference_point)

        LAST_GEN = max(all_fitnesses.keys())
        fits = all_fitnesses[LAST_GEN]

        # The interesting solutions are those with the minimum obj 2
        min_obj2 = np.min(fits[:, 1])
        min_obj2_mask = fits[:, 1] == min_obj2
            
        return OptimisationMetrics(
            decisions=all_decisions,
            fitnesses=all_fitnesses,
            hypervolumes=hvs,
            global_hypervolumes=global_hvs,
            pareto_front_decisions=all_decisions[LAST_GEN][min_obj2_mask, :].copy(),
            pareto_front_fitnesses=all_fitnesses[LAST_GEN][min_obj2_mask, :].copy()
        )

def _replace_options(
        all_connections_df: pd.DataFrame,
        origin_df: pd.DataFrame,
        a_province: Province,
        pipes_roughnesses_history: pd.DataFrame,
        cnns_rel_decay_history: Dict[str, float],
        cnns_ages_in_2000: Dict[str, int]
    ) -> None:

    pv_mask = all_connections_df['province'] == a_province.cbs_id

    # Bulk updates of pd.dataframes
    upt_connections_pipe_options = {}
    upt_pipe_rghn = {}
    for conn_id, conn_data in all_connections_df[pv_mask].iterrows():

        # If it was not something that we wanted to optimise, leave unchanged
        if not conn_data['optimisable'] or conn_data['pipes-option_ids'] == '':
            continue

        pipes_option_ids = str(origin_df.loc[str(conn_id), 'pipes-option_ids'])

        # If we don't have a value, we remove the pipe
        if pipes_option_ids == '' or pipes_option_ids == 'nan':
            all_connections_df.loc[str(conn_id), [
                'pipes-option_ids',
                'pipes-installation_dates'
            ]] = ['', pd.NaT]
            continue
        
        # pipes_option_ids may not be a simple string with the pipe option if it 
        # is coming from a backup dataframe. In that case, it could have multiple 
        # values (in theory identical). we take the first.
        pipe_option_id = str(pipes_option_ids).split(';')[0].strip()
        
        # assign the option
        upt_connections_pipe_options[str(conn_id)] = pipe_option_id

        # finally, we know the option so we can also derive the real roughness of the pipe
        # in 2000
        start_dff = epanet_utils.DIAM_OPTIONS_NFF_MAP[pipe_option_id]
        decay_bounds_dff = epanet_utils.DIAM_OPTIONS_DECAY_BOUNDS_MAP[pipe_option_id]
        rel_ub_dff = decay_bounds_dff[1]-decay_bounds_dff[0]
        age = cnns_ages_in_2000[str(conn_id)]
        rel_decay = cnns_rel_decay_history[str(conn_id)]
        pipe_roughness = (
            start_dff + # base value
            age*decay_bounds_dff[0] + # minimum amount due to age
            rel_decay * rel_ub_dff # relative amount 
        )
        upt_pipe_rghn[str(conn_id)+'-00'] = pipe_roughness

    # Finalise bulk update
    all_connections_df.loc[
        list(upt_connections_pipe_options.keys()),
        'pipes-option_ids'
    ] = list(upt_connections_pipe_options.values())

    pipes_roughnesses_history.loc[
        pd.to_datetime("2000-01-01"),
        list(upt_pipe_rghn.keys())
    ] = list(upt_pipe_rghn.values())

    return

def replace_options_with_backup(
        all_connections_df: pd.DataFrame,
        backup_df: pd.DataFrame,
        a_province: Province,
        pipes_roughnesses_history: pd.DataFrame,
        cnns_rel_decay_history: Dict[str, float],
        cnns_ages_in_2000: Dict[str, int]
    ) -> None:

    return _replace_options(
        all_connections_df=all_connections_df,
        origin_df=backup_df,
        a_province=a_province,
        pipes_roughnesses_history=pipes_roughnesses_history,
        cnns_rel_decay_history=cnns_rel_decay_history,
        cnns_ages_in_2000=cnns_ages_in_2000
    )


def replace_options_with_selected_solution(
        all_connections_df: pd.DataFrame,
        a_province: Province,
        opt_results: OptimisationResult,
        opt_metrics: OptimisationMetrics,
        select_sol_idx: int,
        pipes_roughnesses_history: pd.DataFrame,
        cnns_rel_decay_history: Dict[str, float],
        cnns_ages_in_2000: Dict[str, int]
    ) -> Dict[str, float]:

    # Take from the optimisation information, which IDS were optimised, they will be our index
    opt_cnns_ids = opt_results.connection_ids

    # While from the metrics, we take the selected solution
    solution_dvs = opt_metrics.pareto_front_decisions[select_sol_idx, :]

    # Account for the first n decision variables being a pumping station speed (if that problem was used)
    pipediam_shift_dvs = opt_results.pipediam_dv_shift
    pumpspeed_dvs = solution_dvs[:pipediam_shift_dvs] 
    pipediam_dvs = solution_dvs[pipediam_shift_dvs:]

    options_ids = list(epanet_utils.DIAM_OPTIONS_MAP.values())
    solution_option_ids = [options_ids[int(i)-1] if i > 0 else '' for i in pipediam_dvs]

    print(solution_option_ids)

    # It makes sense adding the pump speeds if they are there
    if pipediam_shift_dvs > 0:
        ps_speeds = dict(zip(
            opt_results.pumping_stations_ids,
            pumpspeed_dvs
        ))
    else:
        ps_speeds = {}
        
    
    selected_sol_df = pd.DataFrame(
        data={'pipes-option_ids': solution_option_ids},
        index=[str(i) for i in opt_cnns_ids]
    )

    _replace_options(
        all_connections_df=all_connections_df,
        origin_df=selected_sol_df,
        a_province=a_province,
        pipes_roughnesses_history=pipes_roughnesses_history,
        cnns_rel_decay_history=cnns_rel_decay_history,
        cnns_ages_in_2000=cnns_ages_in_2000
    )

    return ps_speeds