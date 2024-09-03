import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import os
from datetime import datetime

# Function to load data within a specified date and time range
def load_data(start_datetime=None, end_datetime=None):
    all_data = []
    for filename in os.listdir('.'):
        if filename.startswith('live_data_') and filename.endswith('.csv'):
            df = pd.read_csv(filename, parse_dates=['timestamp'])
            all_data.append(df)
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
    else:
        combined_df = pd.DataFrame()
    
    if start_datetime and end_datetime:
        combined_df = combined_df[(combined_df['timestamp'] >= start_datetime) & (combined_df['timestamp'] <= end_datetime)]
    
    return combined_df

# Function to get the latest values from the data
def get_latest_values():
    df = load_data()
    if not df.empty:
        latest_row = df.iloc[-1]
    else:
        latest_row = pd.Series()
    return latest_row

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server  # Required for deploying with Flask server

# Available ADC channels
adc_channels = ['X1', 'X2', 'Y1', 'Y2', 'D1', 'D2', 'Z1', 'Z2']

app.layout = html.Div(style={'textAlign': 'center', 'padding': '20px'}, children=[
    html.Div(style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}, children=[
        html.Img(src='assets/logo.png', className='custom-header', style={'height': '180px', 'margin-right': '60px'}),
        html.H1("ADC Channel Data Visualization", className='custom-header', style={'color': '#007bff', 'flex': '1'}),
        html.Img(src='assets/logo2.png', className='custom-header', style={'height': '160px', 'margin-left': '60px'})
    ]),
    
    dcc.DatePickerRange(
        id='date-range',
        display_format='YYYY-MM-DD',
        className='date-picker-range'
    ),
    
    html.Div(style={'display': 'flex', 'justify-content': 'center', 'margin-top': '10px'}, children=[
        html.Div([
            html.Label('Start Time:'),
            dcc.Input(id='start-time', type='text', placeholder='HH:MM:SS', className='time-input')
        ], style={'margin-right': '10px'}),
        html.Div([
            html.Label('End Time:'),
            dcc.Input(id='end-time', type='text', placeholder='HH:MM:SS', className='time-input')
        ])
    ]),
    
    html.Div(style={'display': 'flex', 'justify-content': 'center', 'margin-top': '20px'}, children=[
        html.Div(style={'flex': '1'}, children=[
            dcc.Dropdown(
                id='adc-dropdown',
                options=[{'label': channel, 'value': channel} for channel in adc_channels],
                value=adc_channels,
                multi=True,
                className='dropdown-style'
            )
        ]),
        html.Div(style={'flex': '1'}, children=[
            html.Div(id='latest-values-table', className='table-container', style={'margin-left': '20px'})
        ])
    ]),

    dcc.Graph(id='adc-graph', className='custom-graph'),
    
    dcc.RadioItems(
        id='time-format',
        options=[
            {'label': 'Normal Timestamp', 'value': 'timestamp'},
            {'label': 'Modified Julian Date (MJD)', 'value': 'mjd'}
        ],
        value='timestamp',
        className='custom-container'
    ),

    dcc.Interval(
        id='update-interval',
        interval=30 * 1000,  # 30 seconds
        n_intervals=0
    ),

    html.Button("Download Data", id="download-button", className="custom-button"),
    dcc.Download(id="download-data"),

    html.Div(id='click-data', className='click-data-style')
])

@app.callback(
    Output('adc-graph', 'figure'),
    [
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
        Input('start-time', 'value'),
        Input('end-time', 'value'),
        Input('adc-dropdown', 'value'),
        Input('update-interval', 'n_intervals'),
        Input('time-format', 'value'),
    ]
)
def update_graph(start_date, end_date, start_time, end_time, selected_channels, n_intervals, time_format):
    if not start_date or not end_date or not start_time or not end_time:
        return go.Figure()

    start_datetime = f"{start_date} {start_time}"
    end_datetime = f"{end_date} {end_time}"
    
    df = load_data(start_datetime, end_datetime)
    
    if df.empty:
        return go.Figure()

    figure = go.Figure()
    for column in selected_channels:
        figure.add_trace(go.Scatter(
            x=df[time_format],
            y=df[column],
            mode='lines+markers',
            name=column,
            hoverinfo='text',
            hovertemplate=f"{column}: %{{y}}<br>{time_format}: %{{x}}<extra></extra>",
            text=df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        ))

    figure.update_layout(
        title="ADC Channel Data",
        xaxis_title="Timestamp",
        yaxis_title="Value",
        hovermode='closest',
        xaxis_rangeslider_visible=True,
    )

    return figure

@app.callback(
    Output('latest-values-table', 'children'),
    Input('update-interval', 'n_intervals')
)
def update_table(n_intervals):
    latest_row = get_latest_values()
    
    if latest_row.empty:
        return html.Table([])

    table_header = [
        html.Thead(html.Tr([html.Th('ADC Channel'), html.Th('Latest Value')]))
    ]
    table_body = [
        html.Tbody([
            html.Tr([html.Td(channel), html.Td(latest_row.get(channel, 'N/A'))]) for channel in adc_channels
        ])
    ]
    
    table = table_header + table_body
    return html.Table(table)

@app.callback(
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    [State('date-range', 'start_date'),
     State('date-range', 'end_date'),
     State('start-time', 'value'),
     State('end-time', 'value')],
    prevent_initial_call=True
)
def generate_csv(n_clicks, start_date, end_date, start_time, end_time):
    if not n_clicks:
        return dash.no_update

    if not start_date or not end_date or not start_time or not end_time:
        return None

    start_datetime = f"{start_date} {start_time}"
    end_datetime = f"{end_date} {end_time}"

    df = load_data(start_datetime, end_datetime)
    return dcc.send_data_frame(df.to_csv, f"data_{start_date}_{start_time}_to_{end_date}_{end_time}.csv")

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8051)
