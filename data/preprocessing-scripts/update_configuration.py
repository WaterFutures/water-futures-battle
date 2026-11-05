import os 
from pathlib import Path

import numpy as np
RNG = np.random.default_rng(seed=128128)

import yaml

STAGE_SEEDS = [int(s) for s in RNG.integers(0, 2**32 - 1, size=(3,))]
STAGE_BUDGETS = [1e9, 450e6, 850e6]

def main(
        folder: Path,
        stage_number: int,
        team_name: str
    ) -> None:
    
    configuration_filename = folder / "configuration.yaml"

    if not os.path.exists(configuration_filename) or not os.path.isfile(configuration_filename):
        raise ValueError("Configuration file not found")
    
    with open(configuration_filename, 'r') as f_yaml:
        config = yaml.safe_load(f_yaml)
    
    # Start changin things and names
    #------ OUTPUT DATA directory
    config['scenario_name'] = team_name + "-stage_" + str(stage_number)

    #------ SETTINGS (SEED and BUDGET)
    if team_name.startswith('TEAM0') and stage_number == 1:
        config['settings']['national_budget'] = 0.0
    else:
        config['settings']['national_budget'] = STAGE_BUDGETS[stage_number-1]
    config['settings']['seed'] = STAGE_SEEDS[stage_number-1]

    #------ SYSTEM INPUT FILES (manual, based on configuration.yaml structure)
    # State
    config['state']['jurisdictions-static_properties'] = f"./jurisdictions/jurisdictions-static_properties-stage_{stage_number}.xlsx"
    config['state']['municipalities-dynamic_properties'] = f"./jurisdictions/municipalities-dynamic_properties-stage_{stage_number}.xlsx"

    # Water demand model
    config['water_demand_model']['water_demand_model-dynamic_properties'] = f"./water_demand_model/water_demand_model-dynamic_properties-stage_{stage_number}.xlsx"

    # NRW model
    #config['nrw_model']['nrw_model-dynamic_properties'] = f"./nrw_model/nrw_model-dynamic_properties-stage_{stage_number}.xlsx"

    # Sources
    config['sources']['sources-static_properties'] = f"./sources/sources-static_properties-stage_{stage_number}.xlsx"
    config['sources']['groundwater-dynamic_properties'] = f"./sources/groundwater-dynamic_properties-stage_{stage_number}.xlsx"
    config['sources']['surface_water-dynamic_properties'] = f"./sources/surface_water-dynamic_properties-stage_{stage_number}.xlsx"
    #config['sources']['desalination-dynamic_properties'] = f"./sources/desalination-dynamic_properties-stage_{stage_number}.xlsx"

    # Pumping infrastructure
    config['pumping_infrastructure']['pumping_stations-static_properties'] = f"./pumping_stations/pumping_stations-static_properties-stage_{stage_number}.xlsx"
    #config['pumping_infrastructure']['pump_options-dynamic_properties'] = f"./pumps/pump_options-dynamic_properties-stage_{stage_number}.xlsx"

    # Piping infrastructure
    config['piping_infrastructure']['connections-static_properties'] = f"./connections/connections-static_properties-stage_{stage_number}.xlsx"
    #config['piping_infrastructure']['pipes-dynamic_properties'] = f"./pipes/pipes-dynamic_properties-stage_{stage_number}.xlsx"
    config['piping_infrastructure']['pipe_options-dynamic_properties'] = f"./pipes/pipe_options-dynamic_properties-stage_{stage_number}.xlsx"

    # Climate
    config['climate']['climate-dynamic_properties'] = f"./climate/climate-dynamic_properties-stage_{stage_number}.xlsx"

    # Economy
    config['economy']['economy-dynamic_properties'] = f"./economy/economy-dynamic_properties-stage_{stage_number}.xlsx"

    # Energy system
    config['energy_system']['energy_system-dynamic_properties'] = f"./energy/energy_system-dynamic_properties-stage_{stage_number}.xlsx"

    # Water utilities
    #config['water_utilities']['water_utilities-dynamic_properties'] = f"./water_utilities/water_utilities-dynamic_properties-stage_{stage_number}.xlsx"
    config['save_results'] = {
        'entities': {
            'format': 'csv',
            'sources': True,
            'municipalities': True,
            'pumps': True,
            'solar_farms': True,
            'water_utilities': True
        },
        'analytics': {
            'peak_demands': True
        },
        'epanet_networks': {
            'mode': 'average_week'
        }
    }
    
    with open(configuration_filename, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False)

if __name__ == "__main__":
    # This script is intended to modify a configuration.yaml file with the inforamtion
    # for the new stage and team.

    import argparse
    parser = argparse.ArgumentParser(
        description="Update the BWF configuration.yaml file in the passed folder with the team info and the next stage values"
    )
    parser.add_argument(
        "next_stage_inputs",
        type=Path,
        help="Path to the folder containing the configuration.yaml file to update"
    )
    parser.add_argument(
        "stage_number",
        type=int,
        choices=[1,2,3],
        help="Stage of the compeition for which to generate the new data (1, 2, or 3)"
    )
    parser.add_argument(
        "team_name",
        type=str,
        help="Name/ID of the competitors"
    )
    args = parser.parse_args()

    next_stage_inputs = args.next_stage_inputs
    if not next_stage_inputs.is_absolute():
        next_stage_inputs = Path(os.getcwd()) / next_stage_inputs

    # We work form this file directory to have all paths relative to this file.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main(next_stage_inputs, args.stage_number, args.team_name)