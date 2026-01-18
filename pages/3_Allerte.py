import streamlit as st
import plotly.express as px
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


st.markdown("### Analisi Sismologica (Gutenberg-Richter)")

# Utilizziamo direttamente il dataframe filtrato dall'utente per tutte le statistiche
# Questo permette all'esperto di vedere come cambiano i parametri (b-value) 
# al variare dei filtri (es. taglio magnitudo).
if df.empty:
    st.warning("Nessun dato selezionato per l'analisi statistica.")
else:
    # 2. Stima Parametri G-R su dati FILTRATI

    gr_params = calculate_gutenberg_richter(df)
    mc = gr_params['mc']
    b_value = gr_params['b_value']
    a_value = gr_params['a_value']
    n_total = gr_params['n_total']
    
    # Se mc torna NaN (es. dataframe vuoto ma non intercettato prima), fallback a 0.0 per display
    if np.isnan(mc): mc = 0.0

    if not gr_params['valid']:
        st.warning(f"Troppi pochi eventi ({n_total}) nel range selezionato (>= Mc={mc}) per calcolare un b-value affidabile.")

    # Meteiche UI
    c1, c2, c3 = st.columns(3)
    c1.metric("Magnitudo Completezza (Mc)", f"{mc}", help="Moda della magnitudo nel dataset filtrato.")
    if not np.isnan(b_value):
        c2.metric("b-value (Trend)", f"{b_value:.2f}", help="Pendenza della distribuzione G-R calcolata sui dati filtrati.")
        c3.metric("a-value (Sismicità)", f"{a_value:.2f}", help="Indica il tasso di attività sismica del dataset filtrato.")
    else:
        c2.metric("b-value (Trend)", "N/A")
        c3.metric("a-value (Sismicità)", "N/A")


    # 3. Calcolo Tempo di Ritorno (Return Period)
    
    if not np.isnan(b_value): # Procediamo solo se abbiamo parametri validi
        # Calcolo durata periodo in anni dal dataset filtrato
        if not df.empty:
            delta_t_years = (df['time'].max() - df['time'].min()).days / 365.25
            if delta_t_years < 0.01: delta_t_years = 0.01 
        else:
            delta_t_years = 1.0

        def calc_return_period(m):
            # Gutenberg-Richter: log10(N) = a - bM
            log_n = a_value - (b_value * m)
            n_predicted = 10 ** log_n
            
            if n_predicted == 0: return np.inf
            return delta_t_years / n_predicted

        df['return_period_years'] = df['magnitude'].apply(calc_return_period)

        # Plotting & Allerte
        st.divider()
        st.subheader("Analisi Anomalie Probabilistiche")
        
        tr_thresh = st.slider("Soglia 'Rarità' (Tempo di Ritorno in Anni)", 
                              min_value=0.1, max_value=100.0, value=1.0, step=0.1)

        anomalies = df[df['return_period_years'] > tr_thresh]

        fig_tr = px.scatter(df, x="time", y="return_period_years",
                            size="magnitude",
                            color="return_period_years",
                            color_continuous_scale="Turbo",
                            title="Rarità degli Eventi (Tempo di Ritorno)",
                            labels={"return_period_years": "Tempo di Ritorno Stimato (Anni)", "time": "Data", "magnitude": "Magnitudo"},
                            log_y=True) 
        
        fig_tr.add_hline(y=tr_thresh, line_dash="dash", line_color="red", annotation_text=f"Soglia > {tr_thresh} anni")
        st.plotly_chart(fig_tr, width="stretch")

        if not anomalies.empty:
            st.error(f"Rilevati {len(anomalies)} eventi 'rari' nel dataset selezionato!")
            st.dataframe(
                anomalies[['time', 'magnitude', 'depth', 'return_period_years']]
                .sort_values('return_period_years', ascending=False)
                .head(20)
                .style.format({'return_period_years': "{:.2f}"}),
                hide_index=True
            )
        else:
            st.info("Nessun evento supera la soglia di tempo di ritorno impostata.")


# --- AI Context Generation ---
if df.empty:
    alerts_context = "Nessun dato."
else:
    alerts_context = f"""
    ANALISI ANOMALIE (Tempo di Ritorno):
    - Soglia Rarità impostata: {tr_thresh} anni
    - b-value utilizzato: {b_value:.2f}
    """
    
    if not anomalies.empty:
        alerts_context += f"\n    - EVENTI ANOMALI RILEVATI ({len(anomalies)}):\n"
        # List top 5 anomalies
        top_anomalies = anomalies.sort_values('return_period_years', ascending=False).head(5)
        for _, row in top_anomalies.iterrows():
            alerts_context += f"      * Data: {row['time']}, Mag: {row['magnitude']}, TR: {row['return_period_years']:.1f} anni\n"
    else:
        alerts_context += "\n    - Nessuna anomalia rilevata con i filtri attuali."

st.session_state['ai_context_global'] = alerts_context
st.session_state['ai_context_selection'] = ""

render_ai_assistant(context_text="Pagina Allerte: Analisi probabilistica del Tempo di Ritorno.")
