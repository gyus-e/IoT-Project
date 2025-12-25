import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from scipy.stats import norm

st.set_page_config(page_title="Advanced Stats", page_icon="📈", layout="wide")

st.markdown("# 📈 Analisi Statistica Avanzata")
st.markdown("Verifica delle leggi fisiche (Gutenberg-Richter) e anomalie (Z-Score).")

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
    st.error("Dati non trovati.")
    st.stop()

tab1, tab2 = st.tabs(["Gutenberg-Richter", "Z-Score Analysis"])

with tab1:
    st.markdown("### Legge di Gutenberg-Richter")
    st.latex(r"\log_{10} N = a - bM")
    st.markdown("Una relazione lineare tra Magnitudo (M) e logaritmo del numero di eventi (N).")
    
    # Calculate Frequency-Magnitude Distribution
    magnitudes = df['magnitude'].round(1)
    mag_counts = magnitudes.value_counts().sort_index(ascending=False)
    cdf = mag_counts.cumsum().sort_index() # Cumulative Number of events >= M
    
    gr_df = pd.DataFrame({'Magnitude': cdf.index, 'Count': cdf.values})
    gr_df['LogCount'] = np.log10(gr_df['Count'])
    
    # Linear Fit (approximate for visual)
    # Filter for linear part (usually 2.5 < M < 5.0 for completeness)
    fit_df = gr_df[(gr_df['Magnitude'] >= 2.5) & (gr_df['Magnitude'] <= 5.0)]
    if not fit_df.empty:
        coeffs = np.polyfit(fit_df['Magnitude'], fit_df['LogCount'], 1)
        b_value = -coeffs[0]
        a_value = coeffs[1]
        
        fig_gr = px.scatter(gr_df, x="Magnitude", y="LogCount", title=f"Gutenberg-Richter Plot (b-value={b_value:.2f})")
        
        # Add fit line
        x_range = np.linspace(2.0, 6.5, 100)
        y_fit = a_value - b_value * x_range
        fig_gr.add_trace(go.Scatter(x=x_range, y=y_fit, mode='lines', name=f'Fit (b={b_value:.2f})', line=dict(color='red', dash='dash')))
        
        st.plotly_chart(fig_gr, width="stretch")
        
        if 0.8 <= b_value <= 1.2:
            st.success(f"✅ Il b-value ({b_value:.2f}) è coerente con la sismicità tettonica standard (~1.0).")
        else:
            st.warning(f"⚠️ b-value anomalo ({b_value:.2f}). Possibile incompletezza del catalogo o sciame sismico intenso.")

    st.markdown("---")
    st.markdown("### Analisi Periodicità (Waiting Time)")
    st.markdown("Analizziamo il tempo che passa tra un evento e l'altro.")
    
    # Calculate Inter-event times
    df_sorted = df.sort_values("time")
    df_sorted['delta_time'] = df_sorted['time'].diff().dt.total_seconds() / 3600.0 # hours
    df_clean = df_sorted.dropna()
    
    # Histogram of waiting times
    fig_wait = px.histogram(df_clean[df_clean['delta_time'] < 100], x="delta_time", nbins=50,
                            title="Distribuzione Tempi di Attesa (Ore)",
                            labels={"delta_time": "Ore tra due eventi consecutivi"})
    st.plotly_chart(fig_wait, width="stretch")
    
    st.info("""
    **Interpretazione**:
    - **Esponenziale (Decrescente)** = Processo di Poisson (Casuale - La norma).
    - **Campana (Gaussiana)** = Processo Periodico (es. "Ogni X ore/anni").
    """)

with tab2:
    st.markdown("### Z-Score delle Magnitudo")
    st.markdown("Quante deviazioni standard dista un evento dalla media?")
    
    mean_mag = df['magnitude'].mean()
    std_mag = df['magnitude'].std()
    
    col_stat1, col_stat2 = st.columns(2)
    col_stat1.metric("Magnitudo Media", f"{mean_mag:.2f}")
    col_stat2.metric("Deviazione Std", f"{std_mag:.2f}")
    
    # Interactive Threshold
    z_thresh = st.slider("Soglia Z-Score Allarme", 2.0, 5.0, 3.0)
    
    df['z_score'] = (df['magnitude'] - mean_mag) / std_mag
    
    anomalies = df[df['z_score'] > z_thresh]
    
    fig_z = px.scatter(df, x="time", y="z_score", color="z_score", 
                      color_continuous_scale="RdYlGn_r",
                      title="Z-Score nel Tempo")
    fig_z.add_hline(y=z_thresh, line_dash="dash", line_color="red", annotation_text="Soglia Allarme")
    st.plotly_chart(fig_z, width="stretch")
    
    if not anomalies.empty:
        st.error(f"Rilevati {len(anomalies)} eventi sopra la soglia Z={z_thresh}!")
        st.dataframe(anomalies[['time', 'magnitude', 'depth', 'z_score']].sort_values('z_score', ascending=False).head(10))

from utils.ai_assistant import render_ai_sidebar

# Dynamic Context
context = f"""
Stai analizzando la pagina Statistica Avanzata (Fisica Sismica).

1. GUTENBERG-RICHTER:
   - b-value: {b_value:.2f} (Ideale ~1.0). Se < 0.8: alto stress. Se > 1.2: sciame.

2. Z-SCORE (ANOMALIE):
   - Soglia: {z_thresh} sigma.
   - Anomalie trovate: {len(anomalies)}.

3. ANALISI PERIODICITÀ (INTER-EVENT TIMES):
   - Questo grafico mostra il tempo di attesa tra due eventi.
   - Se decresce esponenzialmente: Processo di Poisson (Casuale, nessuna memoria).
   - Se forma una campana: Processo Periodico (Ciclico, c'è memoria nel sistema).
   
Spiega all'utente quale pattern emerge dai dati.
"""
render_ai_sidebar(context_text=context)
