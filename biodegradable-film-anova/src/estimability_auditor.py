import pandas as pd
import numpy as np
import patsy
import os
from src.utils import get_output_dir, setup_logger

class ANOVAEstimabilityAuditor:
    def __init__(self, output_base_dir):
        self.output_dir = get_output_dir(output_base_dir, "anova")
        self.logger = setup_logger("estimability", os.path.join(output_base_dir, "conversion_log.txt"))
        
        self.design_audit_records = []
        self.model_estimability_records = []
        self.model_comparison_records = []
        
    def evaluate_model(self, data, formula_factors, response_name, model_name):
        try:
            model_matrix = patsy.dmatrix(
                formula_factors,
                data,
                return_type="dataframe"
            )
            
            rank = int(np.linalg.matrix_rank(model_matrix.to_numpy()))
            n_columns = int(model_matrix.shape[1])
            residual_df = len(data) - rank
            is_estimable = rank == n_columns
            
            # Find aliased columns if rank deficient
            aliased_cols = []
            if not is_estimable:
                # Basic method to find zero singular values
                U, S, Vt = np.linalg.svd(model_matrix.to_numpy(), full_matrices=False)
                tol = np.max(model_matrix.shape) * np.finfo(float).eps * np.max(S)
                null_space = Vt[S < tol]
                
                # Identify which columns contribute to the null space
                for i in range(null_space.shape[0]):
                    vector = null_space[i]
                    # Columns where the vector has non-zero components are aliased
                    aliased_indices = np.where(np.abs(vector) > 1e-10)[0]
                    col_names = [model_matrix.columns[idx] for idx in aliased_indices]
                    aliased_cols.append(" + ".join(col_names))
            
            self.model_comparison_records.append({
                "Response": response_name,
                "Model_Name": model_name,
                "Formula": formula_factors,
                "Cols": n_columns,
                "Rank": rank,
                "Residual_df": residual_df,
                "Estimable": is_estimable,
                "Aliased_Terms": " | ".join(aliased_cols) if aliased_cols else ""
            })
            
            return {
                "rank": rank,
                "cols": n_columns,
                "residual_df": residual_df,
                "estimable": is_estimable,
                "aliased_cols": aliased_cols,
                "formula": formula_factors
            }
        except Exception as e:
            self.logger.error(f"Failed to evaluate model '{model_name}' for {response_name}: {e}")
            self.model_comparison_records.append({
                "Response": response_name,
                "Model_Name": model_name,
                "Formula": formula_factors,
                "Cols": np.nan,
                "Rank": np.nan,
                "Residual_df": np.nan,
                "Estimable": False,
                "Aliased_Terms": f"Error: {e}"
            })
            return None

    def run_audit(self, df, response_name):
        factors = ["CMC", "PVA", "Plasticizer"]
        if not set(factors).issubset(df.columns) or response_name not in df.columns:
            return None
            
        data = df.dropna(subset=[response_name] + factors).copy()
        if data.empty:
            return None
            
        n_obs = len(data)
        treatment_cells = data.groupby(factors).size().reset_index()
        n_cells = len(treatment_cells)
        
        # Candidate 1: Full Factorial
        full_factorial = "C(CMC) * C(PVA) * C(Plasticizer)"
        full_res = self.evaluate_model(data, full_factorial, response_name, "Full Factorial")
        
        # Candidate 2: Main Effects
        main_effects = "C(CMC) + C(PVA) + C(Plasticizer)"
        self.evaluate_model(data, main_effects, response_name, "Main Effects")
        
        # Candidate 3: Two-Way Interactions
        two_way = "C(CMC) + C(PVA) + C(Plasticizer) + C(CMC):C(PVA) + C(CMC):C(Plasticizer) + C(PVA):C(Plasticizer)"
        self.evaluate_model(data, two_way, response_name, "Two-Way Interactions")
        
        # Candidate 4: Treatment Formulation
        if "Formulation" in data.columns:
            formulation_model = "C(Formulation) * C(Plasticizer)"
            self.evaluate_model(data, formulation_model, response_name, "Formulation Approach")
            
        if full_res:
            self.design_audit_records.append({
                "Response": response_name,
                "N": n_obs,
                "Cells": n_cells,
                "Cols": full_res["cols"],
                "Rank": full_res["rank"],
                "Rank_Deficient": not full_res["estimable"]
            })
            
            if not full_res["estimable"]:
                for alias in full_res["aliased_cols"]:
                    self.model_estimability_records.append({
                        "Response": response_name,
                        "Deficiency_Source": alias
                    })
                    
        return full_res

    def generate_recommendation_report(self):
        report = []
        report.append("RECOMMENDED STATISTICAL APPROACH")
        report.append("=================================\n")
        
        if not self.model_comparison_records:
            report.append("No models evaluated.")
            return "\n".join(report)
            
        df_comp = pd.DataFrame(self.model_comparison_records)
        df_audit = pd.DataFrame(self.design_audit_records)
        
        recommendations = {}
        
        for response in df_audit["Response"].unique():
            report.append(f"{response}:")
            audit_row = df_audit[df_audit["Response"] == response].iloc[0]
            
            report.append(f"  - Design: N={audit_row['N']}, Cells={audit_row['Cells']}")
            
            resp_comps = df_comp[df_comp["Response"] == response]
            full_fac = resp_comps[resp_comps["Model_Name"] == "Full Factorial"].iloc[0]
            
            if full_fac["Estimable"]:
                report.append("  - Full Factorial: ESTIMABLE")
                report.append("  - Recommendation: Use Full Factorial Model.")
                recommendations[response] = {"Model_Name": "Full Factorial", "Formula": full_fac["Formula"], "Rank": full_fac["Rank"], "Cols": full_fac["Cols"]}
            else:
                report.append("  - Full Factorial: NOT ESTIMABLE (Rank Deficient)")
                report.append("  - Sources of deficiency:")
                def_rows = [r for r in self.model_estimability_records if r["Response"] == response]
                for d in def_rows[:5]:
                    report.append(f"    * {d['Deficiency_Source']}")
                if len(def_rows) > 5:
                    report.append("    * (and more...)")
                
                # Check other models
                estimable_models = resp_comps[(resp_comps["Model_Name"] != "Full Factorial") & (resp_comps["Estimable"] == True)]
                if not estimable_models.empty:
                    # Recommend Formulation Approach if available and estimable, otherwise Main Effects
                    formulation = estimable_models[estimable_models["Model_Name"] == "Formulation Approach"]
                    main_eff = estimable_models[estimable_models["Model_Name"] == "Main Effects"]
                    
                    if not formulation.empty:
                        report.append(f"  - Recommendation: Use Formulation Approach ({formulation.iloc[0]['Formula']})")
                        report.append("    (This correctly models the nested nature of CMC/PVA combinations that actually form biofilms)")
                        recommendations[response] = {"Model_Name": "Formulation Approach", "Formula": formulation.iloc[0]['Formula'], "Rank": formulation.iloc[0]['Rank'], "Cols": formulation.iloc[0]['Cols']}
                    elif not main_eff.empty:
                        report.append(f"  - Recommendation: Use Main Effects ({main_eff.iloc[0]['Formula']})")
                        recommendations[response] = {"Model_Name": "Main Effects", "Formula": main_eff.iloc[0]['Formula'], "Rank": main_eff.iloc[0]['Rank'], "Cols": main_eff.iloc[0]['Cols']}
                    else:
                        report.append(f"  - Recommendation: Use {estimable_models.iloc[0]['Model_Name']}")
                        recommendations[response] = {"Model_Name": estimable_models.iloc[0]['Model_Name'], "Formula": estimable_models.iloc[0]['Formula'], "Rank": estimable_models.iloc[0]['Rank'], "Cols": estimable_models.iloc[0]['Cols']}
                else:
                    report.append("  - Recommendation: NO ESTIMABLE MODELS FOUND.")
                    recommendations[response] = None
            report.append("")
            
        report_path = os.path.join(self.output_dir, "statistical_recommendation.md")
        with open(report_path, "w") as f:
            f.write("\n".join(report))
            
        pd.DataFrame(self.design_audit_records).to_csv(os.path.join(self.output_dir, "design_audit.csv"), index=False)
        pd.DataFrame(self.model_comparison_records).to_csv(os.path.join(self.output_dir, "model_comparison.csv"), index=False)
        pd.DataFrame(self.model_estimability_records).to_csv(os.path.join(self.output_dir, "model_estimability.csv"), index=False)
        
        return report_path, recommendations
