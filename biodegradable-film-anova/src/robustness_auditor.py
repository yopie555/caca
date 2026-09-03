import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols
import os
from src.utils import get_output_dir, setup_logger

class RobustnessAuditor:
    def __init__(self, output_base_dir):
        self.output_dir = get_output_dir(output_base_dir, "anova")
        self.logger = setup_logger("robustness", os.path.join(output_base_dir, "conversion_log.txt"))
        self.effect_sizes = []
        self.confidence_intervals = []
        self.sensitivity_results = []
        self.final_recommendations = []
        self.markdown_report_path = os.path.join(self.output_dir, "statistical_robustness.md")

    def calc_partial_eta_squared(self, aov_table):
        # partial eta^2 = SS_effect / (SS_effect + SS_error)
        res = {}
        if 'sum_sq' not in aov_table.columns:
            return res
        
        ss_error = aov_table.loc['Residual', 'sum_sq'] if 'Residual' in aov_table.index else None
        if ss_error is None:
            return res
            
        for idx, row in aov_table.iterrows():
            if idx != 'Residual' and pd.notna(row.get('sum_sq')):
                ss_effect = row['sum_sq']
                if ss_effect + ss_error > 0:
                    pes = ss_effect / (ss_effect + ss_error)
                    res[idx] = pes
        return res

    def evaluate_sensitivity(self, df, response_name, is_conditional):
        if not is_conditional:
            return
            
        data = df.dropna(subset=[response_name, "CMC", "PVA", "Plasticizer"]).copy()
        if data.empty:
            return
            
        data["Formulation"] = data["CMC"].astype(str) + "_" + data["PVA"].astype(str)
        
        # Approach A: Main Effects
        try:
            model_a = ols(f"{response_name} ~ C(CMC) + C(PVA) + C(Plasticizer)", data=data).fit()
            aov_a = sm.stats.anova_lm(model_a, typ=2)
            pes_a = self.calc_partial_eta_squared(aov_a)
            
            self.sensitivity_results.append({
                "Response": response_name,
                "Model_Type": "A (Main Effects)",
                "Formula": "C(CMC) + C(PVA) + C(Plasticizer)",
                "CMC_p": aov_a.loc["C(CMC)", "PR(>F)"] if "C(CMC)" in aov_a.index else pd.NA,
                "PVA_p": aov_a.loc["C(PVA)", "PR(>F)"] if "C(PVA)" in aov_a.index else pd.NA,
                "Plas_p": aov_a.loc["C(Plasticizer)", "PR(>F)"] if "C(Plasticizer)" in aov_a.index else pd.NA,
                "CMC_pes": pes_a.get("C(CMC)", pd.NA),
                "PVA_pes": pes_a.get("C(PVA)", pd.NA),
                "Plas_pes": pes_a.get("C(Plasticizer)", pd.NA),
                "Status": "Success"
            })
        except Exception as e:
            self.sensitivity_results.append({"Response": response_name, "Model_Type": "A (Main Effects)", "Status": f"Failed: {e}"})

        # Approach B: Formulation Model
        try:
            model_b = ols(f"{response_name} ~ C(Formulation) + C(Plasticizer)", data=data).fit()
            aov_b = sm.stats.anova_lm(model_b, typ=2)
            pes_b = self.calc_partial_eta_squared(aov_b)
            
            self.sensitivity_results.append({
                "Response": response_name,
                "Model_Type": "B (Formulation + Plasticizer)",
                "Formula": "C(Formulation) + C(Plasticizer)",
                "Formulation_p": aov_b.loc["C(Formulation)", "PR(>F)"] if "C(Formulation)" in aov_b.index else pd.NA,
                "Plas_p": aov_b.loc["C(Plasticizer)", "PR(>F)"] if "C(Plasticizer)" in aov_b.index else pd.NA,
                "Formulation_pes": pes_b.get("C(Formulation)", pd.NA),
                "Plas_pes": pes_b.get("C(Plasticizer)", pd.NA),
                "Status": "Success"
            })
        except Exception as e:
            self.sensitivity_results.append({"Response": response_name, "Model_Type": "B (Formulation + Plasticizer)", "Status": f"Failed: {e}"})

        # Approach C: Stratified by Plasticizer
        for plas in data["Plasticizer"].unique():
            sub_data = data[data["Plasticizer"] == plas].copy()
            if len(sub_data) > 0 and sub_data["CMC"].nunique() > 1 and sub_data["PVA"].nunique() > 1:
                try:
                    model_c = ols(f"{response_name} ~ C(CMC) + C(PVA)", data=sub_data).fit()
                    aov_c = sm.stats.anova_lm(model_c, typ=2)
                    pes_c = self.calc_partial_eta_squared(aov_c)
                    
                    self.sensitivity_results.append({
                        "Response": response_name,
                        "Model_Type": f"C (Stratified: {plas})",
                        "Formula": "C(CMC) + C(PVA)",
                        "CMC_p": aov_c.loc["C(CMC)", "PR(>F)"] if "C(CMC)" in aov_c.index else pd.NA,
                        "PVA_p": aov_c.loc["C(PVA)", "PR(>F)"] if "C(PVA)" in aov_c.index else pd.NA,
                        "CMC_pes": pes_c.get("C(CMC)", pd.NA),
                        "PVA_pes": pes_c.get("C(PVA)", pd.NA),
                        "Status": "Success"
                    })
                except Exception as e:
                    self.sensitivity_results.append({"Response": response_name, "Model_Type": f"C (Stratified: {plas})", "Status": f"Failed: {e}"})

    def process_response(self, df, response_name, formula, is_conditional=False):
        data = df.dropna(subset=[response_name, "CMC", "PVA", "Plasticizer"]).copy()
        if data.empty:
            return
            
        try:
            model = ols(formula, data=data).fit()
            aov = sm.stats.anova_lm(model, typ=2)
            pes = self.calc_partial_eta_squared(aov)
            
            for term, val in pes.items():
                self.effect_sizes.append({
                    "Response": response_name,
                    "Term": term.replace("C(", "").replace(")", ""),
                    "Partial_Eta_Squared": val
                })
                
            conf = model.conf_int()
            for idx, row in conf.iterrows():
                if idx != "Intercept":
                    self.confidence_intervals.append({
                        "Response": response_name,
                        "Coefficient": idx,
                        "Estimate": model.params[idx],
                        "CI_Lower": row[0],
                        "CI_Upper": row[1],
                        "p_value": model.pvalues[idx]
                    })
                    
            if is_conditional:
                self.evaluate_sensitivity(df, response_name, True)
                
            # Final model recommendation logic
            final_rec = ""
            reason = ""
            limitations = ""
            
            if not is_conditional:
                final_rec = "FULL FACTORIAL"
                reason = "Design is complete (N=72, 24 cells). Valid for full main effects and interactions."
                limitations = "None for experimental domain."
            else:
                final_rec = "MAIN EFFECTS (Conditional)"
                reason = "Full factorial is rank deficient due to structural missingness (biofilm formability failure for PVA=0 and Formulation F with Sorbitol)."
                limitations = "Interpretations are strictly conditional. We cannot claim independent causal effects of CMC/PVA universally; findings apply ONLY to formulations capable of forming biofilms."
                
            self.final_recommendations.append({
                "Response": response_name,
                "Final_Model": final_rec,
                "Reason": reason,
                "Limitations": limitations
            })
                
        except Exception as e:
            self.logger.error(f"Robustness audit failed for {response_name}: {e}")
            
    def finalize_reports(self):
        if self.effect_sizes:
            pd.DataFrame(self.effect_sizes).to_csv(os.path.join(self.output_dir, "effect_sizes.csv"), index=False)
        if self.confidence_intervals:
            pd.DataFrame(self.confidence_intervals).to_csv(os.path.join(self.output_dir, "confidence_intervals.csv"), index=False)
        if self.sensitivity_results:
            pd.DataFrame(self.sensitivity_results).to_csv(os.path.join(self.output_dir, "sensitivity_analysis.csv"), index=False)
        if self.final_recommendations:
            pd.DataFrame(self.final_recommendations).to_csv(os.path.join(self.output_dir, "final_model_recommendation.csv"), index=False)
            
        with open(self.markdown_report_path, "w") as f:
            f.write("# STATISTICAL ROBUSTNESS AUDIT\n\n")
            f.write("## 1. Experimental Design Overview\n")
            f.write("The complete theoretical design specifies 72 observations (3 CMC × 4 PVA × 2 Plasticizer × 3 Replicates). ")
            f.write("However, only 'matrix-level' variables (FTL, Kelarutan Matriks) were tested on all 72 combinations. ")
            f.write("Downstream mechanical and physical properties were only evaluated on formulations that successfully formed a biofilm, ")
            f.write("resulting in a structurally reduced (conditional) design of N=51.\n\n")
            
            f.write("## 2. Confounding Discussion\n")
            f.write("Because treatment eligibility (N=51) is deterministic (e.g., PVA=0 completely fails formability), ")
            f.write("factors are confounded with formulation viability. Specifically, Main Effects evaluated downstream ")
            f.write("must be interpreted as *conditional associations within viable formulations*, NOT universal independent causal effects. ")
            f.write("Variations in CMC cannot be fully isolated from PVA since only certain CMC/PVA pairings survive the selection step.\n\n")
            
            f.write("## 3. Final Model Recommendations\n\n")
            for rec in self.final_recommendations:
                f.write(f"### {rec['Response']}\n")
                f.write(f"- **Final model:** {rec['Final_Model']}\n")
                f.write(f"- **Reason:** {rec['Reason']}\n")
                f.write(f"- **Limitations:** {rec['Limitations']}\n\n")
                
            f.write("## 4. Overall Methodological Conclusion\n")
            f.write("The current ANOVA pipeline is statistically valid under a **Conditional Inferential Framework**. ")
            f.write("By falling back to Main Effects for downstream variables, we avoid attempting to estimate unidentifiable interactions (Rank Deficiency). ")
            f.write("However, researchers MUST NOT claim universal independent causal effects of CMC/PVA across all configurations. ")
            f.write("The analysis is structurally confounded with formulation viability. ")
            f.write("All conclusions must be strictly prefaced with: ")
            f.write("*'For formulations that successfully formed a biofilm...'*.\n")

        summary_path = os.path.join(self.output_dir, "robustness_summary.txt")
        with open(summary_path, "w") as f:
            f.write("STATISTICAL ROBUSTNESS AUDIT\n")
            f.write("============================\n\n")
            
            for rec in self.final_recommendations:
                f.write(f"{rec['Response']}\n")
                f.write(f"Final model: {rec['Final_Model']}\n")
                f.write(f"Reason: {rec['Reason']}\n")
                f.write(f"Limitations: {rec['Limitations']}\n\n")
                
            f.write("OVERALL METHODOLOGICAL CONCLUSION\n")
            f.write("=================================\n")
            f.write("The current ANOVA pipeline is statistically valid under a **Conditional Inferential Framework**. ")
            f.write("By falling back to Main Effects for downstream variables, we avoid attempting to estimate unidentifiable interactions (Rank Deficiency). ")
            f.write("However, researchers MUST NOT claim universal independent causal effects of CMC/PVA across all configurations. ")
            f.write("The analysis is structurally confounded with formulation viability. ")
            f.write("All conclusions must be strictly prefaced with: ")
            f.write("*'For formulations that successfully formed a biofilm...'*.\n")

