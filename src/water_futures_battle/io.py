import os
from pathlib import Path
from typing import Dict, Set, Tuple

import requests
from rich.progress import Progress
import tempfile
import warnings
import yaml
import zipfile

from .core import Settings
from .climate import configure_climate
from .economy import configure_economy
from .nrw_model import configure_nrw_model
from .water_demand_model import configure_water_demand_model
from .jurisdictions import build_state
from .sources import build_sources
from .pumping_stations import build_pumping_infrastructure
from .energy import configure_energy_system
from .connections import build_piping_infrastructure
from .water_utilities import WaterUtility, configure_water_utilities
from .national_context import NationalContext

def get_package_version():
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
    with open(version_file, encoding="utf-8") as f:
        return f.read().strip()

# Zenodo concept DOI (resolves to latest)
ZENODO_CONCEPT_ID = "17698299"

def configure_system(
        data_path: str = "data",
        configuration_filename: str = "configuration.yaml"
    ) -> Tuple[Settings, NationalContext, Set[WaterUtility]]:
    
    config_file_path = os.path.join(data_path, configuration_filename)

    # Check if data folder exits and not empty - if necessary, download all data into data_path
    if not os.path.exists(data_path) or not os.path.isfile(config_file_path):
        warnings.warn("No data found -- starting automatic download of the data from Zenodo...")

        success = False
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Get the LATEST Zenodo record
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"}
                r = requests.get(f"https://zenodo.org/api/records/{ZENODO_CONCEPT_ID}", headers=headers)

                # Get the file link for the api
                if r.status_code != 200:
                    print(f"Failed to download data from Zenodo -- status code: {r.status_code}")
                    return None

                zenodo_files_record = r.json()['links']['files']
                file_name = "water_futures_battle-data.zip"
                zenodo_api_url = zenodo_files_record + '/' + file_name + '/content'
                print(f"Found latest record with url: {zenodo_files_record}")

                print(f"Download started.")
                response = requests.get(zenodo_api_url, headers=headers)
                file_target_path = os.path.join(temp_dir, file_name)
                with open(file_target_path, 'wb') as f:
                    f.write(response.content)
                print(f"Download completed.")

                print(f"Extracting {file_target_path} -> {data_path}.")
                Path(data_path).mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(file_target_path, 'r') as zip_ref:
                    zip_ref.extractall(path=data_path)

                success = True
        except Exception as ex:
            print(f"An error occured while downloading and unpacking the data -- {ex}")
        finally:
            if success is False:
                print(f"Automatic download failed. Please download the data manually from https://zenodo.org/records/{ZENODO_CONCEPT_ID}")
                os._exit(1)

    # Check version file in data folder
    data_outdated = False
    data_version_file_path = os.path.join(data_path, "VERSION")
    if os.path.isfile(data_version_file_path):
        with open(data_version_file_path) as f:
            data_version = f.read().strip()

            if data_version != get_package_version():
                data_outdated = True
    else:
        data_outdated = True

    if data_outdated is True:
        warnings.warn("Your database is outdated. Please consider downloading the latest version -- do not forget to backup your changes to the data!")
    
    # Load and parse config
    with open(config_file_path, 'r') as f_yaml:
        config = yaml.safe_load(f_yaml)
        config["data_path"] = data_path

        return configure_system_ex(config)


def configure_system_ex(
        config: Dict
    ) -> Tuple[Settings, NationalContext, Set[WaterUtility]]:

    with Progress() as progress:
        config_task = progress.add_task("[red]Configuring system", total=12)

        settings = Settings.from_config(config[Settings.LABEL])
        progress.update(config_task, advance=1)

        climate_db = configure_climate(
            config['climate'],
            config["data_path"],
            settings
        )
        progress.update(config_task, advance=1)

        bonds_settings, economy_db, utilities_bonds = configure_economy(
            config['economy'],
            config["data_path"],
            settings
        )
        progress.update(config_task, advance=1)

        state = build_state(
            config['state'],
            config["data_path"],
            settings
        )
        progress.update(config_task, advance=1)

        water_dem_patterns, water_dem_db = configure_water_demand_model(
            config['water_demand_model'],
            config["data_path"],
            settings
        )
        progress.update(config_task, advance=1)

        nrw_settings, nrw_db = configure_nrw_model(
            config['nrw_model'],
            config["data_path"],
            settings
        )
        progress.update(config_task, advance=1)

        sources, sources_settings = build_sources(
            properties_desc=config['sources'],
            a_state=state,
            data_path=config["data_path"],
            settings=settings
        )
        progress.update(config_task, advance=1)

        pump_options, pumping_stations = build_pumping_infrastructure(
            desc=config['pumping_infrastructure'],
            sources=sources,
            data_path=config["data_path"],
            settings=settings
        )
        progress.update(config_task, advance=1)

        energy_sys_db, solar_farms = configure_energy_system(
            config=config['energy_system'],
            sources=sources,
            pumping_stations=pumping_stations,
            data_path=config["data_path"],
            settings=settings
        )
        progress.update(config_task, advance=1)

        pipe_options, connections = build_piping_infrastructure(
            desc=config['piping_infrastructure'],
            a_state=state,
            sources=sources,
            data_path=config["data_path"],
            settings=settings
        )
        progress.update(config_task, advance=1)

        water_utilities, cross_utility_connections = configure_water_utilities(
            desc=config['water_utilities'],
            a_state=state,
            sources=sources,
            pumping_stations=pumping_stations,
            connections=connections,
            utilities_bonds=utilities_bonds,
            solar_farms=solar_farms,
            data_path=config["data_path"],
            settings=settings
        )
        progress.update(config_task, advance=1)

        national_context = NationalContext(
            state=state,
            water_utilities=water_utilities,
            cross_utility_connections=cross_utility_connections,
            bonds_settings=bonds_settings,
            water_demand_patterns=water_dem_patterns,
            nrw_settings=nrw_settings,
            sources_settings=sources_settings,
            pump_options=pump_options,
            pipe_options=pipe_options,
            climate=climate_db,
            economy=economy_db,
            water_demand_model_db=water_dem_db,
            nrw_model_db=nrw_db,
            energy_sys=energy_sys_db,
            _all_sources=sources,
            _all_pumping_stations=pumping_stations,
            _all_solar_farms=solar_farms,
            _all_connections=connections
        )
        progress.update(config_task, advance=1)

        return settings, national_context, water_utilities

from .core.base_model import DynamicProperties
from .jurisdictions.services import dump_state
from .water_demand_model.services import dump_water_demand_model
from .nrw_model.services import dump_nrw_model
from .sources.services import dump_sources
from .pumping_stations.services import dump_pumping_infrastructure
from .connections.services import dump_piping_infrastructure
from .climate.services import dump_climate
from .economy.services import dump_economy
from .energy.services import dump_energy_system
from .water_utilities.services import dump_water_utilities

from .services.metrics import MetricsT

def save_system_status(
        results_dir: Path,
        settings: Settings,
        national_context: NationalContext,
        water_utilities: Set[WaterUtility]
) -> None:
    
    with Progress() as progress:
        saving_task = progress.add_task("[red]Saving out system status and history", total=11)

        configuration = {}

        # Jurisdictions/State
        configuration['state'] = dump_state(
            national_context.state,
            results_dir
        )
        progress.update(saving_task, advance=1)

        # Water demand model
        configuration['water_demand_model'] = dump_water_demand_model(
            national_context.water_demand_patterns,
            national_context.water_demand_model_db,
            results_dir
        )
        progress.update(saving_task, advance=1)
        
        # NRW model
        configuration['nrw_model'] = dump_nrw_model(
            national_context.nrw_settings,
            national_context.nrw_model_db,
            results_dir
        )
        progress.update(saving_task, advance=1)

        # Sources
        configuration['sources'] = dump_sources(
            national_context._all_sources,
            national_context.sources_settings,
            results_dir
        )
        progress.update(saving_task, advance=1)

        # Pumping infrastructure
        configuration['pumping_infrastructure'] = dump_pumping_infrastructure(
            national_context._all_pumping_stations,
            national_context.pump_options,
            results_dir
        )
        progress.update(saving_task, advance=1)

        # Piping infrastructure
        configuration['piping_infrastructure'] = dump_piping_infrastructure(
            national_context._all_connections,
            national_context.pipe_options,
            results_dir
        )
        progress.update(saving_task, advance=1)

        # Climate
        configuration['climate'] = dump_climate(
            national_context.climate,
            results_dir
        )
        progress.update(saving_task, advance=1)

        # Economy
        configuration['economy'] = dump_economy(
            national_context.bonds_settings,
            national_context.economy,
            {},
            results_dir
        )
        progress.update(saving_task, advance=1)

        # Energy
        configuration['energy_system'] = dump_energy_system(
            national_context.energy_sys,
            national_context._all_solar_farms,
            results_dir
        )
        progress.update(saving_task, advance=1)

        # Water utilities
        configuration['water_utilities'] = dump_water_utilities(
            national_context.water_utilities,
            results_dir
        )
        progress.update(saving_task, advance=1)

        # Write down the configuration with these files so that one can
        # use it out of the box
        configuration['settings'] = {
            settings.START_YEAR: settings.end_year+1,
            settings.END_YEAR: settings.end_year + len(settings.years_to_simulate),
            'national_budget': 0,
            settings.LIFELINE_VOLUME: settings.lifeline_volume,
            settings.SEED: 128
        }

        config_path = results_dir / "configuration.yaml"
        with open(config_path, "w") as f:
            yaml.safe_dump(configuration, f, sort_keys=False)
        progress.update(saving_task, advance=1)

    print(f"Updated system status saved in {results_dir}")
    
    return

def save_metrics(
        results_dir: Path,
        metrics: MetricsT
    ) -> None:

        DynamicProperties('metrics', metrics).dump(results_dir)
    
        print(f"You can visualize this stage metrics at '{results_dir}/metrics.xlsx'")

        return

import typer
from typing_extensions import Annotated

from .masterplan import parse_masterplan
from .services.evaluation import run_eval

def run_eval_from_file(
        masterplan_file: Annotated[str, typer.Argument(help="Masterplan file (.xlsx, .yaml, or .json) ")],
        config_file: Annotated[str, typer.Argument(help=".xlsx file containing the configuration of the scenario")]
    ) -> None:

    # If the configuration file has a folder use that folder to pass it to the configure_system
    # otherwise, it is current directory.
    config_path = Path(config_file)
    data_path = str(config_path.parent) if config_path.parent != Path('') else '.'
    configuration_filename = config_path.name

    settings, national_context, water_utilities = configure_system(
        data_path=data_path,
        configuration_filename=configuration_filename
    ) 

    masterplan = parse_masterplan(Path(masterplan_file))

    # Actually run the evaluation of the solution    
    national_context, water_utilities, metrics = run_eval(
        settings=settings,
        national_context=national_context,
        water_utilities=water_utilities,
        masterplan=masterplan
    )

    # Create results-{scenario_name} directory in the parent of data_path
    # We re-open the configuration to find these info
    data_parent_dir = config_path.parent.parent
    with open(config_file, 'r') as f_yaml:
        config = yaml.safe_load(f_yaml)
        scenario_name = config.get('scenario_name', None)

    if scenario_name:
        results_dir = data_parent_dir / f"bwf_results-{scenario_name}"
    else:
        results_dir = data_parent_dir / "bwf_results"

    results_dir.mkdir(exist_ok=True)

    save_system_status(
        results_dir,
        settings,
        national_context,
        water_utilities
    )

    save_metrics(
        results_dir=results_dir,
        metrics=metrics
    )

    return
