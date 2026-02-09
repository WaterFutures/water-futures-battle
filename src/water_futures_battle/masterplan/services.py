import json
from pathlib import Path
from typing import Dict

import yaml
import pandas as pd

from .default_historical_data import get_historical_masterplan
from .entities import Masterplan

from rich import print

from .pydantic_model import Model

def parse_masterplan(masterplan_file: Path) -> Masterplan:
    masterplan = get_historical_masterplan()

    ext = masterplan_file.suffix.lower()
    new_masterplan = {}
    if ext in ['.json']:
        with open(masterplan_file, 'r') as f_json:
            new_masterplan = json.load(f_json)
    elif ext in ['.yaml', '.yml']:
        with open(masterplan_file, 'r') as f_yaml:
            new_masterplan = yaml.safe_load(f_yaml)
    elif ext in ['.xlsx', '.xls']:
        new_masterplan = parse_excel_masterplan(masterplan_file)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
    
    for year in new_masterplan['years']:
        masterplan['years'].append(year)

    return Masterplan(data=masterplan)

def parse_excel_masterplan(masterplan_file: Path) -> Dict:
    # Load the Excel file (all sheets except 'DATA')
    # Using pandas ExcelFile to get sheet names
    xl = pd.ExcelFile(masterplan_file)
    sheet_names = [s for s in xl.sheet_names if s.upper() != 'DATA']
    
    # Load sheets into a dictionary of DataFrames
    dfs = {s: xl.parse(s) for s in sheet_names}
    
    # Helper to normalize sheet names for easier lookup
    def get_df(name):
        for k in dfs.keys():
            if name.upper() in k.upper():
                return dfs[k]
        return pd.DataFrame()

    # Determine unique years across all sheets
    all_years = set()
    for df in dfs.values():
        if 'YEAR' in df.columns:
            all_years.update(df['YEAR'].dropna().unique())
    
    masterplan = {"years": []}

    for year in sorted(list(all_years)):
        year_entry = {"year": int(year)}
        
        # --- 1. National Policies ---
        budget_df = get_df('BUDGET ALLOCATION')
        if not budget_df.empty:
            year_budget = budget_df[budget_df['YEAR'] == year]
            if not year_budget.empty:
                year_entry['national_policies'] = {
                    'budget_allocation': {
                        'policy': year_budget.iloc[0]['POLICY'].lower().replace(' ', '_')
                    }
                }
        
        # --- 2. National Interventions (Pipes connecting utilities) ---
        pipe_df = get_df('INSTALL PIPE')
        if not pipe_df.empty:
            nat_pipes = pipe_df[(pipe_df['YEAR'] == year) & (pipe_df['WATER UTILITY'].str.upper() == 'NATIONAL')]
            if not nat_pipes.empty:
                year_entry['national_interventions'] = {
                    'install_pipe': [
                        {'connection_id': row['CONNECTION ID'], 'pipe_option_id': row['PIPE OPTION ID']}
                        for _, row in nat_pipes.iterrows()
                    ]
                }
        
        # --- 3. Water Utilities ---
        # Get all unique Water Utility IDs for this year (excluding 'NATIONAL')
        utilities = set()
        relevant_sheets = ['NRW MITIGATION', 'PRICE ADJUSTMENT', 'OPEN SOURCE', 
                           'CLOSE SOURCE', 'INSTALL PIPE', 'INSTALL PUMPS', 'INSTALL SOLAR']
        for sheet in relevant_sheets:
            df = get_df(sheet)
            if not df.empty and 'WATER UTILITY' in df.columns:
                utils = df[(df['YEAR'] == year) & (df['WATER UTILITY'].str.upper() != 'NATIONAL')]['WATER UTILITY'].unique()
                utilities.update(utils)
        
        water_utilities_list = []
        for wu_id in sorted(list(utilities)):
            wu_entry = {"water_utility": wu_id}
            
            # Policies
            policies = {}
            
            # NRW Mitigation
            nrw_df = get_df('NRW MITIGATION')
            if not nrw_df.empty:
                wu_nrw = nrw_df[(nrw_df['YEAR'] == year) & (nrw_df['WATER UTILITY'] == wu_id)]
                if not wu_nrw.empty:
                    policies['nrw_mitigation'] = {
                        'budget': int(wu_nrw.iloc[0]['BUDGET']),
                        'policy': wu_nrw.iloc[0]['POLICY'].lower().replace(' ', '_')
                    }
            
            # Price Adjustment
            price_df = get_df('PRICE ADJUSTMENT')
            if not price_df.empty:
                wu_price = price_df[(price_df['YEAR'] == year) & (price_df['WATER UTILITY'] == wu_id)]
                if not wu_price.empty:
                    policy_type = wu_price.iloc[0]['POLICY'].lower().replace(' ', '_')
                    policies['pricing_adjustment'] = {'policy': policy_type}
                    if policy_type == 'custom':
                        policies['pricing_adjustment']['policy_args'] = {
                            'fixed_component': float(wu_price.iloc[0]['FIXED COMPONENT']),
                            'variable_component': float(wu_price.iloc[0]['VARIABLE COMPONENT']),
                            'selling_price': float(wu_price.iloc[0]['SELLING PRICE'])
                        }
            
            if policies: wu_entry['policies'] = policies
                
            # Interventions
            interventions = {}
            
            # Open/Close Source
            os_df = get_df('OPEN SOURCE')
            if not os_df.empty:
                wu_os = os_df[(os_df['YEAR'] == year) & (os_df['WATER UTILITY'] == wu_id)]
                if not wu_os.empty:
                    interventions['open_source'] = [
                        {'source_id': r['SOURCE ID'], 'source_capacity': int(r['SOURCE CAPACITY']), 
                         'pump_option_id': r['PUMP OPTION ID'], 'n_pumps': int(r['N PUMPS']), 
                         'pipe_option_id': r['PIPE OPTION ID']} for _, r in wu_os.iterrows()
                    ]

            # Install Pumps/Solar/Pipes (utility level)
            pumps_df = get_df('INSTALL PUMPS')
            if not pumps_df.empty:
                wu_pumps = pumps_df[(pumps_df['YEAR'] == year) & (pumps_df['WATER UTILITY'] == wu_id)]
                if not wu_pumps.empty:
                    interventions['install_pumps'] = [
                        {'source_id': r['SOURCE ID'], 'pump_option_id': r['PUMP OPTION ID'], 
                         'n_pumps': int(r['N PUMPS']), 'behaviour': r['BEHAVIOUR'].lower()} 
                        for _, r in wu_pumps.iterrows()
                    ]

            if interventions: wu_entry['interventions'] = interventions
            water_utilities_list.append(wu_entry)
            
        if water_utilities_list:
            year_entry['water_utilities'] = water_utilities_list
            
        masterplan['years'].append(year_entry)
        
    return masterplan
