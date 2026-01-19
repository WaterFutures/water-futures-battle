from enum import IntEnum

_SOURCES_SIZE_CLASSES_BOUNDS_LIST = [0., 4e6, 8e6, 16e6, float('inf')] # in Millions of M^3
_SOURCES_SIZE_CLASSES_BOUNDS = {
    i: (_SOURCES_SIZE_CLASSES_BOUNDS_LIST[i-1], _SOURCES_SIZE_CLASSES_BOUNDS_LIST[i])
    for i in range(1, len(_SOURCES_SIZE_CLASSES_BOUNDS_LIST))
}

class SourceSize(IntEnum):
    """
    Represent the size of a source based on its nominal capacity.
    """
    SMALL = 1
    MEDIUM = 2
    LARGE = 3
    VERY_LARGE = 4

    @classmethod
    def determine_class(cls, nominal_capacity: float) -> 'SourceSize':
        assert nominal_capacity > 0., "Nominal capacity parameter to determins Source class can't be negative"

        for size_class in cls:
            lower_bound, upper_bound = _SOURCES_SIZE_CLASSES_BOUNDS[size_class.value]

            if lower_bound <= nominal_capacity < upper_bound:
                return size_class
            
        # Fallback for error handling (though should be unreachable with float('inf'))
        raise ValueError(f"Impossible to determine the source size. Nominal capacity {nominal_capacity} is outside the defined bounds.")
        
_WD_SEVERITY_BOUNDS_LIST = [-float('inf'), 0., 1e5, 8e6, float('inf')]
_WD_SEVERITY_BOUNDS = {
    (i-1): (_WD_SEVERITY_BOUNDS_LIST[i-1], _WD_SEVERITY_BOUNDS_LIST[i])
    for i in range(1, len(_WD_SEVERITY_BOUNDS_LIST))
}

class GroundwaterPermitDeviation(IntEnum):
    """
    Represent the severity of a deviation from a groundwater permit.
    """
    COMPLIANT = 0
    MILD = 1
    SEVERE = 2
    EXTREME = 3

    @classmethod
    def determine_class(cls, value: float) -> 'GroundwaterPermitDeviation':
    
        for size_class in cls:
            lower_bound, upper_bound = _WD_SEVERITY_BOUNDS[size_class.value]

            if lower_bound <= value < upper_bound:
                return size_class
            
        # Fallback for error handling (though should be unreachable with float('inf'))
        raise ValueError(f"Impossible to determine the severity of a deviation from a groundwater permit. Value {value} is outside the defined bounds.")
        