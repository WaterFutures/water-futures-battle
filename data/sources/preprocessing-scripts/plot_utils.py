from typing import Dict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from water_futures_battle.jurisdictions.entities import State, Province

# Year for the slider plots
START_YEAR = 2000
END_YEAR = 2024
YEARS = range(START_YEAR, END_YEAR + 1)

BLUE_HEX = '#21429D'
BLUE_RGB = '33,66,157'
GREEN_HEX = '#019344'
GREEN_RGB = '1,147,68'

# subfunction to get the ordered locations in a given year
def ordered_volumes(
        a_province: Province,
        yearly_max_MCH: pd.DataFrame,
        province_sources_df: pd.DataFrame,
        year: int
    ) -> pd.DataFrame:
    """
    Docstring for ordered_volumes
    
    :param a_province: Description
    :type a_province: Province
    :param df: Description
    :type df: pd.DataFrame
    :param year: Description
    :type year: int
    :return: A dict with the places in that year and their elevation and capacity (m^3/h)
    :rtype: Any
    """
    ts = pd.Timestamp(year=year, month=1, day=1)

    # initialize with the municipalities
    locations = [{
        'location': m.cbs_id,
        'elevation': m.elevation,
        'capacity': -yearly_max_MCH.loc[year, m.cbs_id]
        }
        for m in a_province.active_municipalities(when=year)
    ]

    # add the one of the active sources
    ACTIVE_SOURCES_MASK = (
        pd.notna(province_sources_df['activation_date']) &
        pd.notna(province_sources_df['capacity-nominal']) & 
        (province_sources_df['activation_date'] <= ts) & 
        (
            pd.isna(province_sources_df['closure_date']) | 
            (province_sources_df['closure_date'] > ts)
        )
    )

    locations += [{
        'location': source_desc['source_id'],
        'elevation': source_desc['elevation'],
        'capacity': source_desc['capacity-nominal']/24 # to m^3/h
        }
        for _, source_desc in province_sources_df[ACTIVE_SOURCES_MASK].iterrows()
    ]

    # Sort locations by elevation (the first element in the tuple)
    return pd.DataFrame(locations).sort_values(by='elevation', ascending=False)


def plot_net_capacity_by_elevation(
        a_state: State,
        nl_sources_df: pd.DataFrame,
        yearly_max_MCH: pd.DataFrame
        ) -> go.Figure:

    provinces = list(sorted(a_state.provinces, key=lambda pv: pv.cbs_id))

    rows = 3
    cols = 4
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[f"{pv.display_name}" for pv in provinces],
        shared_xaxes=True, shared_yaxes=True
    )
    
    # Initial year
    for idx, pv in enumerate(provinces):
        row = idx //cols +1
        col = idx % cols +1

        pv_sources_df = nl_sources_df[nl_sources_df['province'] == pv.cbs_id]

        locations = ordered_volumes(pv, yearly_max_MCH, pv_sources_df, YEARS[0])

        fig.add_trace(
            go.Scatter(
                x=locations['elevation'].values,
                y=locations['capacity'].cumsum().values,
                customdata=locations[['location', 'capacity']].values,
                hovertemplate=(
                    "Elevation: %{x}<br>"
                    "Cumcap: %{y}<br>"
                    "<extra>Location: %{customdata[0]}<br>Capacity: %{customdata[1]:.2f} m³/h</extra>"
                ),
                name=pv.display_name,
                mode='lines'
            ),
            row=row, col=col
        )

    # Slider steps 
    steps = []
    for year in YEARS:
        step_data = []

        for idx, pv in enumerate(provinces):
            pv_sources_df = nl_sources_df[nl_sources_df['province'] == pv.cbs_id]

            locations = ordered_volumes(pv, yearly_max_MCH, pv_sources_df, year)

            step_data.append({
                'x': locations['elevation'].values,
                'y': locations['capacity'].cumsum().values,
                'customdata': locations[['location', 'capacity']].values
            })

        step = dict(
            method='restyle',
            args=[{
                "x": [d['x'] for d in step_data],
                "y": [d['y'] for d in step_data],
                "customdata": [d['customdata'] for d in step_data]
            }],
            label=str(year)
        )
        steps.append(step)

    sliders = [dict(
        active=0,
        currentvalue={"prefix": "Year: "},
        pad={"t": 50},
        steps=steps
    )]

    fig.update_xaxes(autorange='reversed')
    fig.update_layout(
        sliders=sliders,
        height=1000,  # Adjust height for better visualization
        showlegend=False  # Disable legend for individual subplots
    )

    fig.write_html("net_capacity_by_elevation.html")

    return fig

def plot_capacity_distribution(
        nl_sources_df: pd.DataFrame
) -> go.Figure:
    """
    Plot the distribution of the sources' nominal capacity
    """
    df = nl_sources_df.loc[(
        pd.notna(nl_sources_df['activation_date']) &
        pd.notna(nl_sources_df['capacity-nominal'])
        ),
    :].copy()
    MASK_GW = df['source_type'] == 'groundwater'
    MASK_SW = df['source_type'] == 'surface_water'

    def get_filtered_data(df: pd.DataFrame, year: int) -> pd.Series:
        """
        Applies the filter: activation_date is not null AND closure_date > year.
        Returns the 'capacity-nominal' Series in M m^e/year.
        """
        filter_date = pd.to_datetime(f'{year}-01-01')
        
        ACTIVE_MASK = (
            df['activation_date'].notna() &
            (df['activation_date'] <= filter_date) &
            (df['closure_date'].isna() | (df['closure_date'] > filter_date))
        )
        
        return df.loc[ACTIVE_MASK, 'capacity-nominal']*365/1e6
    
    # 1. Initialize the figure with the data for the first year
    MAX_SOURCE_CAPACITY = df['capacity-nominal'].max()*365/1e6
    BINS_SIZE = 2 # MMCY

    fig = go.Figure(
        data=[
            go.Histogram(
                x=get_filtered_data(df[MASK_GW], START_YEAR),
                name='Groundwater',
                marker_color=BLUE_HEX,
                xbins=dict(start=0, end=MAX_SOURCE_CAPACITY, size=BINS_SIZE) 
            ),
            go.Histogram(
                x=get_filtered_data(df[MASK_SW], START_YEAR),
                name='Surface water',
                marker_color=GREEN_HEX,
                xbins=dict(start=0, end=MAX_SOURCE_CAPACITY, size=BINS_SIZE) 
            )
        ],
        layout=go.Layout(
            title=f"Distribution of 'Capacity Nominal' by Type in year {START_YEAR}",
            xaxis=dict(title='Capacity Nominal', automargin=True),
            yaxis=dict(title='Count', automargin=True),
            # Overlay the histograms to compare distributions
            barmode='overlay', 
            bargap=0.01,
            height=500
        )
    )
    fig.update_traces(opacity=0.75)

    # 2. Loop through years to build the slider steps
    steps = []
    for year in YEARS:        
        # Define the step: use method="restyle" to update the trace's data
        step = dict(
            method="restyle",
            # args[0] = trace properties to update (here, the 'x' data)
            args=[
                {"x": [
                        get_filtered_data(df[MASK_GW], year),
                        get_filtered_data(df[MASK_SW], year)
                    ]
                },  
                # args[1] = layout properties to update (here, the title)
                {"title": f"Distribution of 'Capacity Nominal' in year {year}"}
            ],
            label=str(year)
        )
        steps.append(step)

    slider = [dict(
        active=0, # Start at the first step (year 2000)
        currentvalue={"prefix": "Year: "},
        pad={"t": 50}, # Padding at the top
        steps=steps
    )]

    fig.update_layout(
        sliders=slider
    )

    fig.write_html("capacity_distribution.html")

    return fig

def get_capacities_by_year(df: pd.DataFrame) -> np.ndarray:
    capacities = []
    for year in YEARS:
        mask = (
            (df['activation_date'].dt.year <= year) &
            (df['closure_date'].isna() | (df['closure_date'].dt.year > year))
        )
                
        cp = df.loc[mask, 'capacity-nominal'].sum(skipna=True) # to Mm^3/year
        
        capacities.append(cp)

    return np.array(capacities)    

def plot_capacity_across_time(
        nl_sources_df: pd.DataFrame,
        yearly_max_MCD: pd.Series
    ) -> go.Figure:
    """
    Calculates and plots the cumulative 'capacity-nominal' over time by tracking
    capacity added (activation_date) and capacity removed (closure_date).
    
    Args:
        sources_df: The DataFrame containing 'activation_date', 'closure_date', 
                    and 'capacity-nominal'. Date columns must be in datetime format.
    """
    
    # Drop rows where activation date or capacity is invalid
    df = nl_sources_df.loc[(
        pd.notna(nl_sources_df['activation_date']) &
        pd.notna(nl_sources_df['capacity-nominal'])
        ),
    :].copy()
    MASK_GW = df['source_type'] == 'groundwater'
    MASK_SW = df['source_type'] == 'surface_water'

    # --- Capacity Change Calculation ---
    gw_yearly_capacities = get_capacities_by_year(df[MASK_GW])*365/1e6
    sw_yearly_capacities = get_capacities_by_year(df[MASK_SW])*365/1e6
    fig = go.Figure(
        data=[
            go.Scatter(
                x=list(YEARS),
                y=gw_yearly_capacities,
                mode='lines', # No markers needed for filled area
                name='Groundwater',
                line=dict(color=BLUE_HEX, width=0), # Hide line for fill
                fill='tozeroy', # Fill area down to zero
                fillcolor=f'rgba({BLUE_RGB},0.3)', # Semi-transparent dark blue
                hovertemplate='Groundwater Capacity: %{y:.2f} MMCY<extra></extra>'
            ),
            go.Scatter(
                x=list(YEARS),
                y=gw_yearly_capacities+sw_yearly_capacities,
                customdata=sw_yearly_capacities,
                mode='lines',
                name='Surface Water',
                line=dict(color='darkgreen', width=0), # Hide line for fill
                fill='tonexty',
                fillcolor=f'rgba({GREEN_RGB},0.3)', # Semi-transparent dark green
                hovertemplate='Surface Water Capacity: %{customdata:.2f} MMCY<extra></extra>'
            ),
            go.Scatter(
                x=yearly_max_MCD.index,
                y=yearly_max_MCD*365/1e6,
                mode='lines',
                name='National Demand approx',
                line=dict(color='red'),
                hovertemplate='Total demand: %{y:.2f} MMCY<extra></extra>'
            )
        ],
        layout=go.Layout(
            title="Cumulative Capacity Nominal Across Time",
            xaxis=dict(
                title='Year', 
                tickformat='d', 
                automargin=True,
                range=[START_YEAR, END_YEAR]
            ),
            yaxis=dict(title='Cumulative Capacity Nominal (MMCY)', automargin=True),
            hovermode="x unified", # Enhance interactivity
            height=500
        )
    )

    # Enhance interactivity with unified hover
    fig.update_xaxes(showspikes=True, spikecolor="gray", spikethickness=1)
    fig.update_yaxes(showspikes=True, spikecolor="gray", spikethickness=1)
    fig.update_layout(hovermode="x unified")

    fig.write_html("nl_capacity_per_year.html")

    return fig

def plot_capacity_across_time_per_prov(
        a_state: State,
        nl_sources_df: pd.DataFrame,
        yearly_max_MCD: pd.DataFrame,
        yearly_max_MCH: pd.DataFrame
    ) -> go.Figure:

    # Drop rows where activation date or capacity is invalid
    df = nl_sources_df.loc[(
        pd.notna(nl_sources_df['activation_date']) &
        pd.notna(nl_sources_df['capacity-nominal'])
        ),
    :].copy()
    MASK_GW = df['source_type'] == 'groundwater'
    MASK_SW = df['source_type'] == 'surface_water'

    # Create a grid layout for 12 provinces (3 rows x 4 columns)
    provinces = list(sorted(a_state.provinces, key=lambda pv: pv.cbs_id))

    rows = 3
    cols = 4
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[f"{pv.display_name}" for pv in provinces],
        shared_xaxes=True, shared_yaxes=True
    )
    
    for idx, pv in enumerate(provinces):
        MASK_PV = df['province'] == pv.cbs_id

        row = idx //cols +1
        col = idx % cols +1
        
        gw_yearly_capacities = get_capacities_by_year(df[MASK_PV & MASK_GW])*365/1e6
        sw_yearly_capacities = get_capacities_by_year(df[MASK_PV & MASK_SW])*365/1e6

        # Add groundwater trace
        fig.add_trace(
            go.Scatter(
                x=list(YEARS),
                y=gw_yearly_capacities,
                mode='lines',
                name='Groundwater',
                line=dict(color='darkblue'),
                fill="tozeroy",
                fillcolor=f'rgba({BLUE_RGB},0.3)',
                hovertemplate='Groundwater Capacity: %{y:.2f} MMCY<extra></extra>'
            ),
            row=row, col=col
        )

        # Add surface water trace
        fig.add_trace(
            go.Scatter(
                x=list(YEARS),
                y=gw_yearly_capacities+sw_yearly_capacities,
                customdata=sw_yearly_capacities,
                mode='lines',
                name='Surface Water',
                line=dict(color='darkgreen'),
                fill='tonexty',
                fillcolor=f'rgba({GREEN_RGB},0.3)',
                hovertemplate='Surface Water Capacity: %{customdata:.2f} MMCY<extra></extra>'
            ),
            row=row, col=col
        )
        
        # Add demand 
        fig.add_trace(
            go.Scatter(
                x=yearly_max_MCD.index,
                y=yearly_max_MCD[pv.cbs_id]*365/1e6,
                mode='lines',
                name='demand',
                line=dict(color='red'),
                hovertemplate='Demand: %{y:.2f} MMCY<extra></extra>'
            ),
            row=row, col=col
        )
        fig.add_trace(
            go.Scatter(
                x=yearly_max_MCH.index,
                y=yearly_max_MCH[pv.cbs_id]*24*365/1e6,
                mode='lines',
                name='peak-demand',
                line=dict(color='red', dash='dash'),
                hovertemplate='Peak demand: %{y:.2f} MMCY<extra></extra>'
            ),
            row=row, col=col
        )

        # Update layout
        fig.update_layout(
            title="Cumulative Capacity Nominal Across Time by Province",
            xaxis=dict(title='Year', tickformat='d'),
            yaxis=dict(title='Cumulative Capacity Nominal (MMCY)'),
            height=1000,  # Adjust height for better visualization
            showlegend=False,  # Disable legend for individual subplots
            hovermode="x unified"
        )

    fig.write_html("pv_capacity_per_year.html")

    return fig