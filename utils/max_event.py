import streamlit as st

@st.cache_data
def get_max_event(df):
    """
    Get the event with the maximum magnitude from the DataFrame.
    
    Args:
        df: pandas DataFrame with 'magnitude' column.
    
    Returns:
        pandas Series representing the event with maximum magnitude, or None if df is empty.
    """
    if df.empty:
        return None
    return df.loc[df['magnitude'].idxmax()]