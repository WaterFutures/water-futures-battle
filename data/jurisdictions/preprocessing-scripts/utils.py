import io
import glob
from typing import Optional, Any

import pandas as pd

from water_futures_battle.core.utility import keyify

def upload_csv_files_glob(
        name: str,
        columns_names: list[str],
        columns_dtypes: list[Any],
        path: str = '../raw-data',
        separator: str = ';',
        drop_first_n_rows: int = 5,
        drop_last_n_rows: int = 1
        ) -> pd.DataFrame:
    files_list = glob.glob(f'{path}/{name}-*.csv')

    columns_dtypes_map = {
        col: dtype for col, dtype in zip(columns_names, columns_dtypes) 
    }

    dfs = []
    for f in files_list:
        # Read CSV, skip first 5 rows, use ';' as separator, we know the columns
        df = pd.read_csv(
            f,
            sep=separator,
            decimal = ',',
            skiprows=drop_first_n_rows,
            header=None,
            names=columns_names,
            dtype=columns_dtypes_map,
            na_values=['-', '.', 'NaN'],
            keep_default_na=True,
            skipfooter=drop_last_n_rows, # requires engine='python'
            engine='python'
        )

        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)
    return df

# When downloading from the CBS we have a few differences from the files we uploaded...
# For example Utrecht is written Utrecht (gemeente), while in municipalities_df it is just Utrecht
# Also Bergen is the only name that is assigned to 2 municipalities (one in Limburg PV31 and one in Nord Holland PV27)
# Hengelo has a similar problem (Gelderland PV25 and O PV23)
# we clean everything appliying the keyify function

def reconstruct_CBS_fullname(row, cbs_df: pd.DataFrame, expected_matches: int) -> str:
    """
    Row is a row of the dataframe to which we need to associate CBS fullname starting from its name.
    CBS DF is a dataframe downloaded from the CBS that will work as lookup table. So its first column [0] will be the CBS_fullname
    """

    row_key = keyify(row['name'])

    cbs_df['key'] = cbs_df.loc[:,'CBS_fullname'].apply(keyify)
    cbs_df['cleaned_key'] = cbs_df.loc[:,'CBS_fullname'].apply(lambda x: keyify(x.split('(')[0].strip()))

    # Special cases
    if row_key == 'bergen' and row['province'] == 'PV31': # Limburg's Bergen
        return 'Bergen (L.)'
    if row_key == 'bergen' and row['province'] == 'PV27': # Noord-Holland's Bergen
        return 'Bergen (NH.)'
    if row_key == 'hengelo' and row['province'] == 'PV25': # Gelderland's Hengelo
        return 'Hengelo (Gld.)'
    if row_key == 'hengelo' and row['province'] == 'PV23': # Overijssel's Hengelo
        return 'Hengelo (O.)'
    
    # Count how many start with this key, if exactly the same number, then we found the match
    matches = cbs_df['key'].str.startswith(row_key)
    if matches.sum() == expected_matches:
        return cbs_df['CBS_fullname'][matches].iloc[0]
    
    #print(f"{row_key} {matches.sum()}")
    perfect_matches = cbs_df['cleaned_key'] == row_key
    #print(f"{row_key} {perfect_matches.sum()}")
    assert(perfect_matches.sum() == expected_matches)
    return cbs_df[matches].iloc[0, :]['CBS_fullname']
