from .entities import WaterUtility
from .services import (
    configure_water_utilities,
    apply_nrw_interventions,
    apply_water_pricing_adjustments,
    apply_bond_to_debt_ratio,
    age_water_utility,
)
from ..nrw_model.policies import NRWMitigation
from .policies import (
    WaterPricingAdjustment,
    BondRatioAdjustment,
)

WaterUtilityPolicies = [
	NRWMitigation,
	WaterPricingAdjustment,
	BondRatioAdjustment,
]

from .interventions import (
    OpenSource,
    CloseSource,
    InstallPipe,
    InstallPumps,
    InstallSolarFarm,
)

WaterUtilityInterventions = [
	OpenSource,
	CloseSource,
	InstallPumps,
	InstallPipe,
	InstallSolarFarm,
]

__all__ = [
    "WaterUtility",
    "configure_water_utilities",
    "apply_nrw_interventions",
    "apply_water_pricing_adjustments",
    "apply_bond_to_debt_ratio",
    "age_water_utility",
    "WaterUtilityPolicies",
    "WaterUtilityInterventions",
]