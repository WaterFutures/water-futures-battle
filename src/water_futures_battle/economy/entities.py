from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd

from ..core.utility import timestampify, BWFTimeLike

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
        return self.n_bonds * self.FACE_VALUE * self.coupon_rate / 100 # coupon rate is in %

    @property
    def principal(self) -> float:
        """Calculate total principal repayment at maturity."""
        return self.n_bonds * self.FACE_VALUE

    def is_mature(self, year: BWFTimeLike) -> bool:
        """Check if bonds have matured in the current year."""
        return timestampify(year, errors='raise') >= self.maturity_year

    def payment_due(self, year: BWFTimeLike) -> float:
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
    
    def interest_due(self, year: BWFTimeLike) -> float:
        """
        Calculate the interest due in a given year.
        Returns coupon payment
        """
        current_year = timestampify(year, errors='raise')

        if current_year < self.issue_date or current_year > self.maturity_year:
            return 0.0
        
        return self.interest
    
    def principal_due(self, year: BWFTimeLike) -> float:
        current_year = timestampify(year, errors='raise')

        if current_year == self.maturity_year:
            return self.principal
        
        return 0.0

    def net_present_value(self, year: BWFTimeLike, yield_rate: float) -> float:
        """
        Calculates the Net Present Value (NPV) of all remaining cash flows 
        (interest and principal) from the year onwards.
        
        :param year: The year from which we are discounting.
        :param yield_rate: The annual discount rate (e.g., 0.035 for 3.5%).
        """
        ts = timestampify(year, errors='raise')
        
        # If the bond has already matured before this year, NPV is 0
        if ts > self.maturity_year:
            return 0.0
            
        total_npv = 0.0
        
        # Start from the evaluation year and go until maturity
        start_year = ts.year
        end_year = self.maturity_year.year
        
        for year in range(start_year, end_year + 1):
            payment = self.payment_due(year)
            
            if payment > 0:
                # t is the time delta in years
                t = year - start_year
                # Discount the payment to the evaluation_year
                total_npv += payment / ((1 + yield_rate) ** t)
                
        return total_npv

    def to_dict(self) -> Dict[str, Any]:
        return {
            self.ID: self.bwf_id,
            self.N_BONDS: self.n_bonds,
            self.ISSUE_DATE: self.issue_date.strftime('%Y-%m-%d'),
            self.MATURITY_DATE: self.maturity_year.strftime('%Y-%m-%d'),
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