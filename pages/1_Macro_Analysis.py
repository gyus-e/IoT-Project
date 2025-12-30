import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Macro Analysis", page_icon="🌍", layout="wide")

st.markdown("# 🌍 Macro Analisi Spazio-Temporale")
st.markdown("Visualizzazione dell'attività sismica in Italia (2000-2024).")

# Load Data
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
catalog_path = os.path.join(DATA_DIR, 'catalog.csv')

@st.cache_data
def load_data():
    if not os.path.exists(catalog_path):
        return None
    df = pd.read_csv(catalog_path)
    df['time'] = pd.to_datetime(df['time'])
    return df

df = load_data()

if df is None:
    st.error("Dataset 'catalog.csv' non trovato. Esegui lo script di setup!")
    st.stop()

# Sidebar Filters
st.sidebar.header("Filtri")

min_year = int(df['time'].dt.year.min())
max_year = int(df['time'].dt.year.max())
max_depth = df['depth'].max()
min_mag = df['magnitude'].min()
max_mag = df['magnitude'].max()

years = st.sidebar.slider("Intervallo Anni", min_year, max_year, (min_year, max_year))
depth = st.sidebar.slider("Profondità (km)", 0.0, max_depth, (0.0, max_depth), 10.0)
magnitude = st.sidebar.slider("Magnitudo", 0.0, 10.5, (min_mag, max_mag), 0.5)

# Apply filters
filtered_df = df[
    (df['time'].dt.year >= years[0]) & 
    (df['time'].dt.year <= years[1]) & 
    (df['magnitude'] >= magnitude[0]) & 
    (df['magnitude'] <= magnitude[1]) & 
    (df['depth'] >= depth[0]) & 
    (df['depth'] <= depth[1])
].copy()


col1, col2 = st.columns([3, 1])


with col1:
    st.markdown("### Mappa Eventi")
    fig_map = px.scatter_map(
        filtered_df,
        lat="latitude",
        lon="longitude",
        color="magnitude",
        size="magnitude",
        color_continuous_scale=px.colors.cyclical.IceFire,
        size_max=15,
        zoom=5,
        center={"lat": 42.0, "lon": 12.5},
        map_style="carto-darkmatter",
        hover_data=["time", "depth"],
        title=f"Eventi Sismici ({len(filtered_df)} totali)"
    )
    st.plotly_chart(fig_map, width="stretch")

with col2:
    st.markdown("### Statistiche Periodo")
    st.metric("Totale Eventi", len(filtered_df))
    if not filtered_df.empty:
        max_event = filtered_df.loc[filtered_df['magnitude'].idxmax()]
        st.metric("Evento Max (Magnitudo)", f"{max_event['magnitude']}")
        st.write(f"**Data**: {max_event['time'].date()}")
        st.write(f"**Profondità**: {max_event['depth']} km")
    
    st.markdown("### Timeline")
    # Time distribution
    filtered_df['year_month'] = filtered_df['time'].dt.to_period('M').astype(str)
    counts = filtered_df.groupby('year_month').size().reset_index(name='counts')
    fig_hist = px.bar(counts, x='year_month', y='counts', title="Eventi per Mese")
    fig_hist.update_xaxes(showticklabels=False)
    st.plotly_chart(fig_hist, width="stretch")

    st.markdown("### Pattern Spazio-Temporale (Migration)")
    st.markdown("_Permette di vedere se i terremoti si 'spostano' nel tempo (es. sequenze lungo una faglia)._")
    fig_st = px.scatter(filtered_df, x="time", y="latitude", 
                        color="magnitude", size="magnitude",
                        title="Space-Time Plot (Evoluzione Latitudinale)",
                        color_continuous_scale=px.colors.cyclical.IceFire)
    st.plotly_chart(fig_st, width="stretch")

from utils.ai_assistant import render_ai_sidebar

# Dynamic Context for AI
context = f"""
Stai analizzando la pagina Macro Analisi.
DATI GENERALI:
- Eventi visualizzati: {len(filtered_df)}
- Filtri: Anni {years[0]}-{years[1]}, Magnitudo min {min_mag}.
- Evento Max: {filtered_df['magnitude'].max() if not filtered_df.empty else 'N/A'}

NUOVI GRAFICI (PATTERN RECOGNITION):
- Grafico Spazio-Temporale (Latitude vs Time): Serve a identificare la "migrazione sismica". 
  Se vedi diagonali di punti, significa che i terremoti si spostano lungo una faglia.
  Spiega all'utente se la distribuzione appare casuale (nuvole sparse) o se ci sono linee di tendenza (migrazione).
"""
render_ai_sidebar(context_text=context)
