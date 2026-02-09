import numpy as np

class RandomManager:
    """Centralized random number generator management."""

    AVAILABLE_GENERATORS = [
        'municipalities-res_p_weight',
        'nrw_model-sample_demand',
        'nrw_model-intervention_succes_prob',
        'water_demand_model-sample_demand',
        'pipes-fric_f_decay',
        'pipes-lifetime',
        'pumps-lifetime',
    ]
    
    def __init__(self, master_seed: int):
        self.master_seed = master_seed
        base_rng = np.random.default_rng(self.master_seed)
        
        # Spawn independent generators
        spawned = base_rng.spawn(len(self.AVAILABLE_GENERATORS))
        self.generators = dict(zip(self.AVAILABLE_GENERATORS, spawned))
    
    def get(self, module_name: str) -> np.random.Generator:
        """Get the RNG for a specific module."""
        if module_name not in self.generators:
            raise ValueError(f"Unknown module: {module_name}")
        return self.generators[module_name]

class FakeLifetimeGenerator:
    def __init__(self, fixed_value):
        self.fixed_value = fixed_value

    def integers(self, low, high=None, size=None, dtype=int, endpoint=False):
        # Always return the fixed value, ignoring the range
        if size is None:
            return self.fixed_value
        else:
            return np.full(size, self.fixed_value, dtype=dtype)
