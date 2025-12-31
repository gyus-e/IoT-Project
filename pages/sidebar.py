import streamlit as st
import pandas as pd
from utils.load_data import df

st.sidebar.header("Filtri")

if df is None:
    st.error("Dataset 'catalog.csv' non trovato. Esegui lo script di setup!")
    st.stop()
    
min_year = int(df['time'].dt.year.min()) 
max_year = int(df['time'].dt.year.max())
max_depth = df['depth'].max()
min_mag = df['magnitude'].min()
max_mag = df['magnitude'].max()

years = st.sidebar.slider("Intervallo Anni", min_year, max_year, (min_year, max_year))
depth = st.sidebar.slider("Profondità (km)", 0.0, max_depth, (0.0, max_depth), 10.0)
magnitude = st.sidebar.slider("Magnitudo", 0.0, 10.5, (min_mag, max_mag), 0.5)


def apply_filters(df: pd.DataFrame):
    filtered_df = df[
        (df['time'].dt.year >= years[0]) & 
        (df['time'].dt.year <= years[1]) & 
        (df['magnitude'] >= magnitude[0]) & 
        (df['magnitude'] <= magnitude[1]) & 
        (df['depth'] >= depth[0]) & 
        (df['depth'] <= depth[1])
    ].copy()

    return filtered_df, years, depth, magnitude