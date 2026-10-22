import shap
import joblib
import pandas as pd
import matplotlib.pyplot as plt

# 支持中文
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv("../data/merged_data.csv")

exclude = ["SMILES", "IC50_nM", "pIC50", "Caco-2", "CYP3A4", "hERG", "HOB", "MN"]
desc_cols = [c for c in df.columns if c not in exclude]

model = joblib.load("../models/model_activity.pkl")

# 取前 300 个样本做 SHAP 分析
X = df[desc_cols].iloc[:300]

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

# 保存全局重要性图
shap.summary_plot(shap_values, X, plot_type="bar", show=False, max_display=20)
plt.savefig("shap_global.png", bbox_inches="tight", dpi=150)
plt.close()
print("已保存 shap_global.png")

# 打印前 20 个重要特征
import numpy as np
importance = np.abs(shap_values).mean(axis=0)
top20 = np.argsort(importance)[::-1][:20]
print("\n前 20 个最重要的描述符：")
for i in top20:
    print(f"  {desc_cols[i]}: {importance[i]:.4f}")