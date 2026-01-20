import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from obspy import UTCDateTime

from utils.fetch_waveform import fetch_waveform
from utils.ai_assistant import render_ai_assistant
from utils.fetch_waveform import fetch_waveform
from utils.ai_assistant import render_ai_assistant
from utils.seismology import fft_analysis

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Segnali sismici")

with st.sidebar:
    st.markdown("### Impostazioni")
    refresh_rate_options = {
        "30 secondi": 30,
        "1 minuto": 60,
        "2 minuti": 120,
        "5 minuti": 300
    }
    selected_refresh_label = st.selectbox(
        "Tempo di aggiornamento",
        options=list(refresh_rate_options.keys()),
        index=1 # Default to 1 minute
    )
    refresh_rate = refresh_rate_options[selected_refresh_label]

# http://portale2.ov.ingv.it/segnali/OVO_HHZ_attuale.html
stations = [
    "OVO",   # Osservatorio Vesuviano
    "CSFT",  # Campi Solfatara
    "IOCA",  # Ischia Osservatorio Casamicciola
    "SORR",  # Sorrento
]

stations_names = {
    "OVO": "Osservatorio Vesuviano",
    "CSFT": "Campi Flegrei - Solfatara",
    "IOCA": "Ischia - Osservatorio Casamicciola",
    "SORR": "Sorrento",
}

stations_channels = {
    "OVO": "HHZ",
    "CSFT": "HHZ",
    "IOCA": "HHZ",
    "SORR": "HHZ",
}

stations_colors = {
    "OVO": "orange",
    "CSFT": "red",
    "IOCA": "green",
    "SORR": "purple",
}

# Functions defined outside fragment to be reusable/static

# Initialize session state for buffers
if "waveforms" not in st.session_state:
    st.session_state.waveforms = {}



def update_buffer(station, target_end_time, window_duration=300):
    """
    Updates the waveform buffer for a station.
    Fetches only missing data since the last update.
    """
    buffer = st.session_state.waveforms.get(station)
    
    # Define channel
    channel = stations_channels[station]
    
    if buffer is None or buffer.empty:
        # Initial fill
        start_time = target_end_time - pd.Timedelta(seconds=window_duration)
        new_df = fetch_waveform(station, UTCDateTime(start_time), duration=window_duration, channel=channel)
        if new_df is not None and not new_df.empty:
            st.session_state.waveforms[station] = new_df
    else:
        # Incremental update
        last_time = buffer['times'].max()
        
        # If the gap is too large (e.g. > 10s), reset and full fetch
        if (target_end_time - last_time).total_seconds() > 10:
             # Reset buffer
             start_time = target_end_time - pd.Timedelta(seconds=window_duration)
             new_df = fetch_waveform(station, UTCDateTime(start_time), duration=window_duration, channel=channel)
             if new_df is not None and not new_df.empty:
                 st.session_state.waveforms[station] = new_df
             return

        # Fetch only new data if needed
        # We add a small overlap (0.1s) to ensure continuity/stitching
        fetch_start = last_time - pd.Timedelta(seconds=0.1)
        duration_to_fetch = (target_end_time - fetch_start).total_seconds()
        
        if duration_to_fetch > 0:
            new_df = fetch_waveform(station, UTCDateTime(fetch_start), duration=duration_to_fetch, channel=channel)
            
            if new_df is not None and not new_df.empty:
                # Concatenate
                combined = pd.concat([buffer, new_df])
                # Drop duplicates on time
                combined = combined.drop_duplicates(subset='times')
                # Sort
                combined = combined.sort_values('times')
                # Trim to window size
                cutoff_time = target_end_time - pd.Timedelta(seconds=window_duration)
                combined = combined[combined['times'] >= cutoff_time]
                
                st.session_state.waveforms[station] = combined


def render_tab(station):
    df = st.session_state.waveforms.get(station)
    
    if df is None or df.empty:
        st.warning("In attesa di dati...")
        return

    st.subheader(f"Stazione: {stations_names[station]} ({station})")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Dominio del tempo**")
        fig = go.Figure()
        # Ensure times are datetime for proper valid plotting
        fig.add_trace(go.Scatter(x=df['times'], y=df['velocity'], line=dict(color=stations_colors[station], width=1), name="Velocity"))
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), xaxis_title="Time", yaxis_title="Velocity (m/s)")
        st.plotly_chart(fig, width='stretch', height=300)

        st.markdown("**Dominio delle frequenze**")
        fft_df = fft_analysis(df)
        if not fft_df.empty:
            fig_fft = px.line(fft_df, x='Freq (Hz)', y='Power')
            fig_fft.update_traces(line_color=stations_colors[station])
            st.plotly_chart(fig_fft, width='stretch', height=300)

    with col2:
        # Calculate simple Z-Score on a rolling window
        window_size = 100 # 1 second if 100Hz
        # We assume regular sampling approx.
        df['rolling_mean'] = df['velocity'].rolling(window_size).mean()
        df['rolling_std'] = df['velocity'].rolling(window_size).std()        
        # Avoid div by zero
        df['z_score_inst'] = (df['velocity'] - df['rolling_mean']).abs() / (df['rolling_std'] + 1e-6)
        max_z = df['z_score_inst'].max()
        # avg_z = df['z_score_inst'].mean()
        st.metric("Max Z-Score (allarme)", f"{max_z:.1f}", delta="CRITICAL" if max_z > 5 else "NORMAL")
        
        # Update status for AI Context
        if 'realtime_status' not in st.session_state: st.session_state.realtime_status = {}
        st.session_state.realtime_status[station] = {
            "max_z": max_z,
            "status": "ALLARME" if max_z > 5 else "Normale"
        }

        if max_z > 5:
            st.error("ALLARME SISMICO ATTIVATO")
            st.write("Trigger immediato (< 2s)")


@st.fragment(run_every=refresh_rate)
def render_realtime_dashboard():
    # Create tabs inside the fragment
    tab_ovo, tab_csft, tab_ioca, tab_sorr = st.tabs(stations)
    
    # Target time: now (delayed by ~5m to match original logic)
    now = UTCDateTime.now()
    window_duration = 300
    target_end_time = now - 300 
    
    # Convert to pandas timestamp for buffer arithmetic
    target_end_pd = pd.Timestamp(target_end_time.datetime)
    
    update_buffer(stations[0], target_end_pd, window_duration)
    update_buffer(stations[1], target_end_pd, window_duration)
    update_buffer(stations[2], target_end_pd, window_duration)
    update_buffer(stations[3], target_end_pd, window_duration)

    with tab_ovo:
        render_tab(stations[0])

    with tab_csft:
        render_tab(stations[1])

    with tab_ioca:
        render_tab(stations[2])

    with tab_sorr:
        render_tab(stations[3])


# --- Realtime Section ---

st.header("Segnali in tempo reale")
render_realtime_dashboard()

# --- Comparison Section ---

st.markdown("---")
st.header("Confronto eventi: Naturale vs antropico")

event_tabs = st.tabs(["Evento naturale (Terremoto Campania)", "Evento antropico (Festa scudetto)"])

# Load comparison data
@st.cache_data
def load_comparison_data():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    quake = pd.read_csv(os.path.join(data_dir, 'waveform_max_event_flegrei.csv')) if os.path.exists(os.path.join(data_dir, 'waveform_max_event_flegrei.csv')) else None
    napoli = pd.read_csv(os.path.join(data_dir, 'waveform_napoli_scudetto.csv')) if os.path.exists(os.path.join(data_dir, 'waveform_napoli_scudetto.csv')) else None
    return quake, napoli

quake_df, napoli_df = load_comparison_data()

def render_comparison_tab(df, title, color):
    if df is None:
        st.warning("Dati non trovati. Esegui `scripts/fetch_data.py`.")
        return

    st.subheader(f"{title}")
    
    # Time Domain
    st.markdown("**Dominio del tempo**")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['times'], y=df['velocity'], line=dict(color=color, width=1), name="Velocity"))
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="Time", yaxis_title="Velocity (m/s)")
    st.plotly_chart(fig, width='stretch', height=250)

    # Frequency Domain
    st.markdown("**Dominio delle frequenze**")
    fft_df = fft_analysis(df)
    if not fft_df.empty:
        fig_fft = px.line(fft_df, x='Freq (Hz)', y='Power')
        fig_fft.update_traces(line_color=color)
        fig_fft.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_fft, width='stretch', height=250)


# Get specific event info
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
max_event_path = os.path.join(data_dir, "max_event_flegrei.csv")

if os.path.exists(max_event_path):
    max_e_df = pd.read_csv(max_event_path)
    # It's a single row dataframe if saved via transpose
    if not max_e_df.empty:
        max_e = max_e_df.iloc[0]
        date_str = pd.to_datetime(max_e['time']).strftime('%d/%m/%Y')
        quake_title = f"Terremoto Campi Flegrei {date_str} (M{max_e['magnitude']})"
    else:
        quake_title = "Terremoto (Max Campi Flegrei)"
else:
    st.warning("Dati non trovati. Esegui `scripts/fetch_data.py`.")
    quake_title = "Terremoto (Max Campi Flegrei)"

with event_tabs[0]:
    render_comparison_tab(
        quake_df, 
        quake_title, 
        "green"
    )

with event_tabs[1]:
    render_comparison_tab(
        napoli_df, 
        "Festa scudetto Napoli (Stadio Maradona)", 
        "blue"
    )


# --- AI Context Generation ---
realtime_context = "MONITORAGGIO TEMPO REALE:\n"
if 'realtime_status' in st.session_state:
    for st_code, status in st.session_state.realtime_status.items():
        realtime_context += f"- Stazione {st_code}: Z-Score={status['max_z']:.1f} ({status['status']})\n"
else:
    realtime_context += "In attesa di dati dalle stazioni...\n"

comparison_context = f"""
CONFRONTO EVENTI:
1. {quake_title} (Naturale)
2. Festa Scudetto Napoli (Antropico)
"""

st.session_state['ai_context_global'] = realtime_context + "\n" + comparison_context
st.session_state['ai_context_selection'] = ""

render_ai_assistant(context_text="Pagina Lab Segnali: Monitoraggio realtime e confronto firma sismica.")
