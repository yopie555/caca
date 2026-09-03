import os
import pandas as pd
import numpy as np
import csv
from src.utils import (
    COLUMN_ALIASES, RESPONSE_ALIASES, SHEET_RESPONSE_MAP, 
    FORMULATION_MAP, EXPECTED_RESPONSES, setup_logger, normalize_column_name, get_output_dir
)

class Preprocessor:
    def __init__(self, raw_csv_files, output_base_dir):
        self.raw_csv_files = raw_csv_files
        self.output_base_dir = output_base_dir
        self.cleaned_dir = get_output_dir(output_base_dir, "cleaned")
        self.val_dir = get_output_dir(output_base_dir, "validation")
        self.logger = setup_logger("preprocessor", os.path.join(output_base_dir, "conversion_log.txt"))
        self.prep_log_path = os.path.join(self.val_dir, "preprocessing_log.csv")
        
        with open(self.prep_log_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Source_File", "Stage", "Original_N", "Removed_N", "Reason", "Remaining_N"])

    def _log_prep(self, file_name, stage, orig_n, rem_n, reason, final_n):
        with open(self.prep_log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([file_name, stage, orig_n, rem_n, reason, final_n])
            
    def _normalize_plasticizer(self, name):
        if not isinstance(name, str):
            return "Unknown"
        n = name.lower()
        if "sorbitol" in n:
            return "Sorbitol"
        elif "gliserol" in n or "glycerol" in n or "gliseol" in n:
            return "Gliserol"
        return "Unknown"

    def _normalize_columns(self, columns):
        new_cols = []
        for col in columns:
            norm_col = normalize_column_name(col)
            matched = False
            
            for std_name, aliases in COLUMN_ALIASES.items():
                if norm_col in aliases or norm_col == std_name.lower():
                    new_cols.append(std_name)
                    matched = True
                    break
                    
            if matched: continue
                
            for std_name, aliases in RESPONSE_ALIASES.items():
                if norm_col in aliases or norm_col == std_name.lower():
                    new_cols.append(std_name)
                    matched = True
                    break
                    
            if not matched:
                new_cols.append(str(col).strip())
                
        return new_cols

    def process_file(self, file_path):
        try:
            df = pd.read_csv(file_path, header=None)
        except pd.errors.EmptyDataError:
            self.logger.warning(f"File {file_path} is empty. Skipping.")
            return pd.DataFrame()
            
        raw_data = df.values.tolist()
        orig_len = len(raw_data)
        
        base = os.path.basename(file_path).replace(".csv", "")
        sheet_match = None
        for sm in SHEET_RESPONSE_MAP.keys():
            if sm.replace(" ", "_").lower() in base.lower():
                sheet_match = sm
                break
                
        sheet_plasticizer = "Unknown"
        if "sorbitol" in base.lower():
            sheet_plasticizer = "Sorbitol"
        elif "gliserol" in base.lower():
            sheet_plasticizer = "Gliserol"

        current_plasticizer = sheet_plasticizer
        
        clean_data = []
        actual_header = None
        
        removed_empty = 0
        removed_header = 0
        removed_block = 0
        
        for row_idx, row in enumerate(raw_data):
            row_str = [str(x).strip() if pd.notna(x) else "" for x in row]
            row_joined = " ".join(row_str).lower()
            
            if "sorbitol" in row_joined:
                current_plasticizer = "Sorbitol"
                if sum([1 for x in row_str if x]) <= 2:
                    removed_block += 1
                    continue
            elif "gliserol" in row_joined or "glycerol" in row_joined or "gliseol" in row_joined:
                current_plasticizer = "Gliserol"
                if sum([1 for x in row_str if x]) <= 2:
                    removed_block += 1
                    continue
                    
            norm_row = [normalize_column_name(x) for x in row_str]
            header_score = 0
            
            from src.utils import COLUMN_ALIASES, RESPONSE_ALIASES
            all_aliases = {**COLUMN_ALIASES, **RESPONSE_ALIASES}
            
            for c in norm_row:
                if not c:
                    continue
                # Exact match against known aliases
                for aliases in all_aliases.values():
                    if c in aliases:
                        header_score += 1
                        break
            
            # We want at least 2 matching base/response column names to consider it a header
            if header_score >= 2:
                actual_header = self._normalize_columns(row_str)
                actual_header += ["Plasticizer", "source_file", "source_sheet", "source_block", "source_row"]
                removed_header += 1
                header_row_idx = row_idx
                continue
                
            if sum([1 for x in row_str if x]) <= 1:
                removed_empty += 1
                continue
            if set(row_str) == {"", "Ya"} or set(row_str) == {"", "Tidak"}:
                removed_empty += 1
                continue
                
            if actual_header:
                clean_data.append(row_str + [current_plasticizer, base, sheet_match if sheet_match else "Unknown", current_plasticizer, row_idx + 1])
                
        self._log_prep(base, "Header cleaning", orig_len, removed_header, "Removed because repeated header", orig_len - removed_header)
        self._log_prep(base, "Empty/block row cleaning", orig_len - removed_header, removed_empty + removed_block, "Removed because empty or block title", len(clean_data))
                
        if not actual_header:
            self.logger.warning(f"Could not find valid headers in {file_path}")
            return pd.DataFrame()
            
        new_df = pd.DataFrame(clean_data, columns=actual_header)
        
        formulation_col = "Formulation"
        # WVTR formulation usually comes from the first column if no Formulation column exists
        if "Formulation" not in new_df.columns:
            # Often it's named Kode
            if "kode" in new_df.columns:
                new_df.rename(columns={"kode": "Formulation"}, inplace=True)
                formulation_col = "kode"
            elif "kode_cmc_pva" in new_df.columns:
                new_df.rename(columns={"kode_cmc_pva": "Formulation"}, inplace=True)
                formulation_col = "kode_cmc_pva"
            elif "treatment" in new_df.columns:
                new_df.rename(columns={"treatment": "Formulation"}, inplace=True)
                formulation_col = "treatment"
                
        if "Formulation" in new_df.columns:
            new_df["Formulation"] = new_df["Formulation"].replace(r'^\s*$', np.nan, regex=True)
            # Forward fill the formulation!
            new_df["Formulation"] = new_df["Formulation"].ffill()
            
            cmc_vals = []
            pva_vals = []
            cleaned_forms = []
            from src.utils import normalize_factor_value
            
            for idx, row in new_df.iterrows():
                form_raw = row["Formulation"]
                form = normalize_factor_value("Formulation", form_raw)
                cleaned_forms.append(form)
                
                mapped = FORMULATION_MAP.get(form, {"CMC": np.nan, "PVA": np.nan})
                mapped_cmc = mapped["CMC"]
                mapped_pva = mapped["PVA"]
                
                cmc = row.get("CMC", np.nan)
                pva = row.get("PVA", np.nan)
                
                if pd.isna(cmc) or str(cmc).strip() == "":
                    cmc = mapped_cmc
                else:
                    cmc = normalize_factor_value("CMC", cmc)
                        
                if pd.isna(pva) or str(pva).strip() == "":
                    pva = mapped_pva
                else:
                    pva = normalize_factor_value("PVA", pva)
                        
                cmc_vals.append(cmc)
                pva_vals.append(pva)
                
            new_df["Formulation"] = cleaned_forms
            new_df["CMC"] = cmc_vals
            new_df["PVA"] = pva_vals

        if "Plasticizer" in new_df.columns:
            new_df["Plasticizer"] = new_df["Plasticizer"].apply(lambda x: normalize_factor_value("Plasticizer", x))

        new_df.attrs["sheet_match"] = sheet_match
        return new_df

    def clean_all(self):
        response_datasets = {}
        master_data = []
        from src.utils import normalize_factor_value
        
        for f in self.raw_csv_files:
            df = self.process_file(f)
            if df.empty:
                continue
                
            sheet_match = df.attrs.get("sheet_match")
            expected_responses = SHEET_RESPONSE_MAP.get(sheet_match, []) if sheet_match else EXPECTED_RESPONSES
            
            for resp in expected_responses:
                if resp in df.columns:
                    orig_n = len(df)
                    
                    if resp == "Formability":
                        df[resp] = df[resp].apply(lambda x: normalize_factor_value("Formability", x))
                    else:
                        df[resp] = df[resp].astype(str).str.replace(',', '.').replace(r'^\s*$', np.nan, regex=True).replace('nan', np.nan)
                        df[resp] = pd.to_numeric(df[resp], errors='coerce')
                    
                    base_cols = ["Formulation", "Replicate", "CMC", "PVA", "Plasticizer", "source_file", "source_sheet", "source_block", "source_row"]
                    for bc in base_cols:
                        if bc not in df.columns:
                            df[bc] = np.nan
                            
                    if "Replicate" in df.columns:
                        df["Replicate"] = df["Replicate"].apply(lambda x: normalize_factor_value("Replicate", x))
                        df["Replicate"] = pd.to_numeric(df["Replicate"], errors='coerce')
                            
                    keep_cols = base_cols + [resp]
                    resp_df = df[keep_cols].copy()
                    
                    resp_df = resp_df.dropna(subset=[resp])
                    
                    rem_n = orig_n - len(resp_df)
                    self._log_prep(os.path.basename(f), f"Drop missing {resp}", orig_n, rem_n, f"Removed because response {resp} is NaN", len(resp_df))
                    
                    if not resp_df.empty:
                        out_path = os.path.join(self.cleaned_dir, f"{resp}.csv")
                        resp_df.to_csv(out_path, index=False)
                        response_datasets[resp] = resp_df
                        
                        long_df = resp_df.copy()
                        long_df = long_df.rename(columns={resp: "Value"})
                        long_df.insert(0, "Response", resp)
                        long_df.insert(0, "Sheet", sheet_match if sheet_match else "Unknown")
                        master_data.append(long_df)

        if master_data:
            master_df = pd.concat(master_data, ignore_index=True)
            master_df.to_csv(os.path.join(self.output_base_dir, "cleaned_dataset.csv"), index=False)
            
        eligibility_map = {}
        if "Formability" in response_datasets:
            form_df = response_datasets["Formability"]
            for _, row in form_df.iterrows():
                form = row["Formulation"]
                plast = row["Plasticizer"]
                is_eligible = bool(row["Formability"])
                key = (form, plast)
                # If any replicate says it's eligible, we consider it eligible, or we can just map one since they should be consistent
                if key not in eligibility_map or is_eligible:
                    eligibility_map[key] = is_eligible
            
        return response_datasets, eligibility_map
