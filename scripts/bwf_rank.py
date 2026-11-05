# /// script
# dependencies = [
#     "pandas",
#     "plotly",
#     "openpyxl",
# ]
# ///

from dataclasses import dataclass, field
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

FIN = 'financial_sustainability'
EMS = 'GHG_emissions'
REL = 'service_reliability'
AFF = 'affordability'
METRICS = [FIN, EMS, REL, AFF]

STAGES = [1, 2, 3]

REFERENCE_TEAM = "TEAM00"

# Function to create a mapping between the utilitites and their municipalities
def upload_wu_municipality_map(teams_dir: Path) -> dict[str, list[str]]:
    
    wu_map: dict[str, list[str]] = {}

    input_dir_path = teams_dir / REFERENCE_TEAM / "1" / f"bwf_inputs-{REFERENCE_TEAM}-stage_1"

    if not input_dir_path.exists():
        raise FileNotFoundError(
            f"Could not find stage-1 inputs for {REFERENCE_TEAM} in {teams_dir}. "
            "Cannot build water utility to municipality map."
        )

    # Load water utilities and their assigned provinces
    wu_df = pd.read_excel(
        input_dir_path / "water_utilities" / "water_utilities-static_properties.xlsx",
        sheet_name="entities",
        usecols=["water_utility_id", "assigned_provinces"],
    )

    # Load municipalities and their province
    mun_df = pd.read_excel(
        input_dir_path / "jurisdictions" / "jurisdictions-static_properties-stage_1.xlsx",
        sheet_name="municipalities",
        usecols=["cbs_id", "province"],
    )

    # Build province → [municipality ids] lookup
    province_to_municipalities: dict[str, list[str]] = (
        mun_df.groupby("province")["cbs_id"]
        .apply(list)
        .to_dict()
    )

    # Build utility → [municipality ids]
    for _, row in wu_df.iterrows():
        provinces = [p.strip() for p in row["assigned_provinces"].split(";")]
        municipalities = []
        for province in provinces:
            municipalities.extend(province_to_municipalities.get(province, []))
        wu_map[row["water_utility_id"]] = municipalities

    return wu_map

# Variable to hold the map
wu_municipalities_map: dict[str, list[str]] = {}

def reliability_perception(
        rel_df: pd.DataFrame,
        pop_df: pd.DataFrame
    ) -> float:

    # For each municipality, find the minimum reliability,
    # get the population at that time, and sum (min reliability * population at that time)
    total = 0.0
    total_pop = 0.0
    for col in rel_df.columns:
        min_idx = rel_df[col].idxmin()
        min_rel = float(rel_df.at[min_idx, col])

        pop = int(pop_df.at[min_idx, col])
        
        total += min_rel * pop
        total_pop += pop

    return round(float(total/total_pop),3)

def debt_perception(
        debt_df: pd.DataFrame,
        pop_df: pd.DataFrame
    ) -> float:

    total_ppd = 0 # per person debts
    for col in debt_df.columns:
        debt_year = debt_df.index[0] # Debt should only have one row with the alue at the end of the stage
        debt = debt_df.loc[debt_year, col]

        last_year = debt_year - pd.DateOffset(years=1)
        people_in_wu = pop_df.loc[last_year, wu_municipalities_map[col]].sum(skipna=True)

        per_person_debt = debt / people_in_wu
        
        total_ppd += per_person_debt

    avg_ppd = total_ppd / len(debt_df.columns)

    return float(avg_ppd)

def emissions_perception(
        ghg_df: pd.DataFrame
    ) -> float:

    return float(ghg_df.sum().sum())

def affordability_perception(
        aff_df: pd.DataFrame,
        lam: float
    ) -> float:

    f_tilde = aff_df.median(axis=0)
    
    return round(
        float(
            f_tilde.mean() + lam * f_tilde.std(ddof=0)
        ),
        4
    )

# Value set for the affordability perception
LAMBDA_AFF_PERC = 0.0

@dataclass
class TeamData:
    metrics: dict[int, dict[str, pd.DataFrame]] = field(default_factory=dict)
    population: pd.DataFrame = field(default_factory=pd.DataFrame)
    complete: bool = True # start trusting it, as soon as we don't find a stage, reset
    reference: bool = False
    
    _perceptions: dict[int, dict[str, float]] | None = None

    @property
    def perceptions(self) -> dict[int, dict[str, float]]:

        if self._perceptions is None:
            self._perceptions = self._compute_perceptions()

        return self._perceptions

    def _compute_perceptions(self) -> dict[int, dict[str, float]]:
        result = {}
        for stage, stage_metrics in self.metrics.items():
            result[stage] = {
                FIN: debt_perception(
                    debt_df=stage_metrics[FIN],
                    pop_df=self.population
                ),
                EMS: emissions_perception(
                    ghg_df=stage_metrics[EMS]
                ),
                REL: reliability_perception(
                    rel_df=stage_metrics[REL],
                    pop_df=self.population
                ),
                AFF: affordability_perception(
                    aff_df=stage_metrics[AFF],
                    lam=LAMBDA_AFF_PERC
                )
            }

        return result

def upload_teams_data(teams_dir: Path) -> dict[str, TeamData]:
    global wu_municipalities_map
    wu_municipalities_map = upload_wu_municipality_map(teams_dir=teams_dir)

    team_data_dict = {}
    
    for team_path in sorted(teams_dir.iterdir()):
        if not team_path.is_dir():
            continue
        
        team_id = team_path.name.split('-')[0]
        data = TeamData(
            reference=team_id == REFERENCE_TEAM
        )
        
        for stage in STAGES:
            stage_dir = team_path / f"{stage}"
            results_dir = stage_dir / f"bwf_results-{team_id}-stage_{stage}"
            
            if not results_dir.exists():
                data.complete = False
                break  # If a stage is missing, skip the rest for this team

            # Try appending this stage's metrics
            try:
                metrics_file = results_dir / "metrics.xlsx"
                df = pd.read_excel(
                    metrics_file,
                    sheet_name=METRICS,
                    index_col='timestamp',
                    parse_dates=True
                )
                data.metrics[stage] = df
                
            except Exception as e:
                print(f"Failed to read metrics.xlsx for {team_id} stage {stage}: {e}")
                break
                
            # Always update population to latest stage found
            try:
                population_file = results_dir / "jurisdictions" / "municipalities-dynamic_properties.xlsx"
                pop_df = pd.read_excel(
                    population_file,
                    sheet_name='population',
                    index_col='timestamp',
                    parse_dates=True
                )
                data.population = pop_df
                
            except Exception as e:
                print(f"Failed to read population file for {team_id} stage {stage}: {e}")
        
        if data.metrics:
            team_data_dict[team_id] = data

    return team_data_dict

def compute_rankings(
    team_data_dict: dict[str, TeamData]
) -> pd.DataFrame:
    # Collect all perceptions: rows=teams, columns=MultiIndex(metric, stage)
    all_perceptions = {
        team: pd.DataFrame(data.perceptions).stack()
        for team, data in team_data_dict.items()
        if data.complete and not data.reference
    }
    combined = pd.DataFrame(all_perceptions).T  # teams × (metric, stage)
    combined.columns.names = ["metric", "stage"]

    # Rank across teams for each (metric, stage) column
    ranks = pd.DataFrame(index=combined.index, columns=combined.columns, dtype=float)
    for metric in METRICS:
        mask = combined.columns.get_level_values("metric") == metric
        ranks.loc[:, mask] = combined.loc[:, mask].rank(
            axis=0,
            ascending=metric != REL,
            method="min"
        )

    return ranks

def plot_scatter_perceptions(
    team_data_dict: dict[str, TeamData]
) -> go.Figure:
    
    all_perceptions = {
        team: pd.DataFrame(data.perceptions).stack()
        for team, data in team_data_dict.items()
        if data.complete
    }
    combined = pd.DataFrame(all_perceptions).T  # teams × (metric, stage)
    combined.columns.names = ["metric", "stage"]

    TEAMS_SYMBOLS = [
        'circle',
        'square',
        'diamond',
        'cross',
        'x',
        'triangle-up',
        'triangle-down',
        'triangle-left',
        'triangle-right',
        'pentagon',
        'star',
        'hexagram'
    ]

    # Cache the bounds of ghg emissions to use that info as maker size
    ghg_full_df = combined.xs(EMS, axis=1, level="metric")
    min_ghg = float(ghg_full_df.min(axis=None))
    max_ghg = float(ghg_full_df.max(axis=None))
    MIN_MARKER_SIZE = 15
    MARKER_SIZE_SPAN = 10 

    # Similar with fairness to manage the color
    COLOR_SCALE = [[0, '#3059D1'], [0.25, '#3059D1'], [1, '#D63434']]
    aff_full_df = combined.xs(AFF, axis=1, level="metric")
    min_aff = float(aff_full_df.min(axis=None))*100
    max_aff = min(float(aff_full_df.max(axis=None)), 0.015)*100 # clip to account for the participant that messed up the policy

    fig = make_subplots(
        rows=1, cols=len(STAGES),
        subplot_titles=[f"Stage {s}" for s in STAGES],
        horizontal_spacing=0.05,
        vertical_spacing=0.1
    )

    for stage in STAGES:
        df = combined.xs(stage, axis=1, level="stage")

        norm_ems = (df[EMS] - min_ghg) / (max_ghg-min_ghg)
        sizes = (MARKER_SIZE_SPAN*norm_ems + MIN_MARKER_SIZE).astype(int) # marker size

        hover_text = (
            "Team: " + df.index.astype(str) +
            "<br>FIN: " + df[FIN].round(2).astype(str) + " €/person" +
            "<br>EMS: " + (df[EMS]/1e6).round().astype(str) + " ktCO2eq" +
            "<br>REL: " + (df[REL]*100).round(2).astype(str) + " %" +
            "<br>AFF: " + (df[AFF]*100).round(2).astype(str) + " %"
        )

        fig.add_trace(
            go.Scatter(
                x=df[FIN],
                y=df[REL]*100,
                mode='markers',
                showlegend=False,
                marker=dict(
                    symbol=TEAMS_SYMBOLS,
                    color=(df[AFF]*100).clip(lower=None, upper=max_aff),
                    colorscale=COLOR_SCALE,
                    cmin=min_aff,
                    cmax=max_aff,
                    colorbar=dict(
                        title='Affordability [%]',
                        len=0.5,
                        y=0.6,
                    ),
                    size=sizes,
                    showscale=True if stage == STAGES[-1] else False  # Show colorbar only once
                ),
                text=hover_text,
                hoverinfo='text'
            ),
            row=1, col=stage
        )

    # Add invisible markers for legend
    fig.add_trace(
        go.Scatter(
            x=[None], y=[None],
            mode='markers',
            name=f"Symbol: TEAM",
            marker=dict(
                symbol='star-square-open-dot',
                color='#3059D1',
                size=MIN_MARKER_SIZE
            ),
            showlegend=True
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None], y=[None],
            mode='markers',
            name=f"max GHG: {max_ghg/1e6:.1f} ktCO2eq",
            marker=dict(
                symbol='circle-open-dot',
                color='#3059D1',
                size=MIN_MARKER_SIZE + MARKER_SIZE_SPAN
            ),
            showlegend=True
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None], y=[None],
            mode='markers',
            name=f"min GHG: {min_ghg/1e6:.1f} ktCO2eq",
            marker=dict(
                symbol='circle-open-dot',
                color='#3059D1',
                size=MIN_MARKER_SIZE-5 # just artificially increase the difference
            ),
            showlegend=True
        )
    )

    fig.update_layout(
        height=800,
        width=1600,
        font=dict(size=20),
        showlegend=True,
        legend=dict(
            font=dict(size=20),
            title_font=dict(size=22),
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    axes_style=dict(
        ticks='outside',
        tickcolor='lightgray',
        tickwidth=1.5,
        showgrid=True,
        gridcolor='lightgray',
        gridwidth=1.2,
        zeroline=True,
        zerolinecolor='gray',
        zerolinewidth=2,
        title_font=dict(size=22),
        tickfont=dict(size=18),
    )

    fig.update_annotations(font=dict(size=26))

    XAXIS_TITLE = 'Average Debt per capita [€/person]'
    fig.update_xaxes(title_text=XAXIS_TITLE, **axes_style, range=[-50., 1050.], row=1, col=1)
    fig.update_xaxes(title_text=XAXIS_TITLE, **axes_style, row=1, col=2)
    fig.update_xaxes(title_text=XAXIS_TITLE, **axes_style, row=1, col=3)
    fig.update_yaxes(title_text='Weighted Worst Reliability [%]', **axes_style, range=[67,101], row=1, col=1)
    fig.update_yaxes(title_text='', **axes_style, range=[67,101], row=1, col=2)
    fig.update_yaxes(title_text='', **axes_style, range=[67,101], row=1, col=3)

    return fig

def compute_ahp_matrix(comparisons: dict[str, int]) -> pd.DataFrame:

    criteria_count: dict[str, int] = {}
    for c in comparisons:
        c1, c2 = c.split('-')

        # Allocate in case is not existing
        if c1 not in criteria_count:
            criteria_count[c1] = 0
        if c2 not in criteria_count:
            criteria_count[c2] = 0
        
        # Increase always, as we have allocated with 0
        criteria_count[c1] = criteria_count[c1] + 1
        criteria_count[c2] = criteria_count[c2] + 1

    ordered_criteria = [k for k, v in sorted(criteria_count.items(), key=lambda item: item[1])]

    mat:dict[str, dict[str, float]] = {}
    for i, c1 in enumerate(ordered_criteria):
        if c1 not in mat:
            mat[c1] = {}
        mat[c1][c1] = 1 # diagonal is 1 by definition

        for j in range(i+1, len(ordered_criteria)):
            c2 = ordered_criteria[j]

            opt1 = '-'.join([c1,c2])
            opt2 = '-'.join([c2,c1])
            if opt1 in comparisons:    
                mat[c1][c2] = comparisons[opt1]
            elif opt2 in comparisons:
                mat[c1][c2] = 1/comparisons[opt2]
            else:
                raise ValueError(f"Missing comparison between {c1} and {c2}")
            
    df = pd.DataFrame.from_dict(mat, orient='index')

    for i in df.index:
        for j in df.columns:
            if pd.isna(df.at[i, j]):
                assert pd.notna(df.at[j, i])
                df.at[i, j] = 1 / df.at[j, i]
            else: # isna the reciprocal
                assert pd.notna(df.at[i, j])
                df.at[j,i] = 1 / df.at[i, j]

    return df

RI = {2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24}  # Saaty random index

def compute_ahp_weights(matrix: pd.DataFrame) -> tuple[pd.Series, float]:
    A = matrix.values
    n = len(A)

    # normalise columns, average rows → weights
    col_sums = A.sum(axis=0)
    weights = (A / col_sums).mean(axis=1)

    # consistency ratio
    lam_max = (A @ weights / weights).mean()
    ci = (lam_max - n) / (n - 1)
    cr = ci / RI[n]

    return pd.Series(weights, index=matrix.index), cr

BWF_PRIORITIES = {
    1: {
        FIN+'-'+REL:1,
        FIN+'-'+EMS:5,
        FIN+'-'+AFF:7,
        REL+'-'+EMS:5,
        REL+'-'+AFF:7,
        EMS+'-'+AFF:3,
    },
    2: {
        FIN+'-'+REL:3,
        FIN+'-'+EMS:3,
        FIN+'-'+AFF:7,
        REL+'-'+EMS:1,
        REL+'-'+AFF:5,
        EMS+'-'+AFF:5,
    },
    3: {
        FIN+'-'+REL:1/3,
        FIN+'-'+EMS:5,
        FIN+'-'+AFF:1/3,
        REL+'-'+EMS:5,
        REL+'-'+AFF:1,
        EMS+'-'+AFF:1/5,
    }
} 

def main(teams_dir: Path) -> None:
    
    team_data_dict = upload_teams_data(teams_dir=teams_dir)

    n_teams_started = sum(1 for td in team_data_dict.values() if not td.reference)
    n_teams_completed = sum(1 for td in team_data_dict.values() if not td.reference and td.complete)

    print("----------------------")
    print("       BWF            ")
    print("")
    print(f"BWF-STATS:")
    print(f"Number of participants who started: {n_teams_started}")
    print(f"Number of participants who concluded: {n_teams_completed}")
    print("")
    print("Let's calculate the ranking!")
    print("")
    print("Results example for 'TEAM00':")
    print(pd.DataFrame(team_data_dict[REFERENCE_TEAM].perceptions))
    print("")
    rankings = compute_rankings(team_data_dict)
    print(rankings)

    plot_scatter_perceptions(team_data_dict).show()

    weights = {}
    for stage, priorities in BWF_PRIORITIES.items():
        
        ahp_matrix = compute_ahp_matrix(comparisons=priorities)

        stage_weights, stage_cr = compute_ahp_weights(ahp_matrix)

        print(f"Stage {stage}")
        print(stage_weights)

        print(rankings.xs(stage, axis=1, level='stage').mul(stage_weights).sum(axis=1))

        if stage_cr <= 0.1:
            weights[stage] = stage_weights
        else:
            raise ValueError(f"Consistency requirements is not less 0.1: {stage_cr}. Your pairwise judgements are contradicting each other and need revision.")
        
    weights_df = pd.DataFrame(weights)  # metrics × stages
    weights_df.index.name = "metric"
    weights_df.columns.name = "stage"

    print(weights_df)

    final_scores = rankings.mul(weights_df.stack()).sum(axis=1)

    print(final_scores.sort_values(ascending=True))
        

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