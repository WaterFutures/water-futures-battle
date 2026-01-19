from pathlib import Path

from numpy.random import default_rng
RNG_RES_P_WEIGHT = default_rng(128)
import pandas as pd

from .dynamic_properties import MunicipalitiesDB as MuniDB, MunicipalitiesResults as MuniR
from .entities import (
    State, Region, Province, Municipality, 
)


def build_state(config: dict[str,str]) -> State:
    """
    Build a state from a config dictionary.

    Args:
        config (dict): Configuration dictionary.

    Returns:
        State: A state object 
    """
    name = config['name']
    identifier = config['id']

    # Get the dynamic properties search within the `files` properties, the following:
    # - municipalities-dynamic_properties
    # upload the metadata...
    munis_db = MuniDB.load_from_file(Path(config[MuniDB.NAME]))

    # Inject the dynamic properties and the repository into the jurisdiciton classes
    Municipality.set_dynamic_properties(munis_db)
    Municipality.set_results(MuniR())
    
    # Creation order is State, Regions, Provinces, Municipalities.
    # Every Jurisdictions will register itself to the correct parent automatically

    # Let's upload the static properties explaining the jurisdictions
    jurisdictions_sheets = pd.read_excel(Path(config['jurisdictions-static_properties']), sheet_name=None)    

    # Assume we uploaded the 'state' and it only has this:
    a_state = State(name, identifier)

    for _, a_region_data in jurisdictions_sheets['regions'].iterrows():
        assert a_region_data['state'] == identifier
        Region.from_row(row_data=a_region_data.to_dict(), state=a_state)

    for _, a_province_data in jurisdictions_sheets['provinces'].iterrows():
        province_s_region = a_state.region(a_province_data['region'])
        Province.from_row(row_data=a_province_data.to_dict(), region=province_s_region)

    for _, a_municipality_data in jurisdictions_sheets['municipalities'].iterrows():

        municipality_s_province = a_state.province(a_municipality_data['province'])
        Municipality.from_row(
            row_data=a_municipality_data.to_dict(),
            province=municipality_s_province,
            _res_p_weight=RNG_RES_P_WEIGHT.uniform(low=0, high=1, size=1).item()
        
        )

    return a_state
