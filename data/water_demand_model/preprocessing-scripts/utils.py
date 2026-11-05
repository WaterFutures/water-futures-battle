import numpy as np
import pandas as pd
import plotly.graph_objects as go

def short_term_prediction(
        historical_df: pd.DataFrame,
        n_future_years: int,
        n_samples: int,
        rng: np.random.Generator,
        fitting_function,
        actual_function
    ) -> pd.DataFrame:
     
    full_index = pd.date_range(
        start=historical_df.index.min(), 
        periods=len(historical_df) + n_future_years, 
        freq='YS'
    )

    # Create a time index 't' for the full forecast period
    full_time_index = (full_index.year - full_index.year.min()).to_numpy()
    future_time_index = full_time_index[-n_future_years:]

    # Prepare to store all future forecasts
    future_forecasts = []
    # Get the indices of the historical data for sampling
    historical_indices = historical_df.index

    for _ in range(n_samples):
        # 1. Resampling (with replacement, if asked)
        if n_samples > 1:
            sampled_indices = rng.choice(historical_indices, size=len(historical_indices), replace=True)
        else:
            sampled_indices = historical_indices
        sampled_df = historical_df.loc[sampled_indices]
        
        # 2. Refitting
        try:
            params = fitting_function(sampled_df)
        except RuntimeError:
            # Handle cases where the curve fit fails (e.g., due to poor sampling)
            continue 
        
        # 3. Forecasting the future years
        forecast = actual_function(future_time_index, *params)
        future_forecasts.append(forecast)

    # Convert list of forecasts into a DataFrame
    future_forecast_df = pd.DataFrame(
        np.array(future_forecasts).T, 
        index=full_index[-n_future_years:]
    )

    property_name = historical_df.columns[0]

    return pd.DataFrame(data={
            f"{property_name}-min": future_forecast_df.min(axis=1),
            f"{property_name}-max": future_forecast_df.max(axis=1)
        },
        index=future_forecast_df.index
    )


def long_term_prediction(
    df: pd.DataFrame,
    step_years: int,
    n_steps: int,
    uncertainty_bounds_variation: tuple[float, float]
) -> pd.DataFrame:
    """
    Create the long-term predictions by multiplying the last value
    by uncertainty bounds at regular intervals.
    
    Args:
        df: Input dataframe with datetime index
        step_years: Number of years between each prediction step
        n_steps: Number of prediction steps to add
        uncertainty_bounds_variation: Tuple of (lower_multiplier, upper_multiplier)
    
    Returns:
        DataFrame with future predictions
    """
    output_df = df.copy()
    
    last_date = df.index[-1]
    last_year = last_date.year
    
    for step in range(1, n_steps + 1):
        if step == 1:
             future_year = last_year+1
        else:
            future_year = last_year + (step * step_years)
        future_date = pd.to_datetime(f"{future_year}-01-01")
        
        # Apply uncertainty bounds to the last value
        output_df.loc[future_date, :] = (
            output_df.iloc[-1, :] * list(uncertainty_bounds_variation)
        )
    
    return output_df.iloc[-n_steps:, :].copy()

from plotly.subplots import make_subplots
import plotly.graph_objects as go

def plot_unit_demands(house_df: pd.DataFrame, busin_df: pd.DataFrame) -> go.Figure:
    hc = '#21429D'
    hfc = f'rgba({33}, {66}, {157}, 0.7)'
    bc = '#019344'
    bfc = f'rgba({10}, {32}, {36}, 0.7)'

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Per House Demand (left y-axis)
    fig.add_trace(go.Scatter(
        x=house_df.index, y=house_df['NL0000-min'],
        mode='lines',
        line=dict(color=hc),
        name='Per House Demand - Min',
        showlegend=True
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=house_df.index, y=house_df['NL0000-max'],
        mode='lines',
        line=dict(color=hc),
        name='Per House Demand - Max',
        showlegend=True,
        fill='tonexty',
        fillcolor=hfc
    ), secondary_y=False)

    # Per Business Demand (right y-axis)
    fig.add_trace(go.Scatter(
        x=busin_df.index, y=busin_df['NL0000-min'],
        mode='lines',
        line=dict(color=bc),
        name='Per Business Demand - Min',
        showlegend=True
    ), secondary_y=True)
    fig.add_trace(go.Scatter(
        x=busin_df.index, y=busin_df['NL0000-max'],
        mode='lines',
        line=dict(color=bc),
        name='Per Business Demand - Max',
        showlegend=True,
        fill='tonexty',
        fillcolor=bfc
    ), secondary_y=True)

    fig.update_layout(
        legend=dict(itemsizing='constant'),
        template='plotly_white',
        margin=dict(l=40, r=40, t=40, b=40)
    )
    fig.update_yaxes(title_text="Per House Demand [m^3/hour/house]", secondary_y=False)
    fig.update_yaxes(title_text="Per Business Demand [m^3/hour/business]", secondary_y=True)

    return fig