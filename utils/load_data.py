import os
import pandas as pd
import streamlit as st
from dateutil import parser

# Load Data
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
catalog_path = os.path.join(DATA_DIR, 'catalog.csv')

@st.cache_data
def load_data():
    if not os.path.exists(catalog_path):
        return None
    df = pd.read_csv(catalog_path)
    df['time'] = df['time'].apply(parser.parse)
    return df

df = load_data()