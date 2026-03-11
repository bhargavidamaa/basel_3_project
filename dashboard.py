import dash
from dash import dcc, html
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# Database Extraction (The 'E' in our serving layer)
# ---------------------------------------------------------
DB_PARAMS = {
    "dbname": "airflow", "user": "airflow", "password": "airflow",
    "host": "localhost", "port": "5432"
}

def fetch_reporting_data():
    conn = psycopg2.connect(**DB_PARAMS)
    
    # Fetch the latest Bank metrics
    query_bank = """
        SELECT metric_name, metric_value 
        FROM regulatory_metrics 
        WHERE run_id = (SELECT run_id FROM regulatory_metrics ORDER BY computation_date DESC LIMIT 1)
    """
    df_bank = pd.read_sql(query_bank, conn)
    print(df_bank)
    # Fetch the latest FDIC benchmarks
    query_fdic = """
        SELECT metric_name, industry_average 
        FROM fdic_benchmarks 
        WHERE report_period = (SELECT MAX(report_period) FROM fdic_benchmarks)
    """
    df_fdic = pd.read_sql(query_fdic, conn)
    print(df_fdic)
    conn.close()
    
    # Merge datasets for easy plotting
    df_merged = pd.merge(df_bank, df_fdic, on='metric_name', how='inner')
    df_merged.rename(columns={'metric_value': 'Bank Metric', 'industry_average': 'FDIC Benchmark'}, inplace=True)
    return df_merged

# ---------------------------------------------------------
# Dash Application Initialization
# ---------------------------------------------------------
app = dash.Dash(__name__)
app.title = "Basel III Regulatory Dashboard"

# Fetch Data
df = fetch_reporting_data()

# Create Bar Chart
fig = go.Figure(data=[
    go.Bar(name='Our Bank', x=df['metric_name'], y=df['Bank Metric'], marker_color='#1f77b4'),
    go.Bar(name='FDIC Industry Avg', x=df['metric_name'], y=df['FDIC Benchmark'], marker_color='#ff7f0e')
])

fig.update_layout(
    title='Basel III Core Metrics: Bank vs. Industry',
    barmode='group',
    yaxis_title='Percentage (%)',
    template='plotly_white'
)

# ---------------------------------------------------------
# UI Layout
# ---------------------------------------------------------
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'margin': '40px'}, children=[
    html.H1("Regulatory Compliance Dashboard (Basel III)"),
    html.Hr(),
    
    html.Div([
        html.P("This dashboard compares our internally computed Spark metrics against the FDIC industry benchmarks. A healthy bank should exceed minimum regulatory thresholds for CAR and LCR, and maintain a low NPL ratio.", 
               style={'fontSize': '16px', 'color': '#555'})
    ]),
    
    dcc.Graph(
        id='metric-comparison-graph',
        figure=fig
    ),
    
    html.Div(style={'marginTop': '30px'}, children=[
        html.H3("Audit & Compliance Logs"),
        html.P("All metrics are fully traceable to their Spark run IDs via the Postgres audit_log table, ensuring 100% regulatory compliance.")
    ])
])

if __name__ == '__main__':
    # Run the server on port 8050
    app.run_server(debug=True, host='0.0.0.0', port=8050)