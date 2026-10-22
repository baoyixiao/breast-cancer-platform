import streamlit as st
import base64
import os
from config import SYSTEM_NAME
from views import single_eval, batch_screen

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

current_dir = os.path.dirname(os.path.abspath(__file__))

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

img_single_icon = get_base64_image(os.path.join(current_dir, "images", "single_icon.png"))
img_batch_icon = get_base64_image(os.path.join(current_dir, "images", "batch_icon.png"))
img_home_bg = get_base64_image(os.path.join(current_dir, "images", "home_bg.png"))
img_batch_bg = get_base64_image(os.path.join(current_dir, "images", "batch_bg.png"))

st.markdown(f"""
<style>
    section[data-testid="stSidebar"] {{ display: none !important; }}
    [data-testid="collapsedControl"] {{ display: none !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}

    .stApp {{
        background: transparent;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}

    .home-bg {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-image: url("data:image/png;base64,{img_home_bg}");
        background-size: cover; background-position: center; z-index: -2;
    }}
    .single-bg {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: linear-gradient(135deg, #FFF0F5 0%, #FFFFFF 100%);
        z-index: -2;
    }}
    .batch-page-bg {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-image: url("data:image/png;base64,{img_batch_bg}");
        background-size: cover; background-position: center; z-index: -2;
    }}
    .bg-heart {{
        position: fixed; bottom: -50px; right: -50px; width: 600px; height: 600px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23FB923C' stroke-width='1' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z'/%3E%3C/svg%3E");
        background-repeat: no-repeat; opacity: 0.15; z-index: -1; pointer-events: none;
        animation: heartbeat 4s infinite alternate;
    }}
    @keyframes heartbeat {{ 0% {{ transform: scale(1); opacity: 0.1; }} 100% {{ transform: scale(1.05); opacity: 0.2); }} }}

    .block-container {{ 
        padding-top: 6vh !important; 
        padding-left: 3vw !important; 
        margin-left: 0 !important;
        margin-right: auto !important; 
        max-width: 45vw !important;
    }}
    [data-testid="stAppViewContainer"] > .main {{
        display: flex !important;
        justify-content: flex-start !important;
    }}

    .title-container {{ margin-top: 0; margin-bottom: 30px; }}
    .hero-title-line1 {{
        font-size: 38px; font-weight: 900; 
        background: linear-gradient(120deg, #F43F5E, #FB923C);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0; white-space: nowrap; 
    }}
    .hero-title-line2 {{
        font-size: 38px; font-weight: 900; 
        background: linear-gradient(120deg, #FB923C, #F43F5E);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0; white-space: nowrap;
    }}
    .hero-subtitle {{ color: #64748B; font-size: 13px; font-family: monospace; letter-spacing: 1px; margin-top: 5px; white-space: nowrap; }}

    .card-container {{
        display: flex; flex-direction: column; align-items: center; text-align: center; padding: 15px; border-radius: 16px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }}
    .card-container:hover {{
        transform: translateY(-8px);
        background: rgba(255, 255, 255, 0.4);
        box-shadow: 0 10px 20px rgba(251, 146, 60, 0.1);
    }}
    .card-img-circle {{
        width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-bottom: 10px; 
        border: 3px solid #FFFFFF; box-shadow: 0 6px 15px rgba(251, 146, 60, 0.2); transition: all 0.4s ease;
    }}
    .card-container:hover .card-img-circle {{
        transform: scale(1.1) rotate(5deg); box-shadow: 0 12px 25px rgba(251, 146, 60, 0.4);
    }}
    .card-title {{ font-size: 18px; font-weight: 800; color: #1E293B; margin-bottom: 5px; }}
    .card-desc {{ font-size: 13px; color: #64748B; }}

    div.stButton > button {{
        background: #FEF08A !important; color: #854D0E !important; border: 1px solid #FDE047 !important;
        border-radius: 10px !important; font-weight: 700 !important; font-size: 14px !important;
        padding: 8px 0 !important; width: 100% !important; transition: all 0.3s ease !important;
        box-shadow: 0 4px 10px rgba(253, 224, 71, 0.4) !important; margin-top: 8px !important; 
    }}
    div.stButton > button:hover {{
        background: #FDE047 !important; transform: scale(1.05) !important; box-shadow: 0 8px 20px rgba(253, 224, 71, 0.6) !important;
    }}

    .back-btn div.stButton > button {{
        background: #FFFFFF !important; border: 1px solid #CBD5E0 !important; color: #475569 !important; 
        width: 140px !important; font-size: 15px !important; padding: 8px !important; margin-bottom: 20px; border-radius: 8px !important;
    }}
</style>
""", unsafe_allow_html=True)

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

if st.session_state.current_page == 'home':
    st.markdown('<div class="home-bg"></div>', unsafe_allow_html=True)
    st.markdown('<div class="bg-heart"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="title-container">
        <div class="hero-title-line1">乳腺癌 ERα 靶向候选药物</div>
        <div class="hero-title-line2">智能评估平台</div>
        <div class="hero-subtitle">PRECISION ONCOLOGY & MOLECULAR SAR PROFILING SYSTEM</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="small")
    
    with col1:
        st.markdown(f"""
        <div class="card-container">
            <img class="card-img-circle" src="data:image/png;base64,{img_single_icon}">
            <div class="card-title">单分子评估</div>
            <div class="card-desc">药效与安全性分析</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入单分子评估", key="btn_single", use_container_width=True):
            st.session_state.current_page = 'single'
            st.rerun()

    with col2:
        st.markdown(f"""
        <div class="card-container">
            <img class="card-img-circle" src="data:image/png;base64,{img_batch_icon}">
            <div class="card-title">高通量筛选</div>
            <div class="card-desc">批量锁定潜力分子</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入高通量筛选", key="btn_batch", use_container_width=True):
            st.session_state.current_page = 'batch'
            st.rerun()

elif st.session_state.current_page == 'single':
    st.markdown('<div class="single-bg"></div>', unsafe_allow_html=True)
    st.markdown('<div class="bg-heart"></div>', unsafe_allow_html=True)
        
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回平台首页"):
        st.session_state.current_page = 'home'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<style>.block-container { max-width: 100% !important; padding-left: 5vw !important; padding-right: 5vw !important; padding-top: 2rem !important; } [data-testid='stAppViewContainer'] > .main { justify-content: center !important; } </style>", unsafe_allow_html=True)
    single_eval.render()

elif st.session_state.current_page == 'batch':
    if img_batch_bg:
        st.markdown('<div class="batch-page-bg"></div>', unsafe_allow_html=True)
        st.markdown("<style>.stApp { color: white !important; }</style>", unsafe_allow_html=True)
        
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回平台首页"):
        st.session_state.current_page = 'home'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<style>.block-container { max-width: 100% !important; padding-left: 5vw !important; padding-right: 5vw !important; padding-top: 2rem !important; } [data-testid='stAppViewContainer'] > .main { justify-content: center !important; } </style>", unsafe_allow_html=True)
    batch_screen.render()
