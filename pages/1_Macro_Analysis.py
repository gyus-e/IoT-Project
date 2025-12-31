import streamlit as st
import plotly.express as px
from utils.load_data import df

from pages.sidebar import apply_filters

st.set_page_config(page_title="Macro Analysis", page_icon="🌍", layout="wide")

st.markdown("# 🌍 Macro Analisi Spazio-Temporale")
st.markdown("Visualizzazione dell'attività sismica nel Mediterraneo (2000-2025).")

if df is None:
    st.error("Dataset 'catalog.csv' non trovato. Esegui lo script di setup!")
    st.stop()


filtered_df, years, depth, magnitude = apply_filters(df)


col1, col2 = st.columns([3, 1])


with col1:
    filtered_df["name"] = filtered_df["time"].dt.strftime("Evento %Y-%m-%d %H:%M:%S")
    st.markdown("### Mappa Eventi")
    fig_map = px.scatter_map(
        filtered_df,
        # Marker settings
        lat="latitude",
        lon="longitude",
        size="magnitude",
        size_max=15,
        opacity=0.7,
        color="magnitude",
        color_continuous_scale=px.colors.sequential.Burgyl,
        hover_name="name",
        hover_data=["magnitude", "depth", "latitude", "longitude"],
        labels={
            "magnitude": "Magnitudo", 
            "depth": "Profondità (km)",
            "latitude": "Latitudine", 
            "longitude": "Longitudine"
        },
        # Map settings
        zoom=5,
        center={"lat": 42.0, "lon": 12.5},
        map_style="carto-darkmatter",
        title=f"Eventi Sismici ({len(filtered_df)} totali)",
    )
    st.plotly_chart(fig_map, width="stretch")
    

    st.markdown("### Timeline")
    # Time distribution
    filtered_df['year_month'] = filtered_df['time'].dt.to_period('M').astype(str)
    counts = filtered_df.groupby('year_month').size().reset_index(name='counts')
    fig_hist = px.bar(counts, x='year_month', y='counts', title="Eventi per Mese")
    fig_hist.update_xaxes(showticklabels=False)
    st.plotly_chart(fig_hist, width="stretch")


    st.markdown("### Pattern Spazio-Temporale (Migration)")
    st.markdown("_Permette di vedere se i terremoti si 'spostano' nel tempo (es. sequenze lungo una faglia)._")
    fig_st = px.scatter(
        filtered_df, 
        x="time", 
        y="latitude", 
        color="magnitude", 
        # size="magnitude",
        title="Space-Time Plot (Evoluzione Latitudinale)",
        color_continuous_scale=px.colors.sequential.Burgyl,
    )
    st.plotly_chart(fig_st, width="stretch")


with col2:

    st.markdown("### Statistiche Periodo")
    st.metric("Totale Eventi", len(filtered_df))
    if not filtered_df.empty:
        max_event = filtered_df.loc[filtered_df['magnitude'].idxmax()]
        st.metric("Evento Max (Magnitudo)", f"{max_event['magnitude']}")
        st.write(f"**Data**: {max_event['time'].date()}")
        st.write(f"**Coordinate**: ({max_event['latitude']}, {max_event['longitude']})")
        st.write(f"**Profondità**: {max_event['depth']} m")

        st.metric("Mese con più Eventi",
                  f"{filtered_df['time'].dt.to_period('M').mode()[0]} ({len(filtered_df[filtered_df['time'].dt.to_period('M') == filtered_df['time'].dt.to_period('M').mode()[0]])} eventi)")
        
        st.metric("Area più Attiva (Lat/Lon)",
                  f"({filtered_df['latitude'].mode()[0]:.2f}, {filtered_df['longitude'].mode()[0]:.2f})")
    else:
        max_event = None
        st.info("Nessun evento trovato con i filtri attuali.")

from utils.ai_assistant import render_ai_sidebar

# Dynamic Context for AI
active_filters_string = f"""
Filtri Attivi:
- Anni: {years[0]} - {years[1]}
- Magnitudo: {magnitude[0]} - {magnitude[1]}
- Profondità: {depth[0]} - {depth[1]} km
"""

if max_event is not None:
    max_event_string = f"""
    Evento con massima magnitudo:
    - Magnitudo: {max_event['magnitude']}, 
    - Profondità: {max_event['depth']} km,
    - Coordinate ({max_event['latitude']}, {max_event['longitude']}),
    - Data {max_event['time'].date()}.
    """
else:
    max_event_string = "- Nessun evento trovato con i filtri attuali."

context = f"""
Stai analizzando la pagina Macro Analisi.
DATI GENERALI:
- Eventi visualizzati: {len(filtered_df)}
{active_filters_string}
{max_event_string}

NUOVI GRAFICI (PATTERN RECOGNITION):
- Grafico Spazio-Temporale (Latitude vs Time): Serve a identificare la "migrazione sismica". 
  Se vedi diagonali di punti, significa che i terremoti si spostano lungo una faglia.
  Spiega all'utente se la distribuzione appare casuale (nuvole sparse) o se ci sono linee di tendenza (migrazione).
"""
render_ai_sidebar(context_text=context)
