import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import statsmodels.api as sm
from statsmodels.formula.api import ols
from src.utils import get_output_dir, setup_logger

class Plotter:
    def __init__(self, output_base_dir):
        self.output_base_dir = output_base_dir
        self.means_dir = get_output_dir(output_base_dir, "plots/means")
        self.interactions_dir = get_output_dir(output_base_dir, "plots/interactions")
        self.residuals_dir = get_output_dir(output_base_dir, "plots/residuals")
        self.qq_dir = get_output_dir(output_base_dir, "plots/qq")
        self.logger = setup_logger("plotter", os.path.join(output_base_dir, "conversion_log.txt"))
        
        sns.set_theme(style="whitegrid")
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['savefig.dpi'] = 300

    def plot_means(self, df, response_name):
        factors = ["Formulation", "CMC", "PVA", "Plasticizer"]
        if response_name not in df.columns:
            return
            
        for factor in factors:
            if factor in df.columns:
                plt.figure(figsize=(10, 6))
                sns.barplot(data=df, x=factor, y=response_name, errorbar="sd", capsize=.2)
                plt.title(f"Mean ± SD of {response_name} by {factor}")
                plt.tight_layout()
                plt.savefig(os.path.join(self.means_dir, f"means_{response_name}_{factor}.png"))
                plt.close()

    def plot_interactions(self, df, response_name):
        if response_name not in df.columns:
            return
            
        if set(["CMC", "PVA"]).issubset(df.columns) and df["CMC"].nunique() > 1 and df["PVA"].nunique() > 1:
            plt.figure(figsize=(10, 6))
            sns.pointplot(data=df, x="CMC", y=response_name, hue="PVA", dodge=True, capsize=.1, errorbar="sd")
            plt.title(f"Interaction Plot: CMC × PVA on {response_name}")
            plt.tight_layout()
            plt.savefig(os.path.join(self.interactions_dir, f"interaction_CMC_PVA_{response_name}.png"))
            plt.close()
            
        if set(["CMC", "Plasticizer"]).issubset(df.columns) and df["CMC"].nunique() > 1 and df["Plasticizer"].nunique() > 1:
            plt.figure(figsize=(10, 6))
            sns.pointplot(data=df, x="CMC", y=response_name, hue="Plasticizer", dodge=True, capsize=.1, errorbar="sd")
            plt.title(f"Interaction Plot: CMC × Plasticizer on {response_name}")
            plt.tight_layout()
            plt.savefig(os.path.join(self.interactions_dir, f"interaction_CMC_Plasticizer_{response_name}.png"))
            plt.close()
            
        if set(["PVA", "Plasticizer"]).issubset(df.columns) and df["PVA"].nunique() > 1 and df["Plasticizer"].nunique() > 1:
            plt.figure(figsize=(10, 6))
            sns.pointplot(data=df, x="PVA", y=response_name, hue="Plasticizer", dodge=True, capsize=.1, errorbar="sd")
            plt.title(f"Interaction Plot: PVA × Plasticizer on {response_name}")
            plt.tight_layout()
            plt.savefig(os.path.join(self.interactions_dir, f"interaction_PVA_Plasticizer_{response_name}.png"))
            plt.close()

    def plot_diagnostics(self, df, response_name, formula=None):
        factors = ["CMC", "PVA", "Plasticizer"]
        if not set(factors).issubset(df.columns) or response_name not in df.columns:
            return
            
        data = df.dropna(subset=[response_name] + factors).copy()
        if data.empty:
            return
            
        if not formula:
            formula = f"{response_name} ~ C(CMC) * C(PVA) * C(Plasticizer)"
        try:
            model = ols(formula, data=data).fit()
            
            plt.figure(figsize=(8, 6))
            sns.scatterplot(x=model.fittedvalues, y=model.resid)
            plt.axhline(0, color='r', linestyle='--')
            plt.xlabel("Fitted Values")
            plt.ylabel("Residuals")
            plt.title(f"Residual Plot for {response_name}")
            plt.tight_layout()
            plt.savefig(os.path.join(self.residuals_dir, f"residual_{response_name}.png"))
            plt.close()
            
            plt.figure(figsize=(8, 6))
            sm.qqplot(model.resid, line='45', fit=True)
            plt.title(f"Q-Q Plot for {response_name}")
            plt.tight_layout()
            plt.savefig(os.path.join(self.qq_dir, f"qq_{response_name}.png"))
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Failed to generate diagnostic plots for {response_name}: {e}")

    def run_response(self, df, response_name, valid_model=True, formula=None):
        self.plot_means(df, response_name)
        self.plot_interactions(df, response_name)
        if valid_model:
            self.plot_diagnostics(df, response_name, formula)
        else:
            self.logger.warning(f"Skipping diagnostic plots for {response_name} due to invalid/blocked model.")
