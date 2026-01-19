from numpy.random import default_rng
RNG = default_rng(12804)
import itertools

from .dynamic_properties import NRWModelDB
from .enums import NRWClass

from ..jurisdictions.enums import MunicipalitySize
from ..views.services import get_snapshot
from .dynamic_properties import NRWInterventionProbabilityTable


def configure_nrw_model(config: dict) -> NRWModelDB:
    nrw_model_db = NRWModelDB.load_from_file(config[NRWModelDB.NAME])

    # Use layout of cost dataframe for intervention probabilities
    df_cost = nrw_model_db[NRWModelDB.COST]
    nrw_model_db[NRWModelDB.PROBABILITY] = df_cost.copy()

    # Sample NRW intervention probabilities
    proba_lower_bound = config["nrw_model-intervention_success_prob-min"]
    nrw_model_db[NRWModelDB.PROBABILITY]["NL0000"] = nrw_model_db[NRWModelDB.PROBABILITY]["NL0000"].\
        apply(lambda _: NRWInterventionProbabilityTable.from_row({f"{nrw_class.name}-{muni_size_class.name}": RNG.uniform(proba_lower_bound, 1)
                                                                   for nrw_class, muni_size_class in itertools.product(NRWClass, MunicipalitySize)}))

    return nrw_model_db
