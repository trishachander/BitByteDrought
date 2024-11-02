import os
import pathlib
import re
import pandas as pd
import numpy as np
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import cufflinks as cf
from dash.dependencies import Input,Output,State

app = dash.Dash(
    __name__,
    meta_tags = [
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {"name": "viewport", "content": "width=device-height, initial-scale=1.0"}
    ],
    assets_folder = 'assets'
)
server = app.server
YEARS = [i for i in range(2015,2023)]

st = pd.read_csv(
    filepath_or_buffer = 'Data/States.csv',
    index_col = [0],
    header = [0, 1]
)
rs = pd.read_csv(
    filepath_or_buffer = 'Data/RobustStates.csv',
    index_col = [0],
    header = [0, 1]
)
ds = pd.read_csv(
    filepath_or_buffer = 'Data/Districts.csv',
    index_col = [0],
    header = [0, 1]
)
rd = pd.read_csv(
    filepath_or_buffer = 'Data/RobustDistricts.csv',
    index_col = [0],
    header = [0, 1]
)
jss = pd.read_pickle('Data/States.pkl')
jsd = pd.read_pickle('Data/Districts.pkl')

def trend(x):
    if str(x) == 'nan':
        return 'No Data'
    elif x == 0:
        return 'Constant'
    elif x < 0:
        return 'Increase'
    elif x > 0:
        return 'Decrease'
    else:
        print('Problem')

def avg(x):
    z = 0
    for i in [j for j in x]:
        if str(i) == 'nan':
            z += 1
    if z == len(x):
        return np.nan
    return np.nanmean(x)


def NoData(dafr, level):
    na = pd.read_pickle(f'Data/NoData{level}s.pkl')
    nd = pd.DataFrame(
        data = {
            'Pre' : ['No Data' for i in na],
            'Post' : ['No Data' for i in na]
        },
        index = na)
    return dafr.append(nd)

def final_trend(kind, level, year = 2017):
    if level == 'State':
        df = st.copy()
    else:
        df = ds.copy()
    
    df = df[[str(i) for i in range(year - 10, year + 1)]]
    yty = df[str(year)] - df[str(year - 1)]
    yty = yty.applymap(trend)
    
    if (kind=="YTY"):
        yty = NoData(dafr = yty, level = level)
        return yty
    elif (kind == "DA"):
        if level == 'State':
            df = rs.copy()
        else:
            df = rd.copy()
        da = yty.copy()
        i = df[[str(year - 10 + i) for i in range(10)]]
        da['Pre'] =  i.iloc[:,::2].apply(avg, axis = 1)
        da['Post'] = i.iloc[:,1::2].apply(avg, axis = 1)
        da = df[str(year)] - da
        da = da.applymap(trend)
        da = NoData(dafr = da, level = level)
        return da
    
    else:
        print("Unavailable")

def plot(wise, map_df, monsoon):
    if wise == 'District':
        js = jsd
    else:
        js = jss
    fig = px.choropleth(map_df.reset_index(),
                        geojson = js,
                        locations = "index", 
                        featureidkey = f"properties.{wise}",
                        color = monsoon,
                        hover_name = 'index',
                        color_discrete_map = {
                            'Increase' : '#bdf2d8',
                            'Decrease' : '#ff6961',
                            'No Data' : '#666699',
                            'Constant' : '#fdfd96'
                        })
    fig = fig.update_geos(
        fitbounds = "locations" )
#         visible = False)
    fig = fig.update_layout(
        title_text = 'Trend of GroundWater Health',
        title_font_family = 'helvetica',
        legend_font_size = 12
    )
    return fig

def final_plot(kind = 'YTY', monsoon = 'Pre', level = 'State', year = 2017):
    map_df = final_trend(kind = kind, year = year, level = level)
    return plot(wise = level, map_df = map_df, monsoon = monsoon)

app.layout = html.Div(
    id = 'root',
    children = [
        html.H1(
            children = 'GroundWater Management'
        ),
        html.Div(
            id = "Map-container",
            children = [
                html.Div(
                    id = 'slider-container',
                    children = [
                        html.P(
                            id = 'slider-text',
                            children = "Drag the slider to change the year:",
                        ),
                        dcc.Slider(
                            id = "years-slider",
                            min = min(YEARS),
                            max = max(YEARS),
                            value = 2017,
                            marks = {
                                str(year): {
                                    "label": str(year),
                                    "style": {"color": "#7fafdf"},
                                }for year in YEARS
                            },
                        )
                    ]
                ),
                html.Div(
                    id = 'left-options',
                    children = [
                        html.Div(
                            id = 'dropdown-container',
                            children = [
                                dcc.Dropdown(
                                    id = 'dropdown',
                                    options = [{
                                        "label": "Year to Year trend Analysis",
                                        "value": 'YTY'
                                    },
                                        {
                                            "label": "Decadal Average",
                                            "value": 'DA'
                                        },
                                    ],
                                    value = 'YTY'
                                )
                            ],
                        ),
                        html.Div(
                            id = 'monsoon-container',
                            children = [
                                dcc.RadioItems(
                                    id = 'monsoon',
                                    options = [{
                                        "label": " Pre-Monsoon",
                                        "value": 'Pre'
                                    },
                                        {
                                            "label": " Post-Monsoon",
                                            "value": 'Post'
                                        },
                                    ],
                                    value = 'Pre'
                                )
                            ]
                        ),
                        html.Div(
                            id = 'level-container',
                            children = [
                                dcc.RadioItems(
                                    id = 'level',
                                    options = [{
                                        "label": " State     ",
                                        "value": 'State'
                                    },
                                        {
                                            "label": " District",
                                            "value": 'District'
                                        },
                                    ],
                                    value = 'State'
                                )
                            ]
                        )
                    ]
                ),
                html.Div(
                    id = 'Map',
                    children = [
                        dcc.Graph(
                            id = 'India',
                            hoverData = {'points': [{'location' : 'Tamil Nadu'}]},
                            figure = {}
                        )
                    ]
                )
            ],
        ),
        html.Div(
            id = 'right-stuff',
            children = [
                html.Div(
                    id = 'rdropdown-container',
                    children = [
                        dcc.Dropdown(
                            id = 'rdropdown',
                            options = [
                                {
                                    "label": "Line Plot",
                                    "value": 'line'
                                },
                                {
                                    "label": "Scatter trend",
                                    "value": 'trend'
                                },
                                {
                                    "label": "Violin Plot",
                                    "value": 'violin'
                                }
                            ],
                            value = 'trend'
                        )
                    ],
                ),
                html.Div(
                    id = 'scatter-container',
                    children = [
                        dcc.Graph(
                            id = 'dropfig',
                            figure = {}
                        )
                    ]
                )
            ]
        )
    ]
)

@app.callback(
    Output("India", "figure"),
    [Input("dropdown", "value"),
    Input("years-slider", "value"),
    Input("monsoon", "value"),
    Input("level", "value")]
)
def update_figure(input1, input2, input3, input4):
    return final_plot(kind = input1, monsoon = input3, level = input4, year = input2)

@app.callback(
    Output('dropfig', 'figure'),
    [Input('India', 'hoverData'),
    Input("monsoon", "value"),
    Input("level", "value"),
    Input('rdropdown', 'value')]
)
def update_figure(hoverData, input2, input3, input4):
    place = hoverData['points'][0]['location']
    if input3 == 'State':
        df = st.loc[place]
    else:
        df = ds.loc[place]
    if input2 == 'Pre':
        p = 0
    else:
        p = 1
    if input4 == 'line':
        fig = px.line(x = [int(i) for i in range(2010, 2023)], y = df[[str(i) for i in range(2010, 2023)]].iloc[p::2])
        fig = fig.update_layout(
            title_text = place,
            xaxis_title_text = 'Years',
            yaxis_title_text = 'GroundWater Depth (in m)'
        )
        return fig
    elif input4 == 'trend':
        fig = px.scatter(x = [int(i) for i in range(2010, 2023)], y = df[[str(i) for i in range(2010, 2023)]].iloc[p::2], trendline = 'ols')
        fig = fig.update_layout(
            title_text = place,
            xaxis_title_text = 'Years',
            yaxis_title_text = 'GroundWater Depth (in m)'
        )
        return fig
    else:
        fig = px.violin(x = df[[str(i) for i in range(2010, 2023)]].iloc[::2], orientation = 'h', box = True)
        fig = fig.update_layout(
            title_text = place,
            xaxis_title_text = 'GroundWater Depth (in m)'
        )
        return fig

if __name__ == "__main__":
    app.run_server(debug=False, port = 4050)