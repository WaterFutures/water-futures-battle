from typing import Dict, Set, Tuple

import os
import yaml
import pandas as pd
from pathlib import Path
import requests
import tempfile
import warnings
import zipfile

from .utility.utility import timestampify
from .utility import Settings
from .climate import configure_climate
from .economy import configure_economy
from .nrw_model import configure_nrw_model
from .water_demand_model import configure_water_demand_model
from .jurisdictions import build_state
from .sources import build_sources
from .pumping_stations import build_pumping_infrastructure
from .energy import configure_energy_system
from .connections import build_piping_infrastructure
from .water_utility_model import configure_water_utilities, WaterUtility
from .national_context import NationalContext

# Zenodo concept DOI (resolves to latest)
ZENODO_CONCEPT_ID = "17698299"

def configure_system(data_path: str = "data") -> Tuple[Settings, NationalContext, Set[WaterUtility]]:
    config_file_path = os.path.join(data_path, "configuration.yaml")

    # Check if data folder exits and not empty - if necessary, download all data into data_path
    if not os.path.exists(data_path) or not os.path.isfile(config_file_path):
        warnings.warn("No data found -- starting automatic download of the data from Zenodo...")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Get the LATEST Zenodo record
            r = requests.get(f"https://sandbox.zenodo.org/api/records/{ZENODO_CONCEPT_ID}")

            # Get the file link for the api
            print(r)
            print("----------")
            print("----------")
            print("----------")
            print("----------")
            print(r.json())
            zenodo_files_record = r.json()['links']['files']
            file_name = "water_futures_battle-data.zip"
            zenodo_api_url = zenodo_files_record + '/' + file_name + '/content'
            print(f"Found latest record with url: {zenodo_files_record}")

            print(f"Download started.")
            response = requests.get(zenodo_api_url)
            file_target_path = os.path.join(temp_dir, file_name)
            with open(file_target_path, 'wb') as f:
                f.write(response.content)
            print(f"Download completed.")

            print(f"Extracting {file_target_path} -> {data_path}.")
            Path(data_path).mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(file_target_path, 'r') as zip_ref:
                zip_ref.extractall(path=data_path)

    # Load and parse config
    with open(config_file_path, 'r') as f_yaml:
        return configure_system_ex(yaml.safe_load(f_yaml))


def configure_system_ex(config: Dict) -> Tuple[Settings, NationalContext, Set[WaterUtility]]:
    settings = Settings.from_config(config[Settings.LABEL])

    climate_db = configure_climate(config['climate'])
    bonds_settings, economy_db, utilities_bonds = configure_economy(config['economy'])

    state = build_state(config['state'])

    water_dem_patterns, water_dem_db = configure_water_demand_model(config['water_demand_model'])
    nrw_db = configure_nrw_model(config['nrw_model'])

    sources = build_sources(
        properties_desc=config['sources'],
        a_state=state
    )

    pump_options, pumping_stations = build_pumping_infrastructure(
        desc=config['pumping_infrastructure'],
        sources=sources
    )

    energy_sys_db, solar_farms = configure_energy_system(
        config=config['energy_system'],
        sources=sources,
        pumping_stations=pumping_stations
    )

    pipe_options, connections = build_piping_infrastructure(
        desc=config['piping_infrastructure'],
        a_state=state,
        sources=sources
    )

    water_utilities, cross_utility_connections = configure_water_utilities(
        desc=config['water_utilities'],
        a_state=state,
        sources=sources,
        pumping_stations=pumping_stations,
        connections=connections,
        utilities_bonds=utilities_bonds,
        solar_farms=solar_farms
    )

    national_context = NationalContext(
        state=state,
        water_utilities=water_utilities,
        cross_utility_connections=cross_utility_connections,
        bonds_settings=bonds_settings,
        water_demand_patterns=water_dem_patterns,
        pump_options=pump_options,
        pipe_options=pipe_options,
        climate=climate_db,
        economy=economy_db,
        water_demand_model_db=water_dem_db,
        nrw_model_db=nrw_db,
        energy_sys=energy_sys_db
    )

    return settings, national_context, water_utilities
