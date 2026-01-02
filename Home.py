import streamlit as st
import plotly.express as px

from utils.load_data import df as unfiltered_df
from utils.sidebar import Sidebar
from utils.max_event import get_max_event
# from utils.ai_assistant import render_ai_sidebar


st.set_page_config(
    # page_title="Home",
    # page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .metric-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #4a4a4a;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    h1, h2, h3 {
        color: #ff4b4b; /* Streamlit Red/Orange */
    }
</style>
""", unsafe_allow_html=True)


if unfiltered_df is None:
    st.error("Dataset 'catalog.csv' non trovato. Esegui lo script di setup!")
    st.stop()
Sidebar.init_sidebar(unfiltered_df)
df, years, depth, magnitude = Sidebar.apply_filters(unfiltered_df)


col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### Mappa degli Eventi Sismici")
    df["name"] = df["time"].dt.strftime("Evento %Y-%m-%d %H:%M:%S")
    fig_map = px.scatter_map(
        df,
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
        # title=f"Eventi Sismici ({len(filtered_df)} totali)",
        height=800,
    )
    st.plotly_chart(fig_map, width="stretch")

with col2:
    st.markdown("### Statistiche")
    st.metric("Totale Eventi", len(df))
    if not df.empty:
        max_event = get_max_event(df)
        if max_event is not None:
            st.metric("Magnitudo più alta registrata", f"{max_event['magnitude']}")
            st.metric("Data evento con massima magnitudo", f"{max_event['time'].date()}")
            st.metric("Coordinate evento con massima magnitudo", f"({max_event['latitude']}, {max_event['longitude']})")
            st.metric("Profondità evento con massima magnitudo", f"{max_event['depth']} km")

        mean_mag = df['magnitude'].mean()
        std_mag = df['magnitude'].std()
        st.metric("Magnitudo Media", f"{mean_mag:.2f}")
        st.metric("Deviazione Std Magnitudo", f"{std_mag:.2f}")

        st.metric("Mese con più Eventi",
                  f"{df['time'].dt.to_period('M').mode()[0]} ({len(df[df['time'].dt.to_period('M') == df['time'].dt.to_period('M').mode()[0]])} eventi)")
        
        st.metric("Area più Attiva (Lat/Lon)",
                  f"({df['latitude'].mode()[0]:.2f}, {df['longitude'].mode()[0]:.2f})")
    else:
        max_event = None
        st.info("Nessun evento trovato con i filtri attuali.")



# # Dynamic Context for AI
# active_filters_string = f"""
# Filtri Attivi:
# - Anni: {years[0]} - {years[1]}
# - Magnitudo: {magnitude[0]} - {magnitude[1]}
# - Profondità: {depth[0]} - {depth[1]} km
# """

# if max_event is not None:
#     max_event_string = f"""
#     Evento con massima magnitudo:
#     - Magnitudo: {max_event['magnitude']}, 
#     - Profondità: {max_event['depth']} km,
#     - Coordinate ({max_event['latitude']}, {max_event['longitude']}),
#     - Data {max_event['time'].date()}.
#     """
# else:
#     max_event_string = "- Nessun evento trovato con i filtri attuali."

# context = f"""
# Stai analizzando la pagina Macro Analisi.
# DATI GENERALI:
# - Eventi visualizzati: {len(filtered_df)}
# {active_filters_string}
# {max_event_string}

# NUOVI GRAFICI (PATTERN RECOGNITION):
# - Grafico Spazio-Temporale (Latitude vs Time): Serve a identificare la "migrazione sismica". 
#   Se vedi diagonali di punti, significa che i terremoti si spostano lungo una faglia.
#   Spiega all'utente se la distribuzione appare casuale (nuvole sparse) o se ci sono linee di tendenza (migrazione).
# """
# render_ai_sidebar(context_text=context)