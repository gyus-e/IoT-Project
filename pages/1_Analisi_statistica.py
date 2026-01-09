import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.sidebar import Sidebar
from utils.load_data import load_data
from utils.ai_assistant import render_ai_assistant
from utils.seismology import calculate_gutenberg_richter


unfiltered_df = load_data()
if unfiltered_df is None:
    st.error("Dataset 'catalog.csv' non trovato. Esegui lo script di setup!")
    st.stop()
Sidebar.init_sidebar(unfiltered_df)
df, years, depth, magnitude = Sidebar.apply_filters(unfiltered_df)


st.set_page_config(
    # page_title="Macro Analysis", 
    # page_icon="🌍", 
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown("### Distribuzione delle Magnitudo")
st.markdown("Segue la Legge di Gutenberg-Richter:")
help="""
N è il numero cumulativo di eventi con magnitudo ≥ M \n
"""
st.latex(r"\log_{10} N = a - bM")
st.markdown(help)
# Calculate Frequency-Magnitude Distribution
magnitudes = df['magnitude'].round(1)
mag_counts = magnitudes.value_counts().sort_index(ascending=False)
cdf = mag_counts.cumsum().sort_index() # Cumulative Number of events >= M
gr_df = pd.DataFrame({'Magnitude': cdf.index, 'Count': cdf.values})
gr_df['LogCount'] = np.log10(gr_df['Count'])

# Calcolo parametri G-R usando la utility condivisa (MLE)
gr_params = calculate_gutenberg_richter(df)
a_value = gr_params['a_value']
b_value = gr_params['b_value']
mc = gr_params['mc']
valid = gr_params['valid']

if valid:
    fig_gr = px.scatter(gr_df, x="Magnitude", y="LogCount")
    
    # Add fit line
    # Tracciamo la retta su un range esteso per visualizzazione
    x_range = np.linspace(min(gr_df['Magnitude'].min(), mc), max(gr_df['Magnitude'].max(), 8.0), 100)
    y_fit = a_value - b_value * x_range
    
    fig_gr.add_trace(go.Scatter(x=x_range, y=y_fit, mode='lines', 
                                name=f'G-R Fit (b={b_value:.2f})', 
                                line=dict(color='red', dash='dash')))
    
    # Mostriamo Mc
    fig_gr.add_vline(x=mc, line_width=1, line_dash="dot", line_color="green", annotation_text=f"Mc={mc}")

    st.plotly_chart(fig_gr, width="stretch")
    
    st.info(f"a = {a_value:.2f} (Sismicità regionale). Calcolato con MLE su Mc >= {mc}")
    
    if 0.8 <= b_value <= 1.2:
        st.info(f"b = {b_value:.2f} è coerente con la sismicità tettonica standard (~1.0).")
    elif b_value < 0.8:
        st.warning(f"⚠️ b = {b_value:.2f}. Potenziale alto stress sismico.")
    else:
        st.warning(f"⚠️ b = {b_value:.2f}. Potenziale sciame sismico a bassa magnitudo.")
else:
    st.warning("Dati insufficienti per calcolare la distribuzione Gutenberg-Richter (serve più eventi sopra Mc).")

   
st.markdown("### Timeline")
# Time distribution
df['year_month'] = df['time'].dt.to_period('M').astype(str)
counts = df.groupby('year_month').size().reset_index(name='counts')
fig_hist = px.bar(counts, x='year_month', y='counts', title="Eventi per Mese", labels={"year_month": "Mese", "counts": "Numero di Eventi"})
fig_hist.update_xaxes(showticklabels=True)
st.plotly_chart(fig_hist, width="stretch")


st.markdown("### Istogramma dei tempi di Attesa")
# Calculate Inter-event times
df_sorted = df.sort_values("time")
df_sorted['delta_time'] = df_sorted['time'].diff().dt.total_seconds() / 3600.0 # hours
df_clean = df_sorted.dropna()
# Histogram of waiting times
fig_wait = px.histogram(df_clean[df_clean['delta_time'] < 100], x="delta_time", nbins=50,
                        labels={"delta_time": "Ore tra due eventi consecutivi"})
st.plotly_chart(fig_wait, width="stretch")


st.markdown("### Pattern Spazio-Temporale")
fig_st = px.scatter(
    df, 
    x="time", 
    y="latitude", 
    color="magnitude", 
    # size="magnitude",
    color_continuous_scale=px.colors.sequential.Burgyl,
)
st.plotly_chart(fig_st, width="stretch")


#TODO: aggiornare il contesto
context=f"""
"""
render_ai_assistant(context_text=context)