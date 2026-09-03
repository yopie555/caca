import pytest
import pandas as pd
import numpy as np
from src.master_validator import MasterValidator
from src.validation import Validator
import os
import shutil

@pytest.fixture
def temp_dir():
    d = "test_output"
    os.makedirs(os.path.join(d, "validation"), exist_ok=True)
    yield d
    shutil.rmtree(d)

def test_pva_zero(temp_dir):
    df = pd.DataFrame({
        "CMC": [1, 2, 3],
        "PVA": [0, 0, 0],
        "Plasticizer": ["Gliserol", "Gliserol", "Gliserol"],
        "Replicate": [1, 1, 1],
        "Resp": [10, 11, 12]
    })
    
    assert 0 in df["PVA"].values, "PVA=0 must be retained and valid"
    assert len(df.dropna()) == 3, "dropna should not remove PVA=0"

def test_plasticizer_unique(temp_dir):
    df = pd.DataFrame({
        "Plasticizer": ["Gliserol", "Sorbitol"]
    })
    assert df["Plasticizer"].nunique() == 2

def test_duplicate(temp_dir):
    df = pd.DataFrame({
        "CMC": [1, 1],
        "PVA": [0, 0],
        "Plasticizer": ["Gliserol", "Gliserol"],
        "Replicate": [1, 1],
        "Resp": [10, 10],
        "source_sheet": ["s1", "s1"],
        "source_block": ["b1", "b1"],
        "source_row": [1, 2]
    })
    
    val = Validator(temp_dir)
    val.validate_dataset(df, "Resp")
    
    dup_file = os.path.join(temp_dir, "validation", "duplicate_rows.csv")
    assert os.path.exists(dup_file)
    dup_df = pd.read_csv(dup_file)
    assert len(dup_df) == 2, "Both rows involved in duplicate should be logged"

def test_ftl_kelarutan_inconsistency(temp_dir):
    ftl = pd.DataFrame({
        "CMC": [1], "PVA": [0], "Plasticizer": ["Gliserol"], "Replicate": [1], "FTL": [10]
    })
    kel = pd.DataFrame({
        "CMC": [1], "PVA": [0], "Plasticizer": ["Gliserol"], "Replicate": [1], "Kelarutan": [85] # Should be 90
    })
    
    val = Validator(temp_dir)
    val.run_consistency_check(ftl, kel)
    
    cons_file = os.path.join(temp_dir, "validation", "ftl_kelarutan_consistency.csv")
    assert os.path.exists(cons_file)
    cons_df = pd.read_csv(cons_file)
    
    assert len(cons_df) == 1
    assert cons_df["Difference"].iloc[0] == 5
    assert cons_df["Status"].iloc[0] == "Inconsistent"

def test_master_validator_halts_on_duplicate(temp_dir):
    df = pd.DataFrame({
        "CMC": [1, 1], "PVA": [0, 0], "Plasticizer": ["Gliserol", "Gliserol"], "Replicate": [1, 1], "FTL": [10, 10]
    })
    
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"FTL": df})
    
    assert global_safe is False, "Pipeline should halt on duplicates"
    assert response_safety["FTL"]["design_status"] == "DUPLICATES FOUND"
    
def test_master_validator_warns_on_incomplete(temp_dir):
    df = pd.DataFrame({
        "CMC": [1], "PVA": [1], "Plasticizer": ["Gliserol"], "Replicate": [1], "FTL": [10]
    })
    
    mv = MasterValidator(temp_dir)
    global_safe, response_safety = mv.generate_report({"FTL": df})
    
    assert global_safe is False, "Incomplete design must block global safety for full factorial ANOVA"
    assert response_safety["FTL"]["design_status"] == "INCOMPLETE"
