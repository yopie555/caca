import pandas as pd
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import os
from src.utils import get_output_dir, setup_logger

class InteractionAnalyzer:
    def __init__(self, output_base_dir, alpha=0.05):
        self.output_dir = get_output_dir(output_base_dir, "anova")
        self.alpha = alpha
        self.logger = setup_logger("interaction", os.path.join(output_base_dir, "conversion_log.txt"))
        
    def run_response(self, df, response_name, anova_results_path):
        if not anova_results_path or not os.path.exists(anova_results_path):
            return None
            
        anova_df = pd.read_csv(anova_results_path)
        interactions = ["CMC × PVA", "CMC × Plasticizer", "PVA × Plasticizer", "CMC × PVA × Plasticizer"]
        
        data = df.dropna(subset=[response_name, "CMC", "PVA", "Plasticizer"])
        results = []
        
        active_factors = [f for f in ["CMC", "PVA", "Plasticizer"] if data[f].nunique() > 1]
        
        for interaction in interactions:
            factors_involved = interaction.split(" × ")
            if not all(f in active_factors for f in factors_involved):
                continue
                
            eff_row = anova_df[anova_df["Source"] == interaction]
            if not eff_row.empty:
                p_val = eff_row["p-value"].values[0]
                if pd.notna(p_val) and p_val < self.alpha:
                    self.logger.info(f"Significant interaction {interaction} for {response_name}. Running simple effects.")
                    
                    factors_involved = interaction.split(" × ")
                    data_copy = data.copy()
                    data_copy['Combined'] = data_copy[factors_involved[0]].astype(str)
                    for f in factors_involved[1:]:
                        data_copy['Combined'] += "_" + data_copy[f].astype(str)
                        
                    try:
                        tukey = pairwise_tukeyhsd(endog=data_copy[response_name], groups=data_copy['Combined'], alpha=self.alpha)
                        tukey_df = pd.DataFrame(data=tukey._results_table.data[1:], columns=tukey._results_table.data[0])
                        
                        for _, row in tukey_df.iterrows():
                            results.append({
                                "Response": response_name,
                                "Interaction": interaction,
                                "Group 1": row["group1"],
                                "Group 2": row["group2"],
                                "Mean Difference": row["meandiff"],
                                "p-adjusted": row["p-adj"],
                                "Lower": row["lower"],
                                "Upper": row["upper"],
                                "Significant": row["reject"]
                            })
                    except Exception as e:
                        self.logger.error(f"Simple effects failed for {response_name} - {interaction}: {e}")
                        
        if results:
            res_df = pd.DataFrame(results)
            out_path = os.path.join(self.output_dir, f"{response_name}_simple_effects.csv")
            res_df.to_csv(out_path, index=False)
            return out_path
        return None
