# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "water-futures-battle>=1.1.0",
# ]
# ///
"""Print the initial 2025 system table.

Requires LaTeX's booktabs and threeparttable packages and the document's
custom \\headrow command.

Run from the repository root::

    python bwf_competition_analysis/system_characteristics.py > system.tex

By default, load TEAM00's untouched Stage 1 inputs. Use --data-path to select
another initial dataset, and --configuration-filename for a nonstandard config.
No masterplan, hydraulic simulation, or asset ageing is applied.

Billable demand is generated with the evaluator's seeded demand model. Source
capacity is nominal daily capacity times 365. Network statistics cover installed
connection pipes only, not municipal distribution networks. Ages are measured
in model years and weighted by connection length.
Cross-utility links count once nationally and in both incident utilities.
"""

import argparse
from collections.abc import Iterable
from contextlib import redirect_stdout
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from water_futures_battle import configure_system
from water_futures_battle.connections.entities import Connection, PeerConnection
from water_futures_battle.core import Settings, get_snapshot
from water_futures_battle.jurisdictions.services import generate_water_demand
from water_futures_battle.national_context import NationalContext
from water_futures_battle.water_utilities.entities import WaterUtility


YEAR = 2025
DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "teams" / "TEAM00" / "1" / "bwf_inputs-TEAM00-stage_1"
)
ROWS = (
    ("Water utilities (--)", 0),
    ("Provinces (--)", 0),
    ("Municipalities (--)", 0),
    (r"Population served ($10^3$ inhab.)", 1),
    (r"Billable demand (hm$^3$/year)", 1),
    ("Active sources (--)", 0),
    ("Candidate sources (--)", 0),
    (r"Source capacity (hm$^3$/year)", 1),
    ("Active connections (--)", 0),
    ("Candidate connections (--)", 0),
    ("Network length (km)", 1),
    ("Mean network age (yr)", 1),
)


def summarize(
    utilities: Iterable[WaterUtility],
    connections: Iterable[Connection],
    billable_demands: dict[str, float],
) -> list[float]:
    """Aggregate physical entities, deduplicating shared infrastructure."""
    utilities = list(utilities)
    provinces = {p for u in utilities for p in u.provinces}
    municipalities = {m for u in utilities for m in u.active_municipalities(YEAR)}
    sources = {s for u in utilities for s in u.active_sources(YEAR)}
    candidate_sources = {s for u in utilities for s in u.sources} - sources
    existing = []
    candidates = 0
    for connection in sorted(connections, key=lambda c: c.bwf_id):
        if not connection.is_active(YEAR):
            continue
        pipe = connection.active_pipe(YEAR)
        if pipe is not None:
            existing.append((connection.distance, YEAR - pipe.installation_date.year))
        elif isinstance(connection, PeerConnection):
            candidates += 1

    length = sum(distance for distance, _ in existing)
    if not np.isfinite(length) or length <= 0:
        raise ValueError("Network statistics require a positive, finite installed length.")

    return [
        len(utilities),
        len(provinces),
        len(municipalities),
        sum(get_snapshot(m, YEAR).population for m in municipalities) / 1_000,
        sum(billable_demands[m.cbs_id] for m in municipalities) / 1_000_000,
        len(sources),
        len(candidate_sources),
        sum(s.nominal_capacity for s in sources) * 365 / 1_000_000,
        len(existing),
        candidates,
        length / 1_000,
        sum(distance * age for distance, age in existing) / length,
    ]


def compute_statistics(
    settings: Settings,
    context: NationalContext,
    utilities: set[WaterUtility],
) -> pd.DataFrame:
    """Calculate national values and the extrema of utility-level aggregates."""
    if settings.start_year != YEAR:
        raise ValueError(
            f"Expected initial Stage 1 inputs starting in {YEAR}; "
            f"this dataset starts in {settings.start_year}."
        )
    if not utilities:
        raise ValueError("The dataset contains no water utilities.")

    temperatures = context.average__maximum_temperature
    if not isinstance(temperatures.index, pd.DatetimeIndex):
        raise ValueError("Temperature data must use a DatetimeIndex.")
    temperature = float(temperatures.loc[temperatures.index.year == YEAR].max())
    if not np.isfinite(temperature):
        raise ValueError(f"No finite maximum-temperature data available for {YEAR}.")

    demands: dict[str, float] = {}
    for utility in sorted(utilities, key=lambda u: u.bwf_id):
        for municipality in sorted(
            utility.active_municipalities(YEAR), key=lambda m: m.cbs_id
        ):
            if municipality.cbs_id in demands:
                continue
            household, business = generate_water_demand(
                context.water_demand_model_data,
                municipality,
                YEAR,
                max_yearly_temperature=temperature,
                settings=settings,
            )
            demands[municipality.cbs_id] = float(np.sum(household + business))

    connections = {
        c for utility in utilities for c in utility.connections
    } | context.cross_utility_connections
    by_utility = []
    for utility in sorted(utilities, key=lambda u: u.bwf_id):
        incident = {
            c for c in context.cross_utility_connections
            if c.from_node.province in utility.provinces
            or c.to_node.province in utility.provinces
        }
        by_utility.append(summarize([utility], utility.connections | incident, demands))

    values = np.array(by_utility)
    table = pd.DataFrame(
        {
            "National": summarize(utilities, connections, demands),
            "Min": values.min(axis=0),
            "Max": values.max(axis=0),
        },
        index=[label for label, _ in ROWS],
    )
    if not np.isfinite(table.to_numpy()).all():
        raise ValueError("System characteristics contain missing or non-finite values.")
    return table


def render_latex(table: pd.DataFrame) -> str:
    """Render the requested table, with integer counts and one decimal otherwise."""
    lines = [
        r"\begin{table}[hbt!]",
        r"\begin{threeparttable}",
        r"\caption{Main characteristics of the hypothetical Dutch grid at the beginning of the BWF competition, both at the national level and across individual water utilities.}",
        r"\label{tbl:system_overview}",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"\headrow & \multicolumn{1}{c}{National} & \multicolumn{2}{c}{Water Utility} \\",
        r"\headrow & & Min & Max \\",
        r"\midrule",
    ]
    for i, (label, decimals) in enumerate(ROWS):
        cells = [
            f"{table.loc[label, column]:.{decimals}f}"
            for column in ("National", "Min", "Max")
        ]
        if i == 0:
            cells[1:] = ["--", "--"]
        if label in ("Active sources (--)", "Active connections (--)"):
            lines.append(r"\midrule")
        label = label.replace("Mean network age", r"Network age\tnote{a}")
        lines.append(label + " & " + " & ".join(cells) + r" \\")
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{tablenotes}[hang]",
        r"\item[a]Length-weighted mean age of the installed pipes.",
        r"\end{tablenotes}",
        r"\end{threeparttable}",
        r"\end{table}",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--configuration-filename", default="configuration.yaml")
    args = parser.parse_args()
    configuration = args.data_path / args.configuration_filename
    if not configuration.is_file():
        parser.error(f"Initial Stage 1 configuration not found: {configuration}")

    # Keep configuration progress out of the LaTeX stream.
    with redirect_stdout(sys.stderr):
        settings, context, utilities = configure_system(
            data_path=str(args.data_path),
            configuration_filename=args.configuration_filename,
        )
    print(render_latex(compute_statistics(settings, context, utilities)))


if __name__ == "__main__":
    main()
