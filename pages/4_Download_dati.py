import streamlit as st
import datetime
import pandas as pd
import os
from utils.fetch_earthquake_data import fetch_earthquake_data

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Download Dati Sismici")
if st.session_state.get('missing_catalog'):
    st.toast("Catalogo non trovato! Scarica i dati per proseguire.", icon="⚠️")
    st.session_state['missing_catalog'] = False

if "download_success" in st.session_state:
    st.success(st.session_state["download_success"])
    st.balloons()
    del st.session_state["download_success"]

st.markdown("In questa pagina puoi scaricare i dati sismici aggiornati direttamente dal database INGV.")

# --- Filters ---
st.subheader("Filtri di Ricerca")
st.info("Filtri applicati: Magnitudo >= 2.5, Area Mediterranea.")

# Date Range
today = datetime.date.today()
default_start = datetime.date(1990, 1, 1)

date_range = st.date_input(
    "Seleziona intervallo date",
    value=(default_start, today),
    min_value=datetime.date(1980, 1, 1),
    max_value=today,
    format="DD/MM/YYYY",
    
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    # Handle case where user is still selecting
    start_date, end_date = default_start, today
    st.warning("Seleziona entrambe le date (inizio e fine) per procedere.")

# --- Filename ---
filename = "catalog.csv"

# --- Action ---
if st.button("Scarica Dati", type="primary"):
    # Output to user
    st.info(f"Scaricamento dati dal {start_date} al {end_date}...")

    if True: # Validation is implicit with slider
        # Progress Bar
        progress_bar = st.progress(0, text="Inizio download...")
        status_text = st.empty()
        
        # 1. Check existing dataset
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        file_path = os.path.join(data_dir, filename)
        
        final_df = None
        intervals_to_download = []
        
        # User requested boundaries (UTC for comparison)
        user_start_dt = pd.to_datetime(start_date, utc=True)
        user_end_dt = pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

        if os.path.exists(file_path):
            try:
                existing_df = pd.read_csv(file_path)
                existing_df['time'] = pd.to_datetime(existing_df['time'], utc=True)
                
                if not existing_df.empty:
                    # Capture bounds of EXISTING data
                    min_time_existing = existing_df['time'].min()
                    max_time_existing = existing_df['time'].max()
                    
                    st.write(f"Dataset esistente trovato: dal {min_time_existing} al {max_time_existing} ({len(existing_df)} eventi).")
                    
                    # Assume we start with what we have, then modifiy it
                    final_df = existing_df.copy()
                    removed_events = 0

                    # --- LOWER BOUND CHECK ---
                    if user_start_dt > min_time_existing:
                        # User wants LESS data at the start -> TRIM
                        before_trim = len(final_df)
                        final_df = final_df[final_df['time'] >= user_start_dt]
                        removed_events += (before_trim - len(final_df))
                    else:
                        # User wants MORE data at the start -> DOWNLOAD      
                        download_end = min(user_end_dt, min_time_existing - pd.Timedelta(microseconds=1))
                        
                        if user_start_dt <= download_end:
                            intervals_to_download.append((user_start_dt, download_end, "pre"))

                    # --- UPPER BOUND CHECK ---
                    if user_end_dt < max_time_existing:
                        # User wants LESS data at the end -> TRIM
                        before_trim = len(final_df)
                        final_df = final_df[final_df['time'] <= user_end_dt]
                        removed_events += (before_trim - len(final_df))
                    else:
                        # User wants MORE data at the end -> DOWNLOAD
                        download_start = max(user_start_dt, max_time_existing + pd.Timedelta(microseconds=1))
                        
                        if download_start <= user_end_dt:
                            intervals_to_download.append((download_start, user_end_dt, "post"))
                    
                    if removed_events > 0:
                        st.info(f"Rimossi {removed_events} eventi fuori dall'intervallo selezionato.")

                else:
                    # File exists but empty
                    intervals_to_download.append((user_start_dt, user_end_dt, "full"))
                    final_df = pd.DataFrame()

            except Exception as e:
                intervals_to_download.append((user_start_dt, user_end_dt, "full"))
                final_df = pd.DataFrame()
        else:
            intervals_to_download.append((user_start_dt, user_end_dt, "full"))
            final_df = pd.DataFrame()

        
        # 2. Download loop
        new_dfs = []
        total_events = 0
        total_intervals = len(intervals_to_download)
        
        for idx, (i_start, i_end, label) in enumerate(intervals_to_download):
            progress_bar.progress(0, text=f"Scaricamento intervallo {idx+1}/{total_intervals} ({i_start} - {i_end})...")
            
            try:
                downloader = fetch_earthquake_data(
                    starttime=i_start,
                    endtime=i_end
                )
                
                for progress, chunk_df in downloader:
                    # Visual progress for current chunk
                    progress_bar.progress(min(progress, 1.0), text=f"Scaricamento parte {label}... ({int(progress*100)}%)")
                    
                    if chunk_df is not None and not chunk_df.empty:
                        # Ensure UTC
                        if 'time' in chunk_df.columns:
                            chunk_df['time'] = pd.to_datetime(chunk_df['time'], utc=True)
                        new_dfs.append(chunk_df)
                        total_events += len(chunk_df)
                        status_text.text(f"Nuovi eventi trovati: {total_events}")
                        
            except Exception as e:
                st.error(f"Errore durante scaricamento intervallo {i_start}-{i_end}: {e}")

        # 3. Merge and Save
        progress_bar.progress(0.9, text="Unione e salvataggio dati...")
        
        if new_dfs:
            new_data_df = pd.concat(new_dfs, ignore_index=True)
            if not final_df.empty:
                final_df = pd.concat([final_df, new_data_df], ignore_index=True)
            else:
                final_df = new_data_df
        
        if not final_df.empty:
            # Sort
            final_df = final_df.sort_values("time")
            
            # Save
            os.makedirs(data_dir, exist_ok=True)
            final_df.to_csv(file_path, index=False)
            
            from utils.load_data import load_data
            load_data.clear()
            
            st.session_state["download_success"] = f"Operazione completata! Dataset aggiornato. Nuovi: {total_events}. Totale: {len(final_df)}."
            st.rerun()
        else:
             st.warning("Nessun dato finale disponibile.")
