from typing import Dict, Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from water_futures_battle.jurisdictions.entities import State, Province

from opt_utils import OptimisationMetrics

def add_hypervolume_trace(
    a_fig: go.Figure,
    data: Dict[int, float],
    label: str = "Province",
    color: str = "blue"
) -> go.Figure:
    """
    Adds a trace of hypervolume values across generations to a Plotly figure.

    Args:
        fig: The existing plotly.graph_objects.Figure object.
        data: A dictionary where keys are generation (int) and values 
              contain a dictionary with a 'hypervolumes' key.
        label: The name to assign to the new trace (for the legend).
        color: The color for the line trace.

    Returns:
        The modified plotly.graph_objects.Figure object.
    """
    # 2. Create the scatter trace
    hypervolume_trace = go.Scatter(
        x=list(data.keys()),
        y=list(data.values()),
        mode='lines+markers', # Show both a line and markers at each generation
        name=label,
        line=dict(color=color, width=2),
        marker=dict(size=6)
    )
    
    # 3. Add the trace to the figure
    a_fig.add_trace(hypervolume_trace)
    
    # Optional: Update layout for better visibility/context
    a_fig.update_layout(
        xaxis_title="Generation",
        yaxis_title="Hypervolume Value",
        title="Hypervolume Convergence Across Generations"
    )
    
    return a_fig

def add_pf_trace(
    a_fig: go.Figure,
    fits: np.ndarray,
    label: str = "Province",
    color: str = 'blue'
) -> go.Figure:
    """
    Creates a scatter plot of the 1st vs. 3rd objective fitness values.

    Args:
        utility_name: Label for the plot (e.g., the province name).
        data: A single dictionary with a 'fitnesses' key containing objective lists.

    Returns:
        A plotly.graph_objects.Figure object.
    """
    
    solution_indices = np.arange(len(fits)).reshape(-1, 1)
    custom_data = np.hstack((solution_indices, fits))
    
    # Y-axis: 1st objective (Total Network Volume/Length) -> Index 0
    y_values = fits[:,0]
    
    # X-axis: 3rd objective (Total Velocity Constraint Deviation) -> Index 2
    x_values = fits[:, 2]

    # sizes, divide the array in x bins
    sizes = fits[:,1]
    N_SIZE_BINS = 5
    bin_indices = np.digitize(sizes, np.linspace(sizes.min(), sizes.max(), N_SIZE_BINS+1), right=True)
    marker_sizes = 8 + (bin_indices - 1) * (N_SIZE_BINS / N_SIZE_BINS-1)
    
    scatter_trace = go.Scatter(
        x=x_values,
        y=y_values,
        mode='markers+lines', 
        name=label,
        marker=dict(size=marker_sizes, opacity=0.7, line=dict(width=1, color='DarkSlateGrey')),
        line=dict(color=color, width=2),
        customdata=custom_data,
        hovertemplate="""
        Volume: %{customdata[1]:.4f}<br>
        Press D/ Und Dem: %{customdata[2]:.4f}<br>
        Vel Viol: %{customdata[3]:.4f}<br>
        <extra>"""+label+"""<br><b>Solution Index: %{customdata[0]}</b></extra>
        """
    )
    
    a_fig.add_trace(scatter_trace)
    
    return a_fig

from plotly.express import colors as pl_clrs

colors = pl_clrs.qualitative.Set3

def plot_hypervolumes(
          a_state: State,
          metrics: Dict[Province, OptimisationMetrics]
) -> go.Figure:

    fig = go.Figure()
    for i, province in enumerate(sorted(a_state.provinces, key=lambda pv: pv.cbs_id)):
        if province not in metrics:
            continue
        fig = add_hypervolume_trace(
                a_fig=fig,
                data=metrics[province].global_hypervolumes,
                label=province.display_name,
                color=colors[i % len(metrics)]
            )
    return fig

def plot_final_paretos(
          a_state: State,
          metrics: Dict[Province, OptimisationMetrics]
) -> go.Figure:
    
    fig = go.Figure()

    for i, province in enumerate(sorted(a_state.provinces, key=lambda pv: pv.cbs_id)):
        if province not in metrics:
            continue
        fig = add_pf_trace(
                a_fig=fig,
                fits=metrics[province].pareto_front_fitnesses,
                label=province.display_name,
                color=colors[i % len(metrics)]
            )

    fig.update_layout(
        title=f"Final Pareto front",
        xaxis_title="Third objective",
        yaxis_title="Total Network Volume",
        hovermode="closest"
    )
    
    return fig


def plot_ages(all_connections_df: pd.DataFrame) -> go.Figure:
    df = all_connections_df.copy()
    conn_dates = {}
    for conn_id, conn_data in df.iterrows():
        dates = [pd.to_datetime(d) for d in str(conn_data['pipes-installation_dates']).split(';')]
        conn_dates[conn_id] = dates
        
    all_ages = {}
    avg_ages = []
    YEARS = range(2000, 2025)
    for y in YEARS:
        year = pd.Timestamp(year=y, month=1, day=1)
        
        ages = []
        for c, ds in conn_dates.items():
            prev_dates = [d for d in ds if d < year]
            if prev_dates:
                active_pipe_date = max(prev_dates)
                ages.append((year - active_pipe_date).days / 365.25)
        
        all_ages[y] = ages
        avg_ages.append(np.mean(np.array(ages)))

    df = pd.DataFrame({
        'Year': YEARS,
        'Average Age': avg_ages
    })

    # Create the line plot
    fig = px.line(df, x='Year', y='Average Age', 
                title='Average Age Over Time',
                markers=True)  # Add markers to see individual points

    return fig

def plot_undelivered_demands(
        undelivered_demands: Dict[tuple[str, int], float]
) -> go.Figure:
    """
    Plots undelivered demands over time for each province using Plotly.
    Args:
        undelivered_demands: Dict with keys as (province_id, year) and values as undelivered demand (float).
    Returns:
        Plotly Figure with one trace per province, x-axis as year, y-axis as undelivered demand.
    """
    # Organize data by province
    province_data = {}
    for (province_id, year), value in undelivered_demands.items():
        if province_id not in province_data:
            province_data[province_id] = []
        province_data[province_id].append((year, value))

    fig = go.Figure()
    color_list = pl_clrs.qualitative.Set3
    for i, (province_id, data) in enumerate(sorted(province_data.items())):
        # Sort by year
        data_sorted = sorted(data, key=lambda x: x[0])
        years = [year for year, _ in data_sorted]
        values = [val for _, val in data_sorted]
        fig.add_trace(go.Scatter(
            x=years,
            y=values,
            mode='lines+markers',
            name=str(province_id),
            line=dict(color=color_list[i % len(color_list)], width=2),
            marker=dict(size=6)
        ))

    fig.update_layout(
        title="Undelivered Demands Over Time by Province",
        xaxis_title="Year",
        yaxis_title="Undelivered Demand",
        hovermode="closest"
    )
    return fig