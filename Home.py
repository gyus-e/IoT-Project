import streamlit as st
import plotly.express as px

from utils.sidebar import Sidebar
from utils.load_data import load_data
from utils.max_event import get_max_event
from utils.ai_assistant import render_ai_assistant


unfiltered_df = load_data()
if unfiltered_df is None:
    st.error("Dataset 'catalog.csv' non trovato. Esegui lo script di setup!")
    st.stop()
Sidebar.init_sidebar(unfiltered_df)
df, years, depth, magnitude = Sidebar.apply_filters(unfiltered_df)


st.set_page_config(
    # page_title="Home",
    # page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "## Earthquake Analysis Dashboard\nThis dashboard provides insights into seismic activity using interactive visualizations and statistics.",
    }
)


# Custom CSS
# st.markdown("""
# <style>
#     .stApp {
#         background-color: #0e1117;
#         color: #fafafa;
#     }
#     .metric-card {
#         background-color: #262730;
#         padding: 20px;
#         border-radius: 10px;
#         border: 1px solid #4a4a4a;
#         box-shadow: 0 4px 6px rgba(0,0,0,0.3);
#     }
#     h1, h2, h3 {
#         color: #ff4b4b; /* Streamlit Red/Orange */
#     }
# </style>
# """, unsafe_allow_html=True)


col1, col2 = st.columns([3, 1])

with col1:
    # st.markdown("### Mappa degli Eventi Sismici")
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
        map_style="open-street-map",
        title="Mappa degli Eventi Sismici",
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

#TODO: aggiornare il contesto
context=f"""
"""
render_ai_assistant(context_text=context)
