import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
import os
import matplotlib.pyplot as plt
from src.utils import get_output_dir, setup_logger

class AssumptionTester:
    def __init__(self, output_base_dir):
        self.output_dir = get_output_dir(output_base_dir, "validation")
        self.plot_dir_qq = get_output_dir(output_base_dir, "plots/qq")
        self.plot_dir_res = get_output_dir(output_base_dir, "plots/residuals")
        self.outlier_dir = get_output_dir(output_base_dir, "anova/outliers")
        self.logger = setup_logger("assumptions", os.path.join(output_base_dir, "conversion_log.txt"))
        
    def run_response(self, df, response_name, formula=None):
        factors = ["CMC", "PVA", "Plasticizer"]
        if not set(factors).issubset(df.columns) or response_name not in df.columns:
            return None
            
        data = df.dropna(subset=[response_name] + factors).copy()
        if data.empty:
            return None
            
        if not formula:
            formula = f"{response_name} ~ C(CMC) * C(PVA) * C(Plasticizer)"
            
        results = []
        
        # Fit model
        try:
            model = ols(formula, data=data).fit()
        except Exception as e:
            self.logger.error(f"Failed to fit model for assumptions test on {response_name}: {e}")
            return None
            
        # Normality on residuals
        try:
            stat_sw, p_sw = stats.shapiro(model.resid)
            decision_sw = "Violated" if p_sw < 0.05 else "OK"
            if decision_sw == "Violated":
                self.logger.warning(f"Residual normality assumption for {response_name} may be violated.")
                
            # Q-Q Plot
            fig, ax = plt.subplots(figsize=(6, 6))
            sm.qqplot(model.resid, line='s', ax=ax)
            ax.set_title(f"Q-Q Plot for {response_name}")
            plt.tight_layout()
            fig.savefig(os.path.join(self.plot_dir_qq, f"{response_name}_qq.png"))
            plt.close(fig)
            
            # Residual vs Fitted Plot
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.scatter(model.fittedvalues, model.resid, alpha=0.6)
            ax.axhline(0, color='r', linestyle='--')
            ax.set_xlabel("Fitted Values")
            ax.set_ylabel("Residuals")
            ax.set_title(f"Residuals vs Fitted for {response_name}")
            plt.tight_layout()
            fig.savefig(os.path.join(self.plot_dir_res, f"{response_name}_residuals.png"))
            plt.close(fig)
            
        except Exception as e:
            stat_sw, p_sw, decision_sw = None, None, "Error"
            self.logger.error(f"Shapiro-Wilk error for {response_name}: {e}")
            
        # Homogeneity: Levene's test (Brown-Forsythe)
        try:
            groups = [group[response_name].values for name, group in data.groupby(factors)]
            if len(groups) > 1:
                stat_lev, p_lev = stats.levene(*groups, center='median')
                decision_lev = "Violated" if p_lev < 0.05 else "OK"
                if decision_lev == "Violated":
                    self.logger.warning(f"Homogeneity of variance assumption for {response_name} may be violated.")
            else:
                stat_lev, p_lev, decision_lev = None, None, "Not enough groups"
        except Exception as e:
            stat_lev, p_lev, decision_lev = None, None, "Error"
            self.logger.error(f"Levene error for {response_name}: {e}")
            
        # Outlier Detection
        try:
            infl = model.get_influence()
            data['Standardized_Resid'] = infl.resid_studentized_internal
            data['Studentized_Resid'] = infl.resid_studentized_external
            data['Leverage'] = infl.hat_matrix_diag
            cooks_d, _ = infl.cooks_distance
            data['Cooks_D'] = cooks_d
            
            threshold_cooks = 4 / len(data)
            data['Flagged_Outlier'] = (data['Cooks_D'] > threshold_cooks) | (np.abs(data['Standardized_Resid']) > 3)
            
            outliers = data[data['Flagged_Outlier']]
            if not outliers.empty:
                self.logger.info(f"Flagged {len(outliers)} potential outliers for {response_name} (NOT deleted).")
            
            data.to_csv(os.path.join(self.outlier_dir, f"{response_name}_outliers_flagged.csv"), index=False)
        except Exception as e:
            self.logger.error(f"Failed to calculate outliers for {response_name}: {e}")
            
        results.append({
            "Response": response_name,
            "Test": "Shapiro-Wilk (Normality on Residuals)",
            "Statistic": stat_sw,
            "p-value": p_sw,
            "Decision": decision_sw
        })
        
        results.append({
            "Response": response_name,
            "Test": "Levene (Homogeneity)",
            "Statistic": stat_lev,
            "p-value": p_lev,
            "Decision": decision_lev
        })
        
        res_df = pd.DataFrame(results)
        out_path = os.path.join(self.output_dir, f"{response_name}_assumptions.csv")
        res_df.to_csv(out_path, index=False)
        return out_path
