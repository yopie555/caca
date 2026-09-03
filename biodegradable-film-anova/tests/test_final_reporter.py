import pytest
import pandas as pd
import os
from src.final_reporter import FinalReporter

def test_final_reporter_initialization(tmp_path):
    reporter = FinalReporter(str(tmp_path))
    assert os.path.exists(reporter.report_dir)

def test_get_significance_text(tmp_path):
    reporter = FinalReporter(str(tmp_path))
    assert reporter.get_significance_text(0.04) == "Significant"
    assert reporter.get_significance_text(0.05) == "Not Significant"
    assert reporter.get_significance_text(pd.NA) == "N/A"

def test_format_p_val(tmp_path):
    reporter = FinalReporter(str(tmp_path))
    assert reporter.format_p_val(0.0001) == "< 0.001"
    assert reporter.format_p_val(0.0456) == "0.0456"

def test_generate_formulation_summary(tmp_path):
    reporter = FinalReporter(str(tmp_path))
    # mock data
    sol_df = pd.DataFrame({
        "CMC": [1, 3],
        "PVA": [0, 2],
        "Plasticizer": ["Sorbitol", "Sorbitol"],
        "Solubilitas": [10.5, 20.0]
    })
    data_dict = {"Solubilitas": sol_df}
    
    form_df = reporter.generate_formulation_summary(data_dict)
    
    # Formulation A = (1, 0)
    row_A = form_df[(form_df["Formulation"] == "A") & (form_df["Plasticizer"] == "Sorbitol")]
    assert not row_A.empty
    assert row_A.iloc[0]["Formable"] == "Yes"
    assert row_A.iloc[0]["Solubilitas"] == 10.5
    
    # Formulation F = (2, 1) -> not in sol_df (mocked)
    row_F = form_df[(form_df["Formulation"] == "F") & (form_df["Plasticizer"] == "Sorbitol")]
    assert not row_F.empty
    assert row_F.iloc[0]["Formable"] == "No"
    assert row_F.iloc[0]["Solubilitas"] == "NA"
