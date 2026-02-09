from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            self.LATITUDE: self.latitude,
            self.LONGITUDE: self.longitude,
            self.ELEVATION: self.elevation
        }


class Lever:
    """
    Base class for strategic decisions in the BWF competition.
    
    Participants make two types of strategic decisions: policies and interventions.
    This class serves as the conceptual foundation for both decision types.
    
    Levers are defined in the masterplan, which specifies when and where 
    (scope) each decision applies. The actual execution happens during 
    simulation when the apply methods are called with full context.
    """
    pass


class Policy(Lever):
    """
    Policies encompass regulatory and operational rules, such as pricing 
    structures, budget allocations, and maintenance protocols. 
    
    Once set, policies remain in effect until explicitly amended. This means
    that when a policy is defined in a masterplan for a given year, it 
    persists in subsequent years unless a new policy value is specified.
    
    Policy implementations are stateless class methods that receive all 
    necessary context (year, scope, parameters) at execution time.
    """
    pass


class Intervention(Lever):
    """
    Interventions are physical modifications to the system, such as 
    infrastructure upgrades or new installations.
    
    Interventions are specified annually and are always implemented. 
    Unlike policies, interventions are one-time actions that occur in 
    the year they are specified.
    
    Intervention implementations are stateless class methods that receive 
    all necessary context (year, scope, parameters) at execution time.
    """
    pass