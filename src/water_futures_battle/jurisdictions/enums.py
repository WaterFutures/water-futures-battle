from enum import IntEnum

_MUNI_SIZE_CLASSES_BOUNDS_LIST = [0., 50_000., 100_0000., 300_000., float('inf')]
_MUNI_SIZE_CLASSES_BOUNDS = {
    i: (_MUNI_SIZE_CLASSES_BOUNDS_LIST[i-1], _MUNI_SIZE_CLASSES_BOUNDS_LIST[i])
    for i in range(1, len(_MUNI_SIZE_CLASSES_BOUNDS_LIST))
}

class MunicipalitySize(IntEnum):
    """
    Represents the size class of a Dutch municipality based on its population, 
    with classes ordered by rank (1 = smallest, 4 = largest).
    """
    SMALL = 1
    MEDIUM = 2
    LARGE = 3
    G4 = 4

    @classmethod
    def determine_class(cls, population: int | float) -> 'MunicipalitySize':
        """Determines the correct MunicipalitySize enum member for a given population."""
        assert population >= 0., "Population parameter to determine the municipality size class can't be negative"
        
        for size_class in cls:
            lower_bound, upper_bound = _MUNI_SIZE_CLASSES_BOUNDS[size_class.value]
            
            # Check if population falls within the class bounds
            if lower_bound <= population < upper_bound:
                return size_class
        
        # Fallback for error handling (though should be unreachable with float('inf'))
        raise ValueError(f"Population {population} is outside the defined bounds.")