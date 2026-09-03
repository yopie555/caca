import pytest
import pandas as pd
import numpy as np
from src.master_validator import MasterValidator
from src.utils import normalize_factor_value
import os
import shutil
import itertools

@pytest.fixture
def temp_dir():
    d = "test_output_safety"
    os.makedirs(os.path.join(d, "validation"), exist_ok=True)
    yield d
    shutil.rmtree(d)

@pytest.fixture
def dummy_eligibility_map():
    # Downstream eligibility map based on FTL
    # Sorbitol: B,C,D,G,H,J,K,L (8 forms)
    # Gliserol: B,C,D,F,G,H,J,K,L (9 forms)
    emap = {}
    for form in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]:
        for plast in ["Sorbitol", "Gliserol"]:
            eligible = True
            if form in ["A", "E", "I"]: eligible = False
            if form == "F" and plast == "Sorbitol": eligible = False
            emap[(form, plast)] = eligible
    return emap

def generate_full_matrix(resp_name="Resp"):
    all_cells = list(itertools.product([1, 2, 3], [0, 1, 2, 3], ["Gliserol", "Sorbitol"]))
    data = []
    for cell in all_cells:
        for r in [1, 2, 3]:
            data.append({"CMC": cell[0], "PVA": cell[1], "Plasticizer": cell[2], "Replicate": r, resp_name: 10.0})
    return pd.DataFrame(data)

def generate_downstream_matrix(resp_name="Resp", emap=None):
    from src.utils import FORMULATION_MAP
    if emap is None:
        return pd.DataFrame()
        
    all_cells = list(itertools.product([1, 2, 3], [0, 1, 2, 3], ["Gliserol", "Sorbitol"]))
    formulation_reverse = { (v["CMC"], v["PVA"]): k for k, v in FORMULATION_MAP.items() }
    
    data = []
    for cell in all_cells:
        cmc, pva, plast = cell
        form = formulation_reverse.get((cmc, pva))
        if emap.get((form, plast), False):
            for r in [1, 2, 3]:
                data.append({"CMC": cmc, "PVA": pva, "Plasticizer": plast, "Replicate": r, resp_name: 10.0})
    return pd.DataFrame(data)

# Test 1
def test_1_ftl_complete(temp_dir):
    df = generate_full_matrix("FTL")
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"FTL": df})
    assert response_safety["FTL"]["design_status"] == "COMPLETE"
    assert len(df) == 72

# Test 2
def test_2_kelarutan_complete(temp_dir):
    df = generate_full_matrix("Kelarutan")
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"Kelarutan": df})
    assert response_safety["Kelarutan"]["design_status"] == "COMPLETE"
    assert len(df) == 72

# Test 3
def test_3_solubilitas_conditional(temp_dir, dummy_eligibility_map):
    df = generate_downstream_matrix("Solubilitas", dummy_eligibility_map)
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"Solubilitas": df}, eligibility_map=dummy_eligibility_map)
    assert response_safety["Solubilitas"]["design_status"] == "COMPLETE"
    assert len(df) == 51

# Test 4
def test_4_opasitas_conditional(temp_dir, dummy_eligibility_map):
    df = generate_downstream_matrix("Opasitas", dummy_eligibility_map)
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"Opasitas": df}, eligibility_map=dummy_eligibility_map)
    assert response_safety["Opasitas"]["design_status"] == "COMPLETE"
    assert len(df) == 51

# Test 5
def test_5_wvtr_conditional(temp_dir, dummy_eligibility_map):
    df = generate_downstream_matrix("WVTR", dummy_eligibility_map)
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"WVTR": df}, eligibility_map=dummy_eligibility_map)
    assert response_safety["WVTR"]["design_status"] == "COMPLETE"
    assert len(df) == 51

# Test 6
def test_6_uts_conditional(temp_dir, dummy_eligibility_map):
    df = generate_downstream_matrix("UTS", dummy_eligibility_map)
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"UTS": df}, eligibility_map=dummy_eligibility_map)
    assert response_safety["UTS"]["design_status"] == "COMPLETE"
    assert len(df) == 51

# Test 7
def test_7_elongasi_conditional(temp_dir, dummy_eligibility_map):
    df = generate_downstream_matrix("Elongasi", dummy_eligibility_map)
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"Elongasi": df}, eligibility_map=dummy_eligibility_map)
    assert response_safety["Elongasi"]["design_status"] == "COMPLETE"
    assert len(df) == 51

# Test 8
def test_8_unexpected_a_sorbitol(temp_dir, dummy_eligibility_map):
    df = generate_downstream_matrix("Solubilitas", dummy_eligibility_map)
    # A = CMC 1, PVA 0
    df = pd.concat([df, pd.DataFrame([{"CMC": 1, "PVA": 0, "Plasticizer": "Sorbitol", "Replicate": 1, "Solubilitas": 10}])], ignore_index=True)
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"Solubilitas": df}, eligibility_map=dummy_eligibility_map)
    assert response_safety["Solubilitas"]["design_status"] == "INCOMPLETE"

# Test 9
def test_9_unexpected_e_sorbitol(temp_dir, dummy_eligibility_map):
    df = generate_downstream_matrix("Opasitas", dummy_eligibility_map)
    # E = CMC 2, PVA 0
    df = pd.concat([df, pd.DataFrame([{"CMC": 2, "PVA": 0, "Plasticizer": "Sorbitol", "Replicate": 1, "Opasitas": 10}])], ignore_index=True)
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"Opasitas": df}, eligibility_map=dummy_eligibility_map)
    assert response_safety["Opasitas"]["design_status"] == "INCOMPLETE"

# Test 10
def test_10_unexpected_f_sorbitol(temp_dir, dummy_eligibility_map):
    df = generate_downstream_matrix("WVTR", dummy_eligibility_map)
    # F = CMC 2, PVA 1
    df = pd.concat([df, pd.DataFrame([{"CMC": 2, "PVA": 1, "Plasticizer": "Sorbitol", "Replicate": 1, "WVTR": 10}])], ignore_index=True)
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"WVTR": df}, eligibility_map=dummy_eligibility_map)
    assert response_safety["WVTR"]["design_status"] == "INCOMPLETE"

# Test 11
def test_11_unexpected_i_gliserol(temp_dir, dummy_eligibility_map):
    df = generate_downstream_matrix("UTS", dummy_eligibility_map)
    # I = CMC 3, PVA 0
    df = pd.concat([df, pd.DataFrame([{"CMC": 3, "PVA": 0, "Plasticizer": "Gliserol", "Replicate": 1, "UTS": 10}])], ignore_index=True)
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"UTS": df}, eligibility_map=dummy_eligibility_map)
    assert response_safety["UTS"]["design_status"] == "INCOMPLETE"

# Test 12
def test_12_duplicate_detection(temp_dir):
    df = generate_full_matrix("FTL")
    # Duplicate first row
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"FTL": df})
    assert response_safety["FTL"]["design_status"] == "DUPLICATES FOUND"
    assert not global_safe

# Test 13
def test_13_factor_normalization():
    assert normalize_factor_value("CMC", "1") == 1
    assert normalize_factor_value("CMC", 1) == 1
    assert normalize_factor_value("PVA", "2") == 2
    assert normalize_factor_value("PVA", 2.0) == 2
    assert normalize_factor_value("Replicate", "A1") == 1
    assert normalize_factor_value("Plasticizer", "  SORBITOL  ") == "Sorbitol"
    assert normalize_factor_value("Formulation", "a (1%)") == "A"
    assert normalize_factor_value("Formability", "Ya") is True
