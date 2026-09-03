import os
import argparse
import glob
import pandas as pd
from src.utils import setup_logger, EXPECTED_RESPONSES, SHEET_RESPONSE_MAP
from src.excel_converter import ExcelConverter
from src.preprocessing import Preprocessor
from src.validation import Validator
from src.descriptive import DescriptiveStats
from src.assumptions import AssumptionTester
from src.anova import FactorialANOVA
from src.posthoc import PostHocTester
from src.interaction import InteractionAnalyzer
from src.plotter import Plotter
from src.reporting import HTMLReporter

def find_input_file():
    data_dir = "data"
    if not os.path.exists(data_dir):
        return None
        
    files = glob.glob(os.path.join(data_dir, "*.xlsx")) + \
            glob.glob(os.path.join(data_dir, "*.xls")) + \
            glob.glob(os.path.join(data_dir, "*.csv"))
            
    if not files:
        return None
    
    if len(files) == 1:
        return files[0]
        
    print("Multiple files found in data/ directory. Please specify one using --input.")
    return None

def main():
    parser = argparse.ArgumentParser(description="Biodegradable Film Data Processing & Factorial ANOVA")
    parser.add_argument("--input", type=str, help="Path to input Excel or CSV file")
    parser.add_argument("--sheet", type=str, help="Specific sheet to process (if Excel)", default=None)
    parser.add_argument("--output", type=str, help="Output base directory", default="output")
    parser.add_argument("--alpha", type=float, help="Significance level (default: 0.05)", default=0.05)
    parser.add_argument("--convert-only", action="store_true", help="Only perform Excel to CSV conversion and preprocessing")
    parser.add_argument("--debug-schema", action="store_true", help="Print schema debug information for each sheet")
    parser.add_argument("--debug-design", action="store_true", help="Print complete cell audit for factorial design")
    
    args = parser.parse_args()
    
    print("============================================================")
    print("BIODEGRADABLE FILM")
    print("DATA PROCESSING & FACTORIAL ANOVA")
    print("============================================================\n")
    
    input_file = args.input
    if not input_file:
        input_file = find_input_file()
        if not input_file:
            print("Error: No input file found. Please provide one via --input or place it in the data/ folder.")
            return
            
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        return
        
    ext = os.path.splitext(input_file)[1].lower()
    
    print(f"Input:\n{input_file}\n")
    
    logger = setup_logger("main", os.path.join(args.output, "conversion_log.txt"))
    
    # 1. Conversion
    print("------------------------------------------------------------")
    print("DATA CONVERSION")
    print("------------------------------------------------------------\n")
    converter = ExcelConverter(input_file, args.output, args.sheet)
    raw_files = converter.convert()
    
    for rf in raw_files:
        base = os.path.basename(rf).replace(".csv", "")
        # Find sheet name roughly
        sheet_name = base
        for sm in SHEET_RESPONSE_MAP.keys():
            if sm.replace(" ", "_").lower() in base.lower():
                sheet_name = sm
                break
        print(f"✓ {sheet_name}")
        
    if not raw_files:
        print("Error: No data could be extracted.")
        return

    # 2. Preprocessing
    preprocessor = Preprocessor(raw_files, args.output)
    
    if args.debug_schema:
        print("\n============================================================")
        print("SOURCE SCHEMA (DEBUG)")
        print("============================================================")
        for rf in raw_files:
            try:
                df_raw = pd.read_csv(rf)
                base = os.path.basename(rf)
                print(f"\nSHEET: {base}")
                print("\nRaw columns:")
                for i, col in enumerate(df_raw.columns):
                    print(f"{i}: {col}")
                    
                from src.utils import normalize_column_name, RESPONSE_ALIASES
                print("\nNormalized columns:")
                for i, col in enumerate(df_raw.columns):
                    print(f"{i}: {normalize_column_name(col)}")
                    
                if "wvtr" in base.lower():
                    print("\nFirst 10 rows:")
                    print(df_raw.head(10).to_string())
                    print("\nDetected responses:")
                    detected = []
                    for col in df_raw.columns:
                        norm = normalize_column_name(col)
                        for resp in EXPECTED_RESPONSES:
                            aliases = RESPONSE_ALIASES.get(resp, [resp.lower().replace(" ", "_")])
                            if any(a in norm for a in aliases):
                                detected.append(resp)
                    print(", ".join(set(detected)) if detected else "NONE")
            except Exception as e:
                print(f"Error reading {rf}: {e}")
        print("============================================================\n")

    response_datasets, eligibility_map = preprocessor.clean_all()
    
    if not response_datasets:
        print("Error: Cleaned dataset is empty. Check preprocessing logs.")
        return
        
    print("\n------------------------------------------------------------")
    print("RESPONSE DATASETS")
    print("------------------------------------------------------------\n")
    
    valid_responses = []
    
    for resp in EXPECTED_RESPONSES:
        if resp in response_datasets and not response_datasets[resp].empty:
            df_resp = response_datasets[resp]
            print(f"✓ {resp}")
            print(f"   Observations: {len(df_resp)}\n")
            valid_responses.append(resp)
            
    if not valid_responses:
        print("Error: No valid response variables found for analysis.")
        return

    if args.debug_schema:
        print("\n============================================================")
        print("CANONICAL DATAFRAME DEBUG")
        print("============================================================")
        for resp in valid_responses:
            df_resp = response_datasets[resp]
            print(f"\nResponse: {resp}")
            print("Columns:")
            for c in df_resp.columns:
                print(f"- {c} ({df_resp[c].dtype})")
            print(f"\nShape:\n{df_resp.shape}")
            print(f"\nUnique CMC:\n{sorted(df_resp['CMC'].dropna().unique().tolist())}")
            print(f"Unique PVA:\n{sorted(df_resp['PVA'].dropna().unique().tolist())}")
            print(f"Unique Plasticizer:\n{sorted(df_resp['Plasticizer'].dropna().unique().tolist())}")
            print(f"Unique Replicate:\n{sorted(df_resp['Replicate'].dropna().unique().tolist())}")
            print("\nSample (head 10):")
            print(df_resp.head(10).to_string())
            print("-" * 60)
        
        print("\n[CONTINUING] CANONICAL DATASET CHECK complete. Moving to Validation...")

    if args.convert_only:
        print("\nConvert-only flag passed. Process completed.")
        return

    # 3. Validation
    print("------------------------------------------------------------")
    print("VALIDATION & SOURCE AUDIT")
    print("------------------------------------------------------------\n")
    
    validator = Validator(args.output)
    
    for resp in valid_responses:
        df_resp = response_datasets[resp]
        validator.validate_dataset(df_resp, resp)

    # Specific FTL/Kelarutan check
    if "FTL" in valid_responses and "Kelarutan" in valid_responses:
        validator.run_consistency_check(response_datasets["FTL"], response_datasets["Kelarutan"])
        
    from src.source_auditor import SourceAuditor
    auditor = SourceAuditor(args.output)
    auditor.run_audit(raw_files, response_datasets)
    print("✓ Source Audit completed\n")
        
    from src.master_validator import MasterValidator
    master_val = MasterValidator(args.output)
    is_safe, response_safety = master_val.generate_report(response_datasets, eligibility_map)
    
    if args.debug_design:
        print("\n============================================================")
        print("FORENSIC DESIGN AUDIT")
        print("============================================================")
        for resp in valid_responses:
            df_resp = response_datasets[resp]
            audit = master_val.audit_factorial_design(df_resp, resp, eligibility_map)
            print(f"\nDESIGN AUDIT: {resp}")
            print("-" * 60)
            print(f"Expected cells      : {audit['expected_cells']}")
            print(f"Observed cells      : {audit['observed_cells']}")
            print(f"Missing cells       : {audit['missing_cells_count']}")
            print(f"Duplicate cells     : {len(audit['duplicate_cells'])}")
            print(f"Invalid replicates  : {len(audit['invalid_replicates'])}")
            print()
            print(f"Replicate levels    : {df_resp['Replicate'].dropna().nunique()}")
            print(f"Observations        : {len(df_resp)}")
            print(f"Expected            : 72")
            print()
            status = "COMPLETE" if audit['complete'] else "INCOMPLETE"
            print(f"Status              : {status}")
            print("\nCMC PVA Plasticizer   Replicates       N   Status")
            print("-" * 55)
            for d in audit["details"]:
                print(f"{d['CMC']:<3} {d['PVA']:<3} {d['Plasticizer']:<13} {d['Replicates']:<16} {d['N']:<3} {d['Status']}")
        print("\n============================================================")
    
    # Print the requested per-response summary
    print("\n------------------------------------------------------------")
    print("DESIGN VALIDATION STATUS")
    print("------------------------------------------------------------\n")
    
    any_duplicates = False
    
    for resp in EXPECTED_RESPONSES:
        if resp in response_safety and resp in valid_responses:
            df_resp = response_datasets[resp]
            status = response_safety[resp].get("design_status", "UNKNOWN")
            planned_n = response_safety[resp].get("Planned_N", 72)
            
            if status == "DUPLICATES FOUND":
                any_duplicates = True
                
            print(f"{resp}")
            print(f"  CMC levels       : {df_resp['CMC'].dropna().nunique()}")
            print(f"  PVA levels       : {df_resp['PVA'].dropna().nunique()}")
            print(f"  Plasticizer      : {df_resp['Plasticizer'].dropna().nunique()}")
            print(f"  Replicate levels : {df_resp['Replicate'].dropna().nunique()}")
            print(f"  Observations     : {len(df_resp)}")
            print(f"  Expected         : {planned_n}")
            print(f"  Status           : {status}\n")
    
    if any_duplicates:
        print("\n============================================================")
        print("PIPELINE HALTED: CRITICAL VALIDATION ERRORS (DUPLICATES) DETECTED.")
        print(f"Please review {master_val.report_path}")
        print("============================================================\n")
        return
        
    print(f"Master Validation Report generated: {master_val.report_path}\n")

    # 4. Statistical Analysis
    print("------------------------------------------------------------")
    print("FACTORIAL ANOVA & SAFETY CHECK")
    print("------------------------------------------------------------\n")
    
    desc = DescriptiveStats(args.output)
    assumptions_tester = AssumptionTester(args.output)
    from src.estimability_auditor import ANOVAEstimabilityAuditor
    auditor = ANOVAEstimabilityAuditor(args.output)
    anova = FactorialANOVA(args.output, args.alpha, auditor=auditor)
    posthoc = PostHocTester(args.output, args.alpha)
    interaction = InteractionAnalyzer(args.output, args.alpha)
    plotter = Plotter(args.output)
    from src.robustness_auditor import RobustnessAuditor
    robustness_auditor = RobustnessAuditor(args.output)
    
    for i, resp in enumerate(valid_responses):
        df_resp = response_datasets[resp]
        desc.run_response(df_resp, resp)
        
        design_status = response_safety[resp].get("design_status", "UNKNOWN")
        
        if design_status == "COMPLETE":
            # Run ANOVA to check identifiability
            anova_result = anova.run_response(df_resp, resp)
            
            if anova_result and anova_result["status"] == "COMPLETED":
                response_safety[resp]["model"] = "VALID"
                formula = anova_result.get("formula")
                assumptions_tester.run_response(df_resp, resp, formula=formula)
                anova_path = anova_result["path"]
                
                posthoc.run_response(df_resp, resp, anova_path)
                interaction.run_response(df_resp, resp, anova_path)
                
                # Allow plots with interaction context
                plotter.run_response(df_resp, resp, valid_model=True, formula=formula)
                
                is_conditional = (len(df_resp) < 72)
                robustness_auditor.process_response(df_resp, resp, formula, is_conditional)
                
                print(f"[{i+1}/{len(valid_responses)}] {resp}: ✓ ANOVA COMPLETED")
            else:
                reason = anova_result["reason"] if anova_result else "Unknown"
                response_safety[resp]["model"] = "BLOCKED"
                # Allow descriptive plots but block interaction label claims
                plotter.run_response(df_resp, resp, valid_model=False)
                print(f"[{i+1}/{len(valid_responses)}] {resp}: ⚠ ANOVA BLOCKED ({reason})")
        else:
            response_safety[resp]["model"] = "BLOCKED"
            plotter.run_response(df_resp, resp, valid_model=False)
            print(f"[{i+1}/{len(valid_responses)}] {resp}: ⚠ ANOVA BLOCKED (Design is {design_status})")

    # 5. Output and Plots
    print("\n============================================================")
    print("STATISTICAL DESIGN AUDIT")
    print("============================================================")
    
    print(f"{'Response':<18} | {'N':<3} | {'Cells':<5} | {'Full Factorial':<15} | {'Recommended Model':<20} | {'Status':<10}")
    print("-" * 83)
    for resp in EXPECTED_RESPONSES:
        if resp not in response_safety or resp not in valid_responses:
            print(f"{resp:<18} | {'--':<3} | {'--':<5} | {'--':<15} | {'--':<20} | {'BLOCKED':<10}")
            continue
            
        df = response_datasets[resp]
        obs_n = str(len(df))
        n_cells = str(df.groupby(["CMC", "PVA", "Plasticizer"]).size().reset_index().shape[0])
        
        # We need to get info from auditor
        status_model = response_safety[resp].get("model", "BLOCKED")
        status = "COMPLETED" if status_model == "VALID" else "BLOCKED"
        
        print(f"{resp:<18} | {obs_n:<3} | {n_cells:<5} | {'Evaluated':<15} | {'See Recommendation':<20} | {status:<10}")
        
    print("-" * 83)
    
    robustness_auditor.finalize_reports()
    
    robustness_path = os.path.join(args.output, "anova", "robustness_summary.txt")
    if os.path.exists(robustness_path):
        with open(robustness_path, "r") as f:
            print("\n" + f.read())
            
    from src.final_reporter import FinalReporter
    final_rep = FinalReporter(args.output)
    final_rep.generate_all(response_datasets)
    
    print("\nHTML REPORT")
    print("------------------------------------------------------------\n")
    
    reporter = HTMLReporter(args.output)
    reporter.generate_report(valid_responses, response_safety)
    
    print("✓ HTML report generated\n")
    
    print("\nOutput:")
    print(os.path.join(args.output, "report", "final_results.md"))
    print(os.path.join(args.output, "report", "anova_summary.csv"))
    print(os.path.join(args.output, "report", "descriptive_summary.csv"))
    print(os.path.join(args.output, "report", "formulation_summary.csv"))
    print(os.path.join(args.output, "report", "report.html"))
    print("\nCompleted.")

if __name__ == "__main__":
    main()
