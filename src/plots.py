import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import pandas as pd

def plot_histogram(df, col, title, color_seq):
    fig = px.histogram(
        df, 
        x=col, 
        nbins=30, 
        title=title,
        color_discrete_sequence=[color_seq]
    )
    fig.update_layout(showlegend=False, xaxis_title=title, yaxis_title="Number of Districts")
    return fig

def plot_scatter(df, x_col, y_col, size_col, color_col, hover_data):
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        size=size_col,
        color=color_col,
        hover_data=hover_data,
        title=f"{y_col} vs {x_col}",
        color_continuous_scale="RdYlGn_r" # High iceberg index is usually "risk", so Red? Or Blue? Let's use Red for high exposure.
    )
    return fig

def create_map(df):
    """
    Create a PyDeck map for Indian Districts.
    """
    # Filter out rows without lat/long
    map_df = df.dropna(subset=['Latitude', 'Longitude']).copy()
    
    if len(map_df) == 0:
        return None

    # Normalize Size for visualization
    map_df['radius'] = map_df['total_employment'] / map_df['total_employment'].max() * 50000 + 5000

    layer = pdk.Layer(
        "ScatterplotLayer",
        map_df,
        pickable=True,
        opacity=0.6,
        stroked=True,
        filled=True,
        radius_scale=1,
        radius_min_pixels=3,
        radius_max_pixels=50,
        line_width_min_pixels=1,
        get_position=["Longitude", "Latitude"],
        get_radius="radius",
        get_fill_color="[255, (1 - iceberg_index / 100) * 255, 0]", # Red to Yellow/Green gradient logic roughly
        get_line_color=[0, 0, 0],
    )

    # Tooltip
    tooltip = {
        "html": "<b>{District_Name}</b>, {State_Name}<br/>"
                "Iceberg Index: <b>{iceberg_index}</b><br/>"
                "Employment: {total_employment}",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }

    view_state = pdk.ViewState(
        latitude=20.5937,
        longitude=78.9629,
        zoom=4,
        pitch=0,
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/light-v10"
    )
    return r
