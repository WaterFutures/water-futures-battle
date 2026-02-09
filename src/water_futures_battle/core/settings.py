from dataclasses import dataclass
from typing import Self, Dict, Any, List

import numpy as np

from .random_manager import RandomManager, FakeLifetimeGenerator

_HISTORICAL_PERIOD_END = 2024

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
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> Self:
        """Primary constructor from config object (dictionary)"""
        return cls(
            start_year=config[cls.START_YEAR],
            end_year=config[cls.END_YEAR],
            _rnd_manager=RandomManager(
                master_seed=config[cls.SEED]
            ),
            lifeline_volume=config[cls.LIFELINE_VOLUME]
        )
    

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
