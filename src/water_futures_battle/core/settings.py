from dataclasses import dataclass, field
from importlib.resources import files
from typing import Self, Dict, Any, List

import numpy as np
import pandas as pd

from .random_manager import RandomManager, FakeLifetimeGenerator

_HISTORICAL_PERIOD_END = 2024

_COST_NORMALISATION = True # Triggers the use of the cost normalisation dataframe in the water utility balances

def load_cost_normalisation_df() -> pd.DataFrame:
    path = files("water_futures_battle.core").joinpath("cost_normalisation.csv")
    with path.open("r") as f:
        return pd.read_csv(f, index_col='year')
    
try:
    _cost_normalisation_df = load_cost_normalisation_df()
except Exception:
    _cost_normalisation_df = pd.DataFrame(columns=[f"WU{i:02d}" for i in range(1, 11)])

@dataclass(frozen=True)
class Settings:
    LABEL = 'settings'

    START_YEAR = 'start_year'
    END_YEAR = 'end_year'
    start_year: int
    end_year: int

    _rnd_manager: RandomManager
    SEED = 'seed'

    lifeline_volume: float
    LIFELINE_VOLUME = 'lifeline_volume'

    national_investment_budget: float
    NIB='national_budget'

    AVAILABLE_CORES = 'available_cores'
    available_cores: int

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> Self:
        """Primary constructor from config object (dictionary)"""
        global _COST_NORMALISATION
        _COST_NORMALISATION = config.get('_cost_normalisation', True)
        return cls(
            start_year=config[cls.START_YEAR],
            end_year=config[cls.END_YEAR],
            _rnd_manager=RandomManager(
                master_seed=config[cls.SEED]
            ),
            lifeline_volume=config[cls.LIFELINE_VOLUME],
            national_investment_budget=config.get(cls.NIB, 0),
            available_cores=config.get(cls.AVAILABLE_CORES, 1),
        )
    
    def __post_init__(self):
        
        for year in self.years_to_simulate:
            if year not in _cost_normalisation_df.index:
                _cost_normalisation_df.loc[year] = {
                    f"WU{i:02d}": 0.0
                    for i in range(1, 11)
                }

    @property
    def years_to_simulate(self) -> List[int]:
        return list(range(self.start_year, self.end_year+1))

    @property
    def n_years_to_simulate(self) -> int:
        return len(self.years_to_simulate)

    @property
    def _is_simulating_historical_period(self) -> bool:
        return self.end_year <= _HISTORICAL_PERIOD_END

    def get_random_generator(self, name: str) -> np.random.Generator:

        # Handle the case where pumps and pipes lifetime do not need to be sampled
        # because in the historical period, they are generated in the pre-processing scripts
        if self._is_simulating_historical_period and (
            name == 'pipes-lifetime' or name == 'pumps-lifetime'
        ):
            return FakeLifetimeGenerator(fixed_value=200)  # type: ignore

        # Else, default behaviour
        return self._rnd_manager.get(module_name=name)

    @property
    def residential_p_weight_rng(self) -> np.random.Generator:
        return self.get_random_generator('municipalities-res_p_weight')

    @property
    def pipes_frict_f_decay_rng(self) -> np.random.Generator:
        return self.get_random_generator('pipes-fric_f_decay')

    @property
    def pipes_lifetime_rng(self) -> np.random.Generator:
        return self.get_random_generator('pipes-lifetime')
    
    @property
    def solar_radiation_pvlib_year_rng(self) -> np.random.Generator:
        return self.get_random_generator('solar_radiation-pvlib_year')
    
    @property
    def sources_fixed_opex_uc_rng(self) -> np.random.Generator:
        return self.get_random_generator('sources-opex-fixed')

    @property
    def sources_vol_other_opex_uc_rng(self) -> np.random.Generator:
        return self.get_random_generator('sources-opex-volum-other')
    
    def _cost_normalization(self, year: int, wu_id: str) -> float:
        if not _COST_NORMALISATION:
            return 0.0
        return float(_cost_normalisation_df.loc[year, wu_id])
