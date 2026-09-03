import pytest
import pandas as pd
import numpy as np
import patsy
from src.estimability_auditor import ANOVAEstimabilityAuditor

@pytest.fixture
def mock_full_design():
    # 72 combinations (3x4x2x3)
    data = []
    for cmc in [1, 2, 3]:
        for pva in [0, 1, 2, 3]:
            for plas in ['Sorbitol', 'Gliserol']:
                for rep in [1, 2, 3]:
                    data.append({
                        "CMC": cmc,
                        "PVA": pva,
                        "Plasticizer": plas,
                        "Replicate": rep,
                        "FTL": np.random.uniform(10, 50)
                    })
    return pd.DataFrame(data)

@pytest.fixture
def mock_downstream_design(mock_full_design):
    # Remove PVA=0 combinations to simulate biofilm downstream
    df = mock_full_design[mock_full_design["PVA"] != 0].copy()
    df.rename(columns={"FTL": "Solubilitas"}, inplace=True)
    
    # Also simulate Formulation nested effect
    df["Formulation"] = "Formula_" + df["CMC"].astype(str) + "_" + df["PVA"].astype(str)
    
    # Remove Formulation F (CMC=2, PVA=1) with Sorbitol because it fails formability
    # This simulates the 17 cell design (51 observations) instead of 18 (54 observations)
    df = df[~((df["CMC"] == 2) & (df["PVA"] == 1) & (df["Plasticizer"] == "Sorbitol"))]
    
    return df

def test_full_design_rank(mock_full_design, tmp_path):
    auditor = ANOVAEstimabilityAuditor(str(tmp_path))
    res = auditor.run_audit(mock_full_design, "FTL")
    assert res is not None
    assert res["estimable"] is True
    assert res["rank"] == res["cols"]
    assert res["cols"] == 24 # 3 * 4 * 2 = 24 parameters

def test_downstream_design_rank_deficiency(mock_downstream_design, tmp_path):
    auditor = ANOVAEstimabilityAuditor(str(tmp_path))
    res = auditor.run_audit(mock_downstream_design, "Solubilitas")
    assert res is not None
    assert res["estimable"] is False
    assert res["rank"] < res["cols"]
    assert len(res["aliased_cols"]) > 0

def test_candidate_models(mock_downstream_design, tmp_path):
    auditor = ANOVAEstimabilityAuditor(str(tmp_path))
    auditor.run_audit(mock_downstream_design, "Solubilitas")
    
    # There should be 4 candidate models evaluated
    assert len(auditor.model_comparison_records) == 4
    
    main_effects = next(m for m in auditor.model_comparison_records if m["Model_Name"] == "Main Effects")
    assert main_effects["Estimable"] is True
    
    formulation = next(m for m in auditor.model_comparison_records if m["Model_Name"] == "Formulation Approach")
    assert formulation["Estimable"] is False
