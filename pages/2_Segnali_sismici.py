import time
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from obspy import UTCDateTime

from utils.fetch_waveform import fetch_waveform
from utils.ai_assistant import render_ai_assistant

st.set_page_config(
    # page_title="Signal Lab", 
    # page_icon="🔬", 
    layout="wide",
    initial_sidebar_state="expanded",
)

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

@st.cache_data(ttl=60)
def fft_analysis(df: pd.DataFrame):
    if df.empty:
        return pd.DataFrame()
    fft_vals = np.fft.rfft(df['velocity'])
    fft_freq = np.fft.rfftfreq(len(df['velocity']), d=1/100) # assuming 100Hz        
    fft_df = pd.DataFrame({'Freq (Hz)': fft_freq, 'Power': np.abs(fft_vals)})
    fft_df = fft_df[fft_df['Freq (Hz)'] < 20]
    return fft_df


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

    st.markdown (f"## Stazione: {stations_names[station]} ({station})")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### Dominio del tempo")
        fig = go.Figure()
        # Ensure times are datetime for proper valid plotting
        fig.add_trace(go.Scatter(x=df['times'], y=df['velocity'], line=dict(color=stations_colors[station], width=1), name="Velocity"))
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), xaxis_title="Time", yaxis_title="Velocity (m/s)")
        st.plotly_chart(fig, width='stretch', height=300)

        st.markdown("#### Dominio delle frequenze")
        fft_df = fft_analysis(df)
        if not fft_df.empty:
            fig_fft = px.line(fft_df, x='Freq (Hz)', y='Power')
            st.plotly_chart(fig_fft, width='stretch', height=300)

    with col2:
        # Calculate simple Z-Score on a rolling window
        window_size = 100 # 1 second if 100Hz
        # Rolling on dataframe with datetime index or just column? 
        # Rolling works on index or if generic, on rows. 
        # We assume regular sampling approx.
        df['rolling_mean'] = df['velocity'].rolling(window_size).mean()
        df['rolling_std'] = df['velocity'].rolling(window_size).std()        
        # Avoid div by zero
        df['z_score_inst'] = (df['velocity'] - df['rolling_mean']).abs() / (df['rolling_std'] + 1e-6)
        max_z = df['z_score_inst'].max()
        # avg_z = df['z_score_inst'].mean()
        st.metric("Max Z-Score (Allarme)", f"{max_z:.1f}", delta="CRITICAL" if max_z > 5 else "NORMAL")
        if max_z > 5:
            st.error("🚨 ALLARME SISMICO ATTIVATO")
            st.write("Trigger immediato (< 2s)")


@st.fragment(run_every=2)
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

render_realtime_dashboard()





#TODO: aggiornare il contesto
context=f"""
"""
render_ai_assistant(context_text=context)
