import pandas as pd
import lightgbm as lgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, roc_auc_score

df = pd.read_csv("../data/merged_data.csv")

# 特征列：729 个描述符
exclude = ["SMILES", "IC50_nM", "pIC50", "Caco-2", "CYP3A4", "hERG", "HOB", "MN"]
desc_cols = [c for c in df.columns if c not in exclude]

X = df[desc_cols]
y_activity = df["pIC50"]

# ===== 活性回归模型 =====
print("训练活性模型...")
X_train, X_test, y_train, y_test = train_test_split(X, y_activity, test_size=0.2, random_state=42)
model_activity = lgb.LGBMRegressor(n_estimators=500, learning_rate=0.05, verbose=-1)
model_activity.fit(X_train, y_train)

pred = model_activity.predict(X_test)
print("活性模型 RMSE:", round(mean_squared_error(y_test, pred) ** 0.5, 4))
print("活性模型 R2:", round(r2_score(y_test, pred), 4))

joblib.dump(model_activity, "../models/model_activity.pkl")

# ===== ADMET 分类模型 =====
print("\n训练 ADMET 模型...")
for target in ["Caco-2", "CYP3A4", "hERG", "HOB", "MN"]:
    y = df[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = lgb.LGBMClassifier(n_estimators=500, learning_rate=0.05, verbose=-1)
    model.fit(X_train, y_train)
    pred_prob = model.predict_proba(X_test)[:, 1]
    print(f"{target} AUC: {round(roc_auc_score(y_test, pred_prob), 4)}")
    joblib.dump(model, f"model_{target}.pkl")

print("\n全部模型已保存")