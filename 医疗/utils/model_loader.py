import joblib
import pandas as pd
import streamlit as st
from config import ADMET_INFO, EXCLUDE_COLS

@st.cache_resource
def load_models():
    # 加载活性与 ADMET 预测模型
    model_activity = joblib.load("models/model_activity.pkl")
    models_admet = {t: joblib.load(f"models/model_{t}.pkl") for t in ADMET_INFO.keys()}
    return model_activity, models_admet

@st.cache_data
def load_data():
    # 加载训练数据并获取描述符列名
    df_train = pd.read_csv("data/merged_data.csv")
    desc_cols = [c for c in df_train.columns if c not in EXCLUDE_COLS]
    return desc_cols