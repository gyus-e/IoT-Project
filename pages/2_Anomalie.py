import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd

from utils.sidebar import Sidebar
from utils.load_data import load_data
from utils.ai_assistant import render_ai_assistant
from utils.seismology import calculate_gutenberg_richter



def calc_return_period(m, delta_t_years=1.0):
    # Gutenberg-Richter: log10(N) = a - bM
    log_n = a_value - (b_value * m)
    n_predicted = 10 ** log_n
    
    if n_predicted <= 0: return np.inf
    return delta_t_years / n_predicted



# TODO: Refactor by calculating return time offline when loading data
def get_historical_check(df, mag_tolerance=0.2):
    """
    Vectorized historical check - processes all events at once.
    Returns arrays for last_date, years_diff, last_mag
    """
    if df.empty:
        return pd.Series([None] * len(df), index=df.index), pd.Series([None] * len(df), index=df.index), pd.Series([None] * len(df), index=df.index)
    
    # Sort once by time (critical for vectorization)
    df_sorted = df.sort_values('time').copy()
    original_indices = df_sorted.index
    df_sorted = df_sorted.reset_index(drop=True)
    
    n = len(df_sorted)
    last_dates: list = [None] * n
    years_diffs: list[float] = [float('nan')] * n
    last_mags: list = [None] * n
    
    # Pre-compute magnitude bounds
    mags = df_sorted['magnitude'].values
    times = df_sorted['time'].values
    
    for i in range(n):
        current_mag = mags[i]
        current_time = times[i]
        
        # Look backward only (events before index i)
        if i == 0:
            continue
            
        # Find events within magnitude tolerance that occurred before current event
        mask = (np.abs(mags[:i] - current_mag) <= mag_tolerance)
        
        if mask.any():
            # Get the most recent matching event
            matching_indices = np.nonzero(mask)[0]
            last_idx = matching_indices[-1]
            
            last_dates[i] = times[last_idx]
            days_diff = pd.Timedelta(current_time - times[last_idx]).days
            years_diffs[i] = days_diff / 365.25
            last_mags[i] = mags[last_idx]
    
    return pd.Series(last_dates, index=original_indices), pd.Series(years_diffs, index=original_indices), pd.Series(last_mags, index=original_indices)



def is_premature(s, anomaly_threshold):
    if pd.isna(s['last_similar_date']) or \
    pd.isna(s['return_period_years']) or \
    pd.isna(s['observed_interval_years']) or \
    pd.isna(s['diff_years']) or \
    s['diff_years'] >= 0:
        return False
    return  s['observed_interval_years'] < anomaly_threshold * s['return_period_years']



unfiltered_df = load_data()
Sidebar.init_sidebar(unfiltered_df)
df, years, depth, magnitude = Sidebar.apply_filters(unfiltered_df)


st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title("Anomalie sismiche")
st.subheader("Analisi probabilistica del Tempo di Ritorno con verifica storica")



if df.empty:
    st.warning("Nessun dato selezionato per l'analisi statistica.")
    alerts_context = "Nessun dato."

else:
    # Estimate G-R Parameters on FILTERED data

    gr_params = calculate_gutenberg_richter(df)
    mc = gr_params['mc']
    b_value = gr_params['b_value']
    a_value = gr_params['a_value']
    n_total = gr_params['n_total']
    
    # If Mc returns NaN (e.g., empty dataframe not caught earlier), fallback to 0.0 for display
    if np.isnan(mc): mc = 0.0

    if not gr_params['valid']:
        st.warning(f"Troppi pochi eventi ({n_total}) nel range selezionato (>= Mc={mc}) per calcolare un b-value affidabile.")


    # Calculate Return Period
    # Proceed only if we have valid parameters
    if not np.isnan(b_value): 
        # Calculate period duration in years from filtered dataset
        if not df.empty:
            delta_t_years = (df['time'].max() - df['time'].min()).days / 365.25
            if delta_t_years < 0.01: delta_t_years = 1.0
        else:
            delta_t_years = 1.0

        m = df['magnitude']
        df['return_period_years'] = df['magnitude'].apply(lambda m: calc_return_period(m, delta_t_years))
        

        anomaly_threshold = st.slider("Percentuale di prematurità per allerta", 
                              min_value=1.0, max_value=99.0, value=80.0, step=1.0) / 100.0

        # Apply calculation to anomalies
        # df = df.sort_values('time').reset_index(drop=True)
        last_dates, obs_intervals, last_mags = get_historical_check(df, mag_tolerance=0.2)

        df['last_similar_date'] = last_dates
        df['observed_interval_years'] = obs_intervals
        df['last_similar_mag'] = last_mags
        
        # Calculate difference (Positive = Late/Safe, Negative = Premature/Risk)
        # We fill NaNs with 0 for plotting purpose but handle them in display
        df['diff_years'] = df['observed_interval_years'] - df['return_period_years']
        premature_events = df[df.apply(lambda s: is_premature(s, anomaly_threshold), axis=1)]


        
        st.subheader("Verifica Storica: Teoria vs Realtà")
        st.info(f"Periodo osservazione: {delta_t_years:.1f} anni | Mc: {mc:.1f} | Eventi analizzati: {len(df)}")

        # --- PLOT UPDATED WITH HISTORICAL DATA ---
        # We want to color by "Prematureness". 
        # Red = Observed << Theoretical (Negative Diff)
        # Blue = Observed >> Theoretical (Positive Diff)
        # Grey = No historical data
        
        fig_tr = px.scatter(df, x="time", y="magnitude",
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
                            log_y=False) 
        
        # fig_tr.add_hline(y=tr_thresh, line_dash="dash", line_color="red", annotation_text=f"Soglia > {tr_thresh} anni")
        st.plotly_chart(fig_tr, width="stretch")


        
        # Formatting for display table
        column_config = {
                "time": "Data Evento",
                "latitude": "Latitudine",
                "longitude": "Longitudine",
                "magnitude": "Mag",
                "return_period_years": "Tempo di ritorno teorico",
                "observed_interval_years": "Tempo di ritorno reale",
                "diff_years": "Differenza",
                "last_similar_date": "Ultimo Simile",
                "last_similar_mag": "Mag Simile",
            }

        st.error(f"Rilevati {len(premature_events)} eventi con tempo di ritorno reale minore del {anomaly_threshold*100:.1f}% del tempo di ritorno teorico!")

        st.dataframe(
            premature_events[column_config.keys()]
            .sort_values('diff_years', ascending=True)
            .head(20)
            .style.format({
                'time': lambda t: pd.to_datetime(t).strftime('%Y-%m-%d %H:%M'),
                'latitude': "{:.3f}",
                'longitude': "{:.3f}",
                'magnitude': "{:.1f}",
                'return_period_years': "{:.1f} anni",
                'observed_interval_years': "{:.1f} anni",
                'diff_years': "{:+.1f} anni",
                'last_similar_date': lambda t: pd.to_datetime(t).strftime('%Y-%m-%d %H:%M') if pd.notnull(t) else "Mai registrato",
                'last_similar_mag': "{:.1f}",
            }),
            column_config=column_config,
            hide_index=True
        )



    # --- AI Context Generation ---
    if 'b_value' not in locals() or np.isnan(b_value):
        alerts_context = "Dati insufficienti per il calcolo del b-value e delle anomalie."
    else:
        alerts_context = f"""
        ANALISI ANOMALIE (Tempo di Ritorno):
        - b-value utilizzato: {b_value:.2f}
        """
        
        # alerts_context += f"\n    - EVENTI ANOMALI RILEVATI ({len(rare_events)}):\n"
        # List top 5 anomalies with historical check
        top_anomalies = df.sort_values('return_period_years', ascending=False).head(5)
        for _, row in top_anomalies.iterrows():
            obs_int = f"{row['observed_interval_years']:.1f}" if pd.notnull(row['observed_interval_years']) else "N/A"
            diff = f"{row['diff_years']:+.1f}" if pd.notnull(row.get('diff_years')) else "N/A"
            alerts_context += f"      * Data: {row['time']}, Mag: {row['magnitude']}, TR Teorico: {row['return_period_years']:.1f}, TR Reale: {obs_int}, Diff: {diff}\n"


    st.session_state['ai_context_global'] = alerts_context
    st.session_state['ai_context_selection'] = ""

    render_ai_assistant(context_text="Pagina Allerte: Analisi probabilistica del Tempo di Ritorno con verifica storica.")
