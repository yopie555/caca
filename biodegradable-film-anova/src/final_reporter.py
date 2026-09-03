import pandas as pd
import os
import numpy as np

EXPECTED_RESPONSES = [
    "FTL", "Kelarutan", "Solubilitas", "Opasitas", "WVTR", "UTS", "Elongasi"
]

class FinalReporter:
    def __init__(self, output_base_dir):
        self.output_base = output_base_dir
        self.report_dir = os.path.join(output_base_dir, "report")
        self.anova_dir = os.path.join(output_base_dir, "anova")
        self.desc_dir = os.path.join(output_base_dir, "descriptive")
        
        os.makedirs(self.report_dir, exist_ok=True)
        
    def load_effect_sizes(self):
        ef_path = os.path.join(self.anova_dir, "effect_sizes.csv")
        if os.path.exists(ef_path):
            return pd.read_csv(ef_path)
        return pd.DataFrame()
        
    def load_recommendations(self):
        rec_path = os.path.join(self.anova_dir, "final_model_recommendation.csv")
        if os.path.exists(rec_path):
            return pd.read_csv(rec_path)
        return pd.DataFrame()
        
    def get_significance_text(self, p_val):
        if pd.isna(p_val):
            return "N/A"
        if p_val < 0.05:
            return "Significant"
        return "Not Significant"

    def format_p_val(self, p):
        if pd.isna(p):
            return "N/A"
        if p < 0.001:
            return "< 0.001"
        return f"{p:.4f}"

    def get_effect_size_val(self, effect_sizes_df, response, term):
        if effect_sizes_df.empty:
            return pd.NA
        # Attempt to match term directly
        match = effect_sizes_df[(effect_sizes_df["Response"] == response) & (effect_sizes_df["Term"] == term)]
        if not match.empty:
            return match.iloc[0]["Partial_Eta_Squared"]
            
        # sometimes terms in ANOVA output have different order of interactions, fallback check
        for _, row in effect_sizes_df[effect_sizes_df["Response"] == response].iterrows():
            # if sets of factors split by ':' match
            if set(row["Term"].split(":")) == set(term.replace("C(", "").replace(")", "").split(":")):
                return row["Partial_Eta_Squared"]
                
        return pd.NA

    def generate_anova_summary(self, responses):
        effect_sizes = self.load_effect_sizes()
        
        all_anova = []
        for resp in responses:
            anova_path = os.path.join(self.anova_dir, f"{resp}_anova.csv")
            if os.path.exists(anova_path):
                df_anova = pd.read_csv(anova_path)
                if "Response" not in df_anova.columns:
                    df_anova.insert(0, "Response", resp)
                
                # compute effect size and interpretation
                es_col = []
                interp_col = []
                for _, row in df_anova.iterrows():
                    source = row["Source"]
                    if source == "Residual":
                        es_col.append(pd.NA)
                        interp_col.append("N/A")
                    else:
                        pval = row.get("p-value", row.get("PR(>F)", pd.NA))
                        es_val = self.get_effect_size_val(effect_sizes, resp, source)
                        es_col.append(es_val)
                        interp_col.append(self.get_significance_text(pval))
                        
                df_anova["Effect Size (Partial Eta-Sq)"] = es_col
                df_anova["Interpretation"] = interp_col
                all_anova.append(df_anova)
                
        if all_anova:
            combined = pd.concat(all_anova, ignore_index=True)
            combined.to_csv(os.path.join(self.report_dir, "anova_summary.csv"), index=False)
            return combined
        return pd.DataFrame()

    def generate_descriptive_summary(self, responses):
        all_desc = []
        for resp in responses:
            desc_path = os.path.join(self.desc_dir, f"{resp}_descriptive.csv")
            if os.path.exists(desc_path):
                df_desc = pd.read_csv(desc_path)
                if "Response" not in df_desc.columns:
                    df_desc.insert(0, "Response", resp)
                all_desc.append(df_desc)
                
        if all_desc:
            combined = pd.concat(all_desc, ignore_index=True)
            # Reorder columns to exactly what we want in the summary
            cols = ["Response", "Group_By", "Group_Levels", "N", "Mean", "SD", "SE", "Min", "Max"]
            existing_cols = [c for c in cols if c in combined.columns]
            combined = combined[existing_cols]
            combined.to_csv(os.path.join(self.report_dir, "descriptive_summary.csv"), index=False)
            return combined
        return pd.DataFrame()

    def generate_formulation_summary(self, data_dict):
        # We need to build a wide table mapping formulations to mean responses
        # Formulation mappings
        formulations = {
            (1, 0): 'A', (1, 1): 'B', (1, 2): 'C', (1, 3): 'D',
            (2, 0): 'E', (2, 1): 'F', (2, 2): 'G', (2, 3): 'H',
            (3, 0): 'I', (3, 1): 'J', (3, 2): 'K', (3, 3): 'L'
        }
        
        rows = []
        for (cmc, pva), form_id in formulations.items():
            for plas in ["Sorbitol", "Gliserol"]:
                # Check formability (basically if it exists in downstream data)
                # We can check Solubilitas as proxy for downstream existence
                formable = "Yes"
                if "Solubilitas" in data_dict:
                    sol_df = data_dict["Solubilitas"]
                    match = sol_df[(sol_df["CMC"] == cmc) & (sol_df["PVA"] == pva) & (sol_df["Plasticizer"] == plas)]
                    if match.empty:
                        formable = "No"
                else:
                    formable = "Unknown"
                
                row = {
                    "Formulation": form_id,
                    "CMC": cmc,
                    "PVA": pva,
                    "Plasticizer": plas,
                    "Formable": formable
                }
                
                # downstream responses
                for resp in ["Solubilitas", "Opasitas", "WVTR", "UTS", "Elongasi"]:
                    if formable == "No":
                        row[resp] = "NA"
                    elif resp in data_dict:
                        df_resp = data_dict[resp]
                        match = df_resp[(df_resp["CMC"] == cmc) & (df_resp["PVA"] == pva) & (df_resp["Plasticizer"] == plas)]
                        if not match.empty:
                            row[resp] = match[resp].mean()
                        else:
                            row[resp] = "NA"
                    else:
                        row[resp] = "NA"
                        
                rows.append(row)
                
        df_form = pd.DataFrame(rows)
        df_form.to_csv(os.path.join(self.report_dir, "formulation_summary.csv"), index=False)
        return df_form

    def write_markdown_report(self, anova_df, rec_df, form_df):
        md_path = os.path.join(self.report_dir, "final_results.md")
        
        with open(md_path, "w") as f:
            f.write("# FINAL RESEARCH RESULTS\n\n")
            
            # 1. Experimental Design
            f.write("## 1. Experimental Design\n")
            f.write("Penelitian ini menggunakan desain faktorial. ")
            f.write("Pengujian tingkat matriks (FTL, Kelarutan Matriks) dilakukan pada keseluruhan kombinasi (N=72). ")
            f.write("Pengujian downstream (Solubilitas, Opasitas, WVTR, UTS, Elongasi) hanya dilakukan pada formulasi yang berhasil membentuk lembaran biofilm (N=51).\n\n")
            
            # Responses sections
            sections = {
                "FTL": "2. FTL Results",
                "Kelarutan": "3. Matrix Solubility Results",
                "Solubilitas": "4. Biofilm Solubility Results",
                "Opasitas": "5. Opacity Results",
                "WVTR": "6. WVTR Results",
                "UTS": "7. Tensile Strength Results",
                "Elongasi": "8. Elongation Results"
            }
            
            for resp in EXPECTED_RESPONSES:
                f.write(f"## {sections.get(resp, f'{resp} Results')}\n\n")
                
                if resp not in anova_df["Response"].unique():
                    f.write("Data tidak tersedia atau analisis diblokir.\n\n")
                    continue
                    
                is_conditional = resp in ["Solubilitas", "Opasitas", "WVTR", "UTS", "Elongasi"]
                
                if is_conditional:
                    f.write("> Pada formulasi yang berhasil membentuk lembaran biofilm...\n\n")
                    
                # get recommendation
                if not rec_df.empty:
                    rec_match = rec_df[rec_df["Response"] == resp]
                    if not rec_match.empty:
                        model = rec_match.iloc[0]["Final_Model"]
                        f.write(f"**Model yang digunakan:** {model}\n\n")
                        
                sub_anova = anova_df[anova_df["Response"] == resp].copy()
                f.write("### ANOVA Summary\n")
                f.write("| Source | df | SS | MS | F | p-value | Effect Size | Interpretation |\n")
                f.write("|---|---|---|---|---|---|---|---|\n")
                
                significant_terms = []
                for _, row in sub_anova.iterrows():
                    source = row["Source"].replace("C(", "").replace(")", "")
                    df = row.get("df", "")
                    ss = f"{row.get('Sum Sq', row.get('SS', '')):.4f}" if pd.notna(row.get('Sum Sq', row.get('SS', pd.NA))) else ""
                    ms = f"{row.get('Mean Sq', row.get('MS', '')):.4f}" if pd.notna(row.get('Mean Sq', row.get('MS', pd.NA))) else ""
                    f_val = f"{row.get('F', '') :.4f}" if pd.notna(row.get('F', pd.NA)) else ""
                    pval = row.get("p-value", row.get("PR(>F)", pd.NA))
                    pval_str = self.format_p_val(pval)
                    es = f"{row['Effect Size (Partial Eta-Sq)']:.4f}" if pd.notna(row['Effect Size (Partial Eta-Sq)']) else ""
                    interp = row["Interpretation"]
                    
                    if interp == "Significant":
                        significant_terms.append(source)
                        
                    f.write(f"| {source} | {df} | {ss} | {ms} | {f_val} | {pval_str} | {es} | {interp} |\n")
                f.write("\n")
                
                f.write("### Scientific Interpretation\n")
                if significant_terms:
                    f.write(f"Terdapat bukti statistik yang cukup pada taraf signifikansi 5% untuk menyatakan adanya pengaruh yang signifikan dari: **{', '.join(significant_terms)}**.\n")
                else:
                    f.write(f"Tidak terdapat bukti statistik yang cukup pada taraf signifikansi 5% untuk menyatakan adanya pengaruh faktor utama terhadap {resp}.\n")
                    f.write("Gagal menolak H0.\n")
                f.write("\n---\n\n")
                
            # 9. Cross-Response Interpretation
            f.write("## 9. Cross-Response Interpretation\n")
            f.write("Pola konsisten (consistent pattern) dapat diamati dari statistik deskriptif, namun korelasi matematis formal tidak dievaluasi dalam tahap faktorial ini.\n\n")
            
            # 10. Formulation Performance Summary
            f.write("## 10. Formulation Performance Summary\n")
            f.write("Pemilihan formulasi terbaik memerlukan kriteria optimasi multi-respons yang ditetapkan berdasarkan tujuan karakteristik film. ")
            f.write("Tabel di bawah merangkum kinerja aktual (mean):\n\n")
            if not form_df.empty:
                cols = form_df.columns
                f.write("| " + " | ".join(cols) + " |\n")
                f.write("|" + "|".join(["---"] * len(cols)) + "|\n")
                for _, row in form_df.iterrows():
                    vals = []
                    for c in cols:
                        v = row[c]
                        if isinstance(v, float) and pd.notna(v):
                            vals.append(f"{v:.4f}")
                        else:
                            vals.append(str(v))
                    f.write("| " + " | ".join(vals) + " |\n")
            f.write("\n\n")
            
            # 11. Statistical Limitations
            f.write("## 11. Statistical Limitations\n")
            f.write("### Matrix-level (FTL & Kelarutan Matriks)\n")
            f.write("- **Desain:** Complete factorial (N=72)\n")
            f.write("- **Model:** Full factorial model (estimable)\n\n")
            f.write("### Downstream (Solubilitas, Opasitas, WVTR, UTS, Elongasi)\n")
            f.write("- **Desain:** Conditional design (N=51)\n")
            f.write("- **Keterbatasan:** Full factorial rank deficient. Analisis menggunakan Main Effects model.\n")
            f.write("- **Interpretasi:** Terbatas hanya pada formulasi yang berhasil membentuk lembaran biofilm (successful biofilm formulations). ")
            f.write("Data yang hilang bersifat struktural (kegagalan formulasi), bukan missing at random, sehingga tidak dilakukan imputasi.\n")

    def generate_all(self, response_datasets):
        anova_df = self.generate_anova_summary(EXPECTED_RESPONSES)
        self.generate_descriptive_summary(EXPECTED_RESPONSES)
        form_df = self.generate_formulation_summary(response_datasets)
        
        rec_df = self.load_recommendations()
        
        self.write_markdown_report(anova_df, rec_df, form_df)
        
        # print final terminal summary
        print("\n============================================================")
        print("FINAL RESEARCH RESULTS")
        print("============================================================\n")
        
        print(f"{'Response':<20} | {'Model':<25} | {'Significant Factors'}")
        print("-" * 80)
        for resp in EXPECTED_RESPONSES:
            if anova_df.empty or resp not in anova_df["Response"].values:
                print(f"{resp:<20} | {'BLOCKED':<25} | {'--'}")
                continue
                
            model = "Unknown"
            if not rec_df.empty:
                match = rec_df[rec_df["Response"] == resp]
                if not match.empty:
                    model = match.iloc[0]["Final_Model"]
                    
            sub = anova_df[anova_df["Response"] == resp]
            sig_factors = sub[sub["Interpretation"] == "Significant"]["Source"].tolist()
            sig_factors = [f.replace("C(", "").replace(")", "") for f in sig_factors]
            sig_str = ", ".join(sig_factors) if sig_factors else "None"
            
            print(f"{resp:<20} | {model:<25} | {sig_str}")
            
        print("\n============================================================")
        print("FORMULATION PERFORMANCE")
        print("============================================================\n")
        print("Do NOT automatically declare a single best formulation.")
        print("Provide the descriptive performance table and state whether")
        print("a multi-response optimization criterion is required.")
        print("\n(See output/report/formulation_summary.csv and final_results.md for full descriptive matrix)\n")

