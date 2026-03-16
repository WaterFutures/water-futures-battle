from typing import Any, Dict, Set,Optional

from ..core.utility import timestampify
from ..water_utilities import WaterUtility

class BudgetAllocation:
    NAME = 'budget_allocation'
 
    BY_POPULATION = "by_population"
    BY_INVERSE_POPULATION = "by_inverse_population"
    BY_INCOME = "by_income"
    BY_INVERSE_INCOME = "by_inverse_income"
    CUSTOM = "custom"

    @classmethod
    def distribute_budget_population(
            cls, 
            budget: float,
            water_utilities: Set[WaterUtility],
            year: int
        ) -> Dict[str, float]:
        
        populations = {
            wu.bwf_id: wu.population.loc[timestampify(year)]
           for wu in water_utilities
        }
        total_population = sum(populations.values())
        
        return {
            wu_id: (pop / total_population) * budget
            for wu_id, pop in populations.items()
        }
    
    @classmethod
    def distribute_inverse_budget_population(
            cls,
            budget: float,
            water_utilities: Set[WaterUtility],
            year: int
        ) -> Dict[str, float]: 

        inv_populations = {
            wu.bwf_id: 1/wu.population.loc[timestampify(year)]
           for wu in water_utilities
        }
        total_population = sum(inv_populations.values())
        
        return {
            wu_id: (pop / total_population) * budget
            for wu_id, pop in inv_populations.items()
        }
        
    @classmethod
    def distribute_budget_income(
            cls,
            budget: float,
            water_utilities: Set[WaterUtility],
            year: int
        ) -> Dict[str, float]:
        
        incomes = {
            wu.bwf_id: wu.disp_income_avg.loc[timestampify(year)]
            for wu in water_utilities
        }
        total_income = sum(incomes.values())

        return {
            wu_id: (income / total_income) * budget
            for wu_id, income in incomes.items()
        }
    
    @classmethod    
    def distribute_reverse_budget_income(
            cls,
            budget: float,
            water_utilities: Set[WaterUtility],
            year: int
        ) -> Dict[str, float]:
 
        inv_incomes = {
            wu.bwf_id: 1/wu.disp_income_avg.loc[timestampify(year)]
            for wu in water_utilities
        }
        total_income = sum(inv_incomes.values())

        return {
            wu_id: (income / total_income) * budget
            for wu_id, income in inv_incomes.items()
        }
    
    @classmethod
    def distribute_custom(
            cls,
            budget: float,
            water_utilities: Set[WaterUtility],
            policy_arg : Dict[str, float]
        ) -> Dict[str, float]:

        alloc_plan = {
            wu.bwf_id : policy_arg[wu.bwf_id] if wu.bwf_id in policy_arg else 0.0
            for wu in water_utilities
        }

        #check that the policy_arg values sum to 1
        if sum(alloc_plan.values()) > 1.0:
            raise ValueError("The custom budget allocation percentages must sum to 1.")

        return {
            wu_id: wu_share * budget
            for wu_id, wu_share in alloc_plan.items()
        }
    