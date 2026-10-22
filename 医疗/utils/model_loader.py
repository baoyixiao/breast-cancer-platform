import os
import joblib
import pandas as pd
import streamlit as st
from config import ADMET_INFO, EXCLUDE_COLS

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@st.cache_resource
def load_models():
    model_activity = joblib.load(os.path.join(base_dir, "models", "model_activity.pkl"))
    models_admet = {t: joblib.load(os.path.join(base_dir, "models", f"model_{t}.pkl")) for t in ADMET_INFO.keys()}
    return model_activity, models_admet

@st.cache_data
def load_data():
    df_train = pd.read_csv(os.path.join(base_dir, "data", "merged_data.csv"))
    desc_cols = [c for c in df_train.columns if c not in EXCLUDE_COLS]
    return desc_cols
