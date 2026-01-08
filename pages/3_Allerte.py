import streamlit as st
import plotly.express as px
import numpy as np

from utils.sidebar import Sidebar
from utils.load_data import load_data
from utils.ai_assistant import render_ai_assistant


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
    
    # Magnitudo di Completezza (Mc) - Stima basata sulla Moda dei dati VISIBILI
    mags_rounded = df['magnitude'].round(1)
    if not mags_rounded.empty:
        mc = mags_rounded.mode().min() 
    else:
        mc = 0.0

    # Filtriamo dataset sopra Mc per il calcolo del b-value
    # Nota: se l'utente ha già filtrato M > X, Mc sarà sempre >= X
    df_above_mc = df[df['magnitude'] >= mc]

    if len(df_above_mc) < 10:
        st.warning(f"Troppi pochi eventi ({len(df_above_mc)}) nel range selezionato per calcolare un b-value affidabile.")
        b_value = np.nan
        a_value = np.nan
    else:
        # Metodo di Massima Verosimiglianza (Aki, 1965)
        mean_mag = df_above_mc['magnitude'].mean()
        if mean_mag == mc:
            b_value = 1.0 
        else:
            b_value = 0.4343 / (mean_mag - mc)

        # a-value
        n_total = len(df_above_mc)
        a_value = np.log10(n_total) + (b_value * mc)

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


#TODO: aggiornare il contesto
context=f"""
"""
render_ai_assistant(context_text=context)
