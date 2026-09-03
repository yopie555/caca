import os
import pandas as pd
from datetime import datetime
import itertools
from src.utils import get_output_dir, EXPECTED_RESPONSES

class MasterValidator:
    def __init__(self, output_base_dir):
        self.output_base_dir = output_base_dir
        self.val_dir = get_output_dir(output_base_dir, "validation")
        self.report_path = os.path.join(self.val_dir, "MASTER_VALIDATION_REPORT.html")
        self.expected_combinations = list(itertools.product(
            [1, 2, 3],
            [0, 1, 2, 3],
            ["Gliserol", "Sorbitol"],
            [1, 2, 3]
        ))
        
    def audit_factorial_design(self, df, resp, eligibility_map=None):
        import itertools
        from src.utils import MATRIX_LEVEL, DOWNSTREAM_BIOFILM
        
        all_expected_cells = list(itertools.product([1, 2, 3], [0, 1, 2, 3], ["Gliserol", "Sorbitol"]))
        
        expected_cells = all_expected_cells
        if resp in DOWNSTREAM_BIOFILM and eligibility_map:
            expected_cells = []
            for cell in all_expected_cells:
                cmc, pva, plast = cell
                from src.utils import FORMULATION_MAP
                # Find formulation
                form_code = None
                for k, v in FORMULATION_MAP.items():
                    if v["CMC"] == cmc and v["PVA"] == pva:
                        form_code = k
                        break
                if form_code:
                    key = (form_code, plast)
                    # If it's true, it's eligible
                    if eligibility_map.get(key, False):
                        expected_cells.append(cell)
        
        
        audit_results = {
            "expected_cells": len(expected_cells),
            "observed_cells": 0,
            "missing_cells": [],
            "extra_cells": [],
            "duplicate_cells": [],
            "invalid_replicates": [],
            "replicate_counts": {},
            "complete": False,
            "details": []
        }
        
        missing_cells_count = 0
        missing_reps_count = 0
        
        for cell in expected_cells:
            c_cmc, c_pva, c_plast = cell
            
            cell_df = df[(df["CMC"] == c_cmc) & (df["PVA"] == c_pva) & (df["Plasticizer"] == c_plast)]
            
            if cell_df.empty:
                missing_cells_count += 1
                audit_results["missing_cells"].append(cell)
                audit_results["details"].append({
                    "CMC": c_cmc, "PVA": c_pva, "Plasticizer": c_plast,
                    "Replicates": "[]", "N": 0, "Status": "MISSING CELL"
                })
            else:
                audit_results["observed_cells"] += 1
                reps = sorted(cell_df["Replicate"].tolist())
                audit_results["replicate_counts"][cell] = reps
                
                status_str = "OK"
                
                if reps != [1, 2, 3]:
                    expected = [1, 2, 3]
                    missing_reps = [r for r in expected if r not in reps]
                    missing_reps_count += len(missing_reps)
                    
                    if len(reps) > len(set(reps)):
                        audit_results["duplicate_cells"].append(cell)
                        status_str = "DUPLICATE"
                    elif len(reps) > 3 or any(r not in expected for r in reps):
                        audit_results["invalid_replicates"].append(cell)
                        status_str = "INVALID REPLICATE"
                    else:
                        status_str = f"MISSING R{','.join(map(str, missing_reps))}"
                        
                audit_results["details"].append({
                    "CMC": c_cmc, "PVA": c_pva, "Plasticizer": c_plast,
                    "Replicates": str(reps), "N": len(reps), "Status": status_str
                })
                
        # Check for unexpected cells (present but not expected)
        unexpected_cells = 0
        all_present = df.groupby(["CMC", "PVA", "Plasticizer"]).size().reset_index()
        for _, row in all_present.iterrows():
            c_cmc, c_pva, c_plast = row["CMC"], row["PVA"], row["Plasticizer"]
            if (c_cmc, c_pva, c_plast) not in expected_cells:
                unexpected_cells += 1
                audit_results["extra_cells"].append((c_cmc, c_pva, c_plast))
                audit_results["details"].append({
                    "CMC": c_cmc, "PVA": c_pva, "Plasticizer": c_plast,
                    "Replicates": "Unexpected", "N": int(row[0]), "Status": "UNEXPECTED (INELIGIBLE)"
                })

                
        # Duplicate detection (exact row match for same factors and replicate)
        dup_df = df[df.duplicated(subset=["CMC", "PVA", "Plasticizer", "Replicate"], keep=False)]
        num_dups = len(dup_df)
        
        expected_n = len(expected_cells) * 3
        is_complete = missing_cells_count == 0 and missing_reps_count == 0 and num_dups == 0 and unexpected_cells == 0 and len(df) == expected_n
        audit_results["complete"] = is_complete
        audit_results["num_dups"] = num_dups
        audit_results["missing_cells_count"] = missing_cells_count
        audit_results["missing_reps_count"] = missing_reps_count
        audit_results["unexpected_cells_count"] = unexpected_cells
        audit_results["expected_n"] = expected_n
        
        return audit_results
        
    def generate_report(self, response_datasets, eligibility_map=None):
        html_content = [
            "<!DOCTYPE html>",
            "<html lang='id'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "<title>MASTER VALIDATION REPORT</title>",
            "<style>",
            "body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }",
            "h1, h2, h3, h4 { color: #2c3e50; }",
            "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; font-size: 14px; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            ".alert { padding: 15px; margin-bottom: 20px; border: 1px solid transparent; border-radius: 4px; }",
            ".alert-success { color: #3c763d; background-color: #dff0d8; border-color: #d6e9c6; }",
            ".alert-warning { color: #8a6d3b; background-color: #fcf8e3; border-color: #faebcc; }",
            ".alert-danger { color: #a94442; background-color: #f2dede; border-color: #ebccd1; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>MASTER VALIDATION REPORT</h1>",
            f"<p>Laporan dihasilkan pada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        ]
        
        # Expected Design
        html_content.extend([
            "<h2>1. Planned Design</h2>",
            "<ul>",
            "<li>CMC levels: 3 (1, 2, 3)</li>",
            "<li>PVA levels: 4 (0, 1, 2, 3)</li>",
            "<li>Plasticizer levels: 2 (Gliserol, Sorbitol)</li>",
            "<li>Replicate counts: 3 (1, 2, 3)</li>",
            "<li>Planned N per response: 72</li>",
            "</ul>"
        ])
        
        response_safety = {}
        design_summaries = []
        
        for resp, df in response_datasets.items():
            html_content.append(f"<h3>Respons: {resp}</h3>")
            
            if df.empty:
                html_content.append("<div class='alert alert-danger'>Data kosong atau tidak dapat di-parse dengan benar.</div>")
                design_summaries.append({
                    "Response": resp,
                    "Planned_CMC_Levels": 3, "Observed_CMC_Levels": 0,
                    "Planned_PVA_Levels": 4, "Observed_PVA_Levels": 0,
                    "Planned_Plasticizer_Levels": 2, "Observed_Plasticizer_Levels": 0,
                    "Planned_Replicate_Levels": 3, "Observed_Replicate_Levels": 0,
                    "Planned_N": 72, "Observed_N": 0,
                    "Missing_Cells": 0, "Missing_Replicates": 0, "Duplicates": 0,
                    "Unexpected_Cells": 0,
                    "Design_Status": "NOT_AVAILABLE", "Model_Status": "BLOCKED", "ANOVA_Status": "BLOCKED"
                })
                
                response_safety[resp] = {
                    "data_status": "EMPTY",
                    "design_status": "NOT_AVAILABLE",
                    "model_status": "BLOCKED",
                    "anova_status": "BLOCKED",
                    "safe": False,
                    "audit": None
                }
                continue
                
            cmc_levels = sorted(df["CMC"].dropna().unique().tolist())
            pva_levels = sorted(df["PVA"].dropna().unique().tolist())
            plast_levels = sorted(df["Plasticizer"].dropna().unique().tolist())
            rep_levels = sorted(df["Replicate"].dropna().unique().tolist())
            obs_n = len(df)
            
            glis_count = len(df[df["Plasticizer"] == "Gliserol"])
            sorb_count = len(df[df["Plasticizer"] == "Sorbitol"])
            
            html_content.extend([
                "<ul>",
                f"<li>Replicate levels: {len(rep_levels)}</li>",
                f"<li>Sorbitol observations: {sorb_count}</li>",
                f"<li>Gliserol observations: {glis_count}</li>",
                f"<li>Total observations: {obs_n}</li>",
                "</ul>"
            ])
            
            audit = self.audit_factorial_design(df, resp, eligibility_map)
            
            missing_combos_report = [d for d in audit["details"] if d["Status"] != "OK"]
            
            if missing_combos_report:
                missing_df = pd.DataFrame(missing_combos_report)
                missing_df.to_csv(os.path.join(self.val_dir, f"{resp}_missing_combinations.csv"), index=False)
                
                html_content.append(f"<div class='alert alert-warning'><strong>INCOMPLETE/INVALID DESIGN:</strong> Ditemukan {audit['missing_cells_count']} Missing Cells, {audit.get('unexpected_cells_count', 0)} Unexpected Cells, atau ketidaksesuaian Replicate. Detail di <code>{resp}_missing_combinations.csv</code>.</div>")
                
                missing_pva_0 = all(c != 0 for c in pva_levels)
                if missing_pva_0:
                    html_content.append("<div class='alert alert-danger'>PVA level = 0 seluruhnya tidak ditemukan dalam data asli untuk respons ini.</div>")
            else:
                html_content.append("<div class='alert alert-success'>Desain lengkap (COMPLETE) dan seimbang (Balanced Design) untuk respons ini.</div>")
                
            if audit["num_dups"] > 0:
                html_content.append(f"<div class='alert alert-danger'><strong>CRITICAL ISSUE:</strong> Terdapat baris duplikat untuk observasi yang sama. ANOVA BLOCKED.</div>")
                
            is_complete = audit["complete"]
            design_status = "COMPLETE" if is_complete else "INCOMPLETE"
            if audit["num_dups"] > 0:
                design_status = "DUPLICATES FOUND"
                
            design_summaries.append({
                "Response": resp,
                "Planned_CMC_Levels": 3, "Observed_CMC_Levels": len(cmc_levels),
                "Planned_PVA_Levels": 4, "Observed_PVA_Levels": len(pva_levels),
                "Planned_Plasticizer_Levels": 2, "Observed_Plasticizer_Levels": len(plast_levels),
                "Planned_Replicate_Levels": 3, "Observed_Replicate_Levels": len(rep_levels),
                "Planned_N": audit["expected_n"], "Observed_N": obs_n,
                "Missing_Cells": audit["missing_cells_count"], "Missing_Replicates": audit["missing_reps_count"], "Duplicates": audit["num_dups"],
                "Unexpected_Cells": audit.get("unexpected_cells_count", 0),
                "Design_Status": design_status, "Model_Status": "TBD", "ANOVA_Status": "TBD"
            })
            
            response_safety[resp] = {
                "data_status": "VALID",
                "design_status": design_status,
                "model_status": "TBD",
                "anova_status": "TBD",
                "safe": design_status == "COMPLETE"
            }
                
        # Consolidate Summaries
        if design_summaries:
            pd.DataFrame(design_summaries).to_csv(os.path.join(self.val_dir, "design_validation_summary.csv"), index=False)

        # Consistency Check
        html_content.append("<h2>3. Consistency Check (FTL vs Kelarutan)</h2>")
        cons_file = os.path.join(self.val_dir, "ftl_kelarutan_consistency.csv")
        if os.path.exists(cons_file):
            df_cons = pd.read_csv(cons_file)
            inc_df = df_cons[df_cons["Status"] == "Inconsistent"]
            if not inc_df.empty:
                html_content.append("<div class='alert alert-warning'><strong>Inconsistency detected:</strong> Perhitungan matematis Kelarutan = 100 - FTL tidak konsisten. Original data dipertahankan.</div>")
            else:
                html_content.append("<div class='alert alert-success'>Data FTL dan Kelarutan konsisten secara matematis.</div>")
        else:
            html_content.append("<p>Tidak diuji (FTL atau Kelarutan tidak tersedia).</p>")
            
        # Global Safety Check
        html_content.append("<h2>4. Final Pipeline Status</h2>")
        global_safe = True
        for resp, safety in response_safety.items():
            if not safety["safe"]:
                global_safe = False
                break
                
        if not global_safe:
            status_html = "<div class='alert alert-danger'><strong>NOT SAFE</strong>: Terdapat response dengan status INCOMPLETE atau DUPLICATES FOUND. Hal ini membuat keseluruhan pipeline global tidak aman.</div>"
        else:
            status_html = "<div class='alert alert-success'><strong>SAFE</strong>: Seluruh response memiliki status COMPLETE dan tidak ada duplikat.</div>"
            
        html_content.append(status_html)
        html_content.append("</body></html>")
        
        with open(self.report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(html_content))
            
        return global_safe, response_safety
