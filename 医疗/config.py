
SYSTEM_NAME = "乳腺癌 ERα 靶向候选药物智能评估平台"

ADMET_INFO = {
    "Caco-2": {"name": "肠道吸收 (Caco-2)", "good_is_1": True},
    "CYP3A4": {"name": "代谢稳定性 (CYP3A4)", "good_is_1": False},
    "hERG": {"name": "心脏毒性 (hERG)", "good_is_1": False},
    "HOB": {"name": "口服利用度 (HOB)", "good_is_1": True},
    "MN": {"name": "遗传毒性 (MN)", "good_is_1": False}
}

EXCLUDE_COLS = ["SMILES", "IC50_nM", "pIC50", "Caco-2", "CYP3A4", "hERG", "HOB", "MN"]