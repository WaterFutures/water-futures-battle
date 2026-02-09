from __future__ import annotations

from typing import Dict, List, Optional, Literal, Any

from pydantic import BaseModel, field_validator


class PolicyArgs(BaseModel):
    WU01: float
    WU02: float
    WU03: float
    WU04: float
    WU05: float
    WU06: float
    WU07: float
    WU08: float
    WU09: float
    WU10: float

    @field_validator("WU01", "WU02", "WU03", "WU04", "WU05", "WU06", "WU07", "WU08", "WU09", "WU10")
    @classmethod
    def check_sum(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Each WU value must be between 0.0 and 1.0")
        return v

class BudgetAllocation(BaseModel):
    policy: Literal["by_population", "by_inverse_population", "by_income", "by_inverse_income", "custom"]  #maybe optional
    policy_args: Optional[PolicyArgs] = None


class NationalPolicies(BaseModel):
    budget_allocation: BudgetAllocation


class InstallPipeItem(BaseModel):
    connection_id: str
    pipe_option_id: str


class NationalInterventions(BaseModel):
    install_pipe: List[InstallPipeItem]


class NrwMitigation(BaseModel):
    budget: int
    policy: Literal["by_nrw_class","by_population","custom"]
    policy_args: Optional[Dict[str, Any]] = None


class PolicyArgs2(BaseModel):
    fixed_component: float
    variable_component: float
    selling_price: float


class PricingAdjustment(BaseModel):
    policy: Literal["by_inflation","custom"]
    policy_args: Optional[PolicyArgs2] = None


class BondRatio(BaseModel):
    value: float


class Policies(BaseModel):
    nrw_mitigation: NrwMitigation
    pricing_adjustment: Optional[PricingAdjustment] = None
    bond_ratio: Optional[BondRatio] = None


class OpenSourceItem(BaseModel):
    source_id: str
    source_capacity: int
    pump_option_id: str
    n_pumps: int
    pipe_option_id: str


class CloseSourceItem(BaseModel):
    source_id: str


class InstallPipeItem1(BaseModel):
    connection_id: str
    pipe_option_id: str


class InstallPump(BaseModel):
    source_id: str
    pump_option_id: str
    n_pumps: int
    behaviour: Optional[Literal["replace","new"]] = None


class InstallSolarItem(BaseModel):
    source_id: str
    capacity: int


class Interventions(BaseModel):
    open_source: Optional[List[OpenSourceItem]] = None
    close_source: Optional[List[CloseSourceItem]] = None
    install_pipe: Optional[List[InstallPipeItem1]] = None
    install_pumps: Optional[List[InstallPump]] = None
    install_solar: Optional[List[InstallSolarItem]] = None

class WaterUtility(BaseModel):
    water_utility: str
    policies: Policies
    interventions: Optional[Interventions] = None


class Year(BaseModel):
    year: int
    national_policies: NationalPolicies
    national_interventions: Optional[NationalInterventions] = None
    water_utilities: Optional[List[WaterUtility]] = None


class Model(BaseModel):
    years: Optional[List[Year]] = None
