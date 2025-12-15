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

def plot_scatter(df, x_col, y_col, size_col, color_col, hover_data, labels=None):
    # Auto-generate Title Case labels if not provided
    if labels is None:
        labels = {}
        for col in [x_col, y_col, size_col, color_col]:
            labels[col] = col.replace('_', ' ').title()
            
    # Create Title
    x_name = labels.get(x_col, x_col.replace('_', ' ').title())
    y_name = labels.get(y_col, y_col.replace('_', ' ').title())
    title_text = f"{y_name} Vs {x_name}"

    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        size=size_col,
        color=color_col,
        hover_data=hover_data,
        labels=labels,
        title=title_text,
        color_continuous_scale="RdYlGn_r", # High iceberg index is usually "risk", so Red? Or Blue? Let's use Red for high exposure.
        trendline="ols"
    )
    return fig

def create_choropleth(df, geojson):
    """
    Create a Plotly Choropleth Mapbox for Indian Districts.
    """
    if geojson is None:
        return None

    # Ensure df has matching column for GeoJSON feature id
    # Our GeoJSON feature properties have 'District'
    # The DF has 'District_Name'
    
    fig = px.choropleth_mapbox(
        df,
        geojson=geojson,
        locations='District_Name', # Column in DF
        featureidkey='properties.District', # Key in GeoJSON
        color='iceberg_index',
        color_continuous_scale="Reds", # High exposure = Red
        range_color=(20, 60),
        mapbox_style="carto-positron",
        zoom=3.5,
        center = {"lat": 22.0, "lon": 80.0},
        opacity=0.7,
        labels={'iceberg_index': 'Iceberg Index', 'District_Name': 'District'},
        hover_data={
            'District_Name': True, # Explicitly show name
            'State_Name': True,
            'iceberg_index': ':.2f',
            'total_employment': ':.0f'
        }
    )
    
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        coloraxis_colorbar=dict(
            title="Iceberg Index",
            thicknessmode="pixels", thickness=15,
            lenmode="pixels", len=200,
            yanchor="top", y=1,
            xanchor="left", x=0
        )
    )
    
    return fig
