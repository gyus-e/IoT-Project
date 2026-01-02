import streamlit as st
import pandas as pd

class Sidebar:
    years: tuple[int, int] = (0, 0)
    depth: tuple[float, float] = (0.0, 0.0)
    magnitude: tuple[float, float] = (0.0, 0.0)
    latitude: tuple[float, float] = (0.0, 0.0)
    longitude: tuple[float, float] = (0.0, 0.0)

    @classmethod
    def init_sidebar(cls, df: pd.DataFrame):
        st.sidebar.header("Filtri")

        if df is None:
            st.error("Dataset 'catalog.csv' non trovato. Esegui lo script di setup!")
            st.stop()
            
        min_year = int(df['time'].dt.year.min()) 
        max_year = int(df['time'].dt.year.max())
        max_depth = df['depth'].max()
        min_mag = df['magnitude'].min()
        max_mag = df['magnitude'].max()
        minlatitude = 27.0
        maxlatitude = 48.0 
        minlongitude = -7.0 
        maxlongitude = 37.5

        cls.years = st.sidebar.slider("Periodo", min_year, max_year, (min_year, max_year))
        cls.depth = st.sidebar.slider("Profondità (km)", 0.0, max_depth, (0.0, max_depth), 10.0)
        cls.latitude = st.sidebar.slider("Latitudine", minlatitude, maxlatitude, (minlatitude, maxlatitude), 0.1)
        cls.longitude = st.sidebar.slider("Longitudine", minlongitude, maxlongitude, (minlongitude, maxlongitude), 0.1)
        cls.magnitude = st.sidebar.slider("Magnitudo", 0.0, 10.5, (min_mag, max_mag), 0.5)


    @classmethod
    def apply_filters(cls, df: pd.DataFrame):
        filtered_df = df[
            (df['time'].dt.year >= cls.years[0]) & 
            (df['time'].dt.year <= cls.years[1]) & 
            (df['magnitude'] >= cls.magnitude[0]) & 
            (df['magnitude'] <= cls.magnitude[1]) & 
            (df['depth'] >= cls.depth[0]) & 
            (df['depth'] <= cls.depth[1]) & 
            (df['latitude'] >= cls.latitude[0]) &
            (df['latitude'] <= cls.latitude[1]) &
            (df['longitude'] >= cls.longitude[0]) &
            (df['longitude'] <= cls.longitude[1])
        ].copy()

        return filtered_df, cls.years, cls.depth, cls.magnitude