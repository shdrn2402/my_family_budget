import datetime as dt
import os
from datetime import date, datetime

import dash
import pandas as pd
import plotly.graph_objs as go
import psycopg2
from dash import dcc, html
from dash.dependencies import Input, Output
from dotenv import load_dotenv

load_dotenv()


DBNAME = os.environ.get('DBNAME')
USER = os.environ.get('USER')
PASSWORD = os.environ.get('PASSWORD')
HOST = os.environ.get('HOST')
PORT = os.environ.get('PORT')

# Подключение к базе данных
conn = psycopg2.connect(
    dbname=DBNAME,
    user=USER,
    password=PASSWORD,
    host=HOST,
    port=PORT
)


# Создание курсора
cur = conn.cursor()

# SQL-запрос для выборки данных
query = "SELECT * FROM budget.budget ORDER BY purchase_date;"

purchases_raw = pd.read_sql_query(query, conn).set_index('id')
purchases_raw['purchase_date'] = pd.to_datetime(
    purchases_raw['purchase_date'], utc=True)
purchases_raw['purchase_month'] = purchases_raw['purchase_date'].dt.month_name()
purchases_raw['purchase_year'] = purchases_raw['purchase_date'].dt.year
purchases_raw['purchase_year'] = pd.to_datetime(
    purchases_raw['purchase_year'], format='%Y')
conn.close()

month_order = {
    'January': 1,
    'February': 2,
    'March': 3,
    'April': 4,
    'May': 5,
    'June': 6,
    'July': 7,
    'August': 8,
    'September': 9,
    'October': 10,
    'November': 11,
    'December': 12
}

# Form data for the report
purchases_grouped = (purchases_raw.groupby(['purchase_category',
                                            'purchase_month',
                                            'purchase_year'])
                     .agg({'price': 'sum'})
                     .reset_index()
                     .rename(columns={'price': 'total_spents'})
                     )
purchases_grouped['month_order'] = purchases_grouped['purchase_month'].map(
    month_order)
purchases_grouped = purchases_grouped.sort_values('month_order')

# Form plots for visualization
data = []
for category in purchases_grouped['purchase_category'].unique():
    current = purchases_grouped.query('purchase_category == @category')
    data += [go.Scatter(x=current['purchase_month'],
                        y=current['total_spents'],
                        mode='lines',
                        stackgroup='one',
                        name=category)]

# Set layout
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(
    __name__, external_stylesheets=external_stylesheets, compress=False)
app.layout = html.Div(children=[

    # Form HTML
    html.H1(children='Total Spending by Categories'),

    # Year Selector
    html.Label('Select Year:'),
    dcc.DatePickerSingle(display_format='YYYY',
                         date=date(2023, 6, 1),
                         id='year_selector',
                         placeholder='Year'),

    # Mode Selector
    html.Label('Display Mode:'),
    dcc.RadioItems(
        options=[
            {'label': 'Absolute Values', 'value': 'absolute_values'},
            {'label': '% of Total', 'value': 'relative_values'},
        ],
        value='absolute_values',
        id='mode_selector'
    ),

    # Category Selector
    html.Label('Categories:'),
    dcc.Dropdown(options=[{'label': x, 'value': x} for x in purchases_grouped['purchase_category'].unique()],
                 value=purchases_grouped['purchase_category'].unique(
    ).tolist(),
        multi=True,
        id='category_selector'
    ),
    dcc.Graph(
        id='spendings_by_category'
    ),

])

# Define dashboard logic


@app.callback(
    Output('spendings_by_category', 'figure'),
    [Input('year_selector', 'date'),
     Input('mode_selector', 'value'),
     Input('category_selector', 'value')]
)
def update_figures(year_selector_date, mode, selected_categories):
    # Convert input to proper types
    year = dt.datetime.strptime(
        year_selector_date, '%Y-%m-%d').year  # Extract year from date
    year_datetime = datetime(year, 1, 1)
    # Apply filtering
    filtered_data = purchases_grouped[purchases_grouped['purchase_year']
                                      == year_datetime]
    filtered_data = filtered_data[filtered_data['purchase_category'].isin(
        selected_categories)]

    # Transform based on selected display mode
    if mode == 'relative_values':
        total_by_month = (filtered_data.groupby('purchase_month')
                          .agg({'total_spents': 'sum'})
                          .rename(columns={'total_spents': 'total_spent'})
                          )
        filtered_data = (filtered_data.set_index('purchase_month')
                         .join(total_by_month)
                         .reset_index()).sort_values('month_order')
        filtered_data['total_spents'] = filtered_data['total_spents'] / \
            filtered_data['total_spent']

    # Form plots for visualization with applied filters
    data = []
    for category in filtered_data['purchase_category'].unique():
        data += [go.Scatter(x=filtered_data[filtered_data['purchase_category'] == category]['purchase_month'],
                            y=filtered_data[filtered_data['purchase_category']
                                            == category]['total_spents'],
                            mode='lines',
                            stackgroup='one',
                            name=category)]

    # Form result for display
    return {
        'data': data,
        'layout': go.Layout(xaxis={'title': 'Month'},
                            yaxis={'title': 'Total Spendings'},
                            )
    }


if __name__ == '__main__':
    app.run_server(host='localhost', port=3000)
