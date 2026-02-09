from typing import Tuple

from ..core.base_model import Policy

class WaterPricingAdjustment(Policy):
    NAME = "pricing_adjustment"

    BY_INFLATION = "by_inflation"
    CUSTOM = "custom"

    @classmethod
    def _apply(
        cls,
        base_value: float,
        rate: float
    ) -> float:
        return (1 + rate) * base_value
    
    @classmethod
    def apply_by_inflation(
        cls,
        base_fix,
        base_var,
        base_sell,
        inflation_rate
    ) -> Tuple[float, float, float]:
        return (
            cls._apply(base_fix, inflation_rate),
            cls._apply(base_var, inflation_rate),
            cls._apply(base_sell, inflation_rate)
        )
    
    @classmethod
    def apply_custom(
        cls,
        base_fix,
        base_var,
        base_sell,
        fixed_component: float,
        variable_component: float,
        selling_price: float
    ) -> Tuple[float, float, float]:
        return (
            cls._apply(base_fix, fixed_component),
            cls._apply(base_var, variable_component),
            cls._apply(base_sell, selling_price)
        )
    
class BondRatioAdjustment:
    NAME = 'bond_ratio'