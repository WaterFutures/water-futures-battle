import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, NamedTuple

import numpy as np
import pandas as pd
import yaml

from water_futures_battle.core.base_model import DynamicProperties
from water_futures_battle.economy.dynamic_properties import EconomyDB
from water_futures_battle.jurisdictions.enums import MunicipalitySize
from water_futures_battle.jurisdictions.dynamic_properties import MunicipalitiesDB
RNG = np.random.default_rng(seed=12880)

STAGE_SEEDS = RNG.spawn(n_children=3)
STAGE_YEARS = [
    ("2025-01-01", "2049-01-01"),
    ("2050-01-01", "2074-01-01"),
    ("2075-01-01", "2099-01-01"),
]
STAGE_INF_WEIGHT_INCOME = [
    0.25,
    0.4,
    0.17
]
STAGE_TREND_INCOME = [
    0.015,
    0.023,
    0.010
]
STAGE_VOLATILITY_INCOME = [
    0.005,
    0.01,
    0.001
]
STAGE_POP2HOUSE = [ # Currently is around 2.7
    2.5, # less people per house, more singles
    3.2, # bad economic moment, more people per house
    3, # long-term target
]
STAGE_BUS2POP = [ # Unknown currently (check histrorical data and make based on that, these values. are relative)
    0.11 , # put same as historical
    0.02,  # bad economic moment, high inflation, high interest rates, and theregore less new businesses
    0.13   # back to current condition (good development) 
]
STAGE_POPULATION_R = [
    # Stage 1
    {
        "until": pd.Timestamp(year=2040, month=1, day=1),
        "r": {
            MunicipalitySize.SMALL: (0.972, 0.99), # bounds for rate of change
            MunicipalitySize.MEDIUM: (0.994, 1.028), 
            MunicipalitySize.LARGE: (1.003, 1.03),
            MunicipalitySize.G4: (1.006, 1.017)
        }
    },
    {
        "until": pd.Timestamp(year=2055, month=1, day=1),
        "r": {
            MunicipalitySize.SMALL: (0.94, 0.99), # bounds for rate of change
            MunicipalitySize.MEDIUM: (1.007, 1.011), 
            MunicipalitySize.LARGE: (1.013, 1.017),
            MunicipalitySize.G4: (1.013, 1.017)
        }
    },
    {
        "until": pd.Timestamp(year=2070, month=1, day=1),
        "r": {
            MunicipalitySize.SMALL: (0.98, 1.02), # bounds for rate of change
            MunicipalitySize.MEDIUM: (0.98, 1.02), 
            MunicipalitySize.LARGE: (0.98, 1.02),
            MunicipalitySize.G4: (0.98, 1.02)
        }

    },
    {
        "until": pd.Timestamp(year=2100, month=1, day=1),
        "r": {
            MunicipalitySize.SMALL: (1.015, 1.018), # bounds for rate of change
            MunicipalitySize.MEDIUM: (1.015, 1.018), 
            MunicipalitySize.LARGE: (0.998, 1.002),
            MunicipalitySize.G4: (0.998, 1.002)
        }
    }
]

class OpeningDescType(NamedTuple):
    new_municipality_id: str
    closing_municipalities_id: List[str]
    demand_patterns: Dict[str, str]

CollOpeningDescType = Dict[pd.Timestamp, List[OpeningDescType]]
CollClosingDescType = Dict[pd.Timestamp, List[str]]

def process_stage_events(
        new_municipalities_events: Dict[str, Any],
        municipalites_df: pd.DataFrame,
        stage_idx: int
    ) -> Tuple[CollOpeningDescType, CollClosingDescType]:
    """
    Given a dictionary of events (new_municipalities_events file content), filter
    by keeping only this stage's events and process the event in a datastructure 
    that is helpful for these processes:
    opening desc: year as key, list of: (opening municiplaity id, list of closing municipalities id, dictionary of the demand patterns)
    closing desc: year as key, list of ALL closing municipalities id
    """
    stage_years = pd.date_range(
        start=pd.to_datetime(STAGE_YEARS[stage_idx][0]),
        end=pd.to_datetime(STAGE_YEARS[stage_idx][1]),
        freq='YS'
    )

    openings_desc: CollOpeningDescType = {}
    closing_desc: CollClosingDescType = {}
    for year in stage_years:
        for merger in new_municipalities_events['mergers']:
            if pd.to_datetime(merger['date']) != year:
                continue

            new_municipality_id = str(municipalites_df.index[municipalites_df['name'] == merger['name']][0])

            if year not in openings_desc:
                openings_desc[year] = []

            if year not in closing_desc:
                closing_desc[year] = []

            openings_desc[year].append(
                OpeningDescType(
                    new_municipality_id,
                    merger['closing'],
                    { k: v 
                     for k,v in merger.items()
                     if k in ['DP-R1', 'DP-R2', 'DP-B', 'pop_flow']
                    }
                )
            )

            closing_desc[year].extend(
                merger['closing'],
            )

        for absorption in new_municipalities_events['absorptions']:
            if pd.to_datetime(merger['date']) != year:
                continue

            new_municipality_id = absorption['receiving_id']

            if year not in openings_desc:
                openings_desc[year] = []

            if year not in closing_desc:
                closing_desc[year] = []

            openings_desc[year].append(
                OpeningDescType(
                    new_municipality_id,
                    merger['closing'] + [absorption['receiving_id']],
                    { k: v 
                     for k,v in merger.items()
                     if k in ['DP-R1', 'DP-R2', 'DP-B', 'pop_flow']
                    }
                )
            )

            closing_desc[year].extend(
                merger['closing'],
            )
    
    return openings_desc, closing_desc

def append_population_data(
        population_df: pd.DataFrame,
        openings_desc: CollOpeningDescType,
        closing_desc: CollClosingDescType,
        stage_idx: int
) -> pd.DataFrame:
    
    rng = STAGE_SEEDS[stage_idx]

    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")

    cols = set([c for c in population_df.columns if c.startswith('GM')]) # drop national level columns, we add them at the end
    cols = cols.union([ e.new_municipality_id
        for events in openings_desc.values() for e in events
    ])

    population_df = population_df.reindex(
        index=population_df.index.union(YEARS),
        columns=list(sorted(cols))
    )
    population_df.index.name = 'timestamp'

    brake_years = [ i["until"]  for i in STAGE_POPULATION_R if i["until"] > pd.to_datetime(years_start)]
    index = 0

    # Helper for constant population flows
    constant_pop_flows: Dict[str, List[int]] = {}

    for year in YEARS:
        if year >= brake_years[index]:
            index += 1 

        prev_year = year - pd.DateOffset(years=1)

        row = {}
        for municipality in population_df.columns:
            prev_pop = float(population_df.loc[prev_year, municipality])

            if pd.isna(prev_pop):
                # Municipality is already closed, skip
                continue

            if municipality in closing_desc.get(year,[]):
                # municipality is closing this year, skip
                continue

            # Population = Prev * (random_growth) (random growth is around 1)
            # Plus constant population flow is the municipality is in there
            type_mc = MunicipalitySize.determine_class(prev_pop)
            rate_of_change = STAGE_POPULATION_R[index]["r"][type_mc]

            current_pop = int(prev_pop * rng.uniform(rate_of_change[0], rate_of_change[1]))

            if municipality in constant_pop_flows and len(constant_pop_flows[municipality])>0:
                current_pop += constant_pop_flows[municipality].pop()

            row[municipality] = current_pop

        for event in openings_desc.get(year, []):
            municipality = event.new_municipality_id

            # New population is the sum of the populations of the closing municipalities
            # plus the extra flow which is constant for 10 years.
            prev_pops = population_df.loc[prev_year, event.closing_municipalities_id]

            additional_pop_flow = int(event.demand_patterns['pop_flow'])

            current_pop = prev_pops.sum()+additional_pop_flow
            
            row[municipality] = current_pop

            # Also save the next 9 years in the helper constant population flows
            constant_pop_flows[municipality] = [additional_pop_flow] * 9

        population_df.loc[year] = row

    population_df['NL0000'] = population_df.sum(axis=1, skipna=True)
    population_df.sort_index(inplace=True)
    population_df = population_df[population_df.index <= YEARS[-1]]
    
    return population_df

def same_area_over_the_years(
        df: pd.DataFrame,
        openings_desc: CollOpeningDescType,
        closing_desc: CollClosingDescType,
        stage_idx: int
) -> pd.DataFrame:
    
    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")
    
    cols = set(df.columns).union([ e.new_municipality_id
        for events in openings_desc.values() for e in events
    ])
    df = df.reindex(
        index=df.index.union(YEARS),
        columns=list(sorted(cols))
    )
    df.index.name = 'timestamp'
    
    for year in YEARS:
        prev_year = year - pd.DateOffset(years=1)

        row = {}
        for municipality in df.columns:
            prev_value = df.loc[prev_year, municipality]

            if pd.isna(prev_value):
                # Municipality is already closed, skip
                continue

            if municipality in closing_desc.get(year,[]):
                # municipality is closing this year, skip
                continue

            row[municipality] = prev_value

        for event in openings_desc.get(year, []):
            municipality = event.new_municipality_id

            # New data is just the sum of the prev_data
            prev_values = df.loc[prev_year, event.closing_municipalities_id]

            current_value = prev_values.sum()
            
            row[municipality] = current_value

        df.loc[year] = row
        
    return df.sort_index()

def append_population_dependent_data(
        df:pd.DataFrame,
        population_df:pd.DataFrame,
        factor: float,
        openings_desc: CollOpeningDescType,
        closing_desc: CollClosingDescType,
        stage_idx: int
)-> pd.DataFrame:
    
    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")
    
    cols = set(df.columns).union([ e.new_municipality_id
        for events in openings_desc.values() for e in events
    ])
    df = df.reindex(
        index=df.index.union(YEARS),
        columns=list(sorted(cols))
    )
    df.index.name = 'timestamp'

    for year in YEARS:
        prev_year = year - pd.DateOffset(years=1)

        row = {}
        for municipality in df.columns:
            prev_value = df.loc[prev_year, municipality]

            if pd.isna(prev_value):
                # Municipality is already closed, skip
                continue

            if municipality in closing_desc.get(year,[]):
                # municipality is closing this year, skip
                continue

            population_increase = population_df.loc[year, municipality] - population_df.loc[prev_year, municipality]
            assert pd.notna(population_increase)
            
            current_value = prev_value + int(population_increase * factor)
            
            row[municipality] = current_value

        for event in openings_desc.get(year, []):
            municipality = event.new_municipality_id

            # New data is just the sum of the prev_data
            prev_values = df.loc[prev_year, event.closing_municipalities_id]

            current_value = prev_values.sum()
            
            row[municipality] = current_value
    
        df.loc[year] = row

    return df

def same_pattern_over_the_years(
        df: pd.DataFrame,
        key: str,
        openings_desc: CollOpeningDescType,
        closing_desc: CollClosingDescType,
        stage_idx: int
) -> pd.DataFrame:
    
    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")
    
    cols = set(df.columns).union([ e.new_municipality_id
        for events in openings_desc.values() for e in events
    ])
    df = df.reindex(
        index=df.index.union(YEARS),
        columns=list(sorted(cols)),
        fill_value=""
    )
    df.index.name = 'timestamp'
    
    for year in YEARS:
        prev_year = year - pd.DateOffset(years=1)

        row = {}
        for municipality in df.columns:
            prev_value = df.loc[prev_year, municipality]

            if pd.isna(prev_value):
                # Municipality is already closed, skip
                continue

            if municipality in closing_desc.get(year,[]):
                # municipality is closing this year, skip
                continue

            row[municipality] = prev_value

        for event in openings_desc.get(year, []):
            municipality = event.new_municipality_id

            # New data comes from the event
            current_value = event.demand_patterns[key]
            
            row[municipality] = current_value

        df.loc[year] = row
        
    return df.sort_index()

def append_income_data(
        income_df: pd.DataFrame,
        inflation_df: pd.DataFrame,
        population_df: pd.DataFrame,
        openings_desc: CollOpeningDescType,
        closing_desc: CollClosingDescType,
        stage_idx: int
    )-> pd.DataFrame:
    
    rng = STAGE_SEEDS[stage_idx]

    years_start, years_end = STAGE_YEARS[stage_idx]
    YEARS = pd.date_range(start=years_start, end=years_end, freq="1YS")
    
    cols = set(income_df.columns).union([ e.new_municipality_id
        for events in openings_desc.values() for e in events
    ])
    income_df = income_df.reindex(
        index=income_df.index.union(YEARS),
        columns=list(sorted(cols))
    )
    income_df.index.name = 'timestamp'

    k = STAGE_INF_WEIGHT_INCOME[stage_idx]
    ann_growth = STAGE_TREND_INCOME[stage_idx]
    volatility = STAGE_VOLATILITY_INCOME[stage_idx]

    for year in YEARS:
        current_inflation = inflation_df.loc[year, "NL0000"]/100
        prev_year = year - pd.DateOffset(years=1)

        row = {}
        for municipality in income_df.columns:
            prev_income = float(income_df.loc[prev_year, municipality])

            if pd.isna(prev_income):
                # Municipality is already closed, skip
                continue

            if municipality in closing_desc.get(year, []):
                # municipality is closing this year, skip
                continue

            # Income = Prev * (1 + k * (ann_growth + inflation) + volatility * Z)
            
            z_score = rng.standard_normal()
            growth_factor = (
                k * (ann_growth + current_inflation) + 
                (volatility * z_score)
            )
            current_income = prev_income * (1 + growth_factor)

            row[municipality] = current_income

        for event in openings_desc.get(year, []):
            municipality = event.new_municipality_id

            # take population and income of the closing municipalities in the previous year
            # do weighted average of them
            # but assign to this new municipality in this year
            prev_incomes = income_df.loc[prev_year, event.closing_municipalities_id]
            prev_pops = population_df.loc[prev_year, event.closing_municipalities_id]

            current_income = float((prev_incomes * prev_pops).sum() / prev_pops.sum())
            
            row[municipality] = current_income

        income_df.loc[year] = row
            
    return income_df.sort_index().round(1)

def main(previous_stage_results: Path, next_stage_inputs: Path, stage_number: int):
    
    filename = 'municipalities-dynamic_properties.xlsx'
    
    input_path =  previous_stage_results / 'jurisdictions' / filename
    
    municipalities_db = MunicipalitiesDB.load_from_file(input_path)

    # Lookup df to get the new municipalities information and the closing ones
    juris_file = next_stage_inputs / 'jurisdictions' / f'jurisdictions-static_properties-stage_{stage_number}.xlsx'
    municipalities_df = pd.read_excel(juris_file, sheet_name='municipalities', index_col='cbs_id')

    # Events file
    # Relative path to this script for the new municipalities file
    with open('../raw-data/new_municipalities_events.yaml', 'r') as f:
        new_municipalities_events = yaml.safe_load(f)
    
    openings_desc, closures_desc = process_stage_events(new_municipalities_events, municipalities_df, stage_number-1)

    # Firs of all, let's deal with population because many other depend on this
    population_df = municipalities_db[MunicipalitiesDB.POPULATION]
    population_df = append_population_data(
        population_df=population_df,
        openings_desc=openings_desc,
        closing_desc=closures_desc,
        stage_idx=stage_number-1
    )
    
    # The following variables remaing unchanged or are addittive for mergers
    surface_land_df = municipalities_db[MunicipalitiesDB.AREA_LAND]
    surface_water_inland_df = municipalities_db[MunicipalitiesDB.AREA_WATERIN]
    surface_water_open_df = municipalities_db[MunicipalitiesDB.AREA_WATEROUT]

    surface_land_df = same_area_over_the_years(
        df=surface_land_df,
        openings_desc=openings_desc,
        closing_desc=closures_desc,
        stage_idx=stage_number-1
    )
    surface_water_inland_df = same_area_over_the_years(
        df=surface_water_inland_df,
        openings_desc=openings_desc,
        closing_desc=closures_desc,
        stage_idx=stage_number-1
    )
    surface_water_open_df = same_area_over_the_years(
        df=surface_water_open_df,
        openings_desc=openings_desc,
        closing_desc=closures_desc,
        stage_idx=stage_number-1
    )

    # The following variables grow along with population growth by a given factor
    # also additive for mergers
    n_house_df = municipalities_db[MunicipalitiesDB.N_HOUSES]
    n_business_df = municipalities_db[MunicipalitiesDB.N_BUSINESSES]

    n_houses_df = append_population_dependent_data(
        df=n_house_df,
        population_df=population_df,
        factor=1/STAGE_POP2HOUSE[stage_number-1], # we need houses per pop as we multiply the factor
        openings_desc=openings_desc,
        closing_desc=closures_desc,
        stage_idx=stage_number-1
    )
    n_business_df = append_population_dependent_data(
        df=n_business_df,
        population_df=population_df,
        factor=STAGE_BUS2POP[stage_number-1], # this is already the correct factor (new businesses per new person)
        openings_desc=openings_desc,
        closing_desc=closures_desc,
        stage_idx=stage_number-1
    )

    # The following variables remaing unchanged or are addittive for mergers
    assoc_dem_pat_df1 = municipalities_db[MunicipalitiesDB.ASSOC_DM_R1].fillna("").astype(str)
    assoc_dem_pat_df2 = municipalities_db[MunicipalitiesDB.ASSOC_DM_R2].fillna("").astype(str)
    assoc_dem_pat_business_df = municipalities_db[MunicipalitiesDB.ASSOC_DM_B].fillna("").astype(str)
    assoc_dem_pat_df1 = same_pattern_over_the_years(
        df=assoc_dem_pat_df1,
        key='DP-R1',
        openings_desc=openings_desc,
        closing_desc=closures_desc,
        stage_idx=stage_number-1
    )
    assoc_dem_pat_df2 = same_pattern_over_the_years(
        df=assoc_dem_pat_df2,
        key='DP-R2',
        openings_desc=openings_desc,
        closing_desc=closures_desc,
        stage_idx=stage_number-1
    )
    assoc_dem_pat_business_df = same_pattern_over_the_years(
        df=assoc_dem_pat_business_df,
        key='DP-B',
        openings_desc=openings_desc,
        closing_desc=closures_desc,
        stage_idx=stage_number-1
    )

    # Income behaviour depends on inflation
    # for mergets is a weighted average
    disposable_income_df = municipalities_db[MunicipalitiesDB.ADI]
    
    inflation_inputpath = next_stage_inputs / 'economy' / f'economy-dynamic_properties-stage_{stage_number}.xlsx'
    economy_db = EconomyDB.load_from_file(inflation_inputpath)
    inflation_df = economy_db[EconomyDB.INFLATION]

    disposable_income_df = append_income_data(
        income_df=disposable_income_df,
        inflation_df=inflation_df,
        population_df=population_df,
        openings_desc=openings_desc,
        closing_desc=closures_desc,
        stage_idx=stage_number-1
    )

    #assign back and save
    municipalities_db[MunicipalitiesDB.POPULATION] = population_df
    municipalities_db[MunicipalitiesDB.AREA_LAND] = surface_land_df
    municipalities_db[MunicipalitiesDB.AREA_WATERIN] = surface_water_inland_df
    municipalities_db[MunicipalitiesDB.AREA_WATEROUT] = surface_water_open_df
    municipalities_db[MunicipalitiesDB.N_HOUSES] = n_houses_df
    municipalities_db[MunicipalitiesDB.N_BUSINESSES] = n_business_df
    municipalities_db[MunicipalitiesDB.ASSOC_DM_R1] = assoc_dem_pat_df1
    municipalities_db[MunicipalitiesDB.ASSOC_DM_R2] = assoc_dem_pat_df2
    municipalities_db[MunicipalitiesDB.ASSOC_DM_B] = assoc_dem_pat_business_df
    municipalities_db[MunicipalitiesDB.ADI] = disposable_income_df

    municipalities_dps = DynamicProperties(
        name =f"municipalities-dynamic_properties-stage_{stage_number}",
        dataframes= municipalities_db
    )

    municipalities_dps.dump(path = next_stage_inputs / "jurisdictions")

if __name__ == "__main__":
    # This script is intended to be run for each team to append exogenous dynamic properties
    # to the system's final status from the previous stage, producing new input files for the next stage.

    # Parse arguments: previous stage results directory and next stage input directory.
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate dynamic pipe options properties for stage 1 based on the previous stage's final status."
    )
    parser.add_argument(
        "stage_number",
        type=int,
        choices=[1,2,3],
        help="Stage of the compeition for which to generate the new data (1, 2, or 3)"
    )
    parser.add_argument(
        "previous_stage_results",
        type=Path,
        help="Path to the folder containing the final status of the system in the previous stage (absolute or relative to the current working directory)."
    )
    parser.add_argument(
        "next_stage_inputs",
        type=Path,
        help="Path to the output folder where the new input files for the next stage will be saved (absolute or relative to the current working directory)."
    )
    args = parser.parse_args()

    previous_stage_results = args.previous_stage_results
    if not previous_stage_results.is_absolute():
        previous_stage_results = Path(os.getcwd()) / previous_stage_results
    next_stage_inputs = args.next_stage_inputs
    if not next_stage_inputs.is_absolute():
        next_stage_inputs = Path(os.getcwd()) / next_stage_inputs

    # We work form this file directory to have all paths relative to this file.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main(previous_stage_results, next_stage_inputs, args.stage_number)
