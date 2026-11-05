import itertools
from collections import Counter

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
from plotly.subplots import make_subplots
from scipy.stats import pearsonr
from water_futures_battle.nrw_model.enums import NRWClass
from water_futures_battle.sources.entities import GroundWater, SurfaceWater, Desalination
from water_futures_battle.pipes.dynamic_properties import PipeOptionsDB
from water_futures_battle.energy.dynamic_properties import EnergySysDB

from survey_handling import SurveyResponse, QUESTIONS, ChoiceQuestion, LikertQuestion, MultiChoiceQuestion, ScoreQuestion
from data_handling import (
    FIN,
    EMS,
    REL,
    AFF,
    STAGES,
    COMPETITION_YEARS,
    ALL_YEARS,
    STAGE_SEPARATORS,
    REFERENCE_TEAM,
    TeamData,
    MasterplanFormatCounter,
    PoliciesChoiceCounter,
)
from plotting_utils import *

def _participants(
        team_data_dict: dict[str, TeamData],
        rank=False,
    ) -> list[str]:
    """
    Returns participating teams (list of str) of all teams that presented a solution 
    at the conference and submitted the survey.
    """
    teams = [team for team, data in team_data_dict.items() if not data.reference and data.has_submitted_survey]
    if rank:
        teams.sort(key=lambda team: team_data_dict[team].final_rank)
    else:
        teams.sort()
    return teams

def _finishers(
        team_data_dict: dict[str, TeamData],
        rank=False,
    ) -> list[str]:
    """
    Returns teams (list of str) of all teams that competed (succefully submitted
    all 3 stages).
    Use rank to order them by rank instead of by name.
    """
    teams = [team for team, data in team_data_dict.items() if not data.reference and data.complete]

    if rank:
        teams.sort(key=lambda team: team_data_dict[team].final_rank)
    else:
        teams.sort()
    return teams

def _team_symbol_map(team_data_dict: dict[str, TeamData]) -> dict[str, str]:
    """
    Maps each competitor to a marker symbol, following the name order.
    """
    p = _participants(team_data_dict)
    m = dict(zip(p, TEAMS_SYMBOLS))
    m["TEAM00"] = TEAM00_SYMBOL
    return m

def _team_color_map(team_data_dict: dict[str, TeamData]) -> dict[str, str]:
    """
    Maps each complete team to a color, following the name order
    """
    p = _participants(team_data_dict)
    m = dict(zip(p, TEAMS_COLORS))
    m["TEAM00"] = TEAM00_COLORS
    return m

def _perceptions_values(
    team_data_dict: dict[str, TeamData],
    nominal_values: bool,
) -> dict[str, pd.Series]:
    """Collect perceptions, optionally deflating FIN at each stage's final year."""
    all_perceptions = {
        team: pd.DataFrame(data.objectives).stack()
        for team, data in team_data_dict.items()
        if data.complete
    }
    if not nominal_values and all_perceptions:
        price_index = _price_index_2024_base(team_data_dict[REFERENCE_TEAM].final_system)
        for stage, start_year in zip(STAGES, STAGE_SEPARATORS):
            factor = float(price_index.loc[start_year + 24]) / 100.0
            for values in all_perceptions.values():
                values.loc[(FIN, stage)] /= factor
    return all_perceptions

def plot_perceptions_scatter(
    team_data_dict: dict[str, TeamData],
    nominal_values: bool = True,
) -> go.Figure:
    """Plot perceptions; nominal_values=False deflates stage-end debt to 2024 euros.

    Uses TEAM00's cumulative inflation at 2049, 2074, and 2099.
    """
    all_perceptions = _perceptions_values(team_data_dict, nominal_values)
    cost_unit = "€/person" if nominal_values else "€<sub>2024</sub>/person"
    combined = pd.DataFrame(all_perceptions).T  # teams × (metric, stage)
    combined.columns.names = ["metric", "stage"]

    # Cache the bounds of ghg emissions to use that info as maker size
    ghg_full_df = combined.xs(EMS, axis=1, level="metric")
    min_ghg = float(ghg_full_df.min(axis=None))
    max_ghg = float(ghg_full_df.max(axis=None))
    MIN_MARKER_SIZE = 11
    MARKER_SIZE_SPAN = 14 

    # Similar with fairness to manage the color
    COLOR_SCALE = [[0, WF_BLUE], [0.25, WF_BLUE], [1, WF_RED]]
    aff_full_df = combined.xs(AFF, axis=1, level="metric")
    min_aff = float(aff_full_df.min(axis=None))*100
    max_aff = min(float(aff_full_df.max(axis=None)), 0.015)*100 # clip to account for the participant that messed up the policy

    # Get the marker to be consistent across plots
    symbols_map = _team_symbol_map(team_data_dict)
    symbols = [
        symbols_map[t]
        for t in all_perceptions
    ]

    fig = make_subplots(
        rows=1, cols=len(STAGES),
        subplot_titles=[f"Stage {s}" for s in STAGES],
        horizontal_spacing=0.05,
        vertical_spacing=0.1
    )

    for stage in STAGES:
        df = combined.xs(stage, axis=1, level="stage")

        colors = (df[AFF]*100).clip(lower=None, upper=max_aff)

        norm_ems = (df[EMS] - min_ghg) / (max_ghg-min_ghg)
        sizes = (MARKER_SIZE_SPAN*norm_ems + MIN_MARKER_SIZE).astype(int) # marker size

        hover_text = (
            df.index.astype(str) +
            "<br>FIN: " + df[FIN].round(2).astype(str) + f" {cost_unit}" +
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
                    symbol=symbols,
                    color=colors,
                    colorscale=COLOR_SCALE,
                    cmin=min_aff,
                    cmax=max_aff,
                    colorbar=dict(
                        title='Marker Color:<br>Affordability Distress<br> [%]',
                        len=0.6,
                        y=0.25,
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
            name="Team ID",
            legendgroup="symbol",
            legendgrouptitle_text="Marker Symbol:",
            marker=dict(
                symbol='star-square-open-dot',
                color=WF_BLUE,
                size=MIN_MARKER_SIZE + MARKER_SIZE_SPAN //2
            ),
            showlegend=True
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None], y=[None],
            mode='markers',
            name=f"{max_ghg/1e6:.1f}",
            legendgroup="size",
            legendgrouptitle_text="Marker Size:<br>GHG Emissions<br> [ktCO2eq]",
            marker=dict(
                symbol='circle-open-dot',
                color=WF_BLUE,
                size=MIN_MARKER_SIZE + MARKER_SIZE_SPAN
            ),
            showlegend=True
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None], y=[None],
            mode='markers',
            name=f"{min_ghg/1e6:.1f}",
            legendgroup="size",
            marker=dict(
                symbol='circle-open-dot',
                color=WF_BLUE,
                size=MIN_MARKER_SIZE
            ),
            showlegend=True
        )
    )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.6)
    fig.update_layout(
        showlegend=True,
        margin=dict(
            l=10,
            r=10,
            t=50,
            b=10,
            pad=0,
        ),
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
    )

    XAXIS_TITLE = f'Debt Burden<br>[{cost_unit}]'
    fig.update_xaxes(title=dict(text=XAXIS_TITLE, standoff=10), **axes_style, range=[-120., 1050.], row=1, col=1)
    fig.update_xaxes(title=dict(text=XAXIS_TITLE, standoff=10), **axes_style, row=1, col=2)
    fig.update_xaxes(title=dict(text=XAXIS_TITLE, standoff=10), **axes_style, row=1, col=3)
    fig.update_yaxes(title_text='Reliability Perception [%]', **axes_style, range=[67,101], row=1, col=1)
    fig.update_yaxes(title_text='', **axes_style, range=[67,101], row=1, col=2)
    fig.update_yaxes(title_text='', **axes_style, range=[67,101], row=1, col=3)

    return fig

def plot_perceptions_parallel(
        team_data_dict: dict[str, TeamData],
        nominal_values: bool = True,
) -> go.Figure:
    """Plot perceptions; nominal_values=False deflates stage-end debt to 2024 euros.

    Uses TEAM00's cumulative inflation at 2049, 2074, and 2099.
    """
    all_perceptions = _perceptions_values(team_data_dict, nominal_values)
    cost_unit = "€/person" if nominal_values else "€<sub>2024</sub>/person"
    fig = make_subplots(
        rows=1, cols=len(STAGES),
        subplot_titles=[f"Stage {stage}" for stage in STAGES],
        horizontal_spacing=0.08,
    )
    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.6)
    fig.update_annotations(yshift=20)
    if not all_perceptions:
        return fig

    combined = pd.DataFrame(all_perceptions).T
    combined.columns.names = ["metric", "stage"]
    symbols_map = _team_symbol_map(team_data_dict)
    metrics = [FIN, REL, EMS, AFF]
    units = [cost_unit, "%", "ktCO2eq", "%"]

    normalized = {}
    for metric, (lower, upper) in (
        (REL, (0.65, 1.0)),
        (EMS, (0, 3000e6)),
        (AFF, (0, 0.015))
    ):
        values = combined.xs(metric, axis=1, level="metric")
        if metric == AFF:
            values = values.clip(upper=0.015)
        span =  upper - lower
        normalized[metric] = (values - lower) / span if span else values * 0.0

    normalized[REL] = 1 - normalized[REL]

    costs = combined.xs(FIN, axis=1, level="metric")
    cost_min = min(0.0, float(np.nanmin(costs.to_numpy(dtype=float))))
    cost_max = 120e3 if nominal_values else 6e3 #max(0.0, float(np.nanmax(costs.to_numpy(dtype=float))))
    cost_span = cost_max - cost_min or 1.0
    cost_max = cost_min + cost_span
    x_range = [-0.2, 3.2]

    for col, stage in enumerate(STAGES, start=1):
        labels = [
            f"<i>J</i><sup>{index}</sup><sub>{stage},C</sub><br>[{unit}]"
            for index, unit in enumerate(units, start=1)
        ]
        for team in combined.index:
            raw_values = [combined.at[team, (metric, stage)] for metric in metrics]
            positions = [
                raw_values[0],
                cost_min + float(normalized[REL].at[team, stage]) * cost_span,
                cost_min + float(normalized[EMS].at[team, stage]) * cost_span,
                cost_min + float(normalized[AFF].at[team, stage]) * cost_span,
            ]
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(metrics))),
                    y=positions,
                    mode="lines+markers",
                    legendgroup=team,
                    showlegend=False,
                    cliponaxis=False,
                    line=dict(color=WF_BLUE, width=1),
                    marker=dict(symbol=symbols_map[team], color=WF_BLUE, size=7),
                    text=[
                        f"Debt Burden: {raw_values[0]:.2f} {cost_unit}",
                        f"Reliability: {raw_values[1] * 100:.2f} %",
                        f"GHG Emissions: {raw_values[2] / 1e6:.2f} ktCO2eq",
                        f"Affordability: {raw_values[3] * 100:.2f} %",
                    ],
                    hovertemplate="%{text}<extra></extra>",
                ),
                row=1, col=col,
            )

        suffix = '' if col == 1 else str(col)
        domain = fig.layout.to_plotly_json()[f"xaxis{suffix}"]["domain"]
        fig.update_xaxes(
            range=x_range, tickmode="array", tickvals=list(range(len(metrics))),
            ticktext=labels, tickangle=0, showgrid=False, zeroline=False,
            ticklabelstandoff=10,
            row=1, col=col,
        )
        fig.update_yaxes(
            range=[cost_min, cost_max], showgrid=False, zeroline=False,
            anchor="free",
            position=domain[0] + (0 - x_range[0]) / (x_range[1] - x_range[0]) * (domain[1] - domain[0]),
            tickmode="array", tickvals=[0, 40e3, 80e3, 120e3] if nominal_values else [0, 2e3, 4e3, 6e3],
            showline=True, linecolor="lightgray", ticks="outside", nticks=5,
            row=1, col=col,
        )
        for dimension, axis_range, tickvals in (
            (1, [100, 64], [64, 76, 88, 100]),
            (2, [0, 3000], [0, 1000, 2000, 3000]),
            (3, [0, 1.5], [0, 0.5, 1, 1.5]),
        ):
            axis_number = len(STAGES) + (col - 1) * 3 + dimension
            fig.update_layout({
                f"yaxis{axis_number}": dict(
                    overlaying=f"y{suffix}", anchor="free",
                    position=domain[0] + (dimension - x_range[0]) / (x_range[1] - x_range[0]) * (domain[1] - domain[0]),
                    range=axis_range, tickmode="array", tickvals=tickvals,
                    showgrid=False, zeroline=False, showline=True,
                    linecolor="lightgray", ticks="outside", tickfont=font('tick'),
                )
            })
            fig.add_trace(go.Scatter(
                x=[dimension], y=[None],
                xaxis=f"x{suffix}", yaxis=f"y{axis_number}",
                showlegend=False, hoverinfo="skip",
            ))

        if col == 1:
            fig.add_annotation(
                x=0, y=0.0,
                ax=0, ay=-35,
                xref="paper", yref="paper", axref="pixel", ayref="pixel",
                xshift=-18,
                text="Preferred<br>direction", showarrow=True,
                arrowhead=2, arrowsize=1, arrowwidth=1.5,
            )

    # Explain the symbol encoding without identifying individual competitors.
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="markers",
        name="Team",
        marker=dict(symbol="star-square-open-dot", color=WF_BLUE, size=10),
        showlegend=True,
        hoverinfo="skip",
    ))
    fig.update_layout(
        showlegend=True,
        legend=dict(
            title=dict(text="Marker Symbol:", font=font('legend_title')),
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.15, yanchor="top",
            font=font('legend'),
        ),
        margin=dict(l=50, r=10, t=50, b=50, pad=0),
    )
    return fig

def plot_perceptions_radar(
        team_data_dict: dict[str, TeamData],
        nominal_values: bool = True,
) -> go.Figure:
    """Plot perceptions; nominal_values=False deflates stage-end debt to 2024 euros.

    Uses TEAM00's cumulative inflation at 2049, 2074, and 2099.
    """
    all_perceptions = _perceptions_values(team_data_dict, nominal_values)
    cost_unit = "€/person" if nominal_values else "€<sub>2024</sub>/person"
    fig = make_subplots(
        rows=1, cols=len(STAGES),
        specs=[[{"type": "polar"} for stage in STAGES]],
        subplot_titles=[f"Stage {stage}" for stage in STAGES],
        horizontal_spacing=0.0,
    )
    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.5)
    fig.update_layout(margin=dict(l=45, r=45, t=70, b=100, pad=0))
    label_standoff = 24
    plot_width = fig.layout.to_plotly_json()["width"] - 45 - 45
    plot_height = fig.layout.to_plotly_json()["height"] - 70 - 100
    for col, title in enumerate(fig.layout.annotations, start=1):
        y_domain = [0.0, 0.84] if col == 2 else [0.12, 1.0]
        fig.update_polars(domain_y=y_domain, row=1, col=col)
        title.update(y=1.0, yshift=20)
    fig.update_polars(
        gridshape="linear",
        bgcolor="white",
        radialaxis=dict(
            range=[0, 1.0], tickmode="array", tickvals=[0, 0.5, 1],
            showticklabels=False,
            tickfont=font('tick'), angle=45,
            gridcolor="lightgray", showline=False,
        ),
        angularaxis=dict(
            rotation=90, direction="clockwise", tickangle=0,
            showticklabels=False,
            tickfont=font('tick'), gridcolor="lightgray", linecolor="lightgray",
            categoryorder="array",
        ),
    )
    if not all_perceptions:
        return fig

    combined = pd.DataFrame(all_perceptions).T
    combined.columns.names = ["metric", "stage"]
    symbols_map = _team_symbol_map(team_data_dict)
    metrics = [FIN, REL, EMS, AFF]
    units = [cost_unit, "%", "ktCO2eq", "%"]
    costs = combined.xs(FIN, axis=1, level="metric")
    cost_min = min(0.0, float(np.nanmin(costs.to_numpy(dtype=float))))
    cost_max = 120e3 if nominal_values else 6e3
    bounds = {
        FIN: (cost_min, cost_max),
        REL: (0.64, 1.0),
        EMS: (0, 3000e6),
        AFF: (0, 0.015),
    }
    spoke_ticks = [
        [0, 60e3, 120e3] if nominal_values else [0, 3e3, 6e3],
        [64, 82, 100],
        [0, 1500, 3000],
        [0, 0.75, 1.5],
    ]
    unit_factors = [1, 100, 1e-6, 100]
    tick_positions = ["top right", "bottom right", "bottom left", "top left"]
    normalized = {}
    for metric, (lower, upper) in bounds.items():
        values = combined.xs(metric, axis=1, level="metric")
        if metric == AFF:
            values = values.clip(upper=0.015)
        normalized[metric] = (values - lower) / (upper - lower)
        if metric != REL:
            normalized[metric] = 1 - normalized[metric]

    for col, stage in enumerate(STAGES, start=1):
        labels = [
            f"<i>J</i><sup>{index}</sup><sub>{stage},C</sub><br>[{unit}]"
            for index, unit in enumerate(units, start=1)
        ]
        fig.update_polars(angularaxis_categoryarray=labels, row=1, col=col)
        polar_name = "polar" if col == 1 else f"polar{col}"
        domain = fig.layout.to_plotly_json()[polar_name]["domain"]
        center_x = sum(domain["x"]) / 2
        center_y = sum(domain["y"]) / 2
        radius = min(
            (domain["x"][1] - domain["x"][0]) * plot_width,
            (domain["y"][1] - domain["y"][0]) * plot_height,
        ) / 2
        for label, (direction_x, direction_y, xanchor, yanchor) in zip(labels, (
            (0, 0.9, "center", "bottom"),
            (0.8, 0.1, "left", "bottom") if col != 2 else (0.8, -0.075, "left", "top"),
            (0, -0.9, "center", "top"),
            (-0.8, -0.075, "right", "top") if col != 3 else (-0.8, 0.1, "right", "bottom"),
        )):
            fig.add_annotation(
                xref="paper", yref="paper",
                x=center_x + direction_x * (radius + label_standoff) / plot_width,
                y=center_y + direction_y * (radius + label_standoff) / plot_height,
                text=label, textangle=0, showarrow=False,
                xanchor=xanchor, yanchor=yanchor, font=font('tick'),
            )
        for team in combined.index:
            raw_values = [combined.at[team, (metric, stage)] for metric in metrics]
            radii = [float(normalized[metric].at[team, stage]) for metric in metrics]
            hover_text = [
                f"Debt Burden: {raw_values[0]:.2f} {cost_unit}",
                f"Reliability: {raw_values[1] * 100:.2f} %",
                f"GHG Emissions: {raw_values[2] / 1e6:.2f} ktCO2eq",
                f"Affordability: {raw_values[3] * 100:.2f} %",
            ]
            fig.add_trace(
                go.Scatterpolar(
                    theta=labels + labels[:1],
                    r=radii + radii[:1],
                    mode="lines+markers",
                    legendgroup=team, showlegend=False,
                    line=dict(color=WF_BLUE, width=1),
                    marker=dict(symbol=symbols_map[team], color=WF_BLUE, size=7),
                    text=hover_text + hover_text[:1],
                    hovertemplate="%{text}<extra></extra>",
                ),
                row=1, col=col,
            )

        for metric, label, ticks, factor, text_position in zip(
            metrics, labels, spoke_ticks, unit_factors, tick_positions
        ):
            lower, upper = bounds[metric]
            tick_radii = [(tick / factor - lower) / (upper - lower) for tick in ticks]
            if metric != REL:
                tick_radii = [1 - radius for radius in tick_radii]
            fig.add_trace(go.Scatterpolar(
                theta=[label] * len(ticks), r=tick_radii,
                mode="text", text=[
                    f"{tick / 1000:g}k" if metric == FIN and tick >= 1000 else f"{tick:g}"
                    for tick in ticks
                ],
                textposition=text_position, textfont=font('tick'),
                showlegend=False, hoverinfo="skip",
            ), row=1, col=col)

    fig.add_trace(go.Scatterpolar(
        theta=[None], r=[None], mode="markers",
        name="Team", showlegend=True, hoverinfo="skip",
        marker=dict(symbol="star-square-open-dot", color=WF_BLUE, size=10),
    ), row=1, col=1)
    fig.update_layout(
        showlegend=True,
        legend=dict(
            title=dict(text="Marker Symbol:", font=font('legend_title')),
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.15, yanchor="top",
            font=font('legend'),
        ),
        margin=dict(l=45, r=45, t=70, b=100, pad=0),
    )
    return fig

def plot_masterplan_format_count(
        counter: MasterplanFormatCounter,
        presentation_mode: bool = False,
    ) -> go.Figure:
    labels = counter.labels()
    values = counter.values()
    colors = [WF_ORANGE, WF_BLUE, WF_GREEN]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.6,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                sort=False,
                texttemplate="%{label}<br>%{value} (%{percent})",
                textposition="outside",
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            )
        ]
    )

    fig = apply_journal_formatting(fig=fig, column='single', frac=0.75, ratio=1.2)
    fig.update_layout(
        title="Masterplan Submission Format" if presentation_mode else "",
        showlegend=False,
        margin=dict(
            l=10,
            r=10,
            t=60 if presentation_mode else 10,
            b=10,
            pad=0,
        ),
    )

    return fig

def plot_policy_type_usage_bar(
        counter: PoliciesChoiceCounter,
        presentation_mode: bool = False,
    ) -> go.Figure:
    def _format_labels(values: list[int], total: int) -> list[str]:
        if total <= 0:
            return [f"{v} (0%)" for v in values]
        return [f"{v} ({(100 * v / total):.1f}%)" for v in values]

    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=[
            "Budget Allocation",
            "NRW Mitigation",
            "Pricing Adjustment",
        ] if presentation_mode else None,
        horizontal_spacing=0.08,
    )

    ba_values = counter.budget_allocation.values()
    ba_text = _format_labels(ba_values, counter.budget_allocation.total)
    fig.add_trace(
        go.Bar(
            x=counter.budget_allocation.labels(),
            y=ba_values,
            marker_color=[WF_BLUE, WF_BLUE, WF_BLUE, WF_BLUE, WF_GREY],
            marker_line_color=[WF_BLUE, WF_BLUE, WF_BLUE, WF_BLUE, WF_BLUE],
            marker_line_width=[0, 0, 0, 0, 2],
            text=ba_text,
            textposition="outside",
            hovertemplate="%{x}: %{y}<extra></extra>",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    nrw_values = counter.nrw_mitigation.values()
    nrw_text = _format_labels(nrw_values, counter.nrw_mitigation.total)
    fig.add_trace(
        go.Bar(
            x=counter.nrw_mitigation.labels(),
            y=nrw_values,
            marker_color=[WF_GREEN, WF_GREEN, WF_GREY],
            marker_line_color=[WF_GREEN, WF_GREEN, WF_GREEN],
            marker_line_width=[0, 0, 2],
            text=nrw_text,
            textposition="outside",
            hovertemplate="%{x}: %{y}<extra></extra>",
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    custom_total = counter.pricing_adjustment.custom
    custom_below = counter.pricing_adjustment.custom_components_below_inflation//3
    custom_above = max(custom_total - custom_below, 0)
    pricing_total = counter.pricing_adjustment.total

    fig.add_trace(
        go.Bar(
            x=[counter.pricing_adjustment.LABEL_BY_INFLATION],
            y=[counter.pricing_adjustment.by_inflation],
            marker_color=WF_ORANGE,
            text=_format_labels([counter.pricing_adjustment.by_inflation], pricing_total),
            textposition="outside",
            hovertemplate="%{x}: %{y}<extra></extra>",
            showlegend=False,
        ),
        row=1,
        col=3,
    )

    fig.add_trace(
        go.Bar(
            x=[counter.pricing_adjustment.LABEL_CUSTOM],
            y=[custom_below],
            marker_color=WF_GREY,
            marker_line_color=WF_ORANGE,
            marker_line_width=2,
            marker_pattern_shape="/",
            marker_pattern_fgcolor=WF_ORANGE,
            text=_format_labels([custom_below], pricing_total),
            textposition="outside",
            hovertemplate="%{x}: %{y}<extra></extra>",
            name="Below inflation",
            showlegend=True,
        ),
        row=1,
        col=3,
    )
    
    fig.add_trace(
        go.Bar(
            x=[counter.pricing_adjustment.LABEL_CUSTOM],
            y=[custom_above],
            marker_color=WF_GREY,
            marker_line_color=WF_ORANGE,
            marker_line_width=2,
            text=_format_labels([custom_above], pricing_total),
            textposition="outside",
            hovertemplate="%{x}: %{y}<extra></extra>",
            name="Above inflation",
            showlegend=True,
        ),
        row=1,
        col=3,
    )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="Policy Type Usage" if presentation_mode else "",
        barmode="stack",
    )
    if not presentation_mode:
        SUBPLOT_TITLES = ['(a)', '(b)', '(c)']
        for i, label in enumerate(SUBPLOT_TITLES):
            suffix = '' if i == 0 else str(i + 1)  # '', '2' matches Plotly's axis naming
            fig.add_annotation(
                xref=f'x{suffix} domain',
                yref=f'y{suffix} domain',
                x=0, y=1.01,           # x=0 → left edge; y=1.05 → just above the plot
                text=label,
                showarrow=False,
                font=font('legend_title'),
                xanchor='left',
                yanchor='bottom'
            )

    fig.update_xaxes(
        tickangle=-30,
        categoryorder="array",
        categoryarray=["by_population", "by_inverse_population", "by_income", "by_inverse_income", "custom"],
        row=1,
        col=1,
    )
    fig.update_xaxes(
        tickangle=-30,
        categoryorder="array",
        categoryarray=["by_population", "by_nrw_class", "custom"],
        row=1,
        col=2,
    )
    fig.update_xaxes(
        tickangle=-30,
        categoryorder="array",
        categoryarray=["by_inflation", "custom"],
        row=1,
        col=3,
    )
    fig.update_yaxes(title_text="Count", rangemode="tozero", row=1, col=1)
    fig.update_yaxes(title_text="", rangemode="tozero", row=1, col=2)
    fig.update_yaxes(title_text="", rangemode="tozero", row=1, col=3)

    fig.update_layout(
        legend=dict(
            x=1,
            y=0.8,
            xanchor='center',
            yanchor='bottom',
            bgcolor="rgba(255,255,255,0.75)",
            bordercolor="lightgray",
            borderwidth=1,
        ),
        margin=dict(
            l=10,
            r=10,
            t=60 if presentation_mode else 30,
            b=10,
            pad=0,
        ),
    )

    return fig

def plot_policy_type_usage_pie(counter: PoliciesChoiceCounter) -> go.Figure:
    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=[
            "Budget Allocation",
            "NRW Mitigation",
            "Pricing Adjustment",
        ],
        specs=[[{"type": "pie"}, {"type": "pie"}, {"type": "pie"}]],
        horizontal_spacing=0.08,
    )

    fig.add_trace(
        go.Pie(
            labels=counter.budget_allocation.labels(),
            values=counter.budget_allocation.values(),
            hole=0.6,
            marker=dict(colors=[WF_BLUE, WF_GREEN, WF_BLUE, WF_GREEN, WF_GREY]),
            texttemplate="%{label}:<br>%{value} (%{percent})",
            textposition="outside",
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            sort=False,
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Pie(
            labels=counter.nrw_mitigation.labels(),
            values=counter.nrw_mitigation.values(),
            hole=0.6,
            marker=dict(colors=[WF_BLUE, WF_GREEN, WF_GREY]),
            texttemplate="%{label}:<br>%{value} (%{percent}))",
            textposition="outside",
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            sort=False,
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    custom_total = counter.pricing_adjustment.custom
    custom_below = counter.pricing_adjustment.custom_components_below_inflation//3
    custom_above = max(custom_total - custom_below, 0)

    pricing_labels = ["By inflation", "Custom (below inflation)", "Custom (above inflation)"]
    pricing_values = [counter.pricing_adjustment.by_inflation, custom_below, custom_above]
    fig.add_trace(
        go.Pie(
            labels=pricing_labels,
            values=pricing_values,
            hole=0.6,
            marker=dict(colors=[WF_ORANGE, WF_GREY, WF_GREEN]),
            texttemplate="%{label}<br>%{value} (%{percent})",
            textposition="outside",
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            sort=False,
            showlegend=False,
        ),
        row=1,
        col=3,
    )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="Policy Type Usage",
        margin=dict(
            l=10,
            r=10,
            t=60,
            b=10,
            pad=0,
        ),
    )

    return fig

def plot_pricing_adj_vs_inflation_scatter(
    inflation: list[float],
    price_adj_by_inflation: list[float],
    price_adj_custom: list[float],
) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=inflation,
            y=price_adj_custom,
            mode="markers",
            name="Custom",
            marker=dict(color=WF_GREEN, size=6),
            hovertemplate="Inflation: %{x:.2f}<br>Custom: %{y:.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=inflation,
            y=price_adj_by_inflation,
            mode="markers",
            name="By inflation",
            marker=dict(color=WF_BLUE, size=6),
            hovertemplate="Inflation: %{x:.2f}<br>By inflation: %{y:.2f}<extra></extra>",
        )
    )

    # Add the 1:1 reference line.
    all_values = inflation + price_adj_by_inflation + price_adj_custom
    min_v = min(all_values)
    max_v = max(all_values)

    fig.add_trace(
        go.Scatter(
            x=[min_v, max_v],
            y=[min_v, max_v],
            mode="lines",
            name="1:1 reference",
            line=dict(color=WF_GREY, width=2, dash="dash"),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Prepare the correlation between time series to add as annotation.
    shape = (-1, 75, 10)  # team, year, wu
    infl = np.reshape(inflation, shape)[0, :, 0]
    hybrid = np.where(np.isnan(np.reshape(price_adj_by_inflation, shape)),
                    np.reshape(price_adj_custom, shape),
                    np.reshape(price_adj_by_inflation, shape))

    r_ref = pearsonr(infl[:-1], infl[1:])[0]
    r_team = [np.nanmedian([pearsonr(hybrid[t, :, w], infl)[0] for w in range(10)])
            for t in range(11)]

    fig = apply_journal_formatting(fig=fig, column='single', frac=0.9, ratio=1)
    fig.update_layout(
        title="", #"Water Pricing Adjustment Value vs Inflation",
        xaxis_title="Inflation [%]",
        yaxis_title="Pricing adjustment [%]",
        showlegend=True,
        legend=dict(
            title_text="Water Pricing Adj. Policy",
            x = 0.02,
            y = 1,
            xanchor='left',
            yanchor='top',
            bgcolor="rgba(255,255,255,0.75)",
            bordercolor="lightgray",
            borderwidth=1,
        ),
        annotations=[
            dict(
                x=11,
                y=11,
                text="1:1 reference",
                showarrow=False,
                textangle=-45,
                xanchor="right",
                yanchor="middle",
                font=dict(color=WF_GREY, **font('annotation')),
            ),
            dict(
                x=7,xanchor="left",
                y=7,yanchor="top",
                text=(
                    f"<b>r (by inflation)</b> = {r_ref:.2f}<br>"
                    f"<b>r (teams)</b> = {np.median(r_team):.2f}<br>"
                    f"  range: {min(r_team):.2f} to {max(r_team):.2f}"
                ),
                showarrow=False,
                align="left",
                font=dict(color=WF_NAVY, **font('annotation')),
            ),
        ],
        margin=dict(
            l=5,
            r=5,
            t=20,
            b=5,
            pad=0,
        ),
    )

    fig.update_xaxes(range=[0, 12])
    fig.update_yaxes(range=[0, 12])

    return fig

def plot_cost_to_price_ratio_lines(
    inflation: list[float],
    price_adj_by_inflation: list[float],
    price_adj_custom: list[float],
    ghost: bool = False,
    team_data_dict: dict[str, TeamData] | None = None,
) -> go.Figure:
    """Plot cumulative cost/price growth relative to 2024 (ratio = 1).

    Inputs are percentages flattened in team, year (2025-2099), utility
    (WU01-WU10) order, as returned by get_competition_statistics. If supplied,
    team_data_dict must be the mapping used to produce those statistics.
    Otherwise teams are numbered in input order.

    Normal mode shows each utility and its team's median in the team's
    color/marker. Ghost mode shows anonymous team medians and their
    cross-team median, without markers.
    """
    n_years = len(COMPETITION_YEARS)
    n_utilities = 10
    if not (
        len(inflation) == len(price_adj_by_inflation) == len(price_adj_custom)
        and len(inflation) > 0
        and len(inflation) % (n_years * n_utilities) == 0
    ):
        raise ValueError(
            "Inputs must have equal, nonzero lengths with 75 years and "
            "10 water utilities per team."
        )

    shape = (-1, n_years, n_utilities)
    infl = np.reshape(inflation, shape)[0, :, 0] / 100
    by_inflation = np.reshape(price_adj_by_inflation, shape)
    custom = np.reshape(price_adj_custom, shape)
    hybrid = np.where(np.isnan(by_inflation), custom, by_inflation) / 100
    ratio = np.cumprod((1 + infl)[None, :, None] / (1 + hybrid), axis=1)
    ratio = np.concatenate([np.ones((hybrid.shape[0], 1, n_utilities)), ratio], axis=1)
    team_medians = np.median(ratio, axis=2)
    years = [COMPETITION_YEARS[0] - 1, *COMPETITION_YEARS]

    if team_data_dict is None:
        teams = [f"Team {i + 1}" for i in range(ratio.shape[0])]
        color_map = {team: TEAMS_COLORS[i % len(TEAMS_COLORS)] for i, team in enumerate(teams)}
        symbol_map = {team: TEAMS_SYMBOLS[i % len(TEAMS_SYMBOLS)] for i, team in enumerate(teams)}
    else:
        teams = [
            team for team, data in team_data_dict.items()
            if data.complete and not data.reference
        ]
        if len(teams) != ratio.shape[0]:
            raise ValueError("Team data must match the number of teams in the input series.")
        color_map = _team_color_map(team_data_dict)
        symbol_map = _team_symbol_map(team_data_dict)

    fig = go.Figure()
    for i, team in enumerate(teams):
        if ghost:
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=team_medians[i],
                    mode="lines",
                    name="Individual Teams" if i == 0 else None,
                    showlegend=i == 0,
                    line=dict(color=make_opaque(WF_BLUE, 0.25), width=1),
                    hoverinfo="skip",
                )
            )
        else:
            for wu in range(n_utilities):
                fig.add_trace(
                    go.Scatter(
                        x=years,
                        y=ratio[i, :, wu],
                        mode="lines+markers",
                        name=f"{team} WU{wu + 1:02d}",
                        legendgroup=team,
                        showlegend=False,
                        line=dict(color=color_map[team], width=1),
                        marker=dict(color=color_map[team], symbol=symbol_map[team], size=3),
                        hovertemplate=(
                            f"Team: {team}<br>Utility: WU{wu + 1:02d}<br>"
                            "Year: %{x}<br>Cost/price ratio: %{y:.3f}<extra></extra>"
                        ),
                    )
                )
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=team_medians[i],
                    mode="lines+markers",
                    name=team,
                    legendgroup=team,
                    line=dict(color=color_map[team], width=3),
                    marker=dict(color=color_map[team], symbol=symbol_map[team], size=7),
                    hovertemplate=(
                        f"Team: {team}<br>Year: %{{x}}<br>"
                        "Median cost/price ratio: %{y:.3f}<extra></extra>"
                    ),
                )
            )

    if ghost:
        fig.add_trace(
            go.Scatter(
                x=years,
                y=np.median(team_medians, axis=0),
                mode="lines",
                name="Median",
                line=dict(color=WF_BLUE, width=3),
                hovertemplate=(
                    "Year: %{x}<br>Median cost/price ratio: %{y:.3f}<extra></extra>"
                ),
            )
        )

    fig.add_hline(y=1, line=dict(color=WF_GREY, width=1, dash="dash"))
    for sep in STAGE_SEPARATORS:
        fig.add_vline(x=sep, line=dict(color=WF_GREY, width=1.5, dash="dash"))

    fig = apply_journal_formatting(fig=fig, column='full', frac=0.9, ratio=1.8)
    fig.update_layout(
        title="",
        xaxis_title="Year",
        yaxis_title="Cost/price ratio<br>relative to 2024",
        showlegend=True,
    )
    fig.update_xaxes(range=[years[0], years[-1]])
    return fig

def _residual_horn_trace(
    inflation_levels: pd.Series,
    width: pd.Series,
    center: float,
    name: str,
    line_color: str,
    fill_color: str,
) -> go.Scatter:
    x_out = (center - width).tolist() + (center + width).tolist()[::-1]
    y_out = inflation_levels.tolist() + inflation_levels.tolist()[::-1]

    return go.Scatter(
        x=x_out,
        y=y_out,
        mode="lines",
        fill="toself",
        name=name,
        line=dict(color=line_color, width=1),
        fillcolor=fill_color,
        hoverinfo="skip",
        showlegend=False,
    )


def plot_pricing_adj_residual_horn(
    inflation: list[float],
    price_adj_by_inflation: list[float],
    price_adj_custom: list[float],
    width_scale: float = 0.4,
) -> go.Figure:
    df = pd.DataFrame(
        {
            "inflation": inflation,
            "residual_by_inflation": [a - i for a, i in zip(price_adj_by_inflation, inflation)],
            "residual_custom": [a - i for a, i in zip(price_adj_custom, inflation)],
        }
    )

    stats = (
        df.groupby("inflation")[["residual_by_inflation", "residual_custom"]]
        .apply(lambda g: g.abs().mean())
        .sort_index()
        .reset_index()
    )

    max_width = max(
        stats["residual_by_inflation"].max(),
        stats["residual_custom"].max(),
    )
    scale = width_scale / max_width if max_width > 0 else 0.0

    fig = go.Figure()

    fig.add_trace(
        _residual_horn_trace(
            stats["inflation"],
            stats["residual_by_inflation"] * scale,
            center=0.0,
            name="By inflation",
            line_color=WF_BLUE,
            fill_color=WF_BLUE_FILL,
        )
    )
    fig.add_trace(
        _residual_horn_trace(
            stats["inflation"],
            stats["residual_custom"] * scale,
            center=1.0,
            name="Custom",
            line_color=WF_GREEN,
            fill_color=WF_GREEN_FILL,
        )
    )

    fig = apply_journal_formatting(fig=fig, column='single', frac=1, ratio=1)
    fig.update_layout(
        title="Mean Absolute Pricing Adjustment Residual<br>by Inflation Level",
        yaxis_title="Inflation [%]",
        showlegend=True,
        margin=dict(
            l=5,
            r=5,
            t=50,
            b=5,
            pad=0,
        ),
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=[0.0, 1.0],
        title="Water Pricing Adjustment Policy",
        ticktext=["By inflation", "Custom"],
        range=[-0.5 - width_scale, 1.5 + width_scale],
    )

    return fig

def plot_score_vs_ranking(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Ranking"],
            y=df["AHP Score"],
            mode="markers",
            marker=dict(
                color=WF_BLUE,
                size=10,
                line=dict(color=WF_BLUE, width=1),
            ),
            hovertemplate="Ranking: %{x}<br>AHP Score: %{y:.2f}<extra></extra>",
            showlegend=False,
        )
    )

    fig.add_hline(
        y=1,
        line=dict(color=WF_GREEN, width=2, dash="dash"),
        annotation_text="Always first",
        annotation_position="bottom left",
        annotation_font_color=WF_GREEN,
    )
    fig.add_hline(
        y=len(df),
        line=dict(color=WF_ORANGE, width=2, dash="dash"),
        annotation_text="Always last",
        annotation_position="bottom left",
        annotation_font_color=WF_ORANGE,
    )

    fig = apply_journal_formatting(fig=fig, column='single', frac=0.9, ratio=1.6)
    fig.update_layout(
        title="",
        xaxis_title="Ranking",
        yaxis_title="AHP Score",
        showlegend=False,
        margin=dict(
            l=5,
            r=5,
            t=5,
            b=5,
            pad=0,
        ),
    )

    fig.update_xaxes(rangemode="tozero")
    fig.update_yaxes(rangemode="tozero")

    return fig

def plot_resources_use_vs_ranking(
        team_data_dict: dict[str, TeamData]
    ) -> go.Figure:

    teams = _participants(team_data_dict)
    ranks = [team_data_dict[team].final_rank for team in teams]

    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
    )

    team_size_vals = [len(team_data_dict[team].authors) for team in teams]
    token_vals = [team_data_dict[team].survey_response.token_usage for team in teams]
    usage_vals = [team_data_dict[team].survey_response.evaluator_usage for team in teams]
    incor_vals = [team_data_dict[team].survey_response.evaluator_outputs_usage for team in teams]

    metrics = [
        (
            "Team size",
            team_size_vals,
            list(range(min(team_size_vals), max(team_size_vals) + 1)),
            WF_BLUE,
        ),
        (
            "Total hours invested",
            [team_data_dict[team].survey_response.time_spent for team in teams],
            SurveyResponse.get_question_options("time_spent"),
            WF_GREEN,
        ),
        (
            "LLM token usage",
            token_vals,
            SurveyResponse.get_question_options("token_usage"),
            [WF_ORANGE if v != "Unknown" else WF_GREY for v in token_vals],
        ),
        (
            "Evaluator usage",
            usage_vals,
            SurveyResponse.get_question_options("evaluator_usage"),
            [WF_BLUE if v != "None" else WF_GREY for v in usage_vals],
        ),
        (
            "Incorporated evaluator outputs",
            incor_vals,
            SurveyResponse.get_question_options("evaluator_outputs_usage"),
            [WF_GREEN if v != "None" else WF_GREY for v in incor_vals],
        ),
    ]

    for row, (metric, y_vals, categories, marker_color) in enumerate(metrics, start=1):
        fig.add_trace(
            go.Scatter(
                x=ranks,
                y=y_vals,
                mode="markers",
                marker=dict(
                    color=marker_color,
                    size=10,
                    line=dict(color=WF_BLUE, width=1),
                ),
                text=teams,
                hovertemplate="Team: %{text}<br>Rank: %{x}<br>" + metric + ": %{y}<extra></extra>",
                showlegend=False,
            ),
            row=row, col=1,
        )

        fig.update_yaxes(
            title=dict(text=metric, font=dict(size=11)),
            categoryorder="array",
            categoryarray=categories,
            range=[-0.5, len(categories) - 0.5],
            row=row, col=1,
        )

    fig.update_xaxes(
        title="Final Rank",
        range=[0.5, 11.5],
        dtick=1,
        row=len(metrics), col=1,
    )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1/1.3)
    fig.update_layout(
        title="Resources Use vs Ranking",
        showlegend=False,
    )

    return fig

def _stepped_colorscale(colors: list[str]) -> list[list]:
    n = len(colors)
    scale = []
    for i, color in enumerate(colors):
        scale.append([i / n, color])
        scale.append([(i + 1) / n, color])
    return scale

def plot_teams_background_expertise(
        team_data_dict: dict[str, TeamData],
        presentation_mode: bool = False,
) -> go.Figure:
    teams = [team for team, data in team_data_dict.items() if data.has_submitted_survey]
    row_labels = [team if not data.reference else "Organisers" for team, data in team_data_dict.items() if data.has_submitted_survey]

    PANEL_TITLES = ["Background", "Expertise"]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=PANEL_TITLES if presentation_mode else None,
        horizontal_spacing=0.1,
    )

    for col, (question_name, color) in enumerate(
        zip(
            ["authors_background", "authors_expertise"],
            [WF_BLUE, WF_GREEN]
        ), start=1
    ):
        question = QUESTIONS[question_name]
        assert isinstance(question, LikertQuestion)
        field_labels = list(question.options.values())
        field_short = list(question.options.values())
        scale_order = list(question.scale.values())
        scale_short = list(question.scale.keys())
        
        ramp = get_scale(color, n_steps=len(question.scale))

        def _row_values(values: dict[str, str]) -> tuple[list[float], list[str]]:
            z_row, text_row = [], []
            for field in field_labels:
                label = values.get(field)
                if label is None:
                    z_row.append(float("nan"))
                    text_row.append("")
                else:
                    idx = scale_order.index(label)
                    z_row.append(idx)
                    text_row.append(scale_short[idx])
            return z_row, text_row

        z, text = [], []
        for values in [
            (getattr(team_data_dict[team].survey_response, question_name) or {}) for team in teams
        ]:
            z_row, text_row = _row_values(values)
            z.append(z_row)
            text.append(text_row)

        fig.add_trace(
            go.Heatmap(
                z=z,
                text=text,
                # texttemplate="%{text}",  # re-enable to show the bucket key inside each cell
                # textfont=dict(size=11, shadow="auto"),
                x=field_short,
                y=row_labels,
                colorscale=_stepped_colorscale(ramp),
                zmin=0,
                zmax=len(ramp),
                xgap=3,
                ygap=3,
                showscale=False,
                hovertemplate="Team: %{y}<br>%{x}: %{text}<extra></extra>",
            ),
            row=1, col=col,
        )

        fig.update_xaxes(side="top", tickangle=-45, row=1, col=col)
        fig.update_yaxes(autorange="reversed", row=1, col=col)

        # Highlight the organizers' reference row
        fig.add_shape(
            type="rect",
            x0=-0.5, x1=len(field_short) - 0.5,
            y0=-0.5, y1=0.5,
            line=dict(color=WF_PURPLE, width=2),
            fillcolor="rgba(0,0,0,0)",
            row=1, col=col,
        )

        # Separate legend per panel (title on its own row, entries in a
        # single line below), rather than relying on legendgroup layout
        for idx, scale_label in enumerate(scale_order):
            fig.add_trace(
                go.Scatter(
                    x=[None], y=[None],
                    mode="markers",
                    marker=dict(symbol="square", size=14, color=ramp[idx]),
                    name=scale_label,
                    legend="legend" if col == 1 else "legend2",
                    showlegend=True,
                )
            )

    # Push subplot titles clear of the rotated top-axis category labels
    if not presentation_mode:
        SUBPLOT_TITLES = ["(a)", "(b)"]
        for i, label in enumerate(SUBPLOT_TITLES):
            suffix = '' if i == 0 else str(i + 1)  # '', '2', '3' matches Plotly's axis naming
            fig.add_annotation(
                xref=f'x{suffix} domain',
                yref=f'y{suffix} domain',
                x=0, y=1.3,           # x=0 → left edge; y=1.05 → just above the plot
                text=label,
                showarrow=False,
                font=font('legend_title'),
                xanchor='left',
                yanchor='bottom'
            )
    else:
        fig.update_annotations(yshift=90)

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.5)
    fig.update_layout(
        title="",
        margin=dict(
            l=10,
            r=10,
            b=125,
            t=50,
            pad=0,
        ),
        legend=dict(
            title=dict(
                text=PANEL_TITLES[0],
                font=font('legend_title'),
            ),
            orientation="h",
            yanchor="top",
            y=-0.05,
            xanchor="left",
            x=-0.09,
            font=font('legend'),
        ),
        legend2=dict(
            title=dict(
                text=PANEL_TITLES[1]+"    ",
                font=font('legend_title'),
            ),
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="left",
            x=-0.09,
            font=font('legend'),
        ),
    )

    # Explain abbreviations and acronyms
    fig.add_annotation(
            xref="paper", x=-0.09, xanchor="left",
            yref="paper", y=-0.28, yanchor="top",
            text="Abbreviations: Eng. = Engineering; mod. = modelling",
            font=font("annotation"),
            align="left",
            showarrow=False,
        )
    fig.add_annotation(
        xref="paper", x=-0.09, xanchor="left",
        yref="paper", y=-0.33, yanchor="top",
        text="Acronyms: AI, artificial intelligence; DMDU, decision making under deep uncertainty; MO, multi-objective; NRW, non-revenue water;<br>                  WDS, water distribution system.",
        font=font("annotation"),
        align="left",
        showarrow=False,
    )


    return fig

def plot_methodologies_distribution(
        team_data_dict: dict[str, TeamData],
        presentation_mode: bool = False,
    ) -> go.Figure:
    question = QUESTIONS["methodology_categories"]
    assert isinstance(question, MultiChoiceQuestion)
    known_categories = list(dict.fromkeys(question.options.values()))
    categories = known_categories + ["Other"]

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    known = set(known_categories)
    counts = Counter(
        # Free-text "Other" answers (has_other=True) come back as their own
        # verbatim, unrecognized category; bucket all of those as "Other".
        category if category in known else "Other"
        for team in teams
        for category in (team_data_dict[team].survey_response.methodology_categories or [])
    )
    values = [counts.get(category, 0) for category in categories]
    colors = [WF_GREEN if category == "Other" else WF_BLUE for category in categories]

    fig = go.Figure(
        data=[
            go.Bar(
                x=categories,
                y=values,
                marker_color=colors,
                text=values,
                textposition="outside",
                hovertemplate="%{x}: %{y}<extra></extra>",
            )
        ]
    )

    fig = apply_journal_formatting(fig=fig, column='full', frac=0.8, ratio=1.2)
    fig.update_layout(
        title="",
        showlegend=False,
        margin=dict(
            l=5,
            r=5,
            t=5,
            b=5,
            pad=0,
        ),
    )
    fig.update_xaxes(tickangle=-30)
    fig.update_yaxes(title_text="Number of teams", rangemode="tozero")

    return fig

def plot_autonomousness_distribution(
        team_data_dict: dict[str, TeamData]
    ) -> go.Figure:
    question = QUESTIONS["autonomousness"]
    assert isinstance(question, ScoreQuestion)
    categories = question.categories

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    scores = [team_data_dict[team].survey_response.autonomousness for team in teams]
    counts = Counter(scores)
    values = [counts.get(category, 0) for category in categories]
    average = sum(scores) / len(scores)

    fig = go.Figure(
        data=[
            go.Bar(
                x=categories,
                y=values,
                marker_color=WF_GREEN,
                text=values,
                textposition="outside",
                hovertemplate="%{x}: %{y}<extra></extra>",
            )
        ]
    )

    fig = apply_journal_formatting(fig=fig, column='full', frac=0.8, ratio=1.2)
    fig.update_layout(
        title=None,
        showlegend=False,
        margin=dict(
            l=5,
            r=5,
            t=20,
            b=5,
            pad=5,
        ),
    )
    fig.update_xaxes(tickangle=-30, tickmode="array", tickvals=categories)
    fig.update_yaxes(title_text="Number of teams", rangemode="tozero")

    return fig

def plot_approach_sequence(
        team_data_dict: dict[str, TeamData]
    ) -> go.Figure:
    question = QUESTIONS["approach_sequence"]
    assert isinstance(question, ChoiceQuestion)
    categories = question.categories

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    counts = Counter(
        team_data_dict[team].survey_response.approach_sequence for team in teams
    )
    values = [counts.get(category, 0) for category in categories]
    colors = [WF_BLUE, WF_GREEN, WF_ORANGE, WF_PURPLE]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=categories,
                values=values,
                hole=0.6,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                sort=False,
                texttemplate="%{label}<br>%{value} (%{percent})",
                textposition="outside",
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            )
        ]
    )

    fig = apply_journal_formatting(fig=fig, column='single', frac=1.0, ratio=1.0)
    fig.update_layout(
        title="",
        showlegend=False,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
    )

    return fig

def plot_hydraulics_reliance(
        team_data_dict: dict[str, TeamData]
    ) -> go.Figure:
    question = QUESTIONS["hydraulics_reliance"]
    assert isinstance(question, ChoiceQuestion)
    categories = question.categories

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    counts = Counter(
        team_data_dict[team].survey_response.hydraulics_reliance for team in teams
    )
    values = [counts.get(category, 0) for category in categories]
    colors = [WF_BLUE, WF_GREEN, WF_ORANGE, WF_PURPLE, WF_GREY]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=categories,
                values=values,
                hole=0.6,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                sort=False,
                texttemplate="%{label}<br>%{value} (%{percent})",
                textposition="outside",
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            )
        ]
    )

    fig = apply_journal_formatting(fig=fig, column='single', frac=1.0, ratio=1.0)
    fig.update_layout(
        title="",
        showlegend=False,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
    )

    return fig

def plot_deep_uncertainties_modelling(
        team_data_dict: dict[str, TeamData]
    ) -> go.Figure:
    """
    Horizontal stacked bar chart: one bar per exogenous-uncertainty group
    (the `deep_unc_model` question's rows), each split into segments for the
    4 modelling-sophistication scale values, sized by how many teams picked
    that value for that group.
    """
    question = QUESTIONS["deep_unc_model"]
    assert isinstance(question, LikertQuestion)
    categories = list(question.options.values())
    scale_values = list(question.scale.values())
    colors = [WF_BLUE, WF_GREEN, WF_ORANGE, WF_PURPLE]

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    responses = [team_data_dict[team].survey_response.deep_unc_model or {} for team in teams]

    fig = go.Figure()

    for scale_value, color in zip(scale_values, colors):
        counts = [
            sum(1 for response in responses if response.get(category) == scale_value)
            for category in categories
        ]
        fig.add_trace(
            go.Bar(
                y=categories,
                x=counts,
                name=scale_value,
                orientation="h",
                marker=dict(color=color),
                customdata=[count / len(responses) * 100 for count in counts],
                hovertemplate=f"{scale_value}<br>" + "%{y}: %{x} teams (%{customdata:.0f}%)<extra></extra>",
            )
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="",
        barmode="stack",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Number of teams",
        rangemode="tozero",
    )
    fig.update_yaxes(
        autorange="reversed",
    )

    return fig

def plot_parametric_uncertainties_modelling(
        team_data_dict: dict[str, TeamData]
    ) -> go.Figure:
    """
    Horizontal stacked bar chart: one bar per parametric-uncertainty group
    (the `param_unc_model` question's rows), each split into segments for
    the 4 modelling-sophistication scale values, sized by how many teams
    picked that value for that group.
    """
    question = QUESTIONS["param_unc_model"]
    assert isinstance(question, LikertQuestion)
    categories = list(question.options.values())
    scale_values = list(question.scale.values())
    colors = [WF_BLUE, WF_GREEN, WF_ORANGE, WF_PURPLE]

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    responses = [team_data_dict[team].survey_response.param_unc_model or {} for team in teams]

    fig = go.Figure()

    for scale_value, color in zip(scale_values, colors):
        counts = [
            sum(1 for response in responses if response.get(category) == scale_value)
            for category in categories
        ]
        fig.add_trace(
            go.Bar(
                y=categories,
                x=counts,
                name=scale_value,
                orientation="h",
                marker=dict(color=color),
                customdata=[count / len(responses) * 100 for count in counts],
                hovertemplate=f"{scale_value}<br>" + "%{y}: %{x} teams (%{customdata:.0f}%)<extra></extra>",
            )
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="",
        barmode="stack",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Number of teams",
        rangemode="tozero",
    )
    fig.update_yaxes(
        autorange="reversed",
    )

    return fig

def plot_scenario_generation(
        team_data_dict: dict[str, TeamData],
        presentation_mode: bool = False,
    ) -> go.Figure:
    """
    Two pie charts side by side, one for `scenario_combination` and one for
    `scenario_handling`, same style as the other single-question pies (e.g.
    `plot_approach_sequence`).
    """
    combination_question = QUESTIONS["scenario_combination"]
    assert isinstance(combination_question, ChoiceQuestion)
    combination_categories = combination_question.categories

    handling_question = QUESTIONS["scenario_handling"]
    assert isinstance(handling_question, ChoiceQuestion)
    handling_categories = handling_question.categories

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    palette = [WF_BLUE, WF_GREEN, WF_ORANGE, WF_PURPLE, WF_GREY]

    combination_counts = Counter(
        team_data_dict[team].survey_response.scenario_combination for team in teams
    )
    combination_values = [combination_counts.get(category, 0) for category in combination_categories]

    handling_counts = Counter(
        answer for team in teams
        if (answer := team_data_dict[team].survey_response.scenario_handling) is not None
    )
    handling_values = [handling_counts.get(category, 0) for category in handling_categories]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["Scenario Generation","Scenario Use"] if presentation_mode else ["(a)", "(b)"],
        specs=[[{"type": "pie"}, {"type": "pie"}]],
        horizontal_spacing=0.15,
    )

    fig.add_trace(
        go.Pie(
            labels=combination_categories,
            values=combination_values,
            hole=0.6,
            marker=dict(colors=palette, line=dict(color="#FFFFFF", width=2)),
            sort=False,
            texttemplate="%{label}<br>%{value} (%{percent})",
            textposition="outside",
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Pie(
            labels=handling_categories,
            values=handling_values,
            hole=0.6,
            marker=dict(colors=palette, line=dict(color="#FFFFFF", width=2)),
            sort=False,
            texttemplate="%{label}<br>%{value} (%{percent})",
            textposition="outside",
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=2)
    fig.update_layout(
        title="",
        margin=dict(
            l=10,
            r=10,
            t=60,
            b=10,
        ),
    )

    return fig

def plot_timing(
        team_data_dict: dict[str, TeamData],
        presentation_mode: bool = False,
    ) -> go.Figure:
    """
    Two pie charts side by side, one for `planning_horizon` and one for
    `masterplan_timestep`, same style as `plot_scenario_generation`.
    """
    horizon_question = QUESTIONS["planning_horizon"]
    assert isinstance(horizon_question, ChoiceQuestion)
    horizon_categories = horizon_question.categories

    timestep_question = QUESTIONS["masterplan_timestep"]
    assert isinstance(timestep_question, ChoiceQuestion)
    timestep_categories = timestep_question.categories

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    palette = [WF_BLUE, WF_GREEN, WF_ORANGE, WF_PURPLE, WF_GREY]

    horizon_counts = Counter(
        team_data_dict[team].survey_response.planning_horizon for team in teams
    )
    horizon_values = [horizon_counts.get(category, 0) for category in horizon_categories]

    timestep_counts = Counter(
        team_data_dict[team].survey_response.masterplan_timestep for team in teams
    )
    timestep_values = [timestep_counts.get(category, 0) for category in timestep_categories]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["Planning Horizon","Masterplan Timestep"] if presentation_mode else ["(a)", "(b)"],
        specs=[[{"type": "pie"}, {"type": "pie"}]],
        horizontal_spacing=0.2,
    )

    fig.add_trace(
        go.Pie(
            labels=horizon_categories,
            values=horizon_values,
            hole=0.6,
            marker=dict(colors=palette, line=dict(color="#FFFFFF", width=2)),
            sort=False,
            texttemplate="%{label}<br>%{value} (%{percent})",
            textposition="outside",
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Pie(
            labels=timestep_categories,
            values=timestep_values,
            hole=0.6,
            marker=dict(colors=palette, line=dict(color="#FFFFFF", width=2)),
            sort=False,
            texttemplate="%{label}<br>%{value} (%{percent})",
            textposition="outside",
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="",
        margin=dict(
            l=10,
            r=10,
            t=60,
            b=10,
        ),
    )

    return fig

def plot_residual_use(
        team_data_dict: dict[str, TeamData]
    ) -> go.Figure:
    question = QUESTIONS["residual_use"]
    assert isinstance(question, ChoiceQuestion)
    categories = question.categories

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    counts = Counter(
        team_data_dict[team].survey_response.residual_use for team in teams
    )
    values = [counts.get(category, 0) for category in categories]
    colors = [WF_BLUE, WF_GREEN, WF_ORANGE, WF_PURPLE, WF_GREY]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=categories,
                values=values,
                hole=0.6,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                sort=False,
                texttemplate="%{label}<br>%{value} (%{percent})",
                textposition="outside",
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            )
        ]
    )

    fig = apply_journal_formatting(fig=fig, column='single', frac=0.9, ratio=1.0)
    fig.update_layout(
        title="",
        showlegend=False,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
    )

    return fig

def plot_objectives(
        team_data_dict: dict[str, TeamData]
    ) -> go.Figure:
    """
    Horizontal stacked bar chart: one bar per objective (the `objectives`
    question's rows), each split into segments for the 3 similarity scale
    values, sized by how many teams picked that value for that objective.
    """
    question = QUESTIONS["objectives"]
    assert isinstance(question, LikertQuestion)
    categories = list(question.options.values())
    scale_values = list(question.scale.values())
    colors = [WF_BLUE, WF_GREEN, WF_ORANGE]

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    responses = [team_data_dict[team].survey_response.objectives or {} for team in teams]

    fig = go.Figure()

    for scale_value, color in zip(scale_values, colors):
        counts = [
            sum(1 for response in responses if response.get(category) == scale_value)
            for category in categories
        ]
        fig.add_trace(
            go.Bar(
                y=categories,
                x=counts,
                name=scale_value,
                orientation="h",
                marker=dict(color=color),
                customdata=[count / len(responses) * 100 for count in counts],
                hovertemplate=f"{scale_value}<br>" + "%{y}: %{x} teams (%{customdata:.0f}%)<extra></extra>",
            )
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="",
        barmode="stack",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Number of teams",
        rangemode="tozero",
    )
    fig.update_yaxes(
        autorange="reversed",
    )

    return fig

def plot_relative_importance(
        team_data_dict: dict[str, TeamData]
    ) -> go.Figure:
    question = QUESTIONS["relative_importance"]
    assert isinstance(question, ChoiceQuestion)
    known_categories = question.categories
    categories = known_categories + ["Other"]

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    known = set(known_categories)
    counts = Counter(
        answer if answer in known else "Other"
        for team in teams
        if (answer := team_data_dict[team].survey_response.relative_importance) is not None
    )
    values = [counts.get(category, 0) for category in categories]
    colors = [WF_BLUE, WF_GREEN, WF_ORANGE, WF_PURPLE, WF_GREY]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=categories,
                values=values,
                hole=0.6,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                sort=False,
                texttemplate="%{label}<br>%{value} (%{percent})",
                textposition="outside",
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            )
        ]
    )

    fig = apply_journal_formatting(fig=fig, column='single', frac=0.9, ratio=1.0)
    fig.update_layout(
        title="",
        showlegend=False,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
    )

    return fig

def plot_masterplan_selection(
        team_data_dict: dict[str, TeamData]
    ) -> go.Figure:
    question = QUESTIONS["masterplan_selection"]
    assert isinstance(question, ChoiceQuestion)
    known_categories = question.categories
    categories = known_categories + ["Other"]

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    known = set(known_categories)
    counts = Counter(
        answer if answer in known else "Other"
        for team in teams
        if (answer := team_data_dict[team].survey_response.masterplan_selection) is not None
    )
    values = [counts.get(category, 0) for category in categories]
    colors = [WF_BLUE, WF_GREEN, WF_ORANGE, WF_PURPLE, WF_GREY]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=categories,
                values=values,
                hole=0.6,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                sort=False,
                texttemplate="%{label}<br>%{value} (%{percent})",
                textposition="outside",
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            )
        ]
    )

    fig = apply_journal_formatting(fig=fig, column='single', frac=0.9, ratio=1.0)
    fig.update_layout(
        title="",
        showlegend=False,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
    )

    return fig

def plot_shifting_priorities(
        team_data_dict: dict[str, TeamData]
    ) -> go.Figure:
    question = QUESTIONS["shifting_priorities"]
    assert isinstance(question, ChoiceQuestion)
    known_categories = question.categories
    categories = known_categories + ["Other"]

    teams = [
        team for team, data in team_data_dict.items()
        if not data.reference and data.has_submitted_survey
    ]

    known = set(known_categories)
    counts = Counter(
        answer if answer in known else "Other"
        for team in teams
        if (answer := team_data_dict[team].survey_response.shifting_priorities) is not None
    )
    values = [counts.get(category, 0) for category in categories]
    colors = [WF_BLUE, WF_GREEN, WF_ORANGE, WF_PURPLE, WF_GREY]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=categories,
                values=values,
                hole=0.6,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                sort=False,
                texttemplate="%{label}<br>%{value} (%{percent})",
                textposition="outside",
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            )
        ]
    )

    fig = apply_journal_formatting(fig=fig, column='single', frac=0.9, ratio=1.0)
    fig.update_layout(
        title="",
        showlegend=False,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
    )

    return fig

def _team_avg_debt_per_capita_vs_time(team_data: TeamData) -> pd.Series:
    """
    For a team's final (stage-3) system, computes, for each competition year,
    the debt per capita (NPV of already-issued bonds / population) for each
    water utility, then averages across water utilities.
    """
    nc = team_data.final_system
    infl = nc.inflation

    yearly_avg = {}
    for year in COMPETITION_YEARS:
        ts = pd.Timestamp(year=year, month=1, day=1)
        yield_rate = float(infl[ts])/100

        per_capita_by_wu = []
        for wu in nc.water_utilities:
            issued_bonds = [b for b in wu.m_bonds if b.issue_date <= ts]
            total_debt_npv = sum(
                b.net_present_value(year=ts, yield_rate=yield_rate)
                for b in issued_bonds
            )
            population = float(wu.population.loc[ts])
            per_capita_by_wu.append(total_debt_npv / population)

        yearly_avg[year] = float(np.mean(per_capita_by_wu))

    return pd.Series(yearly_avg)

def _price_index_2024_base(nc) -> pd.Series:
    """
    Builds a cumulative price index (year -> price level) from a system's
    yearly inflation rates, normalized so that year 2024 equals 100. Indexed
    by integer calendar year rather than Timestamp.
    """
    infl = nc.inflation.sort_index()
    cum = (1.0 + infl / 100.0).cumprod()
    cum.index = cum.index.year
    return cum / float(cum.loc[2024]) * 100.0

def _team_avg_debt_per_capita_real_vs_time(team_data: TeamData) -> pd.Series:
    """
    Same as _team_avg_debt_per_capita_vs_time, but deflated to constant 2024
    euros using the system's cumulative price index (see
    _price_index_2024_base), i.e. 2024 has an implicit index value of 100.
    """
    nominal = _team_avg_debt_per_capita_vs_time(team_data)
    price_index = _price_index_2024_base(team_data.final_system)
    return nominal * 100.0 / price_index.loc[nominal.index]

def plot_debt_per_capita_vs_time(
        team_data_dict: dict[str, TeamData],
        ghost: bool = False,
        presentation_mode: bool = False,
    ) -> go.Figure:
    """
    Two-row, shared-x view of each team's average (across water utilities)
    debt per capita over the competition years: face (nominal) value in the
    top row, and inflation-adjusted value in constant 2024 euros (deflated
    with the system's cumulative inflation, 2024 = 100) in the bottom row.

    In ghost mode (anonymized) every team's line is drawn thin, with the
    cross-team median overlaid as a thick solid line, one color per row (see
    plot_nrw_analysis_vs_time_line); each row's legend shows only its
    median. Otherwise each team keeps its own color/marker across both rows
    and each row's legend lists the teams.
    """
    teams = _finishers(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)
    color_map = _team_color_map(team_data_dict)

    ROW_TITLES = ["Face Value", "Inflation-Adjusted Value (2024 €)"]
    ROW_COLORS = [WF_BLUE, WF_ORANGE]
    ROW_HOVER_LABELS = ["Avg. Debt per capita", "Avg. Debt per capita (2024 €)"]
    ROW_LEGENDS = ["legend", "legend2"]
    MEDIAN_LINE_WIDTH = 3

    series_by_row = [
        {team: _team_avg_debt_per_capita_vs_time(team_data_dict[team]) for team in teams},
        {team: _team_avg_debt_per_capita_real_vs_time(team_data_dict[team]) for team in teams},
    ]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=ROW_TITLES if presentation_mode else None,
        vertical_spacing=0.08,
    )

    for row, (row_color, team_series, hover_label) in enumerate(
        zip(ROW_COLORS, series_by_row, ROW_HOVER_LABELS), start=1
    ):
        if ghost:
            light_color = make_opaque(row_color, 0.25)
            values = pd.DataFrame({team: s for team, s in team_series.items()})
            median = values.median(axis=1)

            fig.add_trace(
                go.Scatter(
                    x=median.index,
                    y=median.values,
                    mode="lines",
                    name="Median",
                    legend=ROW_LEGENDS[row - 1],
                    showlegend=True,
                    line=dict(color=row_color, width=MEDIAN_LINE_WIDTH),
                    hovertemplate=(
                        f"Year: %{{x}}<br>Median {hover_label}: %{{y:.2f}} €/person<extra></extra>"
                    ),
                ),
                row=row, col=1,
            )

            for team in teams:
                fig.add_trace(
                    go.Scatter(
                        x=values.index,
                        y=values[team],
                        mode="lines",
                        name="Individual Teams" if team == teams[0] else None,
                        line=dict(color=light_color, width=1),
                        legend=ROW_LEGENDS[row - 1],
                        showlegend=team == teams[0],
                        hoverinfo="skip",
                    ),
                    row=row, col=1,
                )
        else:
            for team in teams:
                series = team_series[team]
                fig.add_trace(
                    go.Scatter(
                        x=series.index,
                        y=series.values,
                        mode="lines+markers",
                        name=team,
                        legendgroup=team,
                        legend=ROW_LEGENDS[row - 1],
                        showlegend=True,
                        marker=dict(symbol=symbol_map[team], size=7, color=color_map[team]),
                        line=dict(width=1.5, color=color_map[team]),
                        hovertemplate=(
                            f"Team: {team}<br>Year: %{{x}}<br>"
                            f"{hover_label}: %{{y:.2f}} €/person<extra></extra>"
                        ),
                    ),
                    row=row, col=1,
                )

    for row in (1, 2):
        for sep in STAGE_SEPARATORS:
            fig.add_vline(
                x=sep,
                line=dict(color=WF_GREY, width=1.5, dash="dash"),
                row=row, col=1,
            )

    fig = apply_journal_formatting(fig=fig, column='full', frac=0.9, ratio=1.4)
    if not presentation_mode:
        SUBPLOT_TITLES = ['(a)', '(b)']
        for i, label in enumerate(SUBPLOT_TITLES):
            suffix = '' if i == 0 else str(i + 1)  # '', '2' matches Plotly's axis naming
            fig.add_annotation(
                xref=f'x{suffix} domain',
                yref=f'y{suffix} domain',
                x=0, y=1.01,           # x=0 → left edge; y=1.05 → just above the plot
                text=label,
                showarrow=False,
                font=font('legend_title'),
                xanchor='left',
                yanchor='bottom'
            )

    # One legend box per row, right of the plot, top-aligned with that row
    row_y_domains = [fig.layout.yaxis.domain, fig.layout.yaxis2.domain]
    fig.update_layout(**{
        legend_name: dict(
            y=domain[1],
            yanchor="top",
            x=1.01,
            xanchor="left",
            font=font('legend'),
        )
        for legend_name, domain in zip(ROW_LEGENDS, row_y_domains)
    })

    fig.update_layout(
        title=None,
        showlegend=True,
        margin=dict(
            l=0,
            r=90,
            t=30,
            b=50,
            pad=0,
        ),
    )
    fig.update_xaxes(
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
        row=1, col=1,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
        row=2, col=1,
    )

    fig.update_yaxes(
        title_text="Avg. Debt per capita<br>[€/person]",
        rangemode="tozero",
        row=1, col=1,
    )
    fig.update_yaxes(
        title_text="Avg. Debt per capita<br>[€<sub>2024</sub>/person]",
        rangemode="tozero",
        row=2, col=1,
    )

    return fig

def _team_supply_to_demand_ratio_vs_time(team_data: TeamData) -> pd.Series:
    """
    For a team's final (stage-3) system, computes, for each competition year,
    the ratio of total supply (sum of nominal capacity of all active supplies
    across water utilities) to the total demand across all municipalities.
    """
    nc = team_data.final_system

    yearly_demand = team_data.yearly_total_demand.sum(axis=1)

    ratios = {}
    for year in COMPETITION_YEARS:
        ts = pd.Timestamp(year=year, month=1, day=1)

        total_supply = sum(
            source.nominal_capacity
            for wu in nc.water_utilities
            for source in wu.active_sources(when=ts)
        )*365

        ratios[year] = total_supply / float(yearly_demand.loc[ts])

    return pd.Series(ratios)

def plot_supply_to_demand_ratio_vs_time(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots the ratio of total supply
    to total demand over the competition years, one line per team.
    """
    teams = _finishers(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)

    fig = go.Figure()

    for team in teams:
        series = _team_supply_to_demand_ratio_vs_time(team_data_dict[team])

        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines+markers",
                name=team,
                marker=dict(symbol=symbol_map[team], size=7),
                line=dict(width=1.5),
                hovertemplate=(
                    f"Team: {team}<br>Year: %{{x}}<br>"
                    "Supply/Demand ratio: %{y:.2f}<extra></extra>"
                ),
            )
        )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="Supply-to-Demand Ratio over Time",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )
    fig.update_yaxes(
        title_text="Supply / Demand ratio",
        rangemode="tozero",
    )

    return fig

def _team_nrw_vs_time(team_data: TeamData) -> pd.Series:
    """
    For each competition year, computes the team's total non-revenue water
    volume, i.e. total demand minus billable demand, summed across all
    municipalities.
    """
    total = team_data.yearly_total_demand.sum(axis=1)
    billable = team_data.yearly_billable_demand.sum(axis=1)

    start = pd.Timestamp(year=COMPETITION_YEARS[0], month=1, day=1)
    end = pd.Timestamp(year=COMPETITION_YEARS[-1], month=1, day=1)

    return (total - billable).loc[start:end]

def plot_nrw_vs_time(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots the total non-revenue
    water volume over the competition years, one line per team.
    """
    teams = _participants(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)

    fig = go.Figure()

    for team in teams:
        series = _team_nrw_vs_time(team_data_dict[team])

        fig.add_trace(
            go.Scatter(
                x=series.index.year,
                y=series.values,
                mode="lines+markers",
                name=team,
                marker=dict(symbol=symbol_map[team], size=7),
                line=dict(width=1.5),
                hovertemplate=(
                    f"Team: {team}<br>Year: %{{x}}<br>"
                    "NRW: %{y:.2f} m3<extra></extra>"
                ),
            )
        )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="Non-Revenue Water over Time",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )
    fig.update_yaxes(
        title_text="Non-Revenue Water [m\u00B3/year]",
        rangemode="tozero",
        
    )

    return fig

def _team_avg_network_age_vs_time(team_data: TeamData) -> pd.Series:
    """
    For a team's final (stage-3) system, computes, for each competition year,
    the population-weighted average distribution network age across all
    municipalities.
    """
    ages = team_data.idn_avg_age
    pops = TeamData.population[ages.columns]

    weighted_avg_age = (ages * pops).sum(axis=1) / pops.sum(axis=1)

    start = pd.Timestamp(year=COMPETITION_YEARS[0], month=1, day=1)
    end = pd.Timestamp(year=COMPETITION_YEARS[-1], month=1, day=1)

    return weighted_avg_age.loc[start:end]

def plot_avg_idn_age_vs_time(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots the population-weighted
    average distribution network age over the competition years, one line
    per team.
    """
    teams = _participants(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)

    fig = go.Figure()

    for team in teams:
        series = _team_avg_network_age_vs_time(team_data_dict[team])

        fig.add_trace(
            go.Scatter(
                x=series.index.year,
                y=series.values,
                mode="lines+markers",
                name=team,
                marker=dict(symbol=symbol_map[team], size=7),
                line=dict(width=1.5),
                hovertemplate=(
                    f"Team: {team}<br>Year: %{{x}}<br>"
                    "Avg. Network Age: %{y:.1f} years<extra></extra>"
                ),
            )
        )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="Average Distribution Network Age over Time",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )

    class_bounds = [c.demand_factor_bounds[1] for c in NRWClass if np.isfinite(c.demand_factor_bounds[1])]
    tickvals = [0.] + class_bounds
    ticktext = ["0"] + [f"{bound:.0f} ({c.name}\u2193)" for c, bound in zip(NRWClass, class_bounds)]

    fig.update_yaxes(
        title_text="Avg. Network Age [years]<br>    (NRW Class)",
        range=[0,75],
        tickmode="array",
        tickvals=tickvals,
        ticktext=ticktext,
    )

    return fig

def _team_avg_wds_age_vs_time(team_data: TeamData) -> pd.Series:
    """
    For a team's final (stage-3) system, computes, for each competition year,
    the length-weighted average age of the water distribution system: the
    active pipe on every active connection, weighted by the connection's
    length (distance).
    """
    nc = team_data.final_system

    ages = {}
    for year in COMPETITION_YEARS:
        ts = pd.Timestamp(year=year, month=1, day=1)

        total_weighted_age = 0.0
        total_length = 0.0
        for connection in nc._all_connections:
            if not connection.is_active(when=ts):
                continue

            pipe = connection.active_pipe(when=ts)
            if pipe is None:
                continue

            age = (ts - pipe.installation_date).days / 365.25
            length = connection.distance

            total_weighted_age += age * length
            total_length += length

        ages[year] = total_weighted_age / total_length

    return pd.Series(ages)

def plot_avg_wds_age_vs_time(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots the length-weighted
    average age of the water distribution system over the competition
    years, one line per team.
    """
    teams = _participants(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)

    fig = go.Figure()

    for team in teams:
        series = _team_avg_wds_age_vs_time(team_data_dict[team])

        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines+markers",
                name=team,
                marker=dict(symbol=symbol_map[team], size=7),
                line=dict(width=1.5),
                hovertemplate=(
                    f"Team: {team}<br>Year: %{{x}}<br>"
                    "Avg. WDS Age: %{y:.1f} years<extra></extra>"
                ),
            )
        )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="Average WDS Age over Time",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )
    fig.update_yaxes(
        title_text="Avg. WDS Age [years]",
        rangemode="tozero",
    )

    return fig

SUPPLY_TYPES = [GroundWater, SurfaceWater, Desalination]
SUPPLY_TYPE_LABELS = {
    GroundWater.NAME: "Groundwater",
    SurfaceWater.NAME: "Surface Water",
    Desalination.NAME: "Desalination",
}
SUPPLY_TYPE_PATTERNS = {
    GroundWater.NAME: "",
    SurfaceWater.NAME: "/",
    Desalination.NAME: "x",
}
SUPPLY_TYPE_DASH = {
    GroundWater.NAME: "dash",
    SurfaceWater.NAME: "dot",
    Desalination.NAME: "dashdot",
}

def _team_supply_by_type_vs_time(team_data: TeamData) -> pd.DataFrame:
    """
    For a team's final (stage-3) system, computes, for each competition year,
    the total nominal capacity of active supply sources of each type
    (groundwater, surface water, desalination), summed across water
    utilities.
    """
    nc = team_data.final_system

    yearly = {}
    for year in COMPETITION_YEARS:
        ts = pd.Timestamp(year=year, month=1, day=1)

        totals = {t.NAME: 0.0 for t in SUPPLY_TYPES}
        for wu in nc.water_utilities:
            for source in wu.active_sources(when=ts):
                totals[type(source).NAME] += source.nominal_capacity * 365

        yearly[year] = totals

    return pd.DataFrame(yearly).T  # index: year, columns: supply type NAME

def plot_supply_by_type_vs_time_bar(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots a stacked bar of total
    supply capacity by source type, every 5 competition years. Within each
    year there is one stacked bar per team (via a multicategory x-axis, as
    in the original version); bar color identifies the team, fill pattern
    identifies the supply type. The team level of the axis is kept as an
    invisible (zero-width) key so bars still group/dodge correctly, but no
    team text clutters the x-axis - team identity comes from the legend and
    hover text instead.
    """
    teams = _finishers(team_data_dict)
    color_map = _team_color_map(team_data_dict)

    bar_years = COMPETITION_YEARS[::10]
    team_dfs = {team: _team_supply_by_type_vs_time(team_data_dict[team]) for team in teams}

    # Unique-but-invisible per-team key for the inner multicategory level.
    team_keys = {team: "​" * (i + 1) for i, team in enumerate(teams)}

    fig = go.Figure()

    for source_type in SUPPLY_TYPES:
        x_years, x_teams, y_vals, colors, hover_teams = [], [], [], [], []
        for team in teams:
            df = team_dfs[team]
            for year in bar_years:
                x_years.append(year)
                x_teams.append(team_keys[team])
                y_vals.append(df.loc[year, source_type.NAME])
                colors.append(color_map[team])
                hover_teams.append(team)

        fig.add_trace(
            go.Bar(
                x=[x_years, x_teams],
                y=y_vals,
                customdata=hover_teams,
                marker=dict(
                    color=colors,
                    pattern=dict(shape=SUPPLY_TYPE_PATTERNS[source_type.NAME], fgcolor="white"),
                ),
                name=SUPPLY_TYPE_LABELS[source_type.NAME],
                legend="legend",
                hovertemplate=(
                    "Team: %{customdata}<br>Year: %{x[0]}<br>"
                    + SUPPLY_TYPE_LABELS[source_type.NAME]
                    + ": %{y:.0f} m³/year<extra></extra>"
                ),
            )
        )

    # Separate legend entries for team color, since bar color varies within
    # each trace (per point) and is not otherwise reflected in the legend.
    for team in teams:
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(symbol="square", size=14, color=color_map[team]),
                name=team,
                legend="legend2",
                showlegend=True,
            )
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="Supply Capacity by Type over Time",
        barmode="stack",
        legend=dict(
            title=dict(text="Supply Type", font=font('legend_title')),
            x=1.02, y=1, xanchor='left', yanchor='top',
            font=font('legend'),
        ),
        legend2=dict(
            title=dict(text="Team", font=font('legend_title')),
            x=1.02, y=0.6, xanchor='left', yanchor='top',
            font=font('legend'),
        ),
    )
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(
        title_text="Supply Capacity [m³/year]",
        rangemode="tozero",
    )

    return fig

def plot_supply_by_type_vs_time_scatter(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots three independent lines
    (one per supply type) of total supply capacity over the competition
    years, in a single figure. Line color and marker identify the team;
    line dash identifies the supply type.
    """
    teams = _finishers(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)
    color_map = _team_color_map(team_data_dict)

    fig = go.Figure()

    for team in teams:
        df = _team_supply_by_type_vs_time(team_data_dict[team])
        total = df.sum(axis=1)

        # Total supply (summed across types), solid line
        fig.add_trace(
            go.Scatter(
                x=total.index,
                y=total.values,
                mode="lines",
                name=team,
                legendgroup=team,
                showlegend=False,
                line=dict(width=1.5, color=color_map[team], dash="solid"),
                hovertemplate=(
                    f"Team: {team}<br>Year: %{{x}}<br>"
                    "Total: %{y:.0f} m³/year<extra></extra>"
                ),
            )
        )

        for source_type in SUPPLY_TYPES:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[source_type.NAME],
                    mode="lines+markers",
                    name=team,
                    legendgroup=team,
                    showlegend=(source_type is SUPPLY_TYPES[0]),
                    marker=dict(symbol=symbol_map[team], size=7, color=color_map[team]),
                    line=dict(width=1.5, color=color_map[team], dash=SUPPLY_TYPE_DASH[source_type.NAME]),
                    hovertemplate=(
                        f"Team: {team}<br>Year: %{{x}}<br>"
                        f"{SUPPLY_TYPE_LABELS[source_type.NAME]}: %{{y:.0f}} m³/year<extra></extra>"
                    ),
                )
            )

    # Legend entries for supply type (line dash) and total (solid line)
    fig.add_trace(
        go.Scatter(
            x=[None], y=[None],
            mode="lines",
            name="Total",
            legendgroup="type",
            legendgrouptitle_text="Supply Type",
            line=dict(color=WF_GREY, width=2, dash="solid"),
            showlegend=True,
        )
    )
    for source_type in SUPPLY_TYPES:
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="lines",
                name=SUPPLY_TYPE_LABELS[source_type.NAME],
                legendgroup="type",
                line=dict(color=WF_GREY, width=2, dash=SUPPLY_TYPE_DASH[source_type.NAME]),
                showlegend=True,
            )
        )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="Supply Capacity by Type over Time",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )
    fig.update_yaxes(
        title_text="Supply Capacity [m³/year]",
        rangemode="tozero",
    )

    return fig

DEMAND_COMPONENTS = ["total", "billable", "nrw"]
DEMAND_COMPONENT_LABELS = {
    "total": "Total",
    "billable": "Billable",
    "nrw": "NRW",
}
DEMAND_COMPONENT_DASH = {
    "total": "solid",
    "billable": "dash",
    "nrw": "dot",
}

def _team_demand_components_vs_time(team_data: TeamData) -> pd.DataFrame:
    """
    For each competition year, the team's total demand, billable demand, and
    non-revenue water (total - billable), summed across all municipalities.
    """
    total = team_data.yearly_total_demand.sum(axis=1)
    billable = team_data.yearly_billable_demand.sum(axis=1)
    nrw = total - billable

    start = pd.Timestamp(year=COMPETITION_YEARS[0], month=1, day=1)
    end = pd.Timestamp(year=COMPETITION_YEARS[-1], month=1, day=1)

    df = pd.DataFrame({"total": total, "billable": billable, "nrw": nrw}).loc[start:end]
    df.index = df.index.year
    return df

def plot_supply_and_demand_vs_time_ghost_line(
        team_data_dict: dict[str, TeamData],
) -> go.Figure:
    """
    Anonymized version of plot_supply_by_type_vs_time_scatter_anonymous: individual
    teams are not identified by color/marker. Supply (total plus its 3
    types, in blue) and demand (total, billable, and NRW, in green) are
    each decomposed into components: for every component a light line is
    drawn per team to show spread, overlaid with a bold line for the
    median across teams. The total of each group uses a solid line; its
    other components use distinct dashes.
    """
    teams = _finishers(team_data_dict)
    team_dfs = {team: _team_supply_by_type_vs_time(team_data_dict[team]) for team in teams}

    LIGHT_SUPPLY_COLOR = make_opaque(WF_BLUE, 0.25)
    LIGHT_DEMAND_COLOR = make_opaque(WF_GREEN, 0.25)
    MEDIAN_LINE_WIDTH = 3

    fig = go.Figure()

    # Total supply (summed across types): solid line
    totals = pd.DataFrame({team: df.sum(axis=1) for team, df in team_dfs.items()})
    median_total = totals.median(axis=1)

    for team in teams:
        fig.add_trace(
            go.Scatter(
                x=totals.index,
                y=totals[team],
                mode="lines",
                line=dict(color=LIGHT_SUPPLY_COLOR, width=1, dash="solid"),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=median_total.index,
            y=median_total.values,
            mode="lines",
            name="Total",
            legendgroup="type",
            legendgrouptitle_text="National Supply by Type",
            line=dict(color=WF_BLUE, width=MEDIAN_LINE_WIDTH, dash="solid"),
            hovertemplate="Year: %{x}<br>Median Total: %{y:.0f} m³/year<extra></extra>",
        )
    )

    # Per-type lines
    for source_type in SUPPLY_TYPES:
        values = pd.DataFrame({team: df[source_type.NAME] for team, df in team_dfs.items()})
        median = values.median(axis=1)

        for team in teams:
            fig.add_trace(
                go.Scatter(
                    x=values.index,
                    y=values[team],
                    mode="lines",
                    line=dict(color=LIGHT_SUPPLY_COLOR, width=1, dash=SUPPLY_TYPE_DASH[source_type.NAME]),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        fig.add_trace(
            go.Scatter(
                x=median.index,
                y=median.values,
                mode="lines",
                name=SUPPLY_TYPE_LABELS[source_type.NAME],
                legendgroup="type",
                line=dict(color=WF_BLUE, width=MEDIAN_LINE_WIDTH, dash=SUPPLY_TYPE_DASH[source_type.NAME]),
                hovertemplate=(
                    f"Year: %{{x}}<br>Median {SUPPLY_TYPE_LABELS[source_type.NAME]}: "
                    "%{y:.0f} m³/year<extra></extra>"
                ),
            )
        )

    # Demand components: total, billable, and NRW
    demand_dfs = {team: _team_demand_components_vs_time(team_data_dict[team]) for team in teams}

    for component in DEMAND_COMPONENTS:
        values = pd.DataFrame({team: df[component] for team, df in demand_dfs.items()})
        median = values.median(axis=1)

        for team in teams:
            fig.add_trace(
                go.Scatter(
                    x=values.index,
                    y=values[team],
                    mode="lines",
                    line=dict(color=LIGHT_DEMAND_COLOR, width=1, dash=DEMAND_COMPONENT_DASH[component]),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        fig.add_trace(
            go.Scatter(
                x=median.index,
                y=median.values,
                mode="lines",
                name=DEMAND_COMPONENT_LABELS[component],
                legendgroup="demand",
                legendgrouptitle_text="National Demand by Type",
                line=dict(color=WF_GREEN, width=MEDIAN_LINE_WIDTH, dash=DEMAND_COMPONENT_DASH[component]),
                hovertemplate=(
                    f"Year: %{{x}}<br>Median {DEMAND_COMPONENT_LABELS[component]}: "
                    "%{y:.0f} m³/year<extra></extra>"
                ),
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[None], y=[None],
            mode="lines",
            name="Median",
            legend="legend2",
            line=dict(color=WF_GREY, width=MEDIAN_LINE_WIDTH),
            showlegend=True,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None], y=[None],
            mode="lines",
            name="Individual teams",
            legend="legend2",
            line=dict(color=WF_GREY, width=1),
            showlegend=True,
        )
    )
    # This would work as well without need for a second legend. the problem is
    # that plotly legend height is at most the plot, thus it introduces a scrollbar.
    # I don't want to make the plot taller just to have the scrollbar disappear.
    # fig.add_trace(
    #     go.Scatter(
    #         x=[None], y=[None],
    #         mode="lines",
    #         name="Median",
    #         legendgroup="line_weight",
    #         legendgrouptitle_text="Line weight",
    #         line=dict(color=WF_GREY, width=MEDIAN_LINE_WIDTH),
    #         showlegend=True,
    #     )
    # )
    # fig.add_trace(
    #     go.Scatter(
    #         x=[None], y=[None],
    #         mode="lines",
    #         name="Individual teams",
    #         legendgroup="line_weight",
    #         line=dict(color=WF_GREY, width=1),
    #         showlegend=True,
    #     )
    # )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=0.9, ratio=2.2)
    fig.update_layout(
        title=None,
        showlegend=True,
        legend=dict(
            x=1.02, y=1, xanchor="left", yanchor="top",
        ),
        legend2=dict(
            title=dict(text="Line weight", font=font('legend')),
            x=1.02, y=0.15, xanchor="left", yanchor="top",
            font=font('legend'),
        ),
        margin=dict(
                    l=0,
                    r=0,
                    t=10,
                    b=50,
                    pad=0,
                ),
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )
    fig.update_yaxes(
        title_text="Flow [m³/year]",
        rangemode="tozero",
    )

    return fig

def plot_supply_by_type_bar_and_demand_by_type_fillline_vs_time(
        team_data_dict: dict[str, TeamData],
        ghost: bool = True,
        presentation_mode: bool = False,
) -> go.Figure:
    """Plot component fills, their summed supply medians, and median total demand."""
    teams = _finishers(team_data_dict)
    supply_dfs = {team: _team_supply_by_type_vs_time(team_data_dict[team]) for team in teams}
    demand_dfs = {team: _team_demand_components_vs_time(team_data_dict[team]) for team in teams}
    median_line_width = 3
    supply_fill_colors = get_scale(WF_BLUE, len(SUPPLY_TYPES))
    demand_fill_colors = [make_opaque(WF_GREEN, 0.45), make_opaque(WF_GREEN, 0.18)]

    fig = make_subplots(
        rows=1, cols=2,
        shared_yaxes=True,
        subplot_titles=["Supply", "Demand"] if presentation_mode else None,
        horizontal_spacing=0.05,
    )

    supply_components = [("total", "Total", "solid")]
    demand_components = [("total", "Total", "solid")]
    supply_medians = pd.DataFrame({
        source_type.NAME: pd.DataFrame({
            team: df[source_type.NAME] for team, df in supply_dfs.items()
        }).median(axis=1)
        for source_type in SUPPLY_TYPES
    })
    for col, team_dfs, components, legend_name, color in (
        (1, supply_dfs, supply_components, "legend", WF_BLUE),
        (2, demand_dfs, demand_components, "legend2", WF_GREEN),
    ):
        for component, label, dash in components:
            values = pd.DataFrame({
                team: df.sum(axis=1) if col == 1 and component == "total" else df[component]
                for team, df in team_dfs.items()
            })
            median = supply_medians.sum(axis=1) if col == 1 else values.median(axis=1)
            hover_label = "Sum of component medians" if col == 1 else f"Median {label}"
            fig.add_trace(go.Scatter(
                x=median.index, y=median.values,
                mode="lines",
                name=label,
                legend=legend_name,
                legendgroup=component,
                showlegend=component == "total",
                line=dict(color=color, width=median_line_width, dash=dash),
                hovertemplate=(
                    f"Year: %{{x}}<br>{hover_label}: "
                    "%{y:.0f} m³/year<extra></extra>"
                ),
            ), row=1, col=col)
            if ghost:
                for team in teams:
                    fig.add_trace(go.Scatter(
                        x=values.index, y=values[team],
                        mode="lines",
                        line=dict(color=make_opaque(color, 0.25), width=1, dash=dash),
                        showlegend=False,
                        hoverinfo="skip",
                    ), row=1, col=col)

    supply_boundary = None
    for source_type, fill_color in zip(reversed(SUPPLY_TYPES), reversed(supply_fill_colors)):
        median = supply_medians[source_type.NAME]
        supply_boundary = median if supply_boundary is None else supply_boundary + median
        fig.add_trace(go.Scatter(
            x=supply_boundary.index, y=supply_boundary.values,
            customdata=median.values,
            mode="lines",
            line=dict(width=0),
            fill="tozeroy" if source_type is SUPPLY_TYPES[-1] else "tonexty",
            fillcolor=make_opaque(fill_color, 0.6),
            name=SUPPLY_TYPE_LABELS[source_type.NAME],
            legend="legend",
            legendgroup=source_type.NAME,
            showlegend=True,
            hovertemplate="Year: %{x}<br>Median capacity: %{customdata:.0f} m³/year<extra>%{fullData.name}</extra>",
        ), row=1, col=1)

    billable_values = pd.DataFrame({team: df["billable"] for team, df in demand_dfs.items()})
    total_values = pd.DataFrame({team: df["total"] for team, df in demand_dfs.items()})
    billable_median = billable_values.median(axis=1)
    total_median = total_values.median(axis=1)
    for component, boundary, band_values, fill_color in (
        ("billable", billable_median, billable_median, demand_fill_colors[0]),
        ("nrw", total_median, total_median - billable_median, demand_fill_colors[1]),
    ):
        fig.add_trace(go.Scatter(
            x=boundary.index, y=boundary.values,
            customdata=band_values.values,
            mode="lines",
            line=dict(color=WF_GREEN, width=median_line_width, dash="dash") if component == "billable" else dict(width=0),
            fill="tozeroy" if component == "billable" else "tonexty",
            fillcolor=fill_color,
            name=DEMAND_COMPONENT_LABELS[component],
            legend="legend2",
            legendgroup=component,
            showlegend=True,
            hovertemplate="Year: %{x}<br>Demand band: %{customdata:.0f} m³/year<extra>%{fullData.name}</extra>",
        ), row=1, col=2)

    historical_supply = sum(
        source.nominal_capacity * 365
        for utility in team_data_dict[teams[0]].final_system.water_utilities
        for source in utility.active_sources(when=pd.Timestamp(year=2024, month=1, day=1))
    )
    fig.add_shape(
        type="line",
        xref="x2 domain", yref="y2",
        x0=0, x1=1, y0=historical_supply, y1=historical_supply,
        line=dict(color=WF_BLUE, width=1.5, dash="dot"),
    )
    fig.add_annotation(
        xref="x2 domain", yref="y2",
        x=1, y=historical_supply,
        text="National supply as of 1st Jan 2025",
        showarrow=False,
        xanchor="right", yanchor="bottom",
        font=font('annotation'),
    )

    for label, width in [("Median", median_line_width)] + ([("Individual teams", 1)] if ghost else []):
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="lines",
            name=label,
            legend="legend3",
            line=dict(color=WF_GREY, width=width),
            showlegend=True,
            hoverinfo="skip",
        ), row=1, col=1)

    for col in (1, 2):
        for sep in STAGE_SEPARATORS:
            fig.add_vline(
                x=sep, line=dict(color=WF_GREY, width=1.5, dash="dash"),
                row=1, col=col,
            )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    if not presentation_mode:
        for col, label in enumerate(["(a)", "(b)"], start=1):
            suffix = '' if col == 1 else str(col)
            fig.add_annotation(
                xref=f"x{suffix} domain", yref=f"y{suffix} domain",
                x=0, y=1.01,
                text=label, showarrow=False,
                font=font('legend_title'),
                xanchor="left", yanchor="bottom",
            )
    fig.update_layout(
        title=None,
        showlegend=True,
        legend=dict(
            title=dict(text="Supply by type", font=font('legend_title')),
            orientation="h", x=0, xanchor="left", y=-0.2, yanchor="top",
            font=font('legend'),
        ),
        legend2=dict(
            title=dict(text="Demand", font=font('legend_title')),
            orientation="h", x=0, xanchor="left", y=-0.3, yanchor="top",
            font=font('legend'),
        ),
        legend3=dict(
            title=dict(text="Line weight", font=font('legend_title')),
            orientation="h", x=0, xanchor="left", y=-0.4, yanchor="top",
            font=font('legend'),
        ),
        margin=dict(l=50, r=10, t=35, b=10, pad=0),
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0] - 0.5, COMPETITION_YEARS[-1] + 1],
        tickmode="array",
        tickvals=[2025, 2050, 2075, COMPETITION_YEARS[-1] + 1],
        tickangle=0,
        ticklabelstandoff=5,
        minor=dict(dtick=5, tick0=2025, showgrid=True, gridcolor="lightgray"),
        
    )
    fig.update_yaxes(rangemode="tozero")
    fig.update_yaxes(title_text="Flow [m³/year]", row=1, col=1)
    return fig

def plot_supply_by_type_vs_time_scatter_independent(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots the total supply capacity
    over the competition years, one subplot per supply type. Line color and
    marker identify the team.
    """
    teams = _finishers(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)
    color_map = _team_color_map(team_data_dict)

    fig = make_subplots(
        rows=1, cols=len(SUPPLY_TYPES),
        subplot_titles=[SUPPLY_TYPE_LABELS[t.NAME] for t in SUPPLY_TYPES],
        shared_yaxes=True,
        horizontal_spacing=0.05,
    )

    team_dfs = {team: _team_supply_by_type_vs_time(team_data_dict[team]) for team in teams}

    for col, source_type in enumerate(SUPPLY_TYPES, start=1):
        for team in teams:
            df = team_dfs[team]
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[source_type.NAME],
                    mode="lines+markers",
                    name=team,
                    legendgroup=team,
                    showlegend=(col == 1),
                    marker=dict(symbol=symbol_map[team], size=7, color=color_map[team]),
                    line=dict(width=1.5, color=color_map[team]),
                    hovertemplate=(
                        f"Team: {team}<br>Year: %{{x}}<br>"
                        f"{SUPPLY_TYPE_LABELS[source_type.NAME]}: %{{y:.0f}} m³/year<extra></extra>"
                    ),
                ),
                row=1, col=col,
            )

        for sep in STAGE_SEPARATORS:
            fig.add_vline(
                x=sep,
                line=dict(color=WF_GREY, width=1.5, dash="dash"),
                row=1, col=col,
            )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="Supply Capacity by Type over Time",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )
    fig.update_yaxes(title_text="Supply Capacity [m³/year]", rangemode="tozero", row=1, col=1)
    fig.update_yaxes(title_text="", rangemode="tozero", row=1, col=2)
    fig.update_yaxes(title_text="", rangemode="tozero", row=1, col=3)

    return fig

def _team_active_connections_length_vs_time(team_data: TeamData) -> pd.Series:
    """
    For a team's final (stage-3) system, computes, for each competition year,
    the total length (sum of distance) of all connections that are active,
    across the whole network.
    """
    nc = team_data.final_system

    lengths = {}
    for year in COMPETITION_YEARS:
        ts = pd.Timestamp(year=year, month=1, day=1)

        lengths[year] = sum(
            connection.distance
            for connection in nc._all_connections
            if connection.is_active(when=ts)
        )

    return pd.Series(lengths)

def plot_active_connections_length_vs_time(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots the total length of
    active connections over the competition years, one line per team.
    """
    teams = _participants(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)

    fig = go.Figure()

    for team in teams:
        series = _team_active_connections_length_vs_time(team_data_dict[team])

        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines+markers",
                name=team,
                marker=dict(symbol=symbol_map[team], size=7),
                line=dict(width=1.5),
                hovertemplate=(
                    f"Team: {team}<br>Year: %{{x}}<br>"
                    "Active connections length: %{y:.0f} m<extra></extra>"
                ),
            )
        )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="Active Connections Length over Time",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )
    fig.update_yaxes(
        title_text="Active Connections Length [m]",
        rangemode="tozero",
    )

    return fig

def _team_new_pipes_length_vs_time(team_data: TeamData) -> pd.Series:
    """
    For a team's final (stage-3) system, computes, for each competition
    year, the total length (sum of the parent connection's distance) of all
    pipes installed in that year, across the whole network.
    """
    nc = team_data.final_system

    lengths = {year: 0.0 for year in COMPETITION_YEARS}
    for connection in nc._all_connections:
        for pipe in connection.pipes.values():
            year = pipe.installation_date.year
            if year in lengths:
                lengths[year] += connection.distance

    return pd.Series(lengths)

def plot_new_pipes_length_vs_time(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots the total length of pipes
    installed each competition year, one line per team.
    """
    teams = _participants(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)

    fig = go.Figure()

    for team in teams:
        series = _team_new_pipes_length_vs_time(team_data_dict[team])

        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines+markers",
                name=team,
                marker=dict(symbol=symbol_map[team], size=7),
                line=dict(width=1.5),
                hovertemplate=(
                    f"Team: {team}<br>Year: %{{x}}<br>"
                    "New pipes length: %{y:.0f} m<extra></extra>"
                ),
            )
        )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="New Pipes Length over Time",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )
    fig.update_yaxes(
        title_text="New Pipes Length [m]",
        rangemode="tozero",
    )

    return fig

def _team_active_pumps_vs_time(team_data: TeamData) -> pd.Series:
    """
    For a team's final (stage-3) system, computes, for each competition
    year, the total number of pumps that are active, across all pumping
    stations.
    """
    nc = team_data.final_system

    counts = {}
    for year in COMPETITION_YEARS:
        ts = pd.Timestamp(year=year, month=1, day=1)

        counts[year] = sum(
            1
            for ps in nc._all_pumping_stations
            for pump in ps.pumps.values()
            if pump.is_active(when=ts)
        )

    return pd.Series(counts)

def plot_active_pumps_vs_time(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots the total number of
    active pumps over the competition years, one line per team.
    """
    teams = _participants(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)

    fig = go.Figure()

    for team in teams:
        series = _team_active_pumps_vs_time(team_data_dict[team])

        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines+markers",
                name=team,
                marker=dict(symbol=symbol_map[team], size=7),
                line=dict(width=1.5),
                hovertemplate=(
                    f"Team: {team}<br>Year: %{{x}}<br>"
                    "Active pumps: %{y:.0f}<extra></extra>"
                ),
            )
        )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="Active Pumps over Time",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )
    fig.update_yaxes(
        title_text="Active Pumps [count]",
        rangemode="tozero",
    )

    return fig

def _team_new_pumps_vs_time(team_data: TeamData) -> pd.Series:
    """
    For a team's final (stage-3) system, computes, for each competition
    year, the total number of pumps installed (activated) in that year,
    across all pumping stations.
    """
    nc = team_data.final_system

    counts = {year: 0 for year in COMPETITION_YEARS}
    for ps in nc._all_pumping_stations:
        for pump in ps.pumps.values():
            year = pump.installation_date.year
            if year in counts:
                counts[year] += 1

    return pd.Series(counts)

def plot_new_pumps_vs_time(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots the number of pumps
    installed (activated) each competition year, one line per team.
    """
    teams = _participants(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)

    fig = go.Figure()

    for team in teams:
        series = _team_new_pumps_vs_time(team_data_dict[team])

        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines+markers",
                name=team,
                marker=dict(symbol=symbol_map[team], size=7),
                line=dict(width=1.5),
                hovertemplate=(
                    f"Team: {team}<br>Year: %{{x}}<br>"
                    "New pumps: %{y:.0f}<extra></extra>"
                ),
            )
        )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="New Pumps over Time",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )
    fig.update_yaxes(
        title_text="New Pumps [count]",
        rangemode="tozero",
    )

    return fig

def _team_active_solar_capacity_vs_time(team_data: TeamData) -> pd.Series:
    """
    For a team's final (stage-3) system, computes, for each competition
    year, the total capacity of solar farms that are active, across the
    whole network.
    """
    capacities = {}
    for year in COMPETITION_YEARS:
        ts = pd.Timestamp(year=year, month=1, day=1)

        capacities[year] = sum(
            solar_farm.capacity
            for solar_farm in team_data.solar_farms
            if solar_farm.is_active(when=ts)
        )

    return pd.Series(capacities)

def plot_active_solar_vs_time(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots the total capacity of
    active solar farms over the competition years, one line per team. Teams
    with no solar farms at all are skipped, so they don't appear on the
    plot or in the legend.
    """
    teams = _participants(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)

    fig = go.Figure()

    for team in teams:
        if not team_data_dict[team].solar_farms:
            continue

        series = _team_active_solar_capacity_vs_time(team_data_dict[team])

        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines+markers",
                name=team,
                marker=dict(symbol=symbol_map[team], size=7),
                line=dict(width=1.5),
                hovertemplate=(
                    f"Team: {team}<br>Year: %{{x}}<br>"
                    "Active solar capacity: %{y:.0f} kW<extra></extra>"
                ),
            )
        )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="Active Solar Capacity over Time",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )
    fig.update_yaxes(
        title_text="Active Solar Capacity [kW]",
        rangemode="tozero",
    )

    return fig

def _team_new_solar_capacity_vs_time(team_data: TeamData) -> pd.Series:
    """
    For a team's final (stage-3) system, computes, for each competition
    year, the total capacity of solar farms installed in that year, across
    the whole network.
    """
    capacities = {year: 0.0 for year in COMPETITION_YEARS}
    for solar_farm in team_data.solar_farms:
        year = solar_farm.installation_date.year
        if year in capacities:
            capacities[year] += solar_farm.capacity

    return pd.Series(capacities)

def plot_new_solar_vs_time(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    For each non-reference, completed team, plots the capacity of solar
    farms installed each competition year, one line per team. Teams with no
    solar farms at all are skipped, so they don't appear on the plot or in
    the legend.
    """
    teams = _participants(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)

    fig = go.Figure()

    for team in teams:
        if not team_data_dict[team].solar_farms:
            continue

        series = _team_new_solar_capacity_vs_time(team_data_dict[team])

        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines+markers",
                name=team,
                marker=dict(symbol=symbol_map[team], size=7),
                line=dict(width=1.5),
                hovertemplate=(
                    f"Team: {team}<br>Year: %{{x}}<br>"
                    "New solar capacity: %{y:.0f} kW<extra></extra>"
                ),
            )
        )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="New Solar Capacity over Time",
        showlegend=True,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
    )
    fig.update_yaxes(
        title_text="New Solar Capacity [kW]",
        rangemode="tozero",
    )

    return fig

def plot_optimisations_groups(
        team_data_dict: dict[str, TeamData]
) -> go.Figure:
    """
    Arranges the 7 sub-problem levers on a circle (a heptagon), the first
    lever at the top, the rest following it clockwise. For each pair of
    levers, draws a line whose thickness and color (blue to red) encode
    how many non-reference teams put both levers in the same optimisation
    group, regardless of that group's rank.
    """
    question = QUESTIONS["_levers_groups"]
    assert isinstance(question, LikertQuestion)
    labels = list(question.options.values())
    n = len(labels)

    positions = {
        label: (np.sin(np.radians(k * 360 / n)), np.cos(np.radians(k * 360 / n)))
        for k, label in enumerate(labels)
    }

    teams = _participants(team_data_dict)

    CONNECTIVITY_COLORSCALE = [[0, get_scale(WF_BLUE,10)[0]], [1, WF_BLUE]]
    LINE_WIDTH_SCALE = 1

    pair_counts: dict[tuple[str, str], int] = {
        (a, b): 0
        for i, a in enumerate(labels)
        for b in labels[i + 1:]
    }

    for team in teams:
        groups = team_data_dict[team].survey_response.levers_groups
        for members in groups.values():
            ordered_members = sorted(members, key=labels.index)
            for a, b in itertools.combinations(ordered_members, 2):
                pair_counts[(a, b)] += 1

    max_count = max(pair_counts.values(), default=0)

    fig = go.Figure()

    for (a, b), count in pair_counts.items():
        if count == 0:
            continue
        x0, y0 = positions[a]
        x1, y1 = positions[b]
        color = sample_colorscale(CONNECTIVITY_COLORSCALE, count / max_count)[0]
        fig.add_trace(
            go.Scatter(
                x=[x0, x1], y=[y0, y1],
                mode="lines",
                line=dict(color=color, width=count * LINE_WIDTH_SCALE),
                hovertemplate=f"{a} & {b}<br>{count} teams<extra></extra>",
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(
                colorscale=CONNECTIVITY_COLORSCALE,
                cmin=0,
                cmax=max_count,
                color=[0],
                showscale=True,
                colorbar=dict(
                    title="Count",
                    tickvals=list(range(0, max_count + 1,2)),
                    len=0.65,
                ),
            ),
            showlegend=False,
        )
    )

    for label, (x, y) in positions.items():
        fig.add_annotation(
            x=x, y=y,
            text=label,
            showarrow=False,
            font=font('annotation'),
            bgcolor="white",
            bordercolor=WF_GREY,
            borderwidth=1,
            borderpad=4,
        )

    fig = apply_journal_formatting(fig=fig, column='single', frac=1.0, ratio=1.1)
    fig.update_layout(
        title="",
        showlegend=False,
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0,
            pad=0,
        ),
    )
    fig.update_xaxes(visible=False, range=[-1.5, 1.5])
    fig.update_yaxes(visible=False, range=[-1.5, 1.5], scaleanchor="x", scaleratio=1)
    fig.add_annotation(
        xref="paper", x=0, xanchor="left",
        yref="paper", y=.15, yanchor="top",
        text=(
            "WRS = Water Resources System; WDS = Water Distribution System;<br>"
            "NRW = Non-Revenue Water; WPA = Water Pricing Adjustment."
        ),
        font=font("annotation"),
        align="left",
        showarrow=False,
    )

    return fig

def _team_nrw_mitigation_budget_allocated_vs_time(team_data: TeamData) -> pd.Series:
    """
    For each competition year, computes the team's total NRW mitigation
    budget allocated for that year (from the 'nrw_mitigation' policy of the
    masterplan of the corresponding stage), summed across all water
    utilities.
    """
    water_utilities = [f"WU{x:02d}" for x in range(1, 11)]

    budgets = {}
    for stage in STAGES:
        ms = team_data.masterplan(stage=stage)
        for year in range(2000 + 25 * stage, 2025 + 25 * stage):
            ts = pd.Timestamp(year=year, month=1, day=1)
            budgets[ts] = sum(
                ms.water_utility_policies(water_utility=wu, year=year)["nrw_mitigation"]["budget"]
                for wu in water_utilities
            )

    return pd.Series(budgets).sort_index()

def _team_nrw_mitigation_budget_spent_vs_time(team_data: TeamData) -> pd.Series:
    """
    For each competition year, computes the team's total NRW mitigation
    budget actually spent, summed across all water utilities.
    """
    start = pd.Timestamp(year=COMPETITION_YEARS[0], month=1, day=1)
    end = pd.Timestamp(year=COMPETITION_YEARS[-1], month=1, day=1)

    return team_data.nrw_mitigation_budget_spent.sum(axis=1).loc[start:end]

def _team_total_ghg_emissions_vs_time(team_data: TeamData) -> pd.Series:
    """
    For each competition year, computes the team's total GHG emissions
    (operational + embedded), summed across all water utilities.
    """
    start = pd.Timestamp(year=COMPETITION_YEARS[0], month=1, day=1)
    end = pd.Timestamp(year=COMPETITION_YEARS[-1], month=1, day=1)

    total = team_data.operations_ghg_emissions.sum(axis=1) + team_data.embedded_ghg_emissions.sum(axis=1)
    return total.loc[start:end]

def _team_embedded_ghg_emissions_vs_time(team_data: TeamData) -> pd.Series:
    """
    For each competition year, the team's total embedded GHG emissions,
    summed across all water utilities.
    """
    start = pd.Timestamp(year=COMPETITION_YEARS[0], month=1, day=1)
    end = pd.Timestamp(year=COMPETITION_YEARS[-1], month=1, day=1)

    return team_data.embedded_ghg_emissions.sum(axis=1).loc[start:end]

def _team_operational_ghg_emissions_vs_time(team_data: TeamData) -> pd.Series:
    """
    For each competition year, the team's total operational GHG emissions,
    summed across all water utilities.
    """
    start = pd.Timestamp(year=COMPETITION_YEARS[0], month=1, day=1)
    end = pd.Timestamp(year=COMPETITION_YEARS[-1], month=1, day=1)

    return team_data.operations_ghg_emissions.sum(axis=1).loc[start:end]

def _reference_pipe_emission_factors_vs_time(team_data_dict: dict[str, TeamData]) -> dict[str, pd.Series]:
    """
    New-pipe embodied emission factors (PVC and Welded steel options), exogenous
    and identical for every team, read off any team's final system (here
    TEAM00's), expressed relative to their 2024 value. Each pipe diameter of
    a given type follows the same relative reduction, hence normalizing lets
    a single line per type stand in for all diameters.
    """
    BASELINE = pd.Timestamp(year=2024, month=1, day=1)

    nc = team_data_dict[REFERENCE_TEAM].final_system
    pipe_ef = nc.pipe_options_db[PipeOptionsDB.EMISSION]
    pvc_id, steel_id = pipe_ef.columns[0], pipe_ef.columns[-1]

    def _relative_to_2024(series: pd.Series) -> pd.Series:
        baseline = float(series.asof(BASELINE))
        return series.loc[series.index.year.isin(COMPETITION_YEARS)] / baseline

    return {
        "PVC pipe": _relative_to_2024(pipe_ef[pvc_id]),
        "Steel pipe": _relative_to_2024(pipe_ef[steel_id]),
    }

def _reference_grid_emission_factor_vs_time(team_data_dict: dict[str, TeamData]) -> pd.Series:
    """
    National grid emission factor, exogenous and identical for every team,
    read off any team's final system (here TEAM00's).
    """
    nc = team_data_dict[REFERENCE_TEAM].final_system
    grid_ef = nc.energy_sys[EnergySysDB.EMISS_FACTOR].iloc[:, 0]
    return grid_ef.loc[grid_ef.index.year.isin(COMPETITION_YEARS)]

def plot_nrw_analysis_vs_time_line(
        team_data_dict: dict[str, TeamData],
        ghost: bool = False,
        presentation_mode: bool = False,
        nominal_values: bool = True,
    ) -> go.Figure:
    """
    Three-row, shared-x view of NRW-related metrics over the competition
    years: non-revenue water volume, average distribution network age, and
    NRW mitigation budget (summed across water utilities), one row each.
    Each row gets its own legend, positioned to its right.

    With nominal_values=False, yearly budgets are deflated to constant 2024
    euros using TEAM00's cumulative inflation for each calendar year.
    The NRW volume and network age panels are unchanged.

    In ghost mode (anonymized) every team's line is drawn thin, with the
    cross-team median overlaid as a thick solid line, one color per row (see
    plot_supply_and_demand_vs_time_ghost_line); each row's legend shows only
    its median (row 3 shows both the allocated and spent medians). Otherwise
    each team keeps its own color/marker across all rows and each row's
    legend lists the teams (row 3 also adds a small legend explaining the
    allocated/spent dash convention).
    """
    teams = _finishers(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)
    color_map = _team_color_map(team_data_dict)

    ROW_TITLES = ["Yearly Non-Revenue Water", "Average IDN's age", "NRW Mitigation Expenditure"]
    ROW_COLORS = [WF_BLUE, WF_ORANGE, WF_GREEN]
    ROW_HOVER_LABELS = ["NRW", "Mean Network Age", "NRW Mitigation Expenditure"]
    cost_unit = "€" if nominal_values else "€<sub>2024</sub>"
    ROW_HOVER_UNITS = ["m³/year", "years", cost_unit]
    ROW_LEGENDS = ["legend", "legend2", "legend3"]
    MEDIAN_LINE_WIDTH = 3

    series_by_row = [
        {team: _team_nrw_vs_time(team_data_dict[team]) for team in teams},
        {team: _team_avg_network_age_vs_time(team_data_dict[team]) for team in teams},
    ]
    budget_allocated = {team: _team_nrw_mitigation_budget_allocated_vs_time(team_data_dict[team]) for team in teams}
    budget_spent = {team: _team_nrw_mitigation_budget_spent_vs_time(team_data_dict[team]) for team in teams}
    if not nominal_values and teams:
        price_index = _price_index_2024_base(team_data_dict[REFERENCE_TEAM].final_system)
        for budgets in (budget_allocated, budget_spent):
            for team, series in budgets.items():
                budgets[team] = series * 100.0 / price_index.loc[series.index.year].to_numpy()

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        subplot_titles=ROW_TITLES if presentation_mode else None,
        vertical_spacing=0.07,
    )

    # Rows 1-2: a single line per team (NRW, avg. network age)
    for row, (row_color, team_series, hover_label, hover_unit) in enumerate(
        zip(ROW_COLORS, series_by_row, ROW_HOVER_LABELS, ROW_HOVER_UNITS), start=1
    ):
        if ghost:
            light_color = make_opaque(row_color, 0.25)
            values = pd.DataFrame({team: s for team, s in team_series.items()})
            median = values.median(axis=1)

            fig.add_trace(
                go.Scatter(
                    x=median.index.year,
                    y=median.values,
                    mode="lines",
                    name="Median",
                    legend=ROW_LEGENDS[row - 1],
                    showlegend=True,
                    line=dict(color=row_color, width=MEDIAN_LINE_WIDTH),
                    hovertemplate=(
                        f"Year: %{{x}}<br>Median {hover_label}: %{{y:.1f}} {ROW_HOVER_UNITS[row - 1]}<extra></extra>"
                    ),
                ),
                row=row, col=1,
            )

            for team in teams:
                fig.add_trace(
                    go.Scatter(
                        x=values.index.year,
                        y=values[team],
                        mode="lines",
                        name="Individual Teams" if team == teams[0] else None,
                        line=dict(color=light_color, width=1),
                        legend=ROW_LEGENDS[row - 1],
                        showlegend=team == teams[0],
                        hoverinfo="skip",
                    ),
                    row=row, col=1,
                )

        else:
            for team in teams:
                series = team_series[team]
                fig.add_trace(
                    go.Scatter(
                        x=series.index.year,
                        y=series.values,
                        mode="lines+markers",
                        name=team,
                        legendgroup=team,
                        legend=ROW_LEGENDS[row - 1],
                        showlegend=True,
                        marker=dict(symbol=symbol_map[team], size=7, color=color_map[team]),
                        line=dict(width=1.5, color=color_map[team]),
                        hovertemplate=(
                            f"Team: {team}<br>Year: %{{x}}<br>"
                            f"{hover_label}: %{{y:.1f}} {ROW_HOVER_UNITS[row - 1]}<extra></extra>"
                        ),
                    ),
                    row=row, col=1,
                )

    # Row 3: NRW mitigation budget, allocated (dashed) vs. actually spent (solid)
    row = 3
    row_color = ROW_COLORS[row - 1]
    hover_unit = ROW_HOVER_UNITS[row - 1]

    if ghost:
        light_color = make_opaque(row_color, 0.25)
        allocated_values = pd.DataFrame(budget_allocated)
        spent_values = pd.DataFrame(budget_spent)
        allocated_median = allocated_values.median(axis=1)
        spent_median = spent_values.median(axis=1)

        # fig.add_trace(
        #     go.Scatter(
        #         x=allocated_median.index.year,
        #         y=allocated_median.values,
        #         mode="lines",
        #         name="Median (allocated)",
        #         legend=ROW_LEGENDS[row - 1],
        #         showlegend=True,
        #         line=dict(color=row_color, width=MEDIAN_LINE_WIDTH, dash="dash"),
        #         hovertemplate=f"Year: %{{x}}<br>Median allocated budget: %{{y:.1f}} {hover_unit}<extra></extra>",
        #     ),
        #     row=row, col=1,
        # )
        fig.add_trace(
            go.Scatter(
                x=spent_median.index.year,
                y=spent_median.values,
                mode="lines",
                #name="Median (spent)",
                name="Median",
                legend=ROW_LEGENDS[row - 1],
                showlegend=True,
                line=dict(color=row_color, width=MEDIAN_LINE_WIDTH, dash="solid"),
                hovertemplate=f"Year: %{{x}}<br>Median spent budget: %{{y:.1f}} {hover_unit}<extra></extra>",
            ),
            row=row, col=1,
        )

        for team in teams:
            # fig.add_trace(
            #     go.Scatter(
            #         x=allocated_values.index.year,
            #         y=allocated_values[team],
            #         mode="lines",
            #         line=dict(color=light_color, width=1, dash="dash"),
            #         name="Individual Teams<br>(allocated)" if team == teams[0] else None,
            #         legend=ROW_LEGENDS[row - 1],
            #         showlegend=team==teams[0],
            #         hoverinfo="skip",
            #     ),
            #     row=row, col=1,
            # )
            fig.add_trace(
                go.Scatter(
                    x=spent_values.index.year,
                    y=spent_values[team],
                    mode="lines",
                    line=dict(color=light_color, width=1, dash="solid"),
                    #name="Individual Teams<br>(spent)" if team == teams[0] else None,
                    name="Individual Teams" if team == teams[0] else None,
                    legend=ROW_LEGENDS[row - 1],
                    showlegend=team==teams[0],
                    hoverinfo="skip",
                ),
                row=row, col=1,
            )
        
    else:
        for team in teams:
            allocated = budget_allocated[team]
            spent = budget_spent[team]

            # fig.add_trace(
            #     go.Scatter(
            #         x=allocated.index.year,
            #         y=allocated.values,
            #         mode="lines",
            #         name=team,
            #         legendgroup=team,
            #         showlegend=False,
            #         marker=dict(symbol=symbol_map[team], size=7, color=color_map[team]),
            #         line=dict(width=1.5, color=color_map[team], dash="dash"),
            #         hovertemplate=(
            #             f"Team: {team}<br>Year: %{{x}}<br>"
            #             f"Allocated budget: %{{y:.1f}} {hover_unit}<extra></extra>"
            #         ),
            #     ),
            #     row=row, col=1,
            # )
            fig.add_trace(
                go.Scatter(
                    x=spent.index.year,
                    y=spent.values,
                    mode="lines+markers",
                    name=team,
                    legendgroup=team,
                    legend=ROW_LEGENDS[row - 1],
                    showlegend=True,
                    marker=dict(symbol=symbol_map[team], size=7, color=color_map[team]),
                    line=dict(width=1.5, color=color_map[team], dash="solid"),
                    hovertemplate=(
                        f"Team: {team}<br>Year: %{{x}}<br>"
                        f"Spent budget: %{{y:.1f}} {hover_unit}<extra></extra>"
                    ),
                ),
                row=row, col=1,
            )

        # Legend entries for the dash meaning (allocated vs. spent), shared across teams
        # fig.add_trace(
        #     go.Scatter(
        #         x=[None], y=[None],
        #         mode="lines",
        #         name="Allocated",
        #         legendgroup="dash",
        #         legendgrouptitle_text="NRW Mitigation Budget",
        #         legend=ROW_LEGENDS[row - 1],
        #         showlegend=True,
        #         line=dict(color=WF_GREY, width=1.5, dash="dash"),
        #     ),
        #     row=row, col=1,
        # )
        # fig.add_trace(
        #     go.Scatter(
        #         x=[None], y=[None],
        #         mode="lines",
        #         name="Spent",
        #         legendgroup="dash",
        #         legend=ROW_LEGENDS[row - 1],
        #         showlegend=True,
        #         line=dict(color=WF_GREY, width=1.5, dash="solid"),
        #     ),
        #     row=row, col=1,
        # )

    for row in (1, 2, 3):
        for sep in STAGE_SEPARATORS:
            fig.add_vline(
                x=sep,
                line=dict(color=WF_GREY, width=1.5, dash="dash"),
                row=row, col=1,
            )

    fig = apply_journal_formatting(fig=fig, column='full', frac=0.9, ratio=1.4)
    if not presentation_mode:
        SUBPLOT_TITLES = ['(a)', '(b)', '(c)']
        for i, label in enumerate(SUBPLOT_TITLES):
            suffix = '' if i == 0 else str(i + 1)  # '', '2', '3' matches Plotly's axis naming
            fig.add_annotation(
                xref=f'x{suffix} domain',
                yref=f'y{suffix} domain',
                x=0, y=1.01,           # x=0 → left edge; y=1.05 → just above the plot
                text=label,
                showarrow=False,
                font=font('legend_title'),
                xanchor='left',
                yanchor='bottom'
            )

    # One legend box per row, right of the plot, top-aligned with that row
    row_y_domains = [fig.layout.yaxis.domain, fig.layout.yaxis2.domain, fig.layout.yaxis3.domain]
    fig.update_layout(**{
        legend_name: dict(
            y=domain[1],
            yanchor="top",
            x=1.01,
            xanchor="left",
            font=font('legend'),
        )
        for legend_name, domain in zip(ROW_LEGENDS, row_y_domains)
    })

    fig.update_layout(
        title=None,
        showlegend=True,
        margin=dict(
            l=0,
            r=90,
            t=30,
            b=50,
            pad=0,
        ),
    )
    fig.update_xaxes(
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
        row=1, col=1,
    )
    fig.update_xaxes(
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
        row=2, col=1,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
        row=3, col=1,
    )

    fig.update_yaxes(
        title_text="Non-Revenue<br>Water [m³/year]",
        rangemode="tozero",
        row=1, col=1,
    )

    class_bounds = [c.demand_factor_bounds[1] for c in NRWClass if np.isfinite(c.demand_factor_bounds[1])]
    tickvals = [0.] + class_bounds
    ticktext = ["0"] + [f"{bound:.0f} ({c.name}↓)" for c, bound in zip(NRWClass, class_bounds)]
    ticktext[-1] = "   (E↑)<br>60 (D↓)<br>" # make sure we have the last class there too.
    tickvals += [95.0]
    ticktext += ["95"]

    # We cut off the diverging lines to 75 years, but we report where they end up.
    fig.update_yaxes(
        title_text="Mean Network Age<br>[years] (NRW Class)",
        range=[23, 96],
        tickmode="array",
        tickvals=tickvals,
        ticktext=ticktext,
        row=2, col=1,
    )
    # fig.add_annotation(
    #     xref="x2 domain",
    #     yref="y2 domain",
    #     x=0.72, # just after the second stage
    #     y=0.98,
    #     text="↗in 2099: 95 years",
    #     showarrow=False,
    #     font=font('annotation'),
    #     xanchor='left',
    #     yanchor='middle'
    # )

    fig.update_yaxes(
        title_text=f"NRW Mitigation<br>Expenditure<br>[{cost_unit}/year]",
        rangemode="tozero",
        row=3, col=1,
    )

    return fig

def _add_team_emissions_row(
        fig: go.Figure,
        row: int,
        teams: list[str],
        series_map: dict[str, pd.Series],
        symbol_map: dict[str, str],
        color_map: dict[str, str],
        ghost: bool,
        legend: str,
) -> None:
    """
    Adds one row's worth of per-team GHG emissions traces (on the primary
    y-axis) to a shared-x subplot figure: in ghost mode a thin line per
    team plus a thick WF_BLUE median, otherwise one line per team in its
    own color/marker (see plot_nrw_analysis_vs_time_line).
    """
    MEDIAN_LINE_WIDTH = 3

    if ghost:
        light_blue = make_opaque(WF_BLUE, 0.25)
        values = pd.DataFrame(series_map)
        median = values.median(axis=1)

        fig.add_trace(
            go.Scatter(
                x=median.index.year,
                y=median.values,
                mode="lines",
                name="Median",
                legend=legend,
                line=dict(color=WF_BLUE, width=MEDIAN_LINE_WIDTH),
                hovertemplate="Year: %{x}<br>Median GHG emissions: %{y:.1f} ktCO2eq<extra></extra>",
            ),
            row=row, col=1,
        )

        for team in teams:
            fig.add_trace(
                go.Scatter(
                    x=values.index.year,
                    y=values[team],
                    mode="lines",
                    name="Individual Teams" if team == teams[0] else None,
                    line=dict(color=light_blue, width=1),
                    legend=legend,
                    showlegend=team == teams[0],
                    hoverinfo="skip",
                ),
                row=row, col=1,
            )
    else:
        for team in teams:
            series = series_map[team]
            fig.add_trace(
                go.Scatter(
                    x=series.index.year,
                    y=series.values,
                    mode="lines+markers",
                    name=team,
                    legendgroup=team,
                    legend=legend,
                    marker=dict(symbol=symbol_map[team], size=7, color=color_map[team]),
                    line=dict(width=1.5, color=color_map[team]),
                    hovertemplate=(
                        f"Team: {team}<br>Year: %{{x}}<br>GHG emissions: %{{y:.1f}} ktCO2eq<extra></extra>"
                    ),
                ),
                row=row, col=1,
            )

def plot_emissions_and_decarb(
        team_data_dict: dict[str, TeamData],
        ghost: bool = False,
        presentation_mode: bool = False,
    ) -> go.Figure:
    """
    Three-row, shared-x, dual-y-axis-per-row view over the competition
    years: total, embedded, and operational GHG emissions, one row each.
    Each row's primary axis shows the per-team emissions (in ghost mode,
    anonymized as a thin line per team plus a thick WF_BLUE median;
    otherwise one line per team in its own color/marker, see
    plot_nrw_analysis_vs_time_line). Rows 2 and 3 also show, on their
    secondary axis, the exogenous emission factors driving that component:
    the new-pipe embodied emission factors (PVC and Welded steel, WF_GREEN,
    one dash style each), each expressed relative to its 2024 value since
    every pipe diameter of a given type follows the same relative
    reduction, for embedded emissions; and the national grid emission
    factor (WF_ORANGE), in its native units, for operational emissions.
    """
    teams = _finishers(team_data_dict)
    symbol_map = _team_symbol_map(team_data_dict)
    color_map = _team_color_map(team_data_dict)

    EF_LINE_WIDTH = 3
    PIPE_EF_DASHES = ["dash", "dot"]
    ROW_LEGENDS = ["legend", "legend2", "legend3"]

    series_by_row = {
        1: {team: _team_total_ghg_emissions_vs_time(team_data_dict[team]) / 1e6 for team in teams},
        2: {team: _team_embedded_ghg_emissions_vs_time(team_data_dict[team]) / 1e6 for team in teams},
        3: {team: _team_operational_ghg_emissions_vs_time(team_data_dict[team]) / 1e6 for team in teams},
    }

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        specs=[[{"secondary_y": False}], [{"secondary_y": True}], [{"secondary_y": True}]],
        vertical_spacing=0.06,
    )

    for row in (1, 2, 3):
        _add_team_emissions_row(
            fig, row, teams, series_by_row[row], symbol_map, color_map, ghost, ROW_LEGENDS[row - 1]
        )

    pipe_efs = _reference_pipe_emission_factors_vs_time(team_data_dict)
    for (name, series), dash in zip(pipe_efs.items(), PIPE_EF_DASHES):
        fig.add_trace(
            go.Scatter(
                x=series.index.year,
                y=series.values,
                mode="lines",
                name=name,
                legend=ROW_LEGENDS[1],
                line=dict(color=WF_GREEN, width=EF_LINE_WIDTH, dash=dash),
                hovertemplate=f"Year: %{{x}}<br>{name} emission factor (rel. to 2024): %{{y:.2f}}<extra></extra>",
            ),
            row=2, col=1, secondary_y=True,
        )

    grid_ef = _reference_grid_emission_factor_vs_time(team_data_dict)
    fig.add_trace(
        go.Scatter(
            x=grid_ef.index.year,
            y=grid_ef.values,
            mode="lines",
            name="Grid",
            legend=ROW_LEGENDS[2],
            line=dict(color=WF_ORANGE, width=EF_LINE_WIDTH, dash="dash"),
            hovertemplate="Year: %{x}<br>Grid emission factor: %{y:.3f} tCO2eq/kWh<extra></extra>",
        ),
        row=3, col=1, secondary_y=True,
    )

    for row in (1, 2, 3):
        for sep in STAGE_SEPARATORS:
            fig.add_vline(
                x=sep,
                line=dict(color=WF_GREY, width=1.5, dash="dash"),
                row=row, col=1,
            )

    fig = apply_journal_formatting(fig=fig, column='full', frac=0.9, ratio=1.3)

    # One legend box per row, right of the plot, top-aligned with that row
    row_y_domains = [fig.layout.yaxis.domain, fig.layout.yaxis2.domain, fig.layout.yaxis4.domain]
    fig.update_layout(**{
        legend_name: dict(
            y=domain[1],
            yanchor="top",
            x=1.16,
            xanchor="left",
            font=font('legend'),
        )
        for legend_name, domain in zip(ROW_LEGENDS, row_y_domains)
    })

    fig.add_annotation(
        xref="paper", yref="paper",
        x=-0.2, y=0.5,
        text="GHG Emissions [ktCO2eq/year]",
        showarrow=False,
        textangle=-90,
        font=font('legend_title'),
        xanchor="center",
        yanchor="middle",
    )
    if not presentation_mode:
        SUBPLOT_TITLES = ['(a)', '(b)', '(c)']
        for i, label in enumerate(SUBPLOT_TITLES):
            suffix = '' if i == 0 else str(i + 1)  # '', '2' matches Plotly's axis naming
            fig.add_annotation(
                xref=f'x{suffix} domain',
                yref=f'y{suffix} domain',
                x=0, y=1.01,           # x=0 → left edge; y=1.05 → just above the plot
                text=label,
                showarrow=False,
                font=font('legend_title'),
                xanchor='left',
                yanchor='bottom'
            )

    fig.update_layout(
        title="" if not presentation_mode else "GHG Emissions and Decarbonisation",
        showlegend=True,
        margin=dict(
            l=100,
            r=150,
            t=30 if presentation_mode else 30,
            b=10,
            pad=0,
        ),
    )
    fig.update_xaxes(
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
        row=1, col=1,
    )
    fig.update_xaxes(
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
        row=2, col=1,
    )
    fig.update_xaxes(
        title_text="Year",
        range=[COMPETITION_YEARS[0], COMPETITION_YEARS[-1]],
        dtick=5,
        row=3, col=1,
    )

    fig.update_yaxes(title_text="Total", rangemode="tozero", row=1, col=1)
    fig.update_yaxes(title_text="Embedded", rangemode="tozero", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Pipe Emission Factor<br>(rel. to 2024)", rangemode="tozero", showgrid=False, row=2, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Operational", rangemode="tozero", row=3, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Grid Emission Factor<br>[tCO2eq/kWh]", rangemode="tozero", showgrid=False, row=3, col=1, secondary_y=True)

    return fig

def plot_inflation_vs_time(
        team_data_dict: dict[str, TeamData],
        trends: bool = False,
        presentation_mode: bool = False,
) -> go.Figure:
    """
    Single line (WF_BLUE) of national inflation over historical and
    competition years, exogenous and identical for every team, read off the
    reference team's final system (see _reference_grid_emission_factor_vs_time).

    If trends is True, for each stage that has a following stage a dashed
    trend line is fit (least-squares) on that stage's own values and
    extrapolated across the next stage's years: "Trend on historical" fit on
    the historical years and drawn across stage 1, "Trend on stage 1" fit on
    stage 1 and drawn across stage 2, "Trend on stage 2" fit on stage 2 and
    drawn across stage 3. Stage 3 has no following stage, so it gets no
    trend line.
    """
    TREND_DASHES = ["dash", "dot", "dashdot"]
    TREND_COLOR = make_opaque(WF_BLUE, 0.6)

    nc = team_data_dict[REFERENCE_TEAM].final_system
    infl = nc.inflation
    infl = infl.loc[infl.index.year.isin(ALL_YEARS)].sort_index()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=infl.index.year,
            y=infl.values,
            mode="lines",
            name="Inflation",
            line=dict(color=WF_BLUE, width=2.5),
            hovertemplate="Year: %{x}<br>Inflation: %{y:.2f}%<extra></extra>",
        )
    )

    if trends:
        stage_bounds = STAGE_SEPARATORS + [ALL_YEARS[-1] + 1]
        windows = [(ALL_YEARS[0], stage_bounds[0])] + [
            (stage_bounds[i], stage_bounds[i + 1]) for i in range(len(stage_bounds) - 1)
        ]
        window_names = ["historical"] + [f"stage {s}" for s in STAGES]

        for (start, end), (next_start, next_end), name, dash in zip(
            windows, windows[1:], window_names, TREND_DASHES
        ):
            window_series = infl.loc[(infl.index.year >= start) & (infl.index.year < end)]
            slope, intercept = np.polyfit(window_series.index.year, window_series.values, 1)

            next_years = np.arange(next_start, next_end)
            trend_values = slope * next_years + intercept

            fig.add_trace(
                go.Scatter(
                    x=next_years,
                    y=trend_values,
                    mode="lines",
                    name=f"Trend on {name}",
                    line=dict(color=TREND_COLOR, width=2, dash=dash),
                    hovertemplate=f"Year: %{{x}}<br>Trend on {name}: %{{y:.2f}}%<extra></extra>",
                )
            )

    for sep in STAGE_SEPARATORS:
        fig.add_vline(
            x=sep,
            line=dict(color=WF_GREY, width=1.5, dash="dash"),
        )

    fig = apply_journal_formatting(fig=fig, column='full', frac=1, ratio=1.8)
    fig.update_layout(
        title="" if not presentation_mode else "Inflation over Time",
        showlegend=True,
        margin=dict(
            l=5,
            r=5,
            t=30 if presentation_mode else 5,
            b=5,
            pad=0,
        ),
    )
    fig.update_xaxes(
        title_text="Year",
        range=[ALL_YEARS[0], ALL_YEARS[-1]],
        dtick=10,
    )
    fig.update_yaxes(
        title_text="Inflation [%]",
    )

    return fig

def plot_staged_planning_concept(
    seed: int = 128,
    color_hist: str = WF_NAVY,
    color_plan: str = WF_GREEN,
    color_real: str = WF_BLUE,
    color_grid: str = WF_GREY,
) -> go.Figure:
    """Return a plotly Figure illustrating the plan-execute-observe-adapt cycle.

    Stage 1 plan: drafted in 2025, 5-year resolution, horizon to 2060
    (the part after 2050 is superseded). Stage 2 plan: drafted in 2050
    from the realised state, uneven resolution, horizon to 2085.
    Hexagrams mark interventions, hashes mark policy changes.
    Uses full-width journal formatting unless width or height is overridden.
    """
    rng = np.random.default_rng(seed)
    fig = go.Figure()
    stage_end = 2050

    # ---------------- historical period ----------------
    t_hist = np.linspace(2000, 2025, 300)
    y_hist = (7.2 - 2.4 * ((t_hist - 2000) / 25) ** 1.3
              + 0.18 * np.sin(t_hist * 2.4) + rng.normal(0, 0.05, t_hist.size))
    y0 = y_hist[-1]
    fig.add_trace(go.Scatter(x=t_hist, y=y_hist, mode="lines",
                             line=dict(color=color_hist, width=1.8),
                             name="Observed"))

    # ---------------- stage 1 plan ----------------
    plan1_t = np.arange(2025, 2061, 5)
    plan1_y = np.array([y0, 4.45, 4.55, 4.95, 5.45, 6.0, 6.55, 7.1])
    node = dict(symbol="circle", size=9, color="white",
                line=dict(color=color_plan, width=2))
    inside = plan1_t <= stage_end
    fig.add_trace(go.Scatter(x=plan1_t[inside], y=plan1_y[inside], mode="lines+markers",
                             line=dict(color=color_plan, width=2.2), marker=node,
                             name="Planned"))
    after = plan1_t >= stage_end
    fig.add_trace(go.Scatter(x=plan1_t[after], y=plan1_y[after], mode="lines+markers",
                             line=dict(color=color_plan, width=2.2, dash="dash"),
                             marker=node, opacity=0.45, name="Planned, superseded"))

    # realised performance during stage 1
    t_real = np.linspace(2025, stage_end, 260)
    y_real = (np.interp(t_real, plan1_t, plan1_y) - 0.9 * ((t_real - 2025) / 25) ** 1.4
              + 0.12 * np.sin(t_real * 3.1) + rng.normal(0, 0.04, t_real.size))
    y_real[0] = y0
    y1 = y_real[-1]
    fig.add_trace(go.Scatter(x=t_real, y=y_real, mode="lines",
                             line=dict(color=color_real, width=1.8), name="Realised"))

    # ---------------- stage 2 plan ----------------
    plan2_t = np.array([2050, 2055, 2060, 2070, 2085])
    plan2_y = np.array([y1, y1 + 0.05, y1 + 0.1, y1 + 0.85, y1 + 1.4])
    fig.add_trace(go.Scatter(x=plan2_t, y=plan2_y, mode="lines+markers",
                             line=dict(color=color_plan, width=2.2), marker=node,
                             opacity=0.8, showlegend=False))

    # ---------------- lever stacks ----------------
    stacks = {}  # opacity -> {"int": ([x], [y]), "pol": ([x], [y])}

    def lever_stack(x, y, n_int, n_pol, alpha=1.0):
        group = stacks.setdefault(alpha, {"int": ([], []), "pol": ([], [])})
        yy = y + 0.38
        for key, n in (("int", n_int), ("pol", n_pol)):
            for _ in range(n):
                group[key][0].append(x)
                group[key][1].append(yy)
                yy += 0.27

    for (n_i, n_p), x, y in zip([(2, 2), (3, 0), (4, 1), (1, 0), (2, 1)],
                                plan1_t[:5], plan1_y[:5]):
        lever_stack(x, y, n_i, n_p)
    for (n_i, n_p), x, y in zip([(1, 1), (2, 0)], plan1_t[-2:], plan1_y[-2:]):
        lever_stack(x, y, n_i, n_p, alpha=0.4)
    for (n_i, n_p), x, y in zip([(3, 2), (1, 0), (2, 1), (1, 0), (2, 0)], plan2_t, plan2_y):
        base = max(y, plan1_y[5]) if x == stage_end else y
        lever_stack(x, base, n_i, n_p, alpha=0.8)

    for alpha, group in stacks.items():
        for key, symbol, size in (("int", "hexagram", 8), ("pol", "hash-open", 8)):
            xs, ys = group[key]
            fig.add_trace(go.Scatter(
                x=xs, y=ys, mode="markers", opacity=alpha, showlegend=False,
                hoverinfo="skip",
                marker=dict(symbol=symbol, size=size, color=color_plan,
                            line=dict(color=color_plan, width=1.5))))

    # legend entries for the lever symbols
    for name, symbol, size in (("Intervention", "hexagram", 7),
                               ("Policy update", "hash-open", 7)):
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers", name=name,
            marker=dict(symbol=symbol, size=size, color=color_plan,
                        line=dict(color=color_plan, width=1.5))))

    # ---------------- stage boundaries and decision points ----------------
    for x in (2000, 2025, 2050, 2075, 2100):
        fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1, yref="paper",
                      line=dict(color=color_grid, width=1.5, dash="dash"), opacity=1, layer="below")
    for x, y in ((2025, y0), (2050, y1 )):
        fig.add_shape(type="line", x0=x, x1=x, y0=y - 0.55, y1=y + 0.55,
                      line=dict(color=color_grid, width=7), opacity=0.5, layer="below")

    def interval(x0, x1, y, label, color, h=0.025, arrow=False):
        if arrow:
            fig.add_annotation(
                x=x1, y=y, xref="x", yref="paper",
                ax=x0, ay=0, axref="x", ayref="pixel",
                text="", showarrow=True, arrowhead=2,
                arrowwidth=1.6, arrowcolor=color,
            )
        else:
            fig.add_shape(type="line", xref="x", yref="paper",
                          x0=x0, x1=x1, y0=y, y1=y,
                          line=dict(color=color, width=1.6))
        for endpoint in (x0, x1):
            fig.add_shape(type="line", xref="x", yref="paper",
                            x0=endpoint, x1=endpoint, y0=y - h, y1=y + h,
                            line=dict(color=color, width=1.6))
        fig.add_annotation(x=x0, #(x0 + x1) / 2,
                              xanchor="left",
                           y=y, yref="paper", yanchor="bottom",
                           text=label, showarrow=False, yshift=5,
                           font=dict(**font('annotation'), color=color))

    interval(2025, 2050, 0.10, "Stage period", color_real)
    interval(2025, 2060, 0.95, "Plan horizon", color_plan, arrow=True)
    interval(2025, 2030, 0.85, "Plan resolution", color_plan, h=0.02)

    # ---------------- period labels below the axis ----------------
    for x, label in ((2012.5, "Historical"), (2037.5, "Stage 1"),
                     (2062.5, "Stage 2"), (2084, "Stage 3")):
        fig.add_annotation(x=x, y=-0.09, yref="paper", yanchor="top", text=label,
                           showarrow=False, font=font('annotation'))

    # ---------------- layout ----------------
    fig = apply_journal_formatting(fig=fig, column='full', frac=0.7, ratio=1.2)
    fig.update_layout(
        margin=dict(l=5, r=5, t=20, b=50, pad=0),
        showlegend=True,
        legend=dict(x=0.5, y=-0.3, xanchor="center", yanchor="top",
                    orientation="h", entrywidth=0.33, entrywidthmode="fraction",
                    font=font('tick'),
                    bgcolor="white", bordercolor=color_grid, borderwidth=1),
        xaxis=dict(range=[1999, 2100], tickvals=[2000, 2025, 2050, 2075, 2100],
                   title=dict(text="Battle of the Water Futures Timeline", standoff=25),
                   showline=True, linecolor=color_grid, linewidth=1,
                   ticks="outside", tickcolor=color_grid,
                   showgrid=True, gridcolor=WF_LIGHTGREY, gridwidth=1,
                   minor=dict(dtick=5, tick0=2000, showgrid=True,
                              gridcolor=WF_LIGHTGREY, gridwidth=0.5)),
        yaxis=dict(range=[2.5, 8.9], showticklabels=False, ticks="",
                   title='Performance', showgrid=True,
                   gridcolor=WF_LIGHTGREY, gridwidth=1),
    )
    return fig