from functools import cmp_to_key
from typing import Dict

import numpy as np

from ..core.base_model import Policy
from ..core.views import get_snapshot, YearlyView
from ..core.utility import timestampify
from .enums import NRWClass, _NRW_CLASSES_AGES_LIST
from .dynamic_properties import NRWModelDB
from ..jurisdictions import Municipality

class NRWMitigation(Policy):
    NAME = "nrw_mitigation"

    BY_NRW_CLASS = "by_nrw_class"
    BY_POPULATION = "by_population"
    CUSTOM = "custom"
    
    @classmethod
    def distribute_budget_by_nrw_class(
            cls,
            budget: float,
            municipalities: list[YearlyView[Municipality]],
            year: int,
            nrw_info_db: NRWModelDB
        ) -> Dict[YearlyView[Municipality], float]:
        # Improve nrw class of each municpality in a greedy way (worst cases first)
        # until no budget is left
        
        def cmp_muni(a: YearlyView[Municipality], b: YearlyView[Municipality]) -> int:
            if a.nrw_class == b.nrw_class:
                # Sort descending by dist_network_avg_age
                return (b.dist_network_avg_age > a.dist_network_avg_age) - (b.dist_network_avg_age < a.dist_network_avg_age)
            else:
                # Sort descending by nrw_class
                return (b.nrw_class > a.nrw_class) - (b.nrw_class < a.nrw_class)

        def estimate_cost(municipality: YearlyView[Municipality]) -> float:
            
            # unit cost in in €/km/year
            unit_cost = nrw_info_db[NRWModelDB.COST].loc[
                timestampify(year),
                f'{municipality.state.cbs_id}-{municipality.nrw_class.name}-{municipality.size_class.name}'
            ]

            # we need x ages
            cur_age = municipality.dist_network_avg_age
            target_age = municipality.nrw_class.demand_factor_bounds[0]
            ages_improve = (cur_age - target_age)+1 # getting to the lower bound would mean staying in the same class

            return unit_cost * ages_improve * municipality.dist_network_length
        

        munis_sorted = sorted(municipalities, key=cmp_to_key(cmp_muni))

        r = {m: 0. for m in munis_sorted}
        budget_spent = 0
        for m in munis_sorted:
            cost = estimate_cost(m)
            if cost + budget_spent > budget:
                r[m] = budget - budget_spent
            else:
                r[m] = cost

            budget_spent += cost
            if budget_spent >= budget:    # Stop if no budget is left
                break

        return r
    
    @classmethod
    def distribute_budget_by_population(
            cls,
            budget: float,
            municipalities: list[YearlyView[Municipality]]
        ) -> Dict[YearlyView[Municipality], float]:

        populations = np.array([m.population for m in municipalities])
        shares = populations / np.sum(populations)
        allocations = budget * shares

        return dict(zip(municipalities, allocations))

    @classmethod
    def distribute_budget_custom(
            cls,
            budget: float,
            municipalities: list[YearlyView[Municipality]],
            shares: Dict[str, float]
        ) -> Dict[YearlyView[Municipality], float]:

        if sum(shares.values()) > 1.0:
            raise ValueError(
                "The sum of the municipalities shares for the NRW mitigation exceeds 1. "
                "Keep the sum below one to correctly allocate the budget."
            )
        for key, value in shares.items():
            if value < 0 or value > 1:
                raise ValueError(
                    f"Share for municipality '{key}' is not between 0 and 1: {value}."
                )
    
        r = {}
        for m in municipalities:
            if m.cbs_id in shares:
                r[m] = budget * shares[m.cbs_id]
            else:
                r[m] = 0.0
        return r
