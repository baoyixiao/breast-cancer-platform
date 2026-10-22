import pandas as pd

activity = pd.read_excel("ERα_activity.xlsx", sheet_name="training")
admet = pd.read_excel("ADMET.xlsx", sheet_name="training")
desc = pd.read_excel("Molecular_Descriptor.xlsx", sheet_name="training")

print("活性表：", activity.shape)
print("ADMET表：", admet.shape)
print("描述符表：", desc.shape)

merged = activity.merge(admet, on="SMILES").merge(desc, on="SMILES")
print("合并后：", merged.shape)

merged.to_csv("merged_data.csv", index=False)
print("已保存 merged_data.csv")