# Python file containing helper and utility functions for the journal article's i
# mages generation.
# Initially based on `scripts/bwf_rank.py` and `visualization/presentation_plots.ipynb`

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Self

import pandas as pd

from water_futures_battle.masterplan import parse_masterplan, Masterplan
from water_futures_battle.national_context import NationalContext
from water_futures_battle.energy.entities import SolarFarm
from water_futures_battle.sources.entities import WaterSource
from water_futures_battle.pumping_stations.entities import PumpingStation
from water_futures_battle import configure_system

from survey_handling import upload_survey_responses, SurveyResponse

import warnings
warnings.filterwarnings(
    "ignore",
    message=r"Data Validation extension is not supported and will be removed",
    category=UserWarning,
)

FIN = 'financial_sustainability'
EMS = 'GHG_emissions'
REL = 'service_reliability'
AFF = 'affordability'

STAGES = [1, 2, 3]

COMPETITION_YEARS = list(range(2025, 2100))
ALL_YEARS = list(range(2000, 2100))  # historical + competition years
STAGE_SEPARATORS = [2025, 2050, 2075]

REFERENCE_TEAM = "TEAM00"

TEAMS_INFO_FILE = "authors_info.xlsx"

@dataclass
class AuthorInfo:
    team_id: str
    name: str
    surname: str
    affiliation: list[str]

    TEAM_ID = "Team ID"
    NAME = "Name"
    SURNAME = "Surname"
    AFFILIATIONS = "Affiliations"

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
        people_in_wu = pop_df.loc[last_year, TeamData.wu_municipalities_map[col]].sum(skipna=True)

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

BWF_OBJECTIVES = {
    FIN: debt_perception,
    EMS: emissions_perception,
    REL: reliability_perception,
    AFF: affordability_perception
}

# Value set for the affordability perception
LAMBDA_AFF_PERC = 0.0

@dataclass
class TeamData:
    team_id: str
    metrics: dict[int, dict[str, pd.DataFrame]] = field(default_factory=dict)
    complete: bool = True # start trusting it, as soon as we don't find a stage, reset
    reference: bool = False # only for TEAM00 or other references run
    final_rank: int = -1
    final_score: float = float('nan')
    label: str = ""

    # Shared data across all teams
    _all_authors: ClassVar[list[AuthorInfo]] = []
    _survey_responses: ClassVar[pd.DataFrame] = pd.DataFrame()
    population: ClassVar[pd.DataFrame] = pd.DataFrame()
    inflation: ClassVar[pd.Series] = pd.Series(dtype=float)
    wu_municipalities_map: ClassVar[dict[str, list[str]]] = {}
    
    _objectives: dict[int, dict[str, float]] | None = None

    def _compute_objectives(self) -> dict[int, dict[str, float]]:
        result = {}
        for stage, stage_metrics in self.metrics.items():
            result[stage] = {
                FIN: debt_perception(
                    debt_df=stage_metrics[FIN],
                    pop_df=TeamData.population
                ),
                EMS: emissions_perception(
                    ghg_df=stage_metrics[EMS]
                ),
                REL: reliability_perception(
                    rel_df=stage_metrics[REL],
                    pop_df=TeamData.population
                ),
                AFF: affordability_perception(
                    aff_df=stage_metrics[AFF],
                    lam=LAMBDA_AFF_PERC
                )
            }

        return result
    
    @property
    def objectives(self) -> dict[int, dict[str, float]]:

        if self._objectives is None:
            self._objectives = self._compute_objectives()

        return self._objectives
    
    _masterplan_filenames: dict[int, Path] | None = None
    _masterplans: dict[int, Masterplan] | None = None

    def masterplan_extension(self, stage: int) -> str:
        assert self._masterplan_filenames is not None
        return self._masterplan_filenames[stage].suffix
    
    def masterplan(self, stage: int) -> Masterplan:
        assert self._masterplan_filenames is not None

        if self._masterplans is None:
            self._masterplans = {}
        if stage not in self._masterplans.keys():
            self._masterplans[stage] = parse_masterplan(self._masterplan_filenames[stage])

        return self._masterplans[stage]
    
    def set_stage_masterplan(self, stage: int, filename: Path) -> Self:
        assert stage in STAGES
        if self._masterplan_filenames is None:
            self._masterplan_filenames = {}
        
        self._masterplan_filenames[stage] = filename
        return self
    
    @property
    def authors(self) -> list[AuthorInfo]:
        return [a for a in self._all_authors if a.team_id == self.team_id]
    
    @property
    def survey_response(self) -> SurveyResponse:
        if self.team_id in TeamData._survey_responses.index:
            return SurveyResponse(TeamData._survey_responses.loc[self.team_id])
        
        # fallback, empty because they didn't respond.
        return SurveyResponse({})
    
    @property
    def has_submitted_survey(self) -> bool:
        return self.team_id in TeamData._survey_responses.index

    _nc: NationalContext | None = None
    _solar_farms: frozenset[SolarFarm] | None = None

    @property
    def final_system(self) -> NationalContext:
        if self._nc is None:
            assert self._masterplan_filenames is not None
            # Reset solar farms and other class variables that otherwise would remain present
            WaterSource._global_solar_farms = {}
            PumpingStation._global_solar_farms = {}

            _, nc, _ = configure_system(
                data_path=str(self._masterplan_filenames[3].parent / f"bwf_results-{self.team_id}-stage_3")
            )

            self._nc = nc
            # Solar farms are tracked via containers that are ClassVars shared
            # across WaterSource/PumpingStation, so `nc.all_solar_farms` gets
            # silently overwritten as soon as another team's system is
            # configured. Snapshot it here, right after this team's system is
            # built, so `solar_farms` below stays correct for this team.
            self._solar_farms = frozenset(nc.all_solar_farms)

        return self._nc

    @property
    def solar_farms(self) -> frozenset[SolarFarm]:
        if self._solar_farms is None:
            self.final_system  # populates _solar_farms as a side effect
        assert self._solar_farms is not None
        return self._solar_farms

    _yearly_billable_demand: pd.DataFrame = field(default_factory=pd.DataFrame)
    _yearly_undelivered_demand: pd.DataFrame = field(default_factory=pd.DataFrame)
    _yearly_total_demand: pd.DataFrame = field(default_factory=pd.DataFrame)
    _idn_avg_age: pd.DataFrame = field(default_factory=pd.DataFrame)
    _nrw_mitigation_budget_spent: pd.DataFrame = field(default_factory=pd.DataFrame)
    _operations_ghg_emissions: pd.DataFrame = field(default_factory=pd.DataFrame)
    _embedded_ghg_emissions: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def yearly_billable_demand(self) -> pd.DataFrame:
        MUNI_DEMAND_BILLABLE_FILE = "municipalites-results-demand-billable.csv"
        assert self._masterplan_filenames is not None
        if len(self._yearly_billable_demand) == 0:            

            dfs = []
            for stage in STAGES:
                dfs.append(
                    pd.read_csv(
                        self._masterplan_filenames[stage].parent / f"bwf_results-{self.team_id}-stage_{stage}" / MUNI_DEMAND_BILLABLE_FILE,
                        index_col="timestamp",
                        parse_dates=True,
                    )
                )

            self._yearly_billable_demand = pd.concat(dfs, axis=0)

        return self._yearly_billable_demand

    @property
    def yearly_undelivered_demand(self) -> pd.DataFrame:
        MUNI_DEMAND_UNDELIVERED_FILE = "municipalites-results-demand-undelivered.csv"
        assert self._masterplan_filenames is not None
        if len(self._yearly_undelivered_demand) == 0:

            dfs = []
            for stage in STAGES:
                dfs.append(
                    pd.read_csv(
                        self._masterplan_filenames[stage].parent / f"bwf_results-{self.team_id}-stage_{stage}" / MUNI_DEMAND_UNDELIVERED_FILE,
                        index_col="timestamp",
                        parse_dates=True,
                    )
                )

            self._yearly_undelivered_demand = pd.concat(dfs, axis=0)

        return self._yearly_undelivered_demand

    @property
    def yearly_total_demand(self) -> pd.DataFrame:
        MUNI_DEMAND_TOTAL_GLOB = "municipalites-results-*-demand-total.csv"
        assert self._masterplan_filenames is not None
        if len(self._yearly_total_demand) == 0:

            totals = {}
            for stage in STAGES:
                results_dir = self._masterplan_filenames[stage].parent / f"bwf_results-{self.team_id}-stage_{stage}"
                for file in results_dir.glob(MUNI_DEMAND_TOTAL_GLOB):
                    df = pd.read_csv(file, index_col="timestamp", parse_dates=True)
                    totals[df.index[0]] = df.sum(axis=0, skipna=True)

            self._yearly_total_demand = pd.DataFrame.from_dict(totals, orient="index").sort_index()

        return self._yearly_total_demand

    @property
    def nrw_mitigation_budget_spent(self) -> pd.DataFrame:
        """
        Actual NRW mitigation budget spent per water utility per year, i.e.
        the result of the allocated budget (from the masterplan's
        'nrw_mitigation' policy) after execution.
        """
        WU_NRW_MITIGATION_BUDGET_FILE = "water_utilities-results-NRW_mitigation_budget.csv"
        assert self._masterplan_filenames is not None
        if len(self._nrw_mitigation_budget_spent) == 0:

            dfs = []
            for stage in STAGES:
                dfs.append(
                    pd.read_csv(
                        self._masterplan_filenames[stage].parent / f"bwf_results-{self.team_id}-stage_{stage}" / WU_NRW_MITIGATION_BUDGET_FILE,
                        index_col="timestamp",
                        parse_dates=True,
                    )
                )

            self._nrw_mitigation_budget_spent = pd.concat(dfs, axis=0)

        return self._nrw_mitigation_budget_spent

    @property
    def operations_ghg_emissions(self) -> pd.DataFrame:
        """
        Operational GHG emissions per water utility per year.
        """
        WU_OPERATIONS_GHG_FILE = "water_utilities-results-operations_ghg_emissions.csv"
        assert self._masterplan_filenames is not None
        if len(self._operations_ghg_emissions) == 0:

            dfs = []
            for stage in STAGES:
                dfs.append(
                    pd.read_csv(
                        self._masterplan_filenames[stage].parent / f"bwf_results-{self.team_id}-stage_{stage}" / WU_OPERATIONS_GHG_FILE,
                        index_col="timestamp",
                        parse_dates=True,
                    )
                )

            self._operations_ghg_emissions = pd.concat(dfs, axis=0)

        return self._operations_ghg_emissions

    @property
    def embedded_ghg_emissions(self) -> pd.DataFrame:
        """
        Embedded (embodied) GHG emissions per water utility per year.
        """
        WU_EMBEDDED_GHG_FILE = "water_utilities-results-ghg_embedded_emissions.csv"
        assert self._masterplan_filenames is not None
        if len(self._embedded_ghg_emissions) == 0:

            dfs = []
            for stage in STAGES:
                dfs.append(
                    pd.read_csv(
                        self._masterplan_filenames[stage].parent / f"bwf_results-{self.team_id}-stage_{stage}" / WU_EMBEDDED_GHG_FILE,
                        index_col="timestamp",
                        parse_dates=True,
                    )
                )

            self._embedded_ghg_emissions = pd.concat(dfs, axis=0)

        return self._embedded_ghg_emissions

    @property
    def idn_avg_age(self) -> pd.DataFrame:
        """
        Population-weighted-average distribution network age per municipality,
        read directly from the team's stage-3 results (final system), rather
        than from the live entities: those store their time series on a
        shared, mutable class-level attribute, so a value read from a cached
        NationalContext can silently become another team's data once that
        other team's system gets (re)configured.
        """
        MUNI_DYN_PROPS_FILE = "jurisdictions/municipalities-dynamic_properties.xlsx"
        DIST_NETWORK_AGE_SHEET = "dist_network-age-avg"
        stage = 3
        assert self._masterplan_filenames is not None
        if len(self._idn_avg_age) == 0:
            self._idn_avg_age = pd.read_excel(
                self._masterplan_filenames[stage].parent / f"bwf_results-{self.team_id}-stage_{stage}" / MUNI_DYN_PROPS_FILE,
                sheet_name=DIST_NETWORK_AGE_SHEET,
                index_col="timestamp",
                parse_dates=True,
            )

        return self._idn_avg_age

def upload_authors_info(teams_dir: Path) -> list[AuthorInfo]:
    """
    Load author/affiliation info, one row per team (teams_dir/authors_info.xlsx).
    """
    info_file = teams_dir / TEAMS_INFO_FILE

    if not info_file.exists():
        raise FileNotFoundError(f"Could not find teams info file at {info_file}.")

    df = pd.read_excel(info_file)
    
    return [
        AuthorInfo(
            team_id=str(row[AuthorInfo.TEAM_ID]),
            name=str(row[AuthorInfo.NAME]),
            surname=str(row[AuthorInfo.SURNAME]),
            affiliation=str(row[AuthorInfo.AFFILIATIONS]).split(';'),
        )
        for _, row in df.iterrows()
    ]

def upload_wu_municipality_map(teams_dir: Path) -> dict[str, list[str]]:
    """
    Create a map connecting each water utility (id) to a list of municipalities in it.
    Same as using the battle object and calling WaterUtility.municipalities
    """
    
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

def upload_reference_population(teams_dir: Path) -> pd.DataFrame:
    """
    Load the municipalities population from reference team stage-3 inputs (same for all teams)
    """
    stage = 3
    input_dir = teams_dir / REFERENCE_TEAM / f"{stage}" / f"bwf_inputs-{REFERENCE_TEAM}-stage_{stage}"
    population_file = input_dir / "jurisdictions" / f"municipalities-dynamic_properties-stage_{stage}.xlsx"

    if not population_file.exists():
        raise FileNotFoundError(
            f"Could not find stage-{stage} input population file for {REFERENCE_TEAM} in {teams_dir}."
        )

    return pd.read_excel(
        population_file,
        sheet_name='population',
        index_col='timestamp',
        parse_dates=True
    )

def upload_reference_inflation(teams_dir: Path) -> pd.Series:
    """
    Load national inflation from reference team stage-3 inputs (same for all teams)
    """
    stage = 3
    input_dir = teams_dir / REFERENCE_TEAM / f"{stage}" / f"bwf_inputs-{REFERENCE_TEAM}-stage_{stage}"
    inflation_file = input_dir / "economy" / f"economy-dynamic_properties-stage_{stage}.xlsx"

    if not inflation_file.exists():
        raise FileNotFoundError(
            f"Could not find stage-{stage} input inflation file for {REFERENCE_TEAM} in {teams_dir}."
        )

    inflation_df = pd.read_excel(
        inflation_file,
        sheet_name='inflation',
        index_col='timestamp',
        parse_dates=True
    )

    return inflation_df['NL0000']

def upload_desk_rejected(teams_dir: Path) -> set[str]:
    """
    Load the list of desk rejected team ids from a local, gitignored text file
    (teams_dir/desk_rejected), containing team ids separated by ';'.
    """
    desk_rejected_file = teams_dir / "desk_rejected"

    if not desk_rejected_file.exists():
        return set()

    content = desk_rejected_file.read_text().strip()

    if not content:
        return set()

    return {team_id.strip() for team_id in content.split(';') if team_id.strip()}

def upload_teams_data(teams_dir: Path) -> dict[str, TeamData]:
    TeamData._all_authors = upload_authors_info(teams_dir=teams_dir)
    TeamData._survey_responses = upload_survey_responses(teams_dir=teams_dir)
    TeamData.wu_municipalities_map = upload_wu_municipality_map(teams_dir=teams_dir)
    TeamData.population = upload_reference_population(teams_dir=teams_dir)
    TeamData.inflation = upload_reference_inflation(teams_dir=teams_dir)

    desk_rejected = upload_desk_rejected(teams_dir=teams_dir)

    team_data_dict = {}

    for team_path in sorted(teams_dir.iterdir()):
        if not team_path.is_dir():
            continue
        
        team_id = team_path.name.split('-')[0]

        if team_id in desk_rejected:
            continue

        data = TeamData(
            team_id=team_id,
            reference=team_id == REFERENCE_TEAM,
        )
        
        for stage in STAGES:
            stage_dir = team_path / f"{stage}"

            if not stage_dir.exists():
                data.complete = False
                break # If a stage is missing, skip the rest for this team

            # Extract the masterplan file and make sure it is the only one
            ms_files = [f for f in stage_dir.iterdir() if f.is_file() and str(f.stem).startswith('masterplan-')]
            assert len(ms_files) == 1, f"team {team_id} has more than 1 ms"
            data.set_stage_masterplan(stage=stage, filename=ms_files[0])

            results_dir = stage_dir / f"bwf_results-{team_id}-stage_{stage}"
            
            if not results_dir.exists():
                data.complete = False
                break  # If a stage is missing, skip the rest for this team

            # Try appending this stage's metrics
            try:
                metrics_file = results_dir / "metrics.xlsx"
                df = pd.read_excel(
                    metrics_file,
                    sheet_name=list(BWF_OBJECTIVES.keys()),
                    index_col='timestamp',
                    parse_dates=True
                )
                data.metrics[stage] = df
                
            except Exception as e:
                print(f"Failed to read metrics.xlsx for {team_id} stage {stage}: {e}")
                break
                
        if data.metrics:
            team_data_dict[team_id] = data

    rankings = compute_rankings(team_data_dict)

    weights = {}
    for stage, priorities in BWF_PRIORITIES.items():
        ahp_matrix = compute_ahp_matrix(comparisons=priorities)
        stage_weights, stage_cr = compute_ahp_weights(ahp_matrix)

        if stage_cr > 0.1:
            raise ValueError(f"Consistency requirements is not less 0.1: {stage_cr}. Your pairwise judgements are contradicting each other and need revision.")
        weights[stage] = stage_weights

    weights_df = pd.DataFrame(weights)  # metrics × stages
    weights_df.index.name = "metric"
    weights_df.columns.name = "stage"

    final_scores = rankings.mul(weights_df.stack()).sum(axis=1) / 3
    final_scores.sort_values(ascending=True, inplace=True)
    final_scores.index.name = "Team ID"
    final_scores.name = "AHP Score"
    final_scores = final_scores.to_frame()
    final_scores.insert(final_scores.shape[1], "Ranking", range(1, len(final_scores) + 1))

    for team_id, data in team_data_dict.items():
        if data.reference:
            continue

        if not data.complete:
            final_scores.loc[team_id] = [float('nan'), len(final_scores) + 1]

        team_rank = int(final_scores.at[team_id, "Ranking"])
        data.final_rank = team_rank
        data.final_score = float(final_scores.at[team_id, "AHP Score"])

        if team_rank < 5:  # We announced the first 4 teams
            data.label = team_id
        else:
            data.label = f"TR{team_rank:02d}"

    return team_data_dict

def compute_rankings(
    team_data_dict: dict[str, TeamData]
) -> pd.DataFrame:
    # Collect all perceptions: rows=teams, columns=MultiIndex(metric, stage)
    all_perceptions = {
        team: pd.DataFrame(data.objectives).stack()
        for team, data in team_data_dict.items()
        if data.complete and not data.reference
    }
    combined = pd.DataFrame(all_perceptions).T  # teams × (metric, stage)
    combined.columns.names = ["metric", "stage"]

    # Rank across teams for each (metric, stage) column
    ranks = pd.DataFrame(index=combined.index, columns=combined.columns, dtype=float)
    for metric in BWF_OBJECTIVES:
        mask = combined.columns.get_level_values("metric") == metric
        ranks.loc[:, mask] = combined.loc[:, mask].rank(
            axis=0,
            ascending=metric != REL,
            method="min"
        )

    return ranks

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

@dataclass
class MasterplanFormatCounter:
    yaml: int = 0
    json: int = 0
    xlsx: int = 0

    LABEL_YAML: ClassVar[str] = "YAML"
    LABEL_JSON: ClassVar[str] = "JSON"
    LABEL_XLSX: ClassVar[str] = "Excel (xlsx)"

    @property
    def total(self) -> int:
        return self.yaml + self.json + self.xlsx

    def keys(self) -> list[str]:
        return ["yaml", "json", "xlsx"]

    def values(self) -> list[int]:
        return [self.yaml, self.json, self.xlsx]

    def labels(self) -> list[str]:
        return [self.LABEL_YAML, self.LABEL_JSON, self.LABEL_XLSX]

@dataclass
class BudgetAllocationCounter:
    by_population: int = 0
    by_inverse_population: int = 0
    by_income: int = 0
    by_inverse_income: int = 0
    custom: int = 0

    LABEL_BY_POPULATION: ClassVar[str] = "By population"
    LABEL_BY_INVERSE_POPULATION: ClassVar[str] = "By inv. population"
    LABEL_BY_INCOME: ClassVar[str] = "By income"
    LABEL_BY_INVERSE_INCOME: ClassVar[str] = "By inv. income"
    LABEL_CUSTOM: ClassVar[str] = "Custom"

    @property
    def total(self) -> int:
        return (
            self.by_population +
            self.by_inverse_population +
            self.by_income +
            self.by_inverse_income +
            self.custom
        )

    def keys(self) -> list[str]:
        return ["by_population", "by_inverse_population", "by_income", "by_inverse_income", "custom"]

    def values(self) -> list[int]:
        return [self.by_population, self.by_inverse_population, self.by_income, self.by_inverse_income, self.custom]

    def labels(self) -> list[str]:
        return [
            self.LABEL_BY_POPULATION,
            self.LABEL_BY_INVERSE_POPULATION,
            self.LABEL_BY_INCOME,
            self.LABEL_BY_INVERSE_INCOME,
            self.LABEL_CUSTOM,
        ]

@dataclass
class NrwMitigationCounter:
    custom: int = 0
    by_population: int = 0
    by_nrw_class: int = 0

    LABEL_BY_POPULATION: ClassVar[str] = "By population"
    LABEL_BY_NRW_CLASS: ClassVar[str] = "By NRW class"
    LABEL_CUSTOM: ClassVar[str] = "Custom"

    @property
    def total(self) -> int:
        return self.by_population + self.by_nrw_class + self.custom

    def keys(self) -> list[str]:
        return ["by_population", "by_nrw_class", "custom"]

    def values(self) -> list[int]:
        return [self.by_population, self.by_nrw_class, self.custom]

    def labels(self) -> list[str]:
        return [self.LABEL_BY_POPULATION, self.LABEL_BY_NRW_CLASS, self.LABEL_CUSTOM]

@dataclass
class PricingAdjustmentCounter:
    custom: int = 0
    by_inflation: int = 0
    # Number of custom pricing components below inflation. Divide by 3 for policy-equivalent count.
    custom_components_below_inflation: int = 0

    LABEL_CUSTOM: ClassVar[str] = "Custom"
    LABEL_BY_INFLATION: ClassVar[str] = "By inflation"

    @property
    def total(self) -> int:
        return self.custom + self.by_inflation

    def keys(self) -> list[str]:
        return ["custom", "by_inflation"]

    def values(self) -> list[int]:
        return [self.custom, self.by_inflation]

    def labels(self) -> list[str]:
        return [self.LABEL_CUSTOM, self.LABEL_BY_INFLATION]

@dataclass
class PoliciesChoiceCounter:
    budget_allocation: BudgetAllocationCounter = field(default_factory=BudgetAllocationCounter)
    nrw_mitigation: NrwMitigationCounter = field(default_factory=NrwMitigationCounter)
    pricing_adjustment: PricingAdjustmentCounter = field(default_factory=PricingAdjustmentCounter)

@dataclass
class CompetitionStatistics:
    n_teams_started: int = 0
    n_teams_completed: int = 0
    masterplan_format_counter: MasterplanFormatCounter = field(default_factory=MasterplanFormatCounter)
    policies_counter: PoliciesChoiceCounter = field(default_factory=PoliciesChoiceCounter)
    inflation_series: list[float] = field(default_factory=list)
    price_adj_by_inflation: list[float] = field(default_factory=list)
    price_adj_custom: list[float] = field(default_factory=list)

def get_competition_statistics(team_data_dict: dict[str, TeamData]) -> CompetitionStatistics:
    stats = CompetitionStatistics(
        n_teams_started=sum(1 for td in team_data_dict.values() if not td.reference),
        n_teams_completed=sum(1 for td in team_data_dict.values() if not td.reference and td.complete),
    )

    for team_id, team_data in team_data_dict.items():
        if not team_data.complete or team_data.reference:
            continue

        for stage in STAGES:
            ms_ext = team_data.masterplan_extension(stage=stage)

            if ms_ext == '.yaml' or ms_ext == '.yml':
                stats.masterplan_format_counter.yaml += 1
            elif ms_ext == '.json':
                stats.masterplan_format_counter.json += 1
            elif ms_ext == '.xlsx':
                stats.masterplan_format_counter.xlsx += 1
            else:
                raise ValueError(f"Unkonwn file {ms_ext}")

            ms = team_data.masterplan(stage=stage)

            for year in range(2000 + 25*stage, 2025 + 25*stage):

                policies = ms.national_policies(year=year)
                inflation = float(team_data.inflation.at[pd.Timestamp(year=year, month=1, day=1)])
                prev_inflation = float(team_data.inflation.at[pd.Timestamp(year=year-1, month=1, day=1)])

                if policies['budget_allocation']['policy'] == 'custom':
                    stats.policies_counter.budget_allocation.custom += 1
                elif policies['budget_allocation']['policy'] == 'by_population':
                    stats.policies_counter.budget_allocation.by_population += 1
                elif policies['budget_allocation']['policy'] == 'by_inverse_population':
                    stats.policies_counter.budget_allocation.by_inverse_population += 1
                elif policies['budget_allocation']['policy'] == 'by_income':
                    stats.policies_counter.budget_allocation.by_income += 1
                elif policies['budget_allocation']['policy'] == 'by_inverse_income':
                    stats.policies_counter.budget_allocation.by_inverse_income += 1
                else:
                    raise ValueError(f"Uknown {policies['budget_allocation']['policy']}")

                for water_utility in [f"WU{x:02d}" for x in range(1, 11)]:
                    policies = ms.water_utility_policies(
                        water_utility=water_utility,
                        year=year
                    )

                    if policies['nrw_mitigation']['policy'] == 'custom':
                        stats.policies_counter.nrw_mitigation.custom += 1
                    elif policies['nrw_mitigation']['policy'] == 'by_population':
                        stats.policies_counter.nrw_mitigation.by_population += 1
                    elif policies['nrw_mitigation']['policy'] == 'by_nrw_class':
                        stats.policies_counter.nrw_mitigation.by_nrw_class += 1
                    else:
                        raise ValueError(f"Uknown {policies['nrw_mitigation']['policy']}")

                    # Let's track inflation and the water price increases
                    stats.inflation_series.append(inflation)

                    if policies['pricing_adjustment']['policy'] == 'custom':
                        stats.policies_counter.pricing_adjustment.custom += 1

                        fixed = policies['pricing_adjustment']['policy_args']['fixed_component']
                        variable = policies['pricing_adjustment']['policy_args']['variable_component']
                        selling_price = policies['pricing_adjustment']['policy_args']['selling_price']

                        if fixed < inflation/100:
                            stats.policies_counter.pricing_adjustment.custom_components_below_inflation += 1
                        if variable < inflation/100:
                            stats.policies_counter.pricing_adjustment.custom_components_below_inflation += 1
                        if selling_price < inflation/100:
                            stats.policies_counter.pricing_adjustment.custom_components_below_inflation += 1

                        stats.price_adj_by_inflation.append(float('nan'))
                        stats.price_adj_custom.append((fixed + variable + selling_price)/3*100)

                    elif policies['pricing_adjustment']['policy'] == 'by_inflation':
                        stats.policies_counter.pricing_adjustment.by_inflation += 1

                        stats.price_adj_custom.append(float('nan'))
                        stats.price_adj_by_inflation.append(prev_inflation)
                    else:
                        raise ValueError(f"Uknown {policies['pricing_adjustment']['policy']}")

    return stats