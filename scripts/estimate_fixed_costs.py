import os
from pathlib import Path

import pandas as pd

def main(teams_dir: Path, stage_number: int) -> None:
    
    TEAM_ID = "TEAM00"
    STAGE_YEARS = list(range(
        2000+25*stage_number,
        2000+25*(stage_number+1)
    ))

    results_dir = teams_dir / TEAM_ID / f"{stage_number}" / f"bwf_results-{TEAM_ID}-stage_{stage_number}"

    if stage_number == 1:
        balances_file = results_dir / "water_utilities" / "water_utilities-dynamic_properties-original.xlsx"
    else:
        balances_file = results_dir / "water_utilities" / "water_utilities-dynamic_properties.xlsx"

    balance_df = pd.read_excel(
        balances_file,
        sheet_name='balance',
        index_col='timestamp',
        parse_dates=True
    )

    # Compute annual earnings as the difference between consecutive years
    # shift by one because balances are set to the year after
    earnings_df = balance_df.diff().shift(-1).dropna()
    earnings_df.index = earnings_df.index.year
    earnings_df = earnings_df[earnings_df.index.isin(STAGE_YEARS)]
    print(earnings_df)

    # 3-year rolling average as estimated fixed cost
    earnings_df = earnings_df.rolling(window=3, min_periods=1, center=True).mean()*1.01

    # Cost normalisation uses the name year for the index instead of timestamp
    earnings_df.index.name = 'year'

    # Save to CSV
    earnings_df.round(-3).astype(int).to_csv(f"cost_normalisation-stage_{stage_number}.csv")

    return

if __name__ == "__main__":
    """
    This script is intended to be run once all teams have been evaluated across all 
    stages to rank the participants.

    how to run -> scores
    """
    import argparse
    parser = argparse.ArgumentParser(
        description="Estimate the fixed costs of a competition stage from the do-nothing solution (TEAM00)."
    )
    parser.add_argument(
        "stage_number",
        type=int,
        choices=[1,2,3],
        help="Stage of the compeition for which to generate the new data (1, 2, or 3)"
    )
    args = parser.parse_args()

    # We work form the repository directory to have all paths relative to this file.
    script_dir = Path(__file__).resolve().parent
    repo_dir = script_dir.parent
    os.chdir(repo_dir)

    main(
        teams_dir= repo_dir / "teams",
        stage_number=args.stage_number
    ) 