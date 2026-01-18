import numpy as np
import pandas as pd
import streamlit as st

@st.cache_data
def calculate_gutenberg_richter(df: pd.DataFrame, magnitude_col: str = 'magnitude', mc: float = None):
    """
    Calculates the a and b parameters of the Gutenberg-Richter law using the MLE method (Aki, 1965).
    
    Args:
        df: DataFrame containing seismic data.
        magnitude_col: Name of the magnitude column.
        mc: Magnitude of completeness. If None, it is estimated as the mode of the distribution (rounded to 0.1).
        
    Returns:
        A dictionary containing:
        - 'a_value': calculated a value
        - 'b_value': calculated b value
        - 'mc': Magnitude of completeness used
        - 'n_total': Number of events >= Mc used for calculation
        - 'valid': Boolean, True if calculation was successful (enough data)
    """
    if df.empty or magnitude_col not in df.columns:
        return {'a_value': np.nan, 'b_value': np.nan, 'mc': np.nan, 'n_total': 0, 'valid': False}

    mags = df[magnitude_col].dropna()
    
    # Round to 1 decimal place for consistency with standard seismological practice
    mags_rounded = mags.round(1)

    # 1. Estimate Mc if not provided
    if mc is None:
        if not mags_rounded.empty:
            # The mode is a simple but effective estimate for Mc as a first approximation
            # If there are multiple modes, we take the minimum (conservative approach to not lose data, 
            # although technically one should take the maximum to be sure of completeness.)
            mc = mags_rounded.mode().min()
        else:
            mc = 0.0
            
    # 2. Filter dataset for M >= Mc
    # Use original data (not rounded) for filtering and mean, for greater precision,
    # but the cut is made with respect to Mc (which is rounded)
    df_above_mc = df[df[magnitude_col] >= mc]
    mags_above = df_above_mc[magnitude_col]
    n_total = len(mags_above)

    # 3. Check minimum number of events
    if n_total < 10:
        return {
            'a_value': np.nan, 
            'b_value': np.nan, 
            'mc': mc, 
            'n_total': n_total,
            'valid': False
        }

    # 4. MLE Calculation (Aki, 1965)
    mean_mag = mags_above.mean()
    
    # Avoid division by zero
    if np.isclose(mean_mag, mc):
        # Degenerate case: all events have exactly magnitude Mc
        b_value = np.nan 
        valid = False
    else:
        b_value = 0.4343 / (mean_mag - mc)
        valid = True

    # 5. Calculate a-value
    # log10(N) = a - b * Mc  =>  a = log10(N) + b * Mc
    if valid:
        a_value = np.log10(n_total) + (b_value * mc)
    else:
        a_value = np.nan

    return {
        'a_value': a_value,
        'b_value': b_value,
        'mc': mc,
        'n_total': n_total,
        'valid': valid
    }

@st.cache_data
def fft_analysis(df: pd.DataFrame, sampling_rate: float = 100.0) -> pd.DataFrame:
    """
    Computes the Fast Fourier Transform (FFT) of the velocity signal.
    
    Args:
        df: DataFrame containing 'velocity' column.
        sampling_rate: Sampling rate in Hz (default 100.0).
        
    Returns:
        DataFrame with 'Freq (Hz)' and 'Power' columns.
    """
    if df.empty or 'velocity' not in df.columns:
        return pd.DataFrame()
        
    # Remove DC component (detrending constant)
    velocity = df['velocity'] - df['velocity'].mean()
    
    fft_vals = np.fft.rfft(velocity)
    fft_freq = np.fft.rfftfreq(len(velocity), d=1/sampling_rate)
    
    fft_df = pd.DataFrame({'Freq (Hz)': fft_freq, 'Power': np.abs(fft_vals)})
    # Limit to relevant frequencies (e.g., < 20Hz for seismic signals often sufficient for visualization)
    fft_df = fft_df[fft_df['Freq (Hz)'] < 20]
    
    return fft_df
