from dash import Dash, html, dcc, Input, Output, callback
import pandas as pd
from urllib.request import urlopen
import json
import plotly.express as px
import dash

app = Dash(__name__)

cols_to_drop = ["ViolentCrimesPerPop", "nonViolPerPop", "state", "population", "PctSpeakEnglOnly", "PctNotSpeakEnglWell",
                "PctImmigRecent", "PctImmigRec5", "PctImmigRec8", "PctImmigRec10", "PctRecentImmig", "PctRecImmig5",
                "PctRecImmig8", "PctRecImmig10"]

df = pd.read_csv("crimedata.csv")
df.dropna(axis="index", how="any", subset=cols_to_drop, inplace=True)
df.reset_index(drop=True, inplace=True)
df["ViolentCrimes"] = df["ViolentCrimesPerPop"] / 100000 * df["population"]
df["nonViolentCrimes"] = df["nonViolPerPop"] / 100000 * df["population"]
df["TotalCrimes"] = df["ViolentCrimes"] + df["nonViolentCrimes"]
df["TotalCrimesPerPop"] = df["TotalCrimes"] / df["population"] * 100000


df1 = df
df1 = df1.groupby(['state']).agg({"ViolentCrimes" : "sum", "population" : "sum"}).reset_index()
df1["ViolentCrimesPerStateAndPop"] = df1["ViolentCrimes"] / df1["population"] * 100000

fig1 = px.bar(df1, x="state", y="ViolentCrimesPerStateAndPop")
fig1.update_layout(
    title={
        "text": "Rate for violent crimes by state",
         "x" : 0.5,
        "font_size" : 20
    },
    xaxis_title="State",
    yaxis_title="Rate for violent crimes per 100000 population",
    height=700
)

df2 = df
df2["raceBlackTotal"] = df2["racepctblack"] / 100 * df2["population"]
df2["raceWhiteTotal"] = df2["racePctWhite"] / 100 * df2["population"]
df2["raceAsianTotal"] = df2["racePctAsian"] / 100 * df2["population"]
df2["raceHispTotal"] = df2["racePctHisp"] / 100 * df2["population"]
df2 = df2.groupby(["state"]).agg({"population" : "sum", "raceBlackTotal" : "sum", "raceWhiteTotal" : "sum",
                                 "raceAsianTotal" : "sum", "raceHispTotal" : "sum"}).reset_index()


df3 = df
df3 = df3.groupby(["state"]).agg({"population" : "sum", "murders" : "sum", "rapes": "sum", "robberies" : "sum",
                                  "assaults" : "sum", "burglaries" : "sum", "larcenies": "sum", "autoTheft" : "sum",
                                  "arsons" : "sum"}).reset_index()
for columnName in df3:
    if columnName not in ["state", "population"]:
        df3[columnName] = df3[columnName] / df3["population"] * 100000





app.layout = html.Div([
    html.Div([

        html.Div([
            dcc.Graph(
                id='crime_rate_by_state',
                figure=fig1)
        ],
            style={'width': '49%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                df['state'].unique(),
                'AK',
                id = 'state_dropdown'
            ),
            dcc.Graph(
                id='race_by_state'
            ),
            dcc.Graph(
                id='crime_type_by_state'
            )
        ],
            style={'width': '49%', 'display': 'inline-block'})

    ]),
    html.Div([

        html.Div([
            html.Div([
                html.Div([
                    dcc.RadioItems(
                        ['People who speak only English', 'People who dont speak English well'],
                        'People who speak only English',
                        inline=True,
                        id='language_mode'
                    )
                ],
                    style={'width': '49%', 'margin' : 'auto'}),
                html.Div([
                    dcc.Dropdown(
                        ["Violent crimes", "nonVilent crimes"],
                        'Violent crimes',
                        id='violent_mode'
                    ),
                ],
                    style={'width': '49%', 'margin' : 'auto'}),
            ]),
        ]),
        html.Div(
            dcc.Graph(
                            id='crime_rate_by_language'
                        )
        )
    ],
        style={'width': '60%', 'margin' : 'auto'}),

    html.Div([
        html.Div([
            dcc.Slider(
                0,
                10,
                step=None,
                marks={
                    3: '3 years',
                    5: '5 years',
                    8: '8 years',
                    10: '10 years'
                },
                value=5,
                id="years_slider")
        ],
            style={'margin-bottom': '10px'}),
        dcc.Graph(
            id="crime_rate_by_migration"
        ),
        dcc.RadioItems(
            ['Percent of immigrants who immigrated in this period', 'Percent of total population that immigrated in this period'],
            'Percent of immigrants who immigrated in this period',
            inline=True,
            id='immigration_mode'
        )
    ],
        style={'width': '60%', 'margin' : 'auto'})



])



@app.callback(
    Output('race_by_state', 'figure'),
    Output("crime_type_by_state", 'figure'),
    Input('state_dropdown', 'value'))
def update_race_and_type_graph(selected_state):
    df2_state = df2[df2["state"] == selected_state].drop(labels=["population", "state"], axis=1).reset_index(drop=True)
    fig2 = px.pie(df2_state, names=["Black", "White", "Asian", "Hispanic"], values=df2_state.loc[0])
    fig2.update_layout(
        title={
            "text": "Race distribution",
            "x": 0.5,
            "font_size": 20
        },
        height=350
    )
    df3_state = df3[df3["state"] == selected_state].drop(labels=["population", "state"], axis=1).reset_index(drop=True)
    fig3 = px.bar(df3_state, x=['murders', 'rapes', 'robberies', 'assaults', 'burglaries',
                                'larcenies', 'autotheft', 'arsons'], y=df3_state.loc[0])
    fig3.update_layout(
        title={
            "text": "Crime type by state",
            "x": 0.5,
            "font_size": 20
        },
        height=350,
        xaxis_title="Crime type",
        yaxis_title="Crime rate per 100000 population",
    )
    return fig2, fig3

@app.callback(
    Output('crime_rate_by_language', 'figure'),
    Input('language_mode', 'value'),
    Input('violent_mode', 'value'))
def update_language_graph(language_mode, violent_mode):
    df4 = df.reset_index(drop=True)
    df4["PctSpeakEnglOnly"] = df4["PctSpeakEnglOnly"].apply(lambda x: round(x))
    df4["PctNotSpeakEnglWell"] = df4["PctNotSpeakEnglWell"].apply(lambda x: round(x))
    if violent_mode == "Violent crimes":
        column_name = "ViolentCrimes"
    else:
        column_name = "nonViolentCrimes"
    if language_mode == 'People who speak only English':
        df4 = df4.groupby(["PctSpeakEnglOnly"]).agg({column_name : "sum", "population" : "sum"}).reset_index()
        df4[column_name + "PerPopByLang"] = df4[column_name] / df4["population"] * 100000
        fig4 = px.line(df4, x="PctSpeakEnglOnly", y= column_name + "PerPopByLang")
    else:
        df4 = df4.groupby(["PctNotSpeakEnglWell"]).agg({column_name: "sum", "population": "sum"}).reset_index()
        df4[ column_name + "PerPopByLang"] = df4[column_name] / df4["population"] * 100000
        fig4 = px.line(df4, x="PctNotSpeakEnglWell", y= column_name + "PerPopByLang")
    fig4.update_layout(
        title={
            "text": violent_mode + " rate by language skills",
            "x": 0.5,
            "font_size": 20
        },
        height=500,
        xaxis_title="Percantage",
        yaxis_title= violent_mode + "rate per 100000 population",
    )
    return fig4

@app.callback(
    Output('crime_rate_by_migration', 'figure'),
    Input('immigration_mode', 'value'),
    Input('years_slider', 'value'))
def update_migration_graph(immigration_mode, period):
    df5 = df.reset_index(drop=True)
    if immigration_mode == 'Percent of immigrants who immigrated in this period' and period != 3:
        column_name = "PctImmigRec" + str(period)
    elif immigration_mode == 'Percent of immigrants who immigrated in this period':
        column_name = "PctImmigRecent"
    elif period == 3:
        column_name = "PctRecentImmig"
    else:
        column_name = "PctRecImmig" + str(period)
    df5[column_name] = df5[column_name].apply(lambda x: round(x))
    df5 = df5.groupby([column_name]).agg({"TotalCrimes": "sum", "population": "sum"}).reset_index()
    df5["TotalCrimesPerPopByMigration"] = df5["TotalCrimes"] / df5["population"] * 100000
    fig5 = px.line(df5, x=column_name, y="TotalCrimesPerPopByMigration")
    fig5.update_layout(
        title={
            "text": "Total crime rate by migration",
            "x": 0.5,
            "font_size": 20
        },
        height=500,
        xaxis_title="Percantage",
        yaxis_title="Total crime rate per 100000 population",
    )
    return fig5

if __name__ == '__main__':
    app.run_server()