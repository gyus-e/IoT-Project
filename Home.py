import streamlit as st
import os
import pandas as pd

import utils.load_data # preload data to speedup app

st.set_page_config(
    page_title="IoT Earthquake Analytics",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Premium" look
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

st.title("🌋 IoT Earthquake & Noise Analytics")
st.markdown("### Advanced Monitoring Dashboard for Seismology and Urban Sensing")

st.markdown("""
Questa dashboard è parte del progetto universitario di IoT.
Analizza dati sismici reali (**INGV**) e dimostra come distinguere eventi naturali da eventi antropici (es. tifoseria stadio)
utilizzando tecniche di Signal Processing e Machine Learning.
""")

# Check Data Status
data_dir = os.path.join(os.path.dirname(__file__), 'data')
catalog_path = os.path.join(data_dir, 'catalog.csv')

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Source", "INGV Open Data", "Real-time")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    if os.path.exists(catalog_path):
        df = pd.read_csv(catalog_path)
        last_date = df['time'].max()[:10]
        st.metric("Catalog Status", "Connected", f"Events: {len(df)}")
    else:
        st.metric("Catalog Status", "Not Found", "Run Setup Script", delta_color="inverse")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("System Mode", "Analysis", "Active")
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

st.info("👈 Seleziona una pagina dalla barra laterale per iniziare l'analisi.")

# Sidebar info
from utils.ai_assistant import render_ai_assistant
render_ai_assistant(context_text="Home Page. Overview of the project.")

with st.sidebar:
    st.write("---")
    st.caption("Project by Giuseppe & Giuseppe")
    st.caption("University IoT Exam")
