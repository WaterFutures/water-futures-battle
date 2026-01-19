from enum import IntEnum
from typing import Self
import numpy as np
from numpy.typing import NDArray
from numpy.random import default_rng
RNG = default_rng(128)

# NRW bounds per category in cubic meter per km per day (mc/km/day)
_NRW_CLASSES_BOUNDS_LIST = [0.2, 2., 3., 4., 8., float('inf')]
_NRW_CLASSES_AGES_LIST = [0., 25., 43., 54., 60., float('inf')]
_NRW_CLASSES_BOUNDS = {
    i: (_NRW_CLASSES_BOUNDS_LIST[i], _NRW_CLASSES_BOUNDS_LIST[i+1])
    for i in range(0, len(_NRW_CLASSES_BOUNDS_LIST)-1)
}

class NRWClass(IntEnum):
    """
    Class models the properties of leaks and other losses in a municipality (i.e., its base demand to be added
    to the normal consumer demands).

    Parameters
    ----------
    nrw_class_id : `int`
        NRW category/class.
        Must be one of the following constants:

            - A = 0
            - B = 1
            - C = 2
            - D = 3
            - E = 4
    """
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4

    @classmethod
    def determine_class(cls, age: float) -> 'NRWClass':
        """Determines the NRW class based on the network age"""
        assert age >= 0., "Age parameter to determine the NRW class can't be negative"

        for size_class in cls:
            upper_bound = _NRW_CLASSES_AGES_LIST[size_class.value+1]

            if age < upper_bound:
                return size_class
            
        # Fallback for error handling (e.g., NaNs)
        raise ValueError(f"Age to determine the NRW class {age} is outside the defined bounds.")

    @property
    def demand_factor_bounds(self) -> tuple[float, float]:
        return _NRW_CLASSES_AGES_LIST[self.value], _NRW_CLASSES_AGES_LIST[self.value+1]

    def sample_demand(self, n_points: int = 1) -> NDArray[np.float64]:
        """
        Returns a sampled nrw demand.

        Returns
        -------
        `float`
            NRW demand.
        """
        base_demand_range = _NRW_CLASSES_BOUNDS[self.value]

        if self != NRWClass.E:
            if self != NRWClass.A:
                return RNG.uniform(
                    low=base_demand_range[0],
                    high=base_demand_range[1],
                    size=n_points
                )
            else:
                # First nrw class: Shift probability mass towards upper bound -- we use a Beta distribution.
                return base_demand_range[1] * RNG.beta(5, 1, size=n_points)
        else:
            # Use the exponential distribution for sampling demands because there is no upper bound!
            # Ensures that the demand will always greater or equal then the specified
            # lower bound from 'nrw_base_demands'
            return base_demand_range[0] + base_demand_range[0] * .3 * RNG.exponential(size=n_points)

    @classmethod
    def _get_shifted_class(cls, current_value: int, shift: int) -> Self:
        """Calculates and returns the shifted NRWClass member safely."""
        max_value = max(member.value for member in cls)
        min_value = min(member.value for member in cls)

        new_value = current_value + shift

        # Clamp the new value to stay within the valid range
        clamped_value = max(min_value, min(max_value, new_value))

        # Return the new Enum member instance
        return cls(clamped_value)

    def __add__(self, other: int) -> Self:
        """
        Implements self + integer, returning a new NRWClass member.
        e.g., NRWClass.A + 1 == NRWClass.B.
        """
        if not isinstance(other, int):
            return NotImplemented
        return self._get_shifted_class(self.value, other)

    def __sub__(self, other: int) -> Self:
        """
        Implements self - integer, returning a new NRWClass member.
        e.g., NRWClass.B - 1 == NRWClass.A.
        """
        if not isinstance(other, int):
            return NotImplemented
        return self._get_shifted_class(self.value, -other)
