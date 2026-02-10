import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd

from utils.sidebar import Sidebar
from utils.load_data import load_data
from utils.ai_assistant import render_ai_assistant
from utils.seismology import calculate_gutenberg_richter


unfiltered_df = load_data()
Sidebar.init_sidebar(unfiltered_df)
df, years, depth, magnitude = Sidebar.apply_filters(unfiltered_df)


st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Allerte e anomalie")

st.header("Analisi sismologica (Gutenberg-Richter)")

# Directly use the user's filtered dataframe for all statistics.
# This allows the expert to see how parameters (b-value) change 
# with filters (e.g. magnitude cut).
if df.empty:
    st.warning("Nessun dato selezionato per l'analisi statistica.")
else:
    # 2. Estimate G-R Parameters on FILTERED data

    gr_params = calculate_gutenberg_richter(df)
    mc = gr_params['mc']
    b_value = gr_params['b_value']
    a_value = gr_params['a_value']
    n_total = gr_params['n_total']
    
    # If Mc returns NaN (e.g., empty dataframe not caught earlier), fallback to 0.0 for display
    if np.isnan(mc): mc = 0.0

    if not gr_params['valid']:
        st.warning(f"Troppi pochi eventi ({n_total}) nel range selezionato (>= Mc={mc}) per calcolare un b-value affidabile.")

    # UI Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Magnitudo completezza (Mc)", f"{mc}", help="Moda della magnitudo nel dataset filtrato.")
    if not np.isnan(b_value):
        c2.metric("b-value (Trend)", f"{b_value:.2f}", help="Pendenza della distribuzione G-R calcolata sui dati filtrati.")
        c3.metric("a-value (Sismicità)", f"{a_value:.2f}", help="Indica il tasso di attività sismica del dataset filtrato.")
    else:
        c2.metric("b-value (Trend)", "N/A")
        c3.metric("a-value (Sismicità)", "N/A")


    # 3. Calculate Return Period
    
    if not np.isnan(b_value): # Proceed only if we have valid parameters
        # Calculate period duration in years from filtered dataset
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

        # Plotting & Alerts
        st.divider()
        st.header("Analisi anomalie probabilistiche")
        
        tr_thresh = st.slider("Soglia 'rarità' (Tempo di ritorno in anni)", 
                              min_value=0.1, max_value=100.0, value=1.0, step=0.1)


        anomalies = df[df['return_period_years'] > tr_thresh].copy()

        if not anomalies.empty:
            st.markdown("---")
            st.subheader("Verifica Storica: Teoria vs Realtà")
            st.markdown(f"""
            Per ogni evento anomalo, cerchiamo nel catalogo storico completo (anche fuori dai filtri attuali) 
            l'ultima volta che si è verificato un evento di magnitudo simile o superiore.
            
            Se l'**Intervallo osservato** è minore del **tempo di ritorno teorico**, l'evento è considerato "anticipato".
            """)

            # Ensure we look at the full history sorted by time
            full_history = unfiltered_df.sort_values('time')

            def get_historical_check(row):
                current_mag = row['magnitude']
                current_time = row['time']

                # 1. OPTIMIZATION: Filter first only for events with >= Magnitude
                # This drastically reduces the search space (e.g. from 50k to 10 events)
                relevant_events = full_history[full_history['magnitude'] >= current_mag]
                
                if relevant_events.empty:
                    return None, None

                # 2. BINARY SEARCH: Find the insertion point of the current event in the timeline
                # We want the last event BEFORE the current time.
                # searchsorted returns the index where current_time would be inserted to maintain order.
                idx = relevant_events['time'].searchsorted(current_time, side='left')
                
                # If idx > 0, it means there is at least one event before this one
                if idx > 0:
                    last_event = relevant_events.iloc[idx - 1]
                    last_date = last_event['time']
                    last_mag = last_event['magnitude']
                    
                    if last_date >= current_time:
                        return None, None, None

                    days_diff = (current_time - last_date).days
                    years_diff = days_diff / 365.25
                    return last_date, years_diff, last_mag
                else:
                    return None, None, None

            # Apply calculation to anomalies
            results = anomalies.apply(get_historical_check, axis=1, result_type='expand')
            anomalies['last_similar_date'] = results[0]
            anomalies['observed_interval_years'] = results[1]
            anomalies['last_similar_mag'] = results[2]
            
            # Calculate difference (Positive = Late/Safe, Negative = Premature/Risk)
            # We fill NaNs with 0 for plotting purpose but handle them in display
            anomalies['diff_years'] = anomalies['observed_interval_years'] - anomalies['return_period_years']
            
            # --- PLOT UPDATED WITH HISTORICAL DATA ---
            # We want to color by "Prematureness". 
            # Red = Observed << Theoretical (Negative Diff)
            # Blue = Observed >> Theoretical (Positive Diff)
            # Grey = No historical data
            
            fig_tr = px.scatter(anomalies, x="time", y="return_period_years",
                                size="magnitude",
                                color="diff_years",
                                color_continuous_scale="RdBu", # Red for negative (bad), Blue for positive (good)
                                color_continuous_midpoint=0,
                                title="Anomalie: Tempo di Ritorno Teorico vs Reale",
                                labels={
                                    "return_period_years": "TR Teorico (anni)", 
                                    "time": "Data Evento", 
                                    "magnitude": "Magnitudo",
                                    "diff_years": "Differenza (anni)",
                                    "observed_interval_years": "TR Reale (anni)",
                                    "last_similar_mag": "Mag Simile"
                                },
                                hover_data={
                                    "observed_interval_years": ":.1f",
                                    "diff_years": ":+.1f",
                                    "return_period_years": ":.1f",
                                    "last_similar_mag": ":.1f",
                                    "magnitude": ":.1f"
                                },
                                log_y=True) 
            
            fig_tr.add_hline(y=tr_thresh, line_dash="dash", line_color="red", annotation_text=f"Soglia > {tr_thresh} anni")
            st.plotly_chart(fig_tr, width="stretch")


            st.error(f"Rilevati {len(anomalies)} eventi con tempo di ritorno teorico > {tr_thresh} anni!")
            
            # Formatting for display table
            display_cols = ['time', 'magnitude', 'return_period_years', 'last_similar_date', 'last_similar_mag', 'observed_interval_years', 'diff_years']
            
            def highlight_premature(s):
                if pd.isna(s['observed_interval_years']): return ['' for _ in s]
                is_prem = s['observed_interval_years'] < s['return_period_years']
                return ['background-color: rgba(255, 75, 75, 0.2)' if is_prem else '' for _ in s]

            st.dataframe(
                anomalies[display_cols]
                .sort_values('return_period_years', ascending=False)
                .head(20)
                .style.format({
                    'time': lambda t: t.strftime('%Y-%m-%d %H:%M'),
                    'last_similar_date': lambda t: t.strftime('%Y-%m-%d %H:%M') if pd.notnull(t) else "Mai registrato",
                    'last_similar_mag': "{:.1f}",
                    'return_period_years': "{:.1f} anni",
                    'observed_interval_years': "{:.1f} anni",
                    'diff_years': "{:+.1f} anni"
                })
                .apply(highlight_premature, axis=1),
                column_config={
                    "time": "Data Evento",
                    "magnitude": "Mag",
                    "return_period_years": "TR Teorico",
                    "last_similar_date": "Ultimo Simile",
                    "last_similar_mag": "Mag Simile",
                    "observed_interval_years": "TR Reale",
                    "diff_years": "Differenza"
                },
                hide_index=True
            )
        else:
            st.info("Nessun evento supera la soglia di tempo di ritorno impostata.")


# --- AI Context Generation ---
if df.empty:
    alerts_context = "Nessun dato."
elif 'b_value' not in locals() or np.isnan(b_value):
    alerts_context = "Dati insufficienti per il calcolo del b-value e delle anomalie."
else:
    alerts_context = f"""
    ANALISI ANOMALIE (Tempo di Ritorno):
    - Soglia Rarità impostata: {tr_thresh} anni
    - b-value utilizzato: {b_value:.2f}
    """
    
    if not anomalies.empty:
        alerts_context += f"\n    - EVENTI ANOMALI RILEVATI ({len(anomalies)}):\n"
        # List top 5 anomalies with historical check
        top_anomalies = anomalies.sort_values('return_period_years', ascending=False).head(5)
        for _, row in top_anomalies.iterrows():
            obs_int = f"{row['observed_interval_years']:.1f}" if pd.notnull(row['observed_interval_years']) else "N/A"
            diff = f"{row['diff_years']:+.1f}" if pd.notnull(row.get('diff_years')) else "N/A"
            alerts_context += f"      * Data: {row['time']}, Mag: {row['magnitude']}, TR Teorico: {row['return_period_years']:.1f}, TR Reale: {obs_int}, Diff: {diff}\n"
    else:
        alerts_context += "\n    - Nessuna anomalia rilevata con i filtri attuali."

st.session_state['ai_context_global'] = alerts_context
st.session_state['ai_context_selection'] = ""

render_ai_assistant(context_text="Pagina Allerte: Analisi probabilistica del Tempo di Ritorno con verifica storica.")
