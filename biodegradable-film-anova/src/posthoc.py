import pandas as pd
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import os
from src.utils import get_output_dir, setup_logger

class PostHocTester:
    def __init__(self, output_base_dir, alpha=0.05):
        self.output_dir = get_output_dir(output_base_dir, "posthoc")
        self.alpha = alpha
        self.logger = setup_logger("posthoc", os.path.join(output_base_dir, "conversion_log.txt"))
        
    def run_response(self, df, response_name, anova_results_path):
        if not anova_results_path or not os.path.exists(anova_results_path):
            return None
            
        anova_df = pd.read_csv(anova_results_path)
        main_effects = ["CMC", "PVA", "Plasticizer"]
        
        data = df.dropna(subset=[response_name] + main_effects)
        results = []
        
        active_factors = [f for f in main_effects if data[f].nunique() > 1]
        
        for effect in active_factors:
            effect_row = anova_df[anova_df["Source"] == effect]
            if not effect_row.empty:
                p_val = effect_row["p-value"].values[0]
                if pd.notna(p_val) and p_val < self.alpha:
                    try:
                        tukey = pairwise_tukeyhsd(endog=data[response_name], groups=data[effect], alpha=self.alpha)
                        tukey_df = pd.DataFrame(data=tukey._results_table.data[1:], columns=tukey._results_table.data[0])
                        
                        for _, row in tukey_df.iterrows():
                            results.append({
                                "Response": response_name,
                                "Factor": effect,
                                "Group 1": row["group1"],
                                "Group 2": row["group2"],
                                "Mean Difference": row["meandiff"],
                                "p-adjusted": row["p-adj"],
                                "Lower": row["lower"],
                                "Upper": row["upper"],
                                "Significant": row["reject"]
                            })
                    except Exception as e:
                        self.logger.error(f"Tukey HSD failed for {response_name} - {effect}: {e}")
                        
        if results:
            res_df = pd.DataFrame(results)
            out_path = os.path.join(self.output_dir, f"{response_name}_tukey.csv")
            res_df.to_csv(out_path, index=False)
            return out_path
        return None
