import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.load_data import df as unfiltered_df
from utils.sidebar import Sidebar
# from utils.ai_assistant import render_ai_sidebar

st.set_page_config(
    # page_title="Macro Analysis", 
    # page_icon="🌍", 
    layout="wide",
    initial_sidebar_state="expanded",
)


if unfiltered_df is None:
    st.error("Dataset 'catalog.csv' non trovato. Esegui lo script di setup!")
    st.stop()
Sidebar.init_sidebar(unfiltered_df)
df, years, depth, magnitude = Sidebar.apply_filters(unfiltered_df)


st.markdown("### Z-Score delle Magnitudo")

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


# # Dynamic Context
# context = f"""
# Stai analizzando la pagina Statistica Avanzata (Fisica Sismica).

# 1. GUTENBERG-RICHTER:
#    - b-value: {b_value:.2f} (Ideale ~1.0). Se < 0.8: alto stress. Se > 1.2: sciame.

# 2. Z-SCORE (ANOMALIE):
#    - Soglia: {z_thresh} sigma.
#    - Anomalie trovate: {len(anomalies)}.

# 3. ANALISI PERIODICITÀ (INTER-EVENT TIMES):
#    - Questo grafico mostra il tempo di attesa tra due eventi.
#    - Se decresce esponenzialmente: Processo di Poisson (Casuale, nessuna memoria).
#    - Se forma una campana: Processo Periodico (Ciclico, c'è memoria nel sistema).
   
# Spiega all'utente quale pattern emerge dai dati.
# """
# render_ai_sidebar(context_text=context)
