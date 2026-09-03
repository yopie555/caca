import os
import sys
import logging

def get_output_dir(base_dir, subdir):
    """Ensure directory exists and return the path."""
    path = os.path.join(base_dir, subdir)
    os.makedirs(path, exist_ok=True)
    return path

def setup_logger(name, log_file):
    """Setup a simple logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
    return logger

import re

def normalize_column_name(name):
    if name is None:
        return ""
    name = str(name).strip().lower()
    name = name.replace("%", "percent")
    # Replace anything not a-z, 0-9 with underscore
    name = re.sub(r'[^a-z0-9]', '_', name)
    # Collapse multiple underscores
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name

COLUMN_ALIASES = {
    "Formulation": ["kode", "formulasi", "formula", "treatment", "kode_formulasi", "variasi_biofilm", "kode_cmc_pva"],
    "Replicate": ["ulangan", "replicate", "replication", "r", "u"],
    "CMC": ["cmc", "cmc_g", "cmc_percent", "konsentrasi_cmc"],
    "PVA": ["pva", "pva_g", "pva_percent", "konsentrasi_pva"]
}

RESPONSE_ALIASES = {
    "FTL": ["ftl", "fraksi_tak_larut_percent", "fraksi_tak_larut", "fraksi_tidak_larut"],
    "Kelarutan": ["kelarutan", "kelarutan_percent", "solubility"],
    "Solubilitas": ["solubilitas", "solubilitas_percent", "solubilitas_air", "water_solubility"],
    "Opasitas": ["opasitas", "opasitas_abs600_x", "opacity"],
    "WVTR": ["wvtr", "water_vapor_transmission_rate", "water_vapor_transmission", "wvtr_w_txa_g_m_24_jam", "wvtr_w_a_g_m_24_jam"],
    "Biodegradabilitas": ["biodegradabilitas", "biodegradability"],
    "UTS": ["uts", "ultimate_tensile_strength", "tensile_strength"],
    "Elongasi": ["elongasi", "elongation", "elongation_at_break", "elongasi_percent"],
    "Formability": ["membentuk_lembaran_biofilm", "membentuk_biofilm", "membentuk_lembaran"]
}

SHEET_RESPONSE_MAP = {
    "Kelarutan Matriks": ["FTL", "Kelarutan", "Formability"],
    "Opasitas": ["Opasitas"],
    "Solubilitas": ["Solubilitas"],
    "WVTR": ["WVTR"],
    "UTS & elong": ["UTS", "Elongasi"],
}

FORMULATION_MAP = {
    "A": {"CMC": 1, "PVA": 0},
    "B": {"CMC": 1, "PVA": 1},
    "C": {"CMC": 1, "PVA": 2},
    "D": {"CMC": 1, "PVA": 3},
    "E": {"CMC": 2, "PVA": 0},
    "F": {"CMC": 2, "PVA": 1},
    "G": {"CMC": 2, "PVA": 2},
    "H": {"CMC": 2, "PVA": 3},
    "I": {"CMC": 3, "PVA": 0},
    "J": {"CMC": 3, "PVA": 1},
    "K": {"CMC": 3, "PVA": 2},
    "L": {"CMC": 3, "PVA": 3},
}

MATRIX_LEVEL = ["FTL", "Kelarutan", "Formability"]
DOWNSTREAM_BIOFILM = ["Solubilitas", "Opasitas", "WVTR", "UTS", "Elongasi"]

EXPECTED_RESPONSES = [
    "FTL", "Kelarutan", "Solubilitas", "Opasitas", "WVTR", "Biodegradabilitas", "UTS", "Elongasi"
]

import pandas as pd

def normalize_factor_value(factor_type, value):
    if pd.isna(value):
        return value
    if factor_type == "Formulation":
        v = str(value).strip().upper()
        if len(v) > 0 and v[0].isalpha():
            return v[0]
        return v
    elif factor_type == "Plasticizer":
        v = str(value).strip().lower()
        if "sorbitol" in v: return "Sorbitol"
        if "gliserol" in v or "glycerol" in v: return "Gliserol"
        return value
    elif factor_type in ["CMC", "PVA", "Replicate"]:
        try:
            v_str = str(value).replace(',', '.')
            if factor_type == "Replicate":
                import re
                m = re.search(r'(\d+)', v_str)
                if m:
                    v_str = m.group(1)
            v = float(v_str)
            if v.is_integer():
                return int(v)
            return v
        except ValueError:
            return value
    elif factor_type == "Formability":
        v = str(value).strip().lower()
        if v in ["ya", "true", "1", "yes"]:
            return True
        if v in ["tidak", "false", "0", "no"]:
            return False
        return value
    return value

