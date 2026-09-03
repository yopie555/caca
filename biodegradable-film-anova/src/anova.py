import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols
import os
from src.utils import get_output_dir, setup_logger

class FactorialANOVA:
    def __init__(self, output_base_dir, alpha=0.05, auditor=None):
        self.output_dir = get_output_dir(output_base_dir, "anova")
        self.alpha = alpha
        self.logger = setup_logger("anova", os.path.join(output_base_dir, "conversion_log.txt"))
        self.auditor = auditor
        
    def run_response(self, df, response_name):
        factors = ["CMC", "PVA", "Plasticizer"]
        if not set(factors).issubset(df.columns) or response_name not in df.columns:
            return {"status": "BLOCKED", "reason": "Missing columns", "path": None}
            
        data = df.dropna(subset=[response_name] + factors).copy()
        if data.empty:
            return {"status": "BLOCKED", "reason": "Empty dataset after dropna", "path": None}
            
        # Validasi kolom faktor (Harus > 1 level untuk tiap faktor di Full Factorial)
        for f in factors:
            if data[f].nunique() <= 1:
                return {"status": "BLOCKED", "reason": f"Factor {f} has only 1 level", "path": None}
            
        # Check balance
        counts = data.groupby(factors).size()
        is_balanced = len(set(counts)) == 1
        typ = 2 if is_balanced else 3
        
        formula_factors = " * ".join([f"C({f})" for f in factors])
        formula = f"{response_name} ~ {formula_factors}"
        
        results = []
        try:
            if not self.auditor:
                from src.estimability_auditor import ANOVAEstimabilityAuditor
                self.auditor = ANOVAEstimabilityAuditor(os.path.dirname(self.output_dir))
            
            audit_result = self.auditor.run_audit(data, response_name)
            if not audit_result:
                return {"status": "BLOCKED", "reason": "Failed to run audit", "path": None}
                
            report_path, recommendations = self.auditor.generate_recommendation_report()
            
            rec = recommendations.get(response_name)
            if not rec:
                self.logger.warning(f"MODEL RANK DEFICIENT for {response_name} and no estimable models found. ANOVA BLOCKED.")
                return {"status": "BLOCKED", "reason": "No estimable models", "rank": audit_result["rank"], "cols": audit_result["cols"], "path": None}
                
            formula = f"{response_name} ~ {rec['Formula']}"
            is_full = rec["Model_Name"] == "Full Factorial"
            rank = rec["Rank"]
            n_columns = rec["Cols"]
            
            if not is_full:
                self.logger.info(f"Using alternative model {rec['Model_Name']} for {response_name} due to rank deficiency.")

                
            model = ols(formula, data=data).fit()
            aov_table = sm.stats.anova_lm(model, typ=typ)
            
            for idx, row in aov_table.iterrows():
                source = str(idx).replace("C(CMC)", "CMC").replace("C(PVA)", "PVA").replace("C(Plasticizer)", "Plasticizer").replace(":", " × ")
                p_val = row.get("PR(>F)", pd.NA)
                
                decision = ""
                if pd.notna(p_val):
                    if p_val < self.alpha:
                        decision = "Tolak H₀ (Signifikan)"
                    else:
                        decision = "Gagal menolak H₀ (Tidak Signifikan)"
                        
                results.append({
                    "Response": response_name,
                    "Source": source,
                    "df": row.get("df"),
                    "Sum Sq": row.get("sum_sq"),
                    "Mean Sq": row.get("mean_sq", pd.NA) if "mean_sq" in row else (row.get("sum_sq")/row.get("df") if row.get("df") else pd.NA),
                    "F": row.get("F", pd.NA),
                    "p-value": p_val,
                    "Decision": decision,
                    "Type": typ
                })
        except Exception as e:
            self.logger.error(f"ANOVA failed for {response_name}: {e}")
            return {"status": "BLOCKED", "reason": f"Exception: {str(e)}", "path": None}
            
        if results:
            res_df = pd.DataFrame(results)
            out_path = os.path.join(self.output_dir, f"{response_name}_anova.csv")
            res_df.to_csv(out_path, index=False)
            return {"status": "COMPLETED", "path": out_path, "reason": "Valid", "rank": rank, "cols": n_columns, "formula": formula}
            
        return {"status": "BLOCKED", "reason": "No results", "path": None}
