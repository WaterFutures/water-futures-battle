import glob
import os

import pandas as pd

def upload_KNMI_csv_files_glob(
        property: str,
        variables: list[str],
        raw_data_dir='../raw-data',
        drop_columns=None,
    ) -> pd.DataFrame:
        """
        Loads all KNMI klimaatdashboard CSV files for a given property and all Dutch seasons,
        parses columns as floats, sets index to Jaar, and adjusts year for winter season.
        Concatenates all results into a single DataFrame.
        Optionally drops columns specified in drop_columns (list of column names).
        """

        # Dutch seasons and their starting months
        seasons = ['winter', 'lente', 'zomer', 'herfst']
        months = [12, 3, 6, 9]
        
        dfs = []
        for season, month, variable in zip(seasons, months, variables):
            season_pattern = f"KNMI_klimaatdashboard_*_{property}_{season}.csv"
            file = glob.glob(os.path.join(raw_data_dir, season_pattern))
            if not file:
                raise FileNotFoundError(f"No file found for season '{season}' with property '{property}'")
            if len(file) > 1:
                raise FileNotFoundError(f"Multiple files found for season '{season}' with property '{property}': {file}")
            file = file[0]
            
            df = pd.read_csv(file, index_col=0)
            df = df.apply(pd.to_numeric, errors='coerce')
            # Adjust year for winter: assign to previous year (winter starts in Dec)
            years = df.index.astype(int)
            if season == 'winter':
                years = years - 1
            # Create datetime index for first day of starting month
            dates = pd.to_datetime({
                'year': years,
                'month': [month]*len(years),
                'day': [1]*len(years)
            })
            df.index = dates
            df.index.name = 'timestamp'
            # Rename the column matching 'variable' to 'NL0000'
            df = df.rename(columns={variable: 'NL0000'})
            dfs.append(df)

        if dfs:
            result = pd.concat(dfs)
            result = result.sort_index()
            if drop_columns is not None:
                result = result.drop(columns=drop_columns, errors='ignore')
            return result
        else:
            raise FileNotFoundError(f"No KNMI CSV files found for property '{property}' in '{raw_data_dir}' matching expected patterns.")

def rename_KNMI_scenarios(df: pd.DataFrame) -> pd.DataFrame:
    MAP = {
        "Hn-klimaatscenario.1": "NL0000-Hn-median",
        "Hn-klimaatscenario range (low)": "NL0000-Hn-min",
        "Hn-klimaatscenario range (high)": "NL0000-Hn-max",
        "Hd-klimaatscenario.1": "NL0000-Hd-median",
        "Hd-klimaatscenario range (low)": "NL0000-Hd-min",
        "Hd-klimaatscenario range (high)": "NL0000-Hd-max",
        "Ln-klimaatscenario.1": "NL0000-Ln-median",
        "Ln-klimaatscenario range (low)": "NL0000-Ln-min",
        "Ln-klimaatscenario range (high)": "NL0000-Ln-max",
        "Ld-klimaatscenario.1": "NL0000-Ld-median",
        "Ld-klimaatscenario range (low)": "NL0000-Ld-min",
        "Ld-klimaatscenario range (high)": "NL0000-Ld-max"
    }

    return df.rename(columns=MAP)

def adjust_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    df.loc[pd.Timestamp("2000-01-01")] = df.loc[pd.Timestamp("1999-12-01")]
    df.sort_index(inplace=True)
    
    result = df.loc[df.index >= pd.Timestamp("2000-01-01")].copy()
    result = result[result.index.year != 2025]
    return result