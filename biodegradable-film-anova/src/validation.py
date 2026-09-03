import pandas as pd
import numpy as np
import os
import csv
from src.utils import setup_logger

class Validator:
    def __init__(self, output_base_dir):
        self.output_base_dir = output_base_dir
        self.val_dir = os.path.join(output_base_dir, "validation")
        self.logger = setup_logger("validator", os.path.join(output_base_dir, "validation_log.txt"))
        
        # Initialize duplicates.csv
        self.dup_path = os.path.join(self.val_dir, "duplicate_rows.csv")
        with open(self.dup_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Sheet", "Block", "CMC", "PVA", "Plasticizer", "Replicate", "Response", "Duplicate_Type", "Source_Row"])

    def _log_duplicate(self, row, response_name):
        with open(self.dup_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                row.get("source_sheet", "Unknown"),
                row.get("source_block", "Unknown"),
                row.get("CMC", ""),
                row.get("PVA", ""),
                row.get("Plasticizer", ""),
                row.get("Replicate", ""),
                response_name,
                "Exact Identifier",
                row.get("source_row", "")
            ])

    def validate_dataset(self, df, response_name):
        self.logger.info(f"Validating dataset for response: {response_name}")
        
        total_obs = len(df)
        self.logger.info(f"{response_name} total observations: {total_obs}")
        
        cmc_levels = df["CMC"].nunique()
        pva_levels = df["PVA"].nunique()
        plasticizers = df["Plasticizer"].unique()
        rep_levels = df["Replicate"].nunique()
        
        for plast in plasticizers:
            plast_obs = len(df[df["Plasticizer"] == plast])
            self.logger.info(f"{response_name} ({plast}) observations: {plast_obs}")
            
        print(f"{response_name}")
        print(f"  CMC levels       : {cmc_levels}")
        print(f"  PVA levels       : {pva_levels}")
        print(f"  Plasticizer      : {len(plasticizers)}")
        print(f"  Replicates       : {rep_levels} (expected)")
        print(f"  Observations     : {total_obs}")
        
        if total_obs == 72 and cmc_levels == 3 and pva_levels == 4 and len(plasticizers) == 2 and rep_levels == 3:
            print(f"  Status           : ✓ Complete factorial design\n")
        else:
            self.logger.warning(f"Response {response_name} has {total_obs} valid observations. Expected complete factorial design = 72. Missing cells/replicates must be investigated.")
            print(f"  Status           : ⚠ Incomplete design\n")
            
        # Check duplicates
        dup_mask = df.duplicated(subset=["CMC", "PVA", "Plasticizer", "Replicate"], keep=False)
        if dup_mask.any():
            self.logger.warning(f"Duplicate observations found in {response_name}.")
            dup_df = df[dup_mask]
            for _, row in dup_df.iterrows():
                self._log_duplicate(row, response_name)

    def run_consistency_check(self, ftl_df, kelarutan_df):
        self.logger.info("Running FTL-Kelarutan consistency check...")
        
        if ftl_df is None or kelarutan_df is None or ftl_df.empty or kelarutan_df.empty:
            return
            
        ftl_base = ftl_df.set_index(["CMC", "PVA", "Plasticizer", "Replicate"])["FTL"]
        kel_base = kelarutan_df.set_index(["CMC", "PVA", "Plasticizer", "Replicate"])["Kelarutan"]
        
        merged = pd.concat([ftl_base, kel_base], axis=1, join="inner").reset_index()
        if merged.empty:
            return
            
        merged["Calculated_Kelarutan"] = 100 - merged["FTL"]
        merged["Difference"] = np.abs(merged["Calculated_Kelarutan"] - merged["Kelarutan"])
        
        def assign_status(diff):
            if pd.isna(diff): return "Unknown"
            return "Consistent" if diff <= 0.001 else "Inconsistent"
            
        merged["Status"] = merged["Difference"].apply(assign_status)
        merged = merged.rename(columns={"Kelarutan": "Recorded_Kelarutan"})
        
        out_path = os.path.join(self.val_dir, "ftl_kelarutan_consistency.csv")
        merged.to_csv(out_path, index=False)
        
        inconsistencies = len(merged[merged["Status"] == "Inconsistent"])
        if inconsistencies > 0:
            self.logger.warning(f"Found {inconsistencies} inconsistent FTL vs Kelarutan records. See {out_path}")
