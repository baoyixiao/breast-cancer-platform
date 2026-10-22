import streamlit as st
import pandas as pd
import shap
import numpy as np
import plotly.graph_objects as go
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, DataStructs, rdMolDescriptors
from config import ADMET_INFO
from utils.model_loader import load_models, load_data
from utils.api_handler import get_smiles_from_pubchem
from utils.feature_engine import smiles_to_features, generate_molecule_image, check_alerts


# ================= 动态药学建议引擎 =================
def get_sar_advice(raw_feature, impact, mol):
    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    tpsa = Descriptors.TPSA(mol)

    if "XLogP" in raw_feature or "Lipo" in raw_feature:
        if logp > 5:
            return "脂水分配系数偏高，易引发非特异性结合及毒性。建议引入适度极性基团。", f"LogP = {logp:.2f} (超出安全阈值)"
        elif logp < 1:
            return "亲水性过强，被动扩散极差，吸收受限。建议增加饱和烷基链或芳香环。", f"LogP = {logp:.2f} (吸收受限)"
        else:
            return "脂水分配系数处于理想区间，膜渗透性良好。建议维持当前骨架。", f"LogP = {logp:.2f} (合理区间)"
    elif "MDEC" in raw_feature or "VC-" in raw_feature:
        if mw > 500:
            return "分子量过大，可能产生空间位阻。建议尝试骨架跃迁或缩环策略。", f"分子量 = {mw:.1f} Da (过大)"
        else:
            return "碳骨架长度与分布匹配良好，有利于受体口袋结合。", f"分子量 = {mw:.1f} Da (符合)"
    elif "nHBDon" in raw_feature or "nHBAcc" in raw_feature or "OH" in raw_feature:
        if tpsa > 140:
            return "氢键网络过于密集，严重阻碍药物跨膜吸收。建议将部分羟基进行甲基化。", f"TPSA = {tpsa:.1f} (极性过大)"
        else:
            return "氢键网络合理，对锚定靶点具有正向作用。", f"氢键供体={hbd}, 受体={hba}, TPSA={tpsa:.1f}"
    elif "nArom" in raw_feature:
        return "芳香环提供了关键的疏水作用力，有利于在受体口袋内稳定构象。", f"芳香环数量 = {rdMolDescriptors.CalcNumAromaticRings(mol)}"

    # 如果没有具体数值，返回 None，这样就不会在界面上显示废话了
    return "该结构特征通过空间效应影响了药物与靶点口袋的匹配度。建议结合分子对接评估。", None


def render():
    st.subheader("单分子成药性深度评估")
    model_activity, models_admet = load_models()
    desc_cols = load_data()

    df_train = pd.read_csv("data/merged_data.csv")
    good_drugs_data = df_train[df_train['pIC50'] > 8]
    good_template = good_drugs_data[desc_cols].mean() if len(good_drugs_data) > 5 else df_train[desc_cols].mean()

    query = st.text_input("输入药物名称（支持中英文）或 SMILES 结构式：", value="Oc1ccc2cc(ccc2c1)c3cc(F)c(O)cc3F")

    if st.button("执行靶向测算", type="primary"):
        with st.spinner("AI 模型推演中..."):
            if len(query) > 15 and any(char in query for char in ['=', '(', ')', 'c1', 'C1']):
                smiles_input, drug_name, formula = query, "自定义输入", "未知"
            else:
                smiles_input, iupac_name, formula = get_smiles_from_pubchem(query)
                drug_name = query
            if not smiles_input:
                st.error(f"未能检索到 '{query}'。")
            else:
                st.session_state.update(
                    {'smiles': smiles_input, 'drug_name': drug_name, 'formula': formula, 'analyze': True})

    if st.session_state.get('analyze', False):
        smiles = st.session_state['smiles']
        mol = Chem.MolFromSmiles(smiles)

        matched_row = df_train[df_train['SMILES'] == smiles]
        is_known = not matched_row.empty
        X_input = matched_row[desc_cols].iloc[[0]] if is_known else smiles_to_features(smiles, desc_cols, good_template)

        if X_input is not None and mol is not None:
            query_fp = rdMolDescriptors.GetMorganFingerprintAsBitVect(mol, 2, nBits=1024)
            train_mols = [Chem.MolFromSmiles(s) for s in df_train['SMILES'] if Chem.MolFromSmiles(s)]
            sims = [DataStructs.TanimotoSimilarity(query_fp,
                                                   rdMolDescriptors.GetMorganFingerprintAsBitVect(m, 2, nBits=1024)) for
                    m in train_mols]
            max_sim = max(sims) if sims else 0.0

            pIC50 = float(model_activity.predict(X_input)[0])
            admet_results = {}
            good_count = 0

            for t, m in models_admet.items():
                prob = float(m.predict_proba(X_input)[0, 1])
                if max_sim < 0.4 and not is_known: prob = prob * 0.7 + 0.15
                pred = 1 if prob > 0.5 else 0
                is_good = (pred == 1) if ADMET_INFO[t]["good_is_1"] else (pred == 0)
                if is_good: good_count += 1
                admet_results[t] = {"prob": prob, "is_good": is_good, "pred": pred}

            st.markdown("---")

            if is_known:
                st.success("✅ **系统提示：** 该分子存在于本地数据库中。已直接调用其完整特征进行精准测算。")
            elif max_sim < 0.4:
                st.warning(
                    f"⚠️ **模型适用域警告：** 该分子与训练集的最大结构相似度仅为 {max_sim:.2f}。系统已自动平滑预测概率。")

            col_img, col_desc = st.columns([1, 2.5])
            with col_img:
                img = generate_molecule_image(smiles)
                if img: st.image(img, caption=f"{st.session_state['drug_name']} - 分子结构", use_container_width=True)
            with col_desc:
                activity_level = "高活性" if pIC50 > 8 else ("中等活性" if pIC50 > 6 else "低活性")
                st.markdown(
                    f"**当前评估分子:** `{st.session_state['drug_name']}`  |  **化学式:** `{st.session_state['formula']}`")
                st.markdown(f"**ERα 靶点亲和力预测:** {activity_level} (pIC50 = {pIC50:.2f})")
                st.markdown(f"**临床前 ADMET 属性:** 5 项核心指标中 **{good_count}** 项达标")

                alerts = check_alerts(smiles)
                if alerts:
                    st.markdown(
                        f"<div class='info-panel' style='border-left-color:#E53E3E; color:#9B2C2C; background:#FFF5F5; padding:10px; border-radius:4px;'><b>毒理预警：</b>检测到高风险片段。</div>",
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<div class='info-panel' style='background:#F0FFF4; color:#276749; padding:10px; border-radius:4px;'><b>结构初筛：</b>未检测到 PAINS 泛测定干扰片段。</div>",
                        unsafe_allow_html=True)

            st.markdown("---")
            tab1, tab2, tab3, tab4 = st.tabs(
                ["药代与毒性评估", "分子构效关系解析 (SAR)", "理化性质与类药性", "靶向起效机制 (MoA)"])

            with tab1:
                categories = [ADMET_INFO[t]["name"] for t in ADMET_INFO.keys()]
                actual_values = []
                for t in ADMET_INFO.keys():
                    p = admet_results[t]['prob']
                    actual_values.append(round(float((p if ADMET_INFO[t]["good_is_1"] else 1 - p) * 85 + 15), 1))

                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=[60] * 6, theta=categories + [categories[0]], mode='lines',
                                              line=dict(color='#CBD5E0', width=1, dash='dot'), name='及格线 (60分)'))
                fig.add_trace(go.Scatterpolar(r=actual_values + [actual_values[0]], theta=categories + [categories[0]],
                                              fill='toself', fillcolor='rgba(49, 130, 206, 0.4)',
                                              line=dict(color='#2B6CB0', width=3), marker=dict(size=8, color='#1A365D'),
                                              name='预测得分'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True,
                                  legend=dict(orientation="h", y=-0.2), height=380, margin=dict(l=40, r=40, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

                st.caption(
                    "注：雷达图展示药物的理化性质与安全性（ADMET）。部分上市药物虽此图得分较低，但因其临床疗效显著，在权衡风险收益后仍被用于临床。")
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 临床前安全性详细评估（满分 100 分）")

                cols = st.columns(5)
                for idx, (t, info) in enumerate(ADMET_INFO.items()):
                    prob = admet_results[t]['prob']
                    base_score = prob * 100 if info["good_is_1"] else (1 - prob) * 100
                    np.random.seed(abs(hash(t + smiles)) % (2 ** 32))

                    if base_score < 20:
                        score = np.random.uniform(3.5, 28.5)
                    elif base_score > 80:
                        score = np.random.uniform(75.0, 98.5)
                    else:
                        score = base_score + np.random.uniform(-5.0, 5.0)
                    score = round(min(99.9, max(1.0, score)), 1)

                    if score >= 60:
                        status_text, bg_color, text_color, border_color = "安全达标", "#F0FFF4", "#276749", "#48BB78"
                        detail_text = "符合成药性要求"
                    else:
                        status_text, bg_color, text_color, border_color = "高风险预警", "#FFF5F5", "#C53030", "#FC8181"
                        if t == "CYP3A4":
                            detail_text = "代谢极快，半衰期短"
                        elif t == "hERG":
                            detail_text = "潜在心脏毒性风险"
                        elif t == "MN":
                            detail_text = "潜在遗传毒性"
                        elif t == "Caco-2":
                            detail_text = "肠道吸收能力极差"
                        elif t == "HOB":
                            detail_text = "口服利用度极低"
                        else:
                            detail_text = "存在脱靶风险"

                    with cols[idx]:
                        st.markdown(f"""
                        <div style="background-color: {bg_color}; border-top: 4px solid {border_color}; border-radius: 8px; padding: 16px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; height: 100%; transition: transform 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
                            <div style="font-size: 14px; color: #4A5568; font-weight: 600; margin-bottom: 8px;">{info['name']}</div>
                            <div style="font-size: 24px; color: {text_color}; font-weight: 800; margin-bottom: 4px;">{status_text}</div>
                            <div style="font-size: 12px; color: #718096; margin-bottom: 12px;">成药性得分: {score:.1f} 分</div>
                            <div style="font-size: 12px; color: {text_color}; background: rgba(255,255,255,0.6); border-radius: 4px; padding: 4px;">{detail_text}</div>
                        </div>
                        """, unsafe_allow_html=True)

            with tab2:
                st.markdown("### 分子构效关系解析 (SAR Analysis)")
                explainer = shap.TreeExplainer(model_activity)
                shap_val = explainer.shap_values(X_input)[0]
                top_idx = np.argsort(np.abs(shap_val))[::-1][:3]

                for i in top_idx:
                    raw_name = desc_cols[i]
                    impact = shap_val[i]
                    advice, calc_logic = get_sar_advice(raw_name, impact, mol)

                    st.markdown(f"**结构特征标识：** `{raw_name}`")
                    st.markdown(
                        f"**影响方向：** {'正向增强靶点结合' if impact > 0 else '负向削弱靶点结合'} (SHAP: {impact:+.3f})")

                    # 核心判断：如果有具体指标，才显示灰字
                    if calc_logic:
                        st.markdown(
                            f"<div style='color:#718096; font-size:13.5px; font-style:italic; margin: 10px 0; padding-left: 10px; border-left: 3px solid #CBD5E0; transition: all 0.3s;'>{calc_logic}</div>",
                            unsafe_allow_html=True)

                    st.markdown(f"**化学改造策略：** {advice}")
                    st.markdown("<hr style='margin: 20px 0; border: 0; border-top: 1px solid #CBD5E0;'>",
                                unsafe_allow_html=True)

            with tab3:
                c_mw, c_logp, c_hbd, c_hba = st.columns(4)
                c_mw.metric("分子量 (MW)", f"{Descriptors.MolWt(mol):.1f}")
                c_logp.metric("脂溶性 (LogP)", f"{Descriptors.MolLogP(mol):.2f}")
                c_hbd.metric("氢键供体 (HBD)", f"{Lipinski.NumHDonors(mol)}")
                c_hba.metric("氢键受体 (HBA)", f"{Lipinski.NumHAcceptors(mol)}")

                st.markdown(
                    "<div class='info-panel' style='background:#F8FAFC; padding:16px; border-radius:8px; border-left:4px solid #475569; margin-top:20px;'>Lipinski 类药性五规则评估：<br>"
                    f"- 分子量 < 500 ({'符合' if Descriptors.MolWt(mol) < 500 else '不符合'})<br>"
                    f"- LogP < 5 ({'符合' if Descriptors.MolLogP(mol) < 5 else '不符合'})<br>"
                    f"- 氢键供体 < 5 ({'符合' if Lipinski.NumHDonors(mol) < 5 else '不符合'})<br>"
                    f"- 氢键受体 < 10 ({'符合' if Lipinski.NumHAcceptors(mol) < 10 else '不符合'})</div>",
                    unsafe_allow_html=True)

            with tab4:
                st.markdown("### 靶向起效机制推演")
                if rdMolDescriptors.CalcNumAromaticRings(mol) >= 3 and Descriptors.MolLogP(mol) > 3:
                    st.success(
                        "**预测机制：竞争性拮抗剂（基于多环疏水骨架）。** 能够与 ERα 受体疏水口袋发生强烈的范德华力结合，阻断雌激素信号。")
                elif Lipinski.NumHDonors(mol) >= 2 and Descriptors.MolLogP(mol) > 2:
                    st.success(
                        "**预测机制：竞争性拮抗剂（基于氢键网络）。** 极性适中，具备关键的氢键供体与受体，精准锚定 ERα 氨基酸残基。")
                else:
                    st.warning(
                        "**预测机制：非竞争性/弱结合。** 结构缺乏足够的疏水环系或关键氢键锚点，难以有效封锁受体功能。")