import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, rdMolDescriptors, Draw
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

params = FilterCatalogParams()
params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
pains_catalog = FilterCatalog(params)

def generate_molecule_image(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol:
        return Draw.MolToImage(mol, size=(450, 350))
    return None

def check_alerts(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if not mol: return []
    matches = pains_catalog.GetMatches(mol)
    return [m.GetDescription() for m in matches]

def smiles_to_features(smiles, desc_cols, train_means):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None: return None
    features = pd.DataFrame([train_means], columns=desc_cols)
    try:
        if 'MW' in desc_cols: features['MW'] = Descriptors.MolWt(mol)
        if 'XLogP' in desc_cols: features['XLogP'] = Descriptors.MolLogP(mol)
        if 'nHBDon' in desc_cols: features['nHBDon'] = Lipinski.NumHDonors(mol)
        if 'nHBAcc' in desc_cols: features['nHBAcc'] = Lipinski.NumHAcceptors(mol)
        if 'nRotB' in desc_cols: features['nRotB'] = Lipinski.NumRotatableBonds(mol)
        if 'TopoPSA' in desc_cols: features['TopoPSA'] = rdMolDescriptors.CalcTPSA(mol)
        if 'nRing' in desc_cols: features['nRing'] = rdMolDescriptors.CalcNumRings(mol)
    except: pass
    return features