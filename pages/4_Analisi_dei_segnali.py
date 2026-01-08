import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.signal import spectrogram
import os

from utils.ai_assistant import render_ai_assistant

st.set_page_config(page_title="Signal Lab", page_icon="🔬", layout="wide")

st.markdown("# 🔬 Laboratorio Analisi Segnali")
st.markdown("Confronto tra segnali naturali (Terremoti) e antropici (Esultanza Stadio).")

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
quake_path = os.path.join(DATA_DIR, 'waveform_quake.csv')
napoli_path = os.path.join(DATA_DIR, 'waveform_napoli.csv')

# Scenario Selector
scenario = st.radio("Seleziona Scenario:", ["🟢 Terremoto (Amatrice/Campi Flegrei)", "🔵 Napoli Scudetto (Stadio Maradona 2023)"], horizontal=True)

@st.cache_data
def load_waveform(path):
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)

# Load selected data
if "Terremoto" in scenario:
    df = load_waveform(quake_path)
    title = "Sismogramma: Evento Tettonico"
    color = "green"
    desc = "Si nota l'arrivo impulsivo delle onde P e S. Il segnale passa da zero a max in pochi secondi."
else:
    df = load_waveform(napoli_path)
    title = "Sismogramma: Esultanza Scudetto"
    color = "blue"
    desc = "Si nota un incremento graduale ('crescendo'). Il segnale persiste per minuti ed è modulato dai canti."

if df is None:
    st.warning(f"File dati non trovato per lo scenario selezionato. Esegui `fetch_data.py`.")
    # Generate dummy data for UI preview if real data missing
    t = np.linspace(0, 60, 6000) # 1 min at 100Hz
    if "Terremoto" in scenario:
        # Impulse
        y = np.random.normal(0, 0.1, 6000)
        y[2000:4000] += np.sin(t[2000:4000]*10) * np.exp(-(t[2000:4000]-20)/5) * 5
    else:
        # Harmonic
        y = np.random.normal(0, 0.1, 6000) + np.sin(t * 2 * np.pi * 2.5) * (t/60) * 2 # 2.5Hz jumping
    df = pd.DataFrame({'times': t, 'velocity': y})
    st.info("⚠️ Visualizzazione dati simulati (Dati reali in download).")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f"### {title}")
    
    # Plot Waveform
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['times'], y=df['velocity'], line=dict(color=color, width=1), name="Velocity"))
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), xaxis_title="Time (s)", yaxis_title="Velocity (m/s)")
    st.plotly_chart(fig, width="stretch")
    st.caption(desc)

with col2:
    st.markdown("### Analisi Real-Time")
    
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
        if "Terremoto" in scenario:
            st.error("🚨 ALLARME SISMICO ATTIVATO")
            st.write("Trigger immediato (< 2s)")
        else:
            st.warning("⚠️ RILEVATA VIBRAZIONE ANTROPICA")
            st.write("Trigger lento (> 10s) o Frequenza anomala")
    
    # FFT / Spectrogram placeholder
    st.markdown("#### Spettro Frequenze")
    # Simple FFT of the whole signal
    fft_vals = np.fft.rfft(df['velocity'])
    fft_freq = np.fft.rfftfreq(len(df['velocity']), d=1/100) # assuming 100Hz
    
    fft_df = pd.DataFrame({'Freq (Hz)': fft_freq, 'Power': np.abs(fft_vals)})
    # Filter useful range 0-20Hz
    fft_df = fft_df[fft_df['Freq (Hz)'] < 20]
    
    fig_fft = px.line(fft_df, x='Freq (Hz)', y='Power', title="Dominio Frequenze")
    st.plotly_chart(fig_fft, width="stretch")
    
    if "Napoli" in scenario:
        st.caption("Nota il picco intorno a **2-3 Hz**: è il ritmo dei salti dei tifosi ('Chi non salta...')!")


#TODO: aggiornare il contesto
context=f"""
"""
render_ai_assistant(context_text=context)
