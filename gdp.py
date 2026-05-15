# Reuse your python file that webscrapes GDP by country from the last homework and plots a stacked interactive bar plot using plotly. 
# Stack countries within regions using the IMF numbers
# Create streamlit app that displays a stacked bar plot of country GDPs stacked within regions.
# allow the user to select between the IMF, UN and World Bank reported numbers.

import requests as rq
import pandas as pd
import plotly.express as px
from io import StringIO
import streamlit as st
import country_converter as coco
import warnings
warnings.filterwarnings('ignore')


# run streamlit
# streamlit run "/Users/shaynademick/Downloads/Hw6/gdp.py"

# --- Fetch & parse ---
url = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"
page = rq.get(url, headers={"User-Agent": "Mozilla/5.0"})
tables = pd.read_html(StringIO(page.text))
GDP = tables[2].copy()

st.markdown("# List of countries by GDP (nominal)")

# Rename and clean
GDP.columns = ['Country', 'IMF_2026', 'WorldBank_2024', 'UN_2024']
GDP = GDP[~GDP['Country'].isin(['World', 'Country/Territory'])].copy()
GDP['Country'] = GDP['Country'].str.replace(r'\[.*?\]', '', regex=True).str.strip()

# Drop territories with known bad/corrupted Wikipedia values
bad_territories = {'U.S. Virgin Islands', 'United States Virgin Islands',
                   'Greenland', 'Saint Martin'}
GDP = GDP[~GDP['Country'].isin(bad_territories)]

# Sidebar select data source
data_source = st.sidebar.radio("Data Source", ["IMF 2026", "UN 2024", "World Bank 2024"])

# Shared region sets
north = {
    'United States', 'Canada', 'Mexico', 'Guatemala', 'Cuba', 'Dominican Republic',
    'Honduras', 'El Salvador', 'Nicaragua', 'Costa Rica', 'Panama', 'Haiti',
    'Jamaica', 'Trinidad and Tobago', 'Bahamas', 'Barbados', 'Belize', 'Puerto Rico'
}
middle_east = {
    'Saudi Arabia', 'Israel', 'United Arab Emirates', 'Qatar', 'Kuwait',
    'Iraq', 'Iran', 'Jordan', 'Bahrain', 'Oman', 'Lebanon', 'Yemen',
    'Syria', 'Palestine'
}


def clean_column(series):
    """Remove parenthetical years, footnotes, non-digits, then convert to numeric."""
    return (
        series
        .astype(str)
        .str.replace(r'\(.*?\)', '', regex=True)   # remove (2022) style years FIRST
        .str.replace(r'\[.*?\]', '', regex=True)   # remove footnotes
        .str.replace(r'[^\d]', '', regex=True)     # strip remaining non-digits
        .replace('', float('nan'))
    )


def assign_regions(df):
    cc = coco.CountryConverter()
    df['Region'] = cc.pandas_convert(series=df['Country'], to='continent', not_found=None)
    df.loc[(df['Region'] == 'America') & (df['Country'].isin(north)), 'Region'] = 'North America'
    df.loc[df['Region'] == 'America', 'Region'] = 'South America'
    df.loc[df['Country'].isin(middle_east), 'Region'] = 'Middle East'
    df = df.dropna(subset=['Region'])
    return df


def label_top_countries(df, col, n=8):
    df['Label'] = ''
    for region, grp in df.groupby('Region'):
        grp = grp.sort_values(col, ascending=False).copy()
        threshold = grp[col].iloc[min(n - 1, len(grp) - 1)]
        grp['Label'] = grp['Country'].where(grp[col] >= threshold, 'Other')
        df.loc[grp.index, 'Label'] = grp['Label']
    return df


if data_source == "IMF 2026":
    GDP['IMF_2026'] = clean_column(GDP['IMF_2026'])
    GDP['IMF_2026'] = pd.to_numeric(GDP['IMF_2026'], errors='coerce')
    GDP = GDP.dropna(subset=['IMF_2026'])
    GDP = GDP[GDP['IMF_2026'] < 50_000_000]
    GDP['IMF_2026'] = GDP['IMF_2026'] / 1_000_000

    GDP = assign_regions(GDP)
    GDP = label_top_countries(GDP, 'IMF_2026')

    GDP_grouped = GDP.groupby(['Region', 'Label'])['IMF_2026'].sum().reset_index()
    region_order = (
        GDP_grouped.groupby('Region')['IMF_2026']
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    fig = px.bar(
        GDP_grouped,
        x='Region',
        y='IMF_2026',
        color='Label',
        title='Nominal GDP by Country, Stacked Within Regions Using IMF Estimates',
        labels={'IMF_2026': 'GDP, IMF estimate (trillion current US$)', 'Label': 'Country'},
        category_orders={'Region': region_order},
    )
    fig.update_layout(
        barmode='stack',
        xaxis_title='Region',
        yaxis_title='GDP, IMF estimate (trillion current US$)',
        legend_title='Country',
        height=650,
        title_font_size=16,
        yaxis_tickformat='.0f',
        plot_bgcolor='#e8edf5',
        paper_bgcolor='white',
    )

elif data_source == "World Bank 2024":
    GDP['WorldBank_2024'] = clean_column(GDP['WorldBank_2024'])
    GDP['WorldBank_2024'] = pd.to_numeric(GDP['WorldBank_2024'], errors='coerce')
    GDP = GDP.dropna(subset=['WorldBank_2024'])
    GDP = GDP[GDP['WorldBank_2024'] < 50_000_000]
    GDP['WorldBank_2024'] = GDP['WorldBank_2024'] / 1_000_000

    GDP = assign_regions(GDP)
    GDP = label_top_countries(GDP, 'WorldBank_2024')

    GDP_grouped = GDP.groupby(['Region', 'Label'])['WorldBank_2024'].sum().reset_index()
    region_order = (
        GDP_grouped.groupby('Region')['WorldBank_2024']
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    fig = px.bar(
        GDP_grouped,
        x='Region',
        y='WorldBank_2024',
        color='Label',
        title='Nominal GDP by Country, Stacked Within Regions Using World Bank Estimates',
        labels={'WorldBank_2024': 'GDP, World Bank estimate (trillion current US$)', 'Label': 'Country'},
        category_orders={'Region': region_order},
    )
    fig.update_layout(
        barmode='stack',
        xaxis_title='Region',
        yaxis_title='GDP, World Bank estimate (trillion current US$)',
        legend_title='Country',
        height=650,
        title_font_size=16,
        yaxis_tickformat='.0f',
        plot_bgcolor='#e8edf5',
        paper_bgcolor='white',
    )

else:  # UN 2024
    GDP['UN_2024'] = clean_column(GDP['UN_2024'])
    GDP['UN_2024'] = pd.to_numeric(GDP['UN_2024'], errors='coerce')
    GDP = GDP.dropna(subset=['UN_2024'])
    GDP = GDP[GDP['UN_2024'] < 50_000_000]
    GDP['UN_2024'] = GDP['UN_2024'] / 1_000_000

    GDP = assign_regions(GDP)
    GDP = label_top_countries(GDP, 'UN_2024')

    GDP_grouped = GDP.groupby(['Region', 'Label'])['UN_2024'].sum().reset_index()
    region_order = (
        GDP_grouped.groupby('Region')['UN_2024']
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    fig = px.bar(
        GDP_grouped,
        x='Region',
        y='UN_2024',
        color='Label',
        title='Nominal GDP by Country, Stacked Within Regions Using UN Estimates',
        labels={'UN_2024': 'GDP, UN estimate (trillion current US$)', 'Label': 'Country'},
        category_orders={'Region': region_order},
    )
    fig.update_layout(
        barmode='stack',
        xaxis_title='Region',
        yaxis_title='GDP, UN estimate (trillion current US$)',
        legend_title='Country',
        height=650,
        title_font_size=16,
        yaxis_tickformat='.0f',
        plot_bgcolor='#e8edf5',
        paper_bgcolor='white',
    )


st.plotly_chart(fig, use_container_width=True)