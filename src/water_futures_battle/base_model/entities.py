from dataclasses import dataclass
from typing import Optional, Tuple

def bwf_entity(
        db_type: Optional[type] = None,
        results_type: Optional[type] = None
    ):
    """
    Decorator factory to inject dynamic properties/results class variables and setters.
    If results_type is None, only injects dynamic properties.
    """
    def decorator(cls):
        if db_type is not None:
            # Inject dynamic properties class variable and setter
            cls._dynamic_properties = None

            @classmethod
            def set_dynamic_properties(cls_, dynamic_properties: db_type):
                cls_._dynamic_properties = dynamic_properties
            cls.set_dynamic_properties = set_dynamic_properties

        # Conditionally inject results class variable and setter
        if results_type is not None:
            cls._results = None

            @classmethod
            def set_results(cls_, results_db: results_type):
                cls_._results = results_db
            cls.set_results = set_results

        return cls
    return decorator

@dataclass(frozen=True)
class Location:
    """BWF entities that have coordinates"""
    LATITUDE = 'latitude'
    LONGITUDE = 'longitude'
    ELEVATION = 'elevation'
    latitude: float
    longitude: float
    elevation: float
    
    @property
    def coordinates(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)
    