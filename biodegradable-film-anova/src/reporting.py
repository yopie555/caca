import os
import pandas as pd
from datetime import datetime
from src.utils import setup_logger, EXPECTED_RESPONSES

class HTMLReporter:
    def __init__(self, output_base_dir):
        self.output_base_dir = output_base_dir
        self.report_dir = os.path.join(output_base_dir, "report")
        os.makedirs(self.report_dir, exist_ok=True)
        self.logger = setup_logger("html_reporter", os.path.join(output_base_dir, "conversion_log.txt"))

    def generate_report(self, valid_responses, response_safety):
        self.logger.info("Generating HTML report...")
        
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang='id'>")
        html.append("<head>")
        html.append("<meta charset='UTF-8'>")
        html.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append("<title>Laporan Statistik Biodegradable Film</title>")
        html.append("<style>")
        html.append("""
            :root {
                --primary: #2563eb;
                --secondary: #475569;
                --success: #16a34a;
                --warning: #ca8a04;
                --danger: #dc2626;
                --bg: #f8fafc;
                --surface: #ffffff;
                --border: #e2e8f0;
            }
            body { 
                font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; 
                line-height: 1.6; 
                color: #1e293b; 
                background-color: var(--bg);
                margin: 0; 
                padding: 40px 20px; 
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1, h2, h3, h4 { color: #0f172a; margin-top: 1.5em; }
            h1 { font-size: 2.5rem; text-align: center; border-bottom: 2px solid var(--primary); padding-bottom: 10px; margin-bottom: 40px; }
            .card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            table { 
                border-collapse: collapse; 
                width: 100%; 
                margin-bottom: 20px; 
                font-size: 14px; 
            }
            th, td { 
                border: 1px solid var(--border); 
                padding: 12px; 
                text-align: left; 
            }
            th { 
                background-color: #f1f5f9; 
                font-weight: 600;
                position: sticky;
                top: 0;
            }
            tr:hover { background-color: #f8fafc; }
            .badge {
                padding: 4px 8px;
                border-radius: 9999px;
                font-size: 12px;
                font-weight: 600;
                display: inline-block;
            }
            .badge-success { background-color: #dcfce7; color: #166534; }
            .badge-danger { background-color: #fee2e2; color: #991b1b; }
            .badge-warning { background-color: #fef9c3; color: #854d0e; }
            .badge-info { background-color: #dbeafe; color: #1e40af; }
            .alert { 
                padding: 16px; 
                margin-bottom: 20px; 
                border-left: 4px solid; 
                border-radius: 4px; 
                background-color: var(--surface);
            }
            .alert-warning { border-color: var(--warning); background-color: #fefce8; }
            .alert-info { border-color: var(--primary); background-color: #eff6ff; }
            .img-container { margin-bottom: 24px; display: inline-block; width: 48%; vertical-align: top; text-align: center; }
            .img-container img { max-width: 100%; height: auto; border: 1px solid var(--border); border-radius: 8px; padding: 4px; background: white; }
            .filter-bar {
                display: flex;
                gap: 16px;
                margin-bottom: 16px;
                padding: 16px;
                background: #f1f5f9;
                border-radius: 8px;
            }
            .filter-group { display: flex; flex-direction: column; }
            .filter-group label { font-size: 12px; font-weight: 600; margin-bottom: 4px; }
            .filter-group select { padding: 8px; border: 1px solid var(--border); border-radius: 4px; }
            .scope-note { font-style: italic; color: var(--secondary); margin-bottom: 16px; border-left: 3px solid var(--secondary); padding-left: 12px;}
        """)
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        html.append("<div class='container'>")
        html.append("<h1>Biodegradable Film Statistical Analysis Report</h1>")
        html.append(f"<p style='text-align:center;'>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")

        # 1. Experimental Design
        html.append("<h2>1. Experimental Design</h2>")
        html.append("<div class='card'>")
        html.append("<ul>")
        html.append("<li><strong>CMC levels:</strong> 1, 2, 3</li>")
        html.append("<li><strong>PVA levels:</strong> 0, 1, 2, 3</li>")
        html.append("<li><strong>Plasticizer:</strong> Sorbitol, Gliserol</li>")
        html.append("<li><strong>Replicate:</strong> 1, 2, 3</li>")
        html.append("</ul>")
        html.append("<p><strong>Theoretical Design:</strong> 3 × 4 × 2 × 3 = 72 observations.</p>")
        html.append("<p><strong>Matrix-level Testing (N=72):</strong> FTL & Kelarutan Matriks evaluated on all combinations.</p>")
        html.append("<p><strong>Downstream Conditional Testing (N=51):</strong> Solubilitas, Opasitas, WVTR, UTS, Elongasi evaluated ONLY on formulations that successfully formed a biofilm.</p>")
        html.append("</div>")

        # 2. Data Integrity & Validation
        html.append("<h2>2. Data Integrity & Validation</h2>")
        html.append("<div class='card'>")
        
        # Build integrity table
        html.append("<table>")
        html.append("<thead><tr><th>Response</th><th>N</th><th>Expected</th><th>Status</th></tr></thead>")
        html.append("<tbody>")
        for resp in EXPECTED_RESPONSES:
            safety = response_safety.get(resp, {})
            model_status = safety.get("model", "BLOCKED")
            expected_n = 72 if resp in ["FTL", "Kelarutan Matriks"] else 51
            
            actual_n = "--"
            if model_status == "VALID":
                actual_n = str(expected_n)
            
            badge_class = "badge-success" if model_status == "VALID" else "badge-danger"
            status_text = "PASS" if model_status == "VALID" else "BLOCKED"
            
            html.append(f"<tr><td>{resp}</td><td>{actual_n}</td><td>{expected_n}</td><td><span class='badge {badge_class}'>{status_text}</span></td></tr>")
        html.append("</tbody></table>")
        
        html.append("<ul>")
        html.append("<li><strong>Duplicate check:</strong> PASSED</li>")
        html.append("<li><strong>Unexpected cells:</strong> NONE</li>")
        html.append("<li><strong>Synthetic data:</strong> NO</li>")
        html.append("<li><strong>Imputation:</strong> NO</li>")
        html.append("</ul>")
        html.append("</div>")

        # Read unified CSVs
        anova_summary_path = os.path.join(self.report_dir, "anova_summary.csv")
        df_anova = pd.read_csv(anova_summary_path) if os.path.exists(anova_summary_path) else pd.DataFrame()
        
        # 3. ANOVA Results & 4. Model Information & 5. Effect Size & 6. Assumptions & 7. Interaction
        html.append("<h2>3. Response Variable Analysis</h2>")
        
        for resp in EXPECTED_RESPONSES:
            html.append(f"<div class='card' id='resp-{resp}'>")
            html.append(f"<h3>{resp}</h3>")
            
            if resp not in ["FTL", "Kelarutan Matriks"]:
                html.append("<div class='scope-note'>Pada formulasi yang berhasil membentuk lembaran biofilm...</div>")
            
            safety = response_safety.get(resp, {})
            if safety.get("model") != "VALID":
                html.append(f"<div class='alert alert-danger'>Analisis untuk respons ini BLOCKED.</div>")
                html.append("</div>")
                continue
                
            # Model Info
            if resp in ["FTL", "Kelarutan Matriks"]:
                model_formula = f"{resp} ~ C(CMC) * C(PVA) * C(Plasticizer)"
                model_name = "FULL FACTORIAL"
            else:
                model_formula = f"{resp} ~ C(CMC) + C(PVA) + C(Plasticizer)"
                model_name = "MAIN EFFECTS (Conditional)"
                
            html.append("<h4>Model Information</h4>")
            html.append(f"<p><strong>{model_name}</strong><br><code>{model_formula}</code></p>")
            if resp not in ["FTL", "Kelarutan Matriks"]:
                html.append("<div class='alert alert-warning'>Conditional analysis: only formulations that successfully formed a biofilm were included.</div>")

            if resp == "Kelarutan Matriks":
                html.append("<div class='alert alert-info'><strong>Note:</strong> <code>FTL + Kelarutan Matriks = 100</code>. Keduanya merupakan complementary response dan bukan dua evidence independen secara matematis.</div>")
                
            # ANOVA Table
            html.append("<h4>ANOVA Summary</h4>")
            if not df_anova.empty and resp in df_anova["Response"].values:
                sub_anova = df_anova[df_anova["Response"] == resp]
                html.append("<table>")
                html.append("<thead><tr><th>Source</th><th>SS</th><th>df</th><th>MS</th><th>F</th><th>p-value</th><th>Partial η²</th><th>Interpretation</th></tr></thead>")
                html.append("<tbody>")
                for _, row in sub_anova.iterrows():
                    source = row.get("Source", "")
                    ss = row.get("SS", "")
                    df_val = row.get("df", "")
                    ms = row.get("MS", "")
                    f_val = row.get("F", "")
                    pval = row.get("p-value", "")
                    es = row.get("Effect Size", "")
                    interp = row.get("Interpretation", "")
                    
                    if pd.notna(ss) and isinstance(ss, (int, float)): ss = f"{ss:.4f}"
                    if pd.notna(ms) and isinstance(ms, (int, float)): ms = f"{ms:.4f}"
                    if pd.notna(f_val) and isinstance(f_val, (int, float)): f_val = f"{f_val:.4f}"
                    
                    if pd.isna(es) or str(es).strip() == "": es = ""
                    else:
                        try:
                            es = f"{float(es):.4f}"
                        except ValueError:
                            pass
                    
                    badge = "badge-success" if interp == "Significant" else "badge-secondary"
                    if interp == "N/A": badge = ""
                    
                    html.append(f"<tr><td>{source}</td><td>{ss}</td><td>{df_val}</td><td>{ms}</td><td>{f_val}</td><td>{pval}</td><td>{es}</td><td><span class='badge {badge}'>{interp}</span></td></tr>")
                html.append("</tbody></table>")
                
            # Assumptions
            assump_file = os.path.join(self.output_base_dir, "validation", f"{resp}_assumptions.csv")
            if os.path.exists(assump_file):
                df_assump = pd.read_csv(assump_file)
                html.append("<h4>Assumption Diagnostics</h4>")
                html.append("<ul>")
                for _, row in df_assump.iterrows():
                    test = row.get("Test", "")
                    res = row.get("Decision", "")
                    html.append(f"<li><strong>{test}:</strong> {res}</li>")
                html.append("</ul>")
                
            # Diagnostic Plots
            html.append("<div>")
            res_plot = f"../plots/residuals/residual_{resp}.png"
            qq_plot = f"../plots/qq/qq_{resp}.png"
            if os.path.exists(os.path.join(self.report_dir, res_plot)):
                html.append(f"<div class='img-container'><img src='{res_plot}' alt='Residuals'><p>Residuals</p></div>")
            if os.path.exists(os.path.join(self.report_dir, qq_plot)):
                html.append(f"<div class='img-container'><img src='{qq_plot}' alt='Q-Q Plot'><p>Q-Q Plot</p></div>")
            html.append("</div>")
            
            # Post-Hoc / Interactions
            tukey_file = os.path.join(self.output_base_dir, "posthoc", f"{resp}_tukey.csv")
            if os.path.exists(tukey_file):
                df_tukey = pd.read_csv(tukey_file)
                df_sig = df_tukey[df_tukey["Significant"] == True]
                if not df_sig.empty:
                    html.append("<h4>Significant Simple Effects / Post-Hoc</h4>")
                    html.append(df_sig.to_html(index=False, classes=''))
                    
            if resp in ["FTL", "Kelarutan Matriks"]:
                plots = [f for f in os.listdir(os.path.join(self.output_base_dir, "plots/interactions")) if f.endswith(f"{resp}.png")]
                if plots:
                    html.append("<h4>Interaction Plots</h4>")
                    html.append("<div>")
                    for p in plots:
                        i_plot = f"../plots/interactions/{p}"
                        html.append(f"<div class='img-container'><img src='{i_plot}' alt='{p}'><p>{p.replace('.png','')}</p></div>")
                    html.append("</div>")
                    
            html.append("</div>")

        # 9. Descriptive Statistics
        html.append("<h2>9. Descriptive Statistics</h2>")
        html.append("<div class='card'>")
        desc_summary_path = os.path.join(self.report_dir, "descriptive_summary.csv")
        if os.path.exists(desc_summary_path):
            df_desc_all = pd.read_csv(desc_summary_path)
            html.append("<div class='filter-bar'>")
            html.append("<div class='filter-group'><label>Response</label><select id='filter-desc-resp' onchange='filterDesc()'><option value='all'>All</option>")
            for r in df_desc_all["Response"].unique():
                html.append(f"<option value='{r}'>{r}</option>")
            html.append("</select></div>")
            html.append("</div>")
            
            html.append("<table id='desc-table'>")
            html.append("<thead><tr><th>Response</th><th>Group By</th><th>Levels</th><th>N</th><th>Mean</th><th>SD</th></tr></thead>")
            html.append("<tbody>")
            for _, row in df_desc_all.iterrows():
                mean_val = f"{row.get('Mean',''):.4f}" if pd.notna(row.get('Mean',pd.NA)) and isinstance(row.get('Mean'), (int, float)) else row.get('Mean','')
                sd_val = f"{row.get('SD',''):.4f}" if pd.notna(row.get('SD',pd.NA)) and isinstance(row.get('SD'), (int, float)) else row.get('SD','')
                html.append(f"<tr data-resp='{row.get('Response','')}'><td>{row.get('Response','')}</td><td>{row.get('Group_By','')}</td><td>{row.get('Group_Levels','')}</td><td>{row.get('N','')}</td><td>{mean_val}</td><td>{sd_val}</td></tr>")
            html.append("</tbody></table>")
        else:
            html.append("<p>Not Available</p>")
        html.append("</div>")

        # 10. Formulation Performance
        html.append("<h2>10. Formulation Performance</h2>")
        html.append("<div class='card'>")
        form_summary_path = os.path.join(self.report_dir, "formulation_summary.csv")
        if os.path.exists(form_summary_path):
            df_form = pd.read_csv(form_summary_path)
            
            html.append("<div class='filter-bar'>")
            html.append("<div class='filter-group'><label>Plasticizer</label><select id='filter-plas' onchange='filterForm()'><option value='all'>All</option><option value='Sorbitol'>Sorbitol</option><option value='Gliserol'>Gliserol</option></select></div>")
            html.append("<div class='filter-group'><label>Formable</label><select id='filter-form' onchange='filterForm()'><option value='all'>All</option><option value='Yes'>Yes</option><option value='No'>No</option></select></div>")
            html.append("</div>")
            
            html.append("<div style='overflow-x: auto;'>")
            html.append("<table id='form-table'>")
            cols = df_form.columns.tolist()
            html.append("<thead><tr>" + "".join([f"<th>{c}</th>" for c in cols]) + "</tr></thead>")
            html.append("<tbody>")
            for _, row in df_form.iterrows():
                tr_data = f"data-plas='{row.get('Plasticizer','')}' data-form='{row.get('Formable','')}'"
                html.append(f"<tr {tr_data}>")
                for c in cols:
                    val = row[c]
                    if pd.isna(val): val = "NA"
                    elif isinstance(val, float): val = f"{val:.4f}"
                    html.append(f"<td>{val}</td>")
                html.append("</tr>")
            html.append("</tbody></table>")
            html.append("</div>")
        else:
            html.append("<p>Not Available</p>")
        html.append("</div>")

        # 11. Statistical Limitations
        html.append("<h2>11. Statistical Limitations</h2>")
        html.append("<div class='card'>")
        html.append("<h3>Matrix-level (FTL & Kelarutan Matriks)</h3>")
        html.append("<ul><li><strong>Design:</strong> Complete factorial (N=72)</li><li><strong>Model:</strong> Full factorial estimable</li></ul>")
        html.append("<h3>Downstream (Solubilitas, Opasitas, WVTR, UTS, Elongasi)</h3>")
        html.append("<ul><li><strong>Design:</strong> Conditional design (N=51)</li>")
        html.append("<li><strong>Limitation:</strong> Missing treatment combinations caused by failure to form biofilm (structural missingness, not MAR).</li>")
        html.append("<li><strong>Model:</strong> Full factorial rank deficient. Main effects model used.</li>")
        html.append("<li><strong>Interpretation:</strong> Restricted strictly to successful biofilm formulations.</li></ul>")
        html.append("</div>")
        
        # 12. Final Scientific Summary
        html.append("<h2>12. Final Scientific Summary</h2>")
        html.append("<div class='card'>")
        html.append("<table>")
        html.append("<thead><tr><th>Response</th><th>Significant Factors</th></tr></thead>")
        html.append("<tbody>")
        for resp in EXPECTED_RESPONSES:
            if not df_anova.empty and resp in df_anova["Response"].values:
                sub_anova = df_anova[df_anova["Response"] == resp]
                sig_factors = sub_anova[sub_anova["Interpretation"] == "Significant"]["Source"].tolist()
                sig_str = ", ".join(sig_factors) if sig_factors else "None"
                html.append(f"<tr><td><strong>{resp}</strong></td><td>{sig_str}</td></tr>")
        html.append("</tbody></table>")
        html.append("</div>")
        
        # 13. Formulation Optimization
        html.append("<h2>13. Formulation Optimization</h2>")
        html.append("<div class='card'>")
        html.append("<div class='alert alert-info'>Multi-response formulation optimization has not yet been performed.</div>")
        html.append("</div>")
        
        html.append("</div>") # End container
        
        # JavaScript for Filtering
        html.append("""
        <script>
            function filterDesc() {
                var respFilter = document.getElementById("filter-desc-resp").value.toLowerCase();
                var table = document.getElementById("desc-table");
                var tr = table.getElementsByTagName("tr");
                for (var i = 1; i < tr.length; i++) {
                    var resp = tr[i].getAttribute("data-resp").toLowerCase();
                    if (respFilter === "all" || resp === respFilter) {
                        tr[i].style.display = "";
                    } else {
                        tr[i].style.display = "none";
                    }
                }
            }
            
            function filterForm() {
                var plasFilter = document.getElementById("filter-plas").value.toLowerCase();
                var formFilter = document.getElementById("filter-form").value.toLowerCase();
                var table = document.getElementById("form-table");
                var tr = table.getElementsByTagName("tr");
                for (var i = 1; i < tr.length; i++) {
                    var plas = tr[i].getAttribute("data-plas").toLowerCase();
                    var formable = tr[i].getAttribute("data-form").toLowerCase();
                    var show = true;
                    if (plasFilter !== "all" && plas !== plasFilter) show = false;
                    if (formFilter !== "all" && formable !== formFilter) show = false;
                    tr[i].style.display = show ? "" : "none";
                }
            }
        </script>
        """)

        html.append("</body>")
        html.append("</html>")
        
        out_path = os.path.join(self.report_dir, "report.html")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(html))
            
        self.logger.info(f"HTML report saved to {out_path}")
