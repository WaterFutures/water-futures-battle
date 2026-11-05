from typing import Dict, Set

import pandas as pd

# Reconstruct the system resources (states, sources, pumping stations)
from water_futures_battle.core import Settings
from water_futures_battle.jurisdictions import build_state, State
from water_futures_battle.sources import build_sources
from water_futures_battle.sources.entities import SourcesContainer
from water_futures_battle.pumps import PumpOption
from water_futures_battle.pumping_stations import build_pumping_infrastructure, PumpingStation

_netherlands: State | None = None
_all_sources: SourcesContainer | None = None
_pump_options: Set[PumpOption] | None = None
_all_pumping_stations: Set[PumpingStation] | None = None

_munic_demands: Dict[str, float] | None = None
_all_connections_df: pd.DataFrame | None = None
_pipe_options_df: pd.DataFrame | None = None
_pipes_roughnesses_history: pd.DataFrame | None = None
_cnns_rel_decay_history: Dict[str, float] | None = None
_cnns_ages_in_2000: Dict[str, int] | None = None
_no_pipe_option: bool | None = None

from opt_problems import PipeDiamPumpSpeedDecider as Problem
_problem: Problem = None

def init_worker(
        settings_desc,
        nl_desc,
        sources_desc,
        pumping_desc,
        munic_demands: Dict[str, float],
        all_connections_df: pd.DataFrame,
        pipe_options_df: pd.DataFrame,
        pipes_roughnesses_history: pd.DataFrame,
        cnns_rel_decay_history: Dict[str, float],
        cnns_ages_in_2000: Dict[str, int],
        no_pipe_option = False
        ):
    global _settings
    global _netherlands
    global _all_sources
    global _pump_options
    global _all_pumping_stations
    global _munic_demands
    global _all_connections_df
    global _pipe_options_df
    global _pipes_roughnesses_history
    global _cnns_rel_decay_history
    global _cnns_ages_in_2000
    global _no_pipe_option

    settings = Settings.from_config(settings_desc)

    _netherlands = build_state(
        nl_desc,
        data_path='../../jurisdictions/',
        settings=settings
    )

    _all_sources, sources_settings = build_sources(
        sources_desc,
        a_state=_netherlands,
        data_path='../../sources/',
        settings=settings
    )
    _pump_options, _all_pumping_stations = build_pumping_infrastructure(
        desc=pumping_desc,
        sources=_all_sources,
        data_path='../../',
        settings=settings
    )

    _munic_demands = munic_demands
    _all_connections_df = all_connections_df
    _pipe_options_df = pipe_options_df
    _pipes_roughnesses_history = pipes_roughnesses_history
    _cnns_rel_decay_history = cnns_rel_decay_history
    _cnns_ages_in_2000 = cnns_ages_in_2000
    _no_pipe_option = no_pipe_option

def get_problem(province_id: str) -> Problem:

    # Assert all required module variables are initialized
    assert _netherlands is not None, "_netherlands must be initialized by init_worker"
    assert _all_sources is not None, "_all_sources must be initialized by init_worker"
    assert _pump_options is not None, "_pump_options must be initialized by init_worker"
    assert _all_pumping_stations is not None, "_all_pumping_stations must be initialized by init_worker"
    assert _munic_demands is not None, "_munic_demands must be initialized by init_worker"
    assert _all_connections_df is not None, "_all_connections_df must be initialized by init_worker"
    assert _pipe_options_df is not None, "_pipe_options_df must be initialized by init_worker"
    assert _pipes_roughnesses_history is not None, "_pipes_roughnesses_history must be initialized by init_worker"
    assert _cnns_rel_decay_history is not None, "_cnns_rel_decay_history must be initialized by init_worker"
    assert _cnns_ages_in_2000 is not None, "_cnns_ages_in_2000 must be initialized by init_worker"
    assert _no_pipe_option is not None, "_no_pipe_option must be initialized by init_worker"

    province = _netherlands.province(province_id)

    pv_connections_df = _all_connections_df[_all_connections_df['province'] == province.cbs_id].copy()

    epyt_args = {
        "province": province,
        "munic_demands": _munic_demands,
        "all_sources": _all_sources,
        "pump_options": _pump_options,
        "all_pumping_stations": _all_pumping_stations,
        "year": 2000,
        "connections_df": pv_connections_df,
        "dates_as_str": False,
        "pipe_options_df": _pipe_options_df,
        "pipes_roughnesses_history": _pipes_roughnesses_history,
        "situation_name": None,
        "pda": True,
        "future_sources": False,
        "pumping_station_representation": "free_parallel_pumps",
    }

    # Optimize only optimisable pipes
    MASK_CNNS2OPT = (
        pv_connections_df['optimisable'] &
        pv_connections_df['pipes-option_ids'].notna() & 
        (pv_connections_df['pipes-option_ids'] != '')
    )
    CNNS2OPT_IDS: list[str] = pv_connections_df.index[MASK_CNNS2OPT].to_list()

    cnns2opt_ages = {
        c: _cnns_ages_in_2000[c]
        for c in CNNS2OPT_IDS
    }

    cnns2opt_reldecay = {
        c: _cnns_rel_decay_history[c]
        for c in CNNS2OPT_IDS
    }

    global _problem
    _problem = Problem(
        a_province=province,
        build_epyt_args=epyt_args,
        optimise_cnns_ages=cnns2opt_ages,
        optimise_cnns_rel_decay=cnns2opt_reldecay,
        no_pipe_option=_no_pipe_option
    )

    return _problem