from dataclasses import dataclass
from typing import Self, Dict, Any, List

@dataclass(frozen=True)
class Settings:
    LABEL = 'settings'

    START_YEAR = 'start_year'
    END_YEAR = 'end_year'
    start_year: int
    end_year: int
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> Self:
        """Primary constructor from config object (dictionary)"""
        return cls(
            start_year=config[cls.START_YEAR],
            end_year=config[cls.END_YEAR]
        )
    
    @property
    def years_to_simulate(self) -> List[int]:
        return list(range(self.start_year, self.end_year+1))
    
    @property
    def n_years_to_simulate(self) -> int:
        return len(self.years_to_simulate)