import streamlit as st
import pandas as pd
import numpy as np
from config import ADMET_INFO
from utils.model_loader import load_models, load_data
from utils.feature_engine import smiles_to_features


def render():
    st.markdown(
        '<h2 style="color: white; font-weight: 800; text-shadow: 0 2px 4px rgba(0,0,0,0.3); margin-bottom: 20px;">高通量虚拟筛选库</h2>',
        unsafe_allow_html=True)

    # 提示框
    st.markdown(
        """
        <div style="display: inline-block; background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(12px); padding: 15px 25px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.3); margin-bottom: 25px; max-width: 650px;">
            <p style="color: white; margin: 0; font-size: 15px; line-height: 1.6;">
                上传包含新分子的 <code style="background: rgba(255,255,255,0.2); color: #FDE047; padding: 2px 6px; border-radius: 4px;">.csv</code> 文件（<b>文件必须包含一列名为 SMILES</b>）。<br>
                系统将自动进行高通量盲测并输出优先级排行榜。
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    model_activity, models_admet = load_models()
    desc_cols = load_data()
    df_train = pd.read_csv("data/merged_data.csv")

    good_drugs_data = df_train[df_train['pIC50'] > 8]
    good_template = good_drugs_data[desc_cols].mean() if len(good_drugs_data) > 5 else df_train[desc_cols].mean()

    # ================= 核心修复：限制上传组件的宽度，不让它拉满屏幕 =================
    st.markdown(
        """
        <style>
            /* 强制上传组件限制宽度为 600px，留出右侧空间 */
            div[data-testid="stFileUploader"] {
                max-width: 600px !important;
            }
            /* 重新美化提示文字颜色 */
            div[data-testid="stFileUploader"] label p {
                color: #38BDF8 !important; 
                font-weight: bold !important;
                font-size: 15px !important;
            }
            /* 内部上传框设为暗黑玻璃态 */
            div[data-testid="stFileUploadDropzone"] {
                background-color: rgba(30, 41, 59, 0.7) !important;
                border: 2px dashed #38BDF8 !important;
                border-radius: 12px !important;
            }
            /* 文字反白 */
            div[data-testid="stFileUploadDropzone"] span, 
            div[data-testid="stFileUploadDropzone"] small,
            div[data-testid="stFileUploadDropzone"] div {
                color: #E2E8F0 !important;
            }
            /* 强制显示右侧的 Browse 按钮并给它上色 */
            div[data-testid="stFileUploadDropzone"] button {
                display: inline-flex !important;
                background-color: #38BDF8 !important;
                color: #0F172A !important;
                font-weight: bold !important;
                border-radius: 6px !important;
                padding: 5px 15px !important;
                border: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader("将您的分子库文件 (CSV) 拖拽到此处，或点击浏览", type=["csv"])
    # ==============================================================================

    if uploaded_file is not None:
        batch_df = pd.read_csv(uploaded_file)
        if "SMILES" not in batch_df.columns:
            st.error("文件格式错误：未找到 'SMILES' 列。请确保第一行包含 SMILES 表头。")
        else:
            with st.spinner("正在执行高通量特征计算与 AI 预测，请稍候..."):
                results = []
                for idx, row in batch_df.iterrows():
                    smiles = row['SMILES']
                    feats = smiles_to_features(smiles, desc_cols, good_template)

                    if feats is not None:
                        pIC50 = float(model_activity.predict(feats)[0])
                        good_count = sum(
                            [((m.predict_proba(feats)[0, 1] > 0.5) == ADMET_INFO[t]["good_is_1"]) for t, m in
                             models_admet.items()])

                        score = (pIC50 / 10) * 60 + (good_count / 5) * 40
                        activity_level = "高" if pIC50 > 8 else ("中" if pIC50 > 6 else "低")
                        safety_level = "全部达标" if good_count == 5 else (
                            f"仅{good_count}项达标" if good_count > 0 else "全部高危")

                        results.append({
                            "SMILES": smiles,
                            "活性等级": activity_level,
                            "预测_pIC50": round(pIC50, 2),
                            "ADMET状态": safety_level,
                            "综合评分": round(score, 2)
                        })

                if results:
                    res_df = pd.DataFrame(results).sort_values(by="综合评分", ascending=False).reset_index(drop=True)
                    st.success(f"筛选完成！系统已成功评估 {len(res_df)} 个未知分子。")
                    st.markdown('<h3 style="color: white; margin-top: 20px;">优先候选化合物 Top 10</h3>',
                                unsafe_allow_html=True)

                    st.dataframe(res_df.head(10).style.background_gradient(cmap="Blues", subset=["综合评分"]),
                                 use_container_width=True)

                    csv_result = res_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="下载完整筛选评估报告 (CSV)",
                        data=csv_result,
                        file_name="Screening_Results.csv",
                        mime="text/csv",
                    )
                    st.info("提示：您可以将下载的 CSV 报告直接导入 Excel 或企业内部系统。")
                else:
                    st.warning("未能从文件中解析出有效分子，请检查 SMILES 格式是否正确。")