import pubchempy as pcp
import streamlit as st

CN_TO_EN_DRUG_DICT = {
    "他莫昔芬": "Tamoxifen", "雷洛昔芬": "Raloxifene", "托瑞米芬": "Toremifene",
    "氟维司群": "Fulvestrant", "来曲唑": "Letrozole", "阿那曲唑": "Anastrozole",
    "依西美坦": "Exemestane", "帕博西尼": "Palbociclib", "阿莫西林": "Amoxicillin",
    "阿司匹林": "Aspirin", "雌二醇": "Estradiol", "紫杉醇": "Paclitaxel"
}

@st.cache_data(show_spinner=False)
def get_smiles_from_pubchem(query):
    search_term = query.strip()
    if search_term in CN_TO_EN_DRUG_DICT:
        search_term = CN_TO_EN_DRUG_DICT[search_term]
    elif any('\u4e00' <= char <= '\u9fff' for char in search_term):
        st.error(f"本地药典暂未收录中文名 '{query}'。请直接输入英文名或 SMILES。")
        return None, None, None
    try:
        compounds = pcp.get_compounds(search_term, 'name')
        if compounds:
            c = compounds[0]
            return c.isomeric_smiles, c.iupac_name, c.molecular_formula
    except Exception:
        pass
    return None, None, None