import pytest
import pandas as pd
import numpy as np
from src.robustness_auditor import RobustnessAuditor

@pytest.fixture
def mock_conditional_design():
    # Similar to downstream design N=51 (missing PVA=0 and Formulation F-Sorbitol)
    data = []
    for cmc in [1, 2, 3]:
        for pva in [1, 2, 3]:
            for plas in ['Sorbitol', 'Gliserol']:
                # Skip CMC=2, PVA=1, Sorbitol (Formulation F)
                if cmc == 2 and pva == 1 and plas == 'Sorbitol':
                    continue
                for rep in [1, 2, 3]:
                    data.append({
                        "CMC": cmc,
                        "PVA": pva,
                        "Plasticizer": plas,
                        "Replicate": rep,
                        "Solubilitas": np.random.uniform(10, 50)
                    })
    return pd.DataFrame(data)

def test_robustness_auditor_initialization(tmp_path):
    auditor = RobustnessAuditor(str(tmp_path))
    assert auditor.output_dir == str(tmp_path) + "/anova"

def test_partial_eta_squared(tmp_path):
    auditor = RobustnessAuditor(str(tmp_path))
    mock_aov = pd.DataFrame({
        "sum_sq": [100, 50, 200, 150],
        "df": [2, 1, 2, 45]
    }, index=["C(CMC)", "C(Plasticizer)", "C(CMC):C(Plasticizer)", "Residual"])
    
    pes = auditor.calc_partial_eta_squared(mock_aov)
    
    # pes = SS_effect / (SS_effect + SS_resid)
    assert round(pes["C(CMC)"], 4) == round(100 / (100 + 150), 4)
    assert round(pes["C(Plasticizer)"], 4) == round(50 / (50 + 150), 4)
    assert "Residual" not in pes

def test_process_response_conditional(mock_conditional_design, tmp_path):
    auditor = RobustnessAuditor(str(tmp_path))
    formula = "Solubilitas ~ C(CMC) + C(PVA) + C(Plasticizer)"
    
    auditor.process_response(mock_conditional_design, "Solubilitas", formula, is_conditional=True)
    
    assert len(auditor.effect_sizes) == 3 # CMC, PVA, Plasticizer
    assert len(auditor.confidence_intervals) > 0
    assert len(auditor.sensitivity_results) > 0 # Should have Model A, Model B, and Model C (Sorbitol/Gliserol)
    
    # Check recommendation
    assert len(auditor.final_recommendations) == 1
    rec = auditor.final_recommendations[0]
    assert "MAIN EFFECTS" in rec["Final_Model"]
    assert "conditional" in rec["Limitations"].lower()
