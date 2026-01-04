import time
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from obspy import UTCDateTime

from utils.fetch_waveform import fetch_waveform


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
    "CSFT": "blue",
    "IOCA": "green",
    "SORR": "purple",
}

starttime = UTCDateTime(UTCDateTime.now() - 180)

tab_ovo, tab_csft, tab_ioca, tab_sorr = st.tabs(stations)

def load_tab(station: str, starttime: UTCDateTime, duration=120):
    df = fetch_waveform(
        station=station, 
        starttime=starttime,
        duration=duration,
        channel=stations_channels[station]
    )
    if df is None:
        st.markdown("Loading...")
        time.sleep(5) # Debounce time
        load_tab(station, starttime, duration) # Retry recursively
        return

    st.markdown (f"## Stazione: {stations_names[station]} ({station})")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### Dominio del tempo")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['times'], y=df['velocity'], line=dict(color=stations_colors[station], width=1), name="Velocity"))
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), xaxis_title="Time (s)", yaxis_title="Velocity (m/s)")
        st.plotly_chart(fig, use_container_width=True, height=300)

        st.markdown("#### Dominio delle frequenze")
        # Simple FFT of the whole signal
        fft_vals = np.fft.rfft(df['velocity'])
        fft_freq = np.fft.rfftfreq(len(df['velocity']), d=1/100) # assuming 100Hz        
        fft_df = pd.DataFrame({'Freq (Hz)': fft_freq, 'Power': np.abs(fft_vals)})
        # Filter useful range 0-20Hz
        fft_df = fft_df[fft_df['Freq (Hz)'] < 20]
        fig_fft = px.line(fft_df, x='Freq (Hz)', y='Power')
        st.plotly_chart(fig_fft, use_container_width=True, height=300)

    with col2:
        # Calculate simple Z-Score on a rolling window
        window_size = 100 # 1 second if 100Hz
        df['rolling_mean'] = df['velocity'].rolling(window_size).mean()
        df['rolling_std'] = df['velocity'].rolling(window_size).std()        
        # Avoid div by zero
        df['z_score_inst'] = (df['velocity'] - df['rolling_mean']).abs() / (df['rolling_std'] + 1e-6)
        max_z = df['z_score_inst'].max()
        avg_z = df['z_score_inst'].mean()
        st.metric("Max Z-Score (Allarme)", f"{max_z:.1f}", delta="CRITICAL" if max_z > 5 else "NORMAL")
        if max_z > 5:
            st.error("🚨 ALLARME SISMICO ATTIVATO")
            st.write("Trigger immediato (< 2s)")
            st.warning("⚠️ RILEVATA VIBRAZIONE ANTROPICA")
            st.write("Trigger lento (> 10s) o Frequenza anomala")


with tab_ovo:
    station = stations[0]
    load_tab(station, starttime)

with tab_csft:
    station = stations[1]
    load_tab(station, starttime)

with tab_ioca:
    station = stations[2]
    load_tab(station, starttime)

with tab_sorr:
    station = stations[3]
    load_tab(station, starttime)



# from utils.ai_assistant import render_ai_sidebar

# # Dynamic Context
# status_msg = "ALLARME SISMICO" if max_z > 5 and "Terremoto" in scenario else "VIBRAZIONE ANTROPICA" if max_z > 5 else "NORMALE"

# context = f"""
# Stai analizzando la pagina Segnali in Tempo Reale.
# SCENARIO ATTIVO: {scenario}

# DATI RILEVATI ORA:
# - Max Z-Score (Anomalia): {max_z:.2f}
# - Soglia di allarme: 5.0
# - Stato Attuale: {status_msg}
# - Frequenze dominanti visibili nello spettro.

# Spiega all'utente perché, basandosi su questi numeri, si tratta di un terremoto o di un evento artificiale (stadio).
# """
# render_ai_sidebar(context_text=context)
