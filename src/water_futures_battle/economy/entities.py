from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd

from ..core.utility import timestampify

@dataclass(frozen=True)
class BondsSettings:

    risk_free_rate: float
    RISKFREE_RATE = 'risk_free_rate'
    spread_sensitivity: float
    SPREAD_SENS = 'spread_sensitivity'
    maturity: int
    MATURITY = 'maturity'

    def to_dict(self) -> Dict[str, Any]:
        return {
            self.RISKFREE_RATE: self.risk_free_rate,
            self.SPREAD_SENS: self.spread_sensitivity,
            self.MATURITY: self.maturity
        }


@dataclass(frozen=True)
class BondIssuance:

    bwf_id: str
    ID = 'bond_issuance_id'
    ID_PREFIX = 'BI' # Bond Issuance

    FACE_VALUE = 100

    n_bonds: int
    N_BONDS = 'n_bonds'

    issue_date: pd.Timestamp
    ISSUE_DATE = 'issue_date'
    maturity_year: pd.Timestamp
    MATURITY_DATE = 'maturity_date'

    coupon_rate: float
    COUPON_RATE = 'coupon_rate'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BondIssuance):
            return NotImplemented
        return self.bwf_id == other.bwf_id

    def __hash__(self) -> int:
        return hash(self.bwf_id)

    @property
    def interest(self) -> float:
        """Calculate total annual coupon payment for all bonds."""
        return self.n_bonds * self.FACE_VALUE * self.coupon_rate

    @property
    def principal(self) -> float:
        """Calculate total principal repayment at maturity."""
        return self.n_bonds * self.FACE_VALUE

    def is_mature(self, year: int) -> bool:
        """Check if bonds have matured in the current year."""
        return timestampify(year, errors='raise') >= self.maturity_year

    def payment_due(self, year: int) -> float:
        """
        Calculate total payment due in a given year.
        Returns coupon payment (and principal if matured).
        """
        current_year = timestampify(year, errors='raise')

        if current_year < self.issue_date or current_year > self.maturity_year:
            return 0.0

        payment = self.interest

        # Add principal repayment in maturity year
        if current_year == self.maturity_year:
            payment += self.principal

        return payment

    def to_dict(self) -> Dict[str, Any]:
        return {
            self.ID: self.bwf_id,
            self.N_BONDS: self.n_bonds,
            self.ISSUE_DATE: self.issue_date,
            self.MATURITY_DATE: self.maturity_year,
            self.COUPON_RATE: self.coupon_rate,
        }

    @classmethod
    def file_columns(cls) -> List[str]:
        return [
            cls.ID,
            cls.N_BONDS,
            cls.ISSUE_DATE,
            cls.MATURITY_DATE,
            cls.COUPON_RATE,
        ]