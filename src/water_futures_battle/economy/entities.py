from dataclasses import dataclass

import pandas as pd

from ..utility.utility import timestampify

@dataclass(frozen=True)
class BondsSettings:

    amount_debt_ratio: float
    AM2DEBT_RATIO = 'amount_to_debt_ratio'
    risk_free_rate: float
    RISKFREE_RATE = 'risk_free_rate'
    spread_sensitivity: float
    SPREAD_SENS = 'spread_sensitivity'
    maturity: int
    MATURITY = 'maturity'

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