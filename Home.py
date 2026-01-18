import streamlit as st
import plotly.express as px

from utils.sidebar import Sidebar
from utils.load_data import load_data
from utils.max_event import get_max_event
from utils.ai_assistant import render_ai_assistant
from utils.fetch_waveform import fetch_waveform, get_nearby_stations
from utils.seismology import fft_analysis


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



@st.fragment
def render_map_with_interaction(df):
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
    fig_map.update_traces(unselected=dict(marker=dict(opacity=0.7))) # do not blur unselected markers, keep default opacity
    event = st.plotly_chart(fig_map, width="stretch", on_select="rerun", selection_mode="points")

    if event and event.selection and event.selection.points:
        # Recupera l'indice del punto selezionato
        point = event.selection.points[0]
        # Handle both object and dict access just in case, but error said dict
        point_idx = point["point_index"] if isinstance(point, dict) else point.point_index
        # Validazione dell'indice
        if point_idx < len(df):
            selected_event = df.iloc[point_idx]
            
            st.markdown("---")
            st.markdown(f"### Analisi Sismica: Evento del {selected_event['time']}")
            
            col_wave_info, col_wave_plot = st.columns([1, 3])
            
            
            col_wave_info, col_wave_plot = st.columns([1, 3])
            
            with col_wave_info:
                status_placeholder = st.empty()
                status_placeholder.info("Ricerca stazioni vicine...")
                
                stations = get_nearby_stations(selected_event['latitude'], selected_event['longitude'], selected_event['time'])
                
                if not stations:
                    status_placeholder.warning("Nessuna stazione trovata (raggio 1.0°).")
                else:
                    status_placeholder.empty() # Clear the info message
                    st.write(f"Stazioni trovate: {', '.join(stations)}")
            
            wave_df = None
            found_station = None
            
            if stations:
                with col_wave_plot:
                    with st.spinner(f"Ricerca dati waveform..."):
                        for station in stations:
                            wave_df = fetch_waveform(station, selected_event['time'])
                            if wave_df is not None:
                                found_station = station
                                break
                    
                    if wave_df is not None:
                        st.success(f"Dati recuperati da stazione: **{found_station}**")
                        
                        # Create two columns for Time Domain and Frequency Domain
                        col_time, col_freq = st.columns(2)
                        
                        with col_time:
                            st.markdown("**Dominio del tempo**")
                            fig_wave = px.line(wave_df, x="times", y="velocity", 
                                             labels={"times": "Tempo", "velocity": "Velocità"})
                            fig_wave.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
                            st.plotly_chart(fig_wave, key="wave_chart_time", width="stretch", on_select="ignore", selection_mode="points")
                            
                        with col_freq:
                            st.markdown("**Dominio delle frequenze**")
                            fft_df = fft_analysis(wave_df)
                            if not fft_df.empty:
                                fig_fft = px.line(fft_df, x='Freq (Hz)', y='Power',
                                                labels={'Freq (Hz)': 'Freq (Hz)', 'Power': 'Power'})
                                fig_fft.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
                                st.plotly_chart(fig_fft, key="wave_chart_freq", width="stretch")
                            else:
                                st.caption("Analisi in frequenza non disponibile.")
                    else:
                        st.error(f"Nessun dato waveform disponibile per le stazioni: {', '.join(stations)}")
            
            # Update Context for AI
            st.session_state['ai_context_selection'] = f"""
            EVENTO SELEZIONATO:
            - Data/Ora: {selected_event['time']}
            - Magnitudo: {selected_event['magnitude']}
            - Profondità: {selected_event['depth']} km
            - Località (Lat/Lon): {selected_event['latitude']}, {selected_event['longitude']}
            - Stazione Dati: {found_station if found_station else 'Nessuna (Nessun dato waveform trovato)'}
            - Dati Waveform: {'Disponibili' if wave_df is not None else 'Non disponibili'}
            """
        else:
             st.session_state['ai_context_selection'] = "Nessun evento selezionato."
    else:
        st.session_state['ai_context_selection'] = "Nessun evento selezionato."


col1, col2 = st.columns([3, 1])

with col1:
    render_map_with_interaction(df)

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

# --- AI Context Generation ---
if not df.empty:
    stats_context = f"""
    STATISTICHE DATASET FILTRATO:
    - Numero eventi: {len(df)}
    - Magnitudo Media: {df['magnitude'].mean():.2f}
    - Magnitudo Max: {df['magnitude'].max()}
    - Profondità Media: {df['depth'].mean():.2f} km
    """
    
    max_event = get_max_event(df)
    if max_event is not None:
        stats_context += f"""
        EVENTO MASSIMO:
        - Data: {max_event['time']}
        - Magnitudo: {max_event['magnitude']}
        - Posizione: {max_event['latitude']}, {max_event['longitude']}
        """
else:
    stats_context = "Nessun evento visibile con i filtri correnti."

st.session_state['ai_context_global'] = stats_context

# Initialize selection context if not present (to avoid errors on first run)
if 'ai_context_selection' not in st.session_state:
    st.session_state['ai_context_selection'] = "Nessun evento selezionato."

render_ai_assistant(context_text="Analisi della Home Page con mappa interattiva.")

