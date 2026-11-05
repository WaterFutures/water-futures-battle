from dataclasses import dataclass, field
import os
from pathlib import Path
import shutil

import pandas as pd
@dataclass
class TeamData:
    metrics: dict[int, dict[str, pd.DataFrame]] = field(default_factory=dict)
    population: pd.DataFrame = field(default_factory=pd.DataFrame)

FIN = 'financial_sustainability'
EMS = 'GHG_emissions'
REL = 'service_reliability'
AFF = 'affordability'
METRICS = [FIN, EMS, REL, AFF]

Y2050 = pd.Timestamp(year=2050, month=1, day=1)

def main(teams_dir: Path) -> None:
    
    # first loop: find the minimum balance and load the data
    min_team_balance = float('inf')
    teams_wu_dp = {}
    for team_path in sorted(teams_dir.iterdir()):
        if not team_path.is_dir():
            continue
        
        # skip private copy
        if '-' in team_path.name:
            continue
        
        team_id = team_path.name
        results_dir = team_path / "1" / f"bwf_results-{team_id}-stage_1"
            
        if not results_dir.exists():
            break # not simulated yet

        balances_file = results_dir / "water_utilities" / "water_utilities-dynamic_properties.xlsx"

        orig_balances_file = results_dir / "water_utilities" / "water_utilities-dynamic_properties-original.xlsx"

        if not orig_balances_file.exists():
            # copy the file as a backup
            shutil.copy(balances_file, orig_balances_file)

        # always open the backup file which contains the original value
        # this makes sure that if we call it twice we don't mess up
        dfs = pd.read_excel(
            orig_balances_file,
            sheet_name=None,
            index_col='timestamp',
            parse_dates=True
        )
        teams_wu_dp[team_id] = dfs

        team_final_balance = float(dfs['balance'].loc[Y2050].sum())

        if team_final_balance < min_team_balance:
            min_team_balance = team_final_balance

    # balance for the lowest team after scaling
    min_team_balance -= 1e9 

    # second loop: update final balances and save
    for team_path in sorted(teams_dir.iterdir()):
        if not team_path.is_dir():
            continue

        # skip private copy
        if '-' in team_path.name:
            continue

        team_id = team_path.name
        results_dir = team_path / "1" / f"bwf_results-{team_id}-stage_1"
            
        if not results_dir.exists():
            break # not simulated yet

        team_balances = teams_wu_dp[team_id]['balance']

        team_final_balances = team_balances.loc[Y2050]

        team_total_final_balance = float(team_final_balances.sum())

        team_new_balances = team_final_balances / team_total_final_balance * (team_total_final_balance - min_team_balance)

        teams_wu_dp[team_id]['balance'].loc[Y2050] = team_new_balances

        # done, save it 
        balances_file = results_dir / "water_utilities" / "water_utilities-dynamic_properties.xlsx"
    
        with pd.ExcelWriter(balances_file) as writer:
            for sheet, df in teams_wu_dp[team_id].items():
                
                df.index = df.index.strftime('%Y-%m-%d')

                df.to_excel(writer, sheet_name=sheet, index=True)
        
        print(f"{balances_file} DONE")

    return

if __name__ == "__main__":
    """
    This script is intended to be run once all teams have been evaluated across all 
    stages to rank the participants.

    how to run -> scores
    """
    
    # We work form the repository directory to have all paths relative to this file.
    script_dir = Path(__file__).resolve().parent
    repo_dir = script_dir.parent
    os.chdir(repo_dir)

    main(teams_dir= repo_dir / "teams") 