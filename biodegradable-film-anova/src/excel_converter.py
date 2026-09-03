import os
import pandas as pd
from datetime import datetime
from src.utils import get_output_dir, setup_logger

class ExcelConverter:
    def __init__(self, input_file, output_base_dir, target_sheet=None):
        self.input_file = input_file
        self.output_base_dir = output_base_dir
        self.target_sheet = target_sheet
        self.raw_csv_dir = get_output_dir(output_base_dir, "raw_csv")
        self.log_file = os.path.join(output_base_dir, "conversion_log.txt")
        self.report_file = os.path.join(output_base_dir, "conversion_report.csv")
        self.logger = setup_logger("excel_converter", self.log_file)
        self.report_data = []

    def log_conversion(self, sheet_name, rows_read, rows_retained, plasticizer, status):
        self.report_data.append({
            "Input File": os.path.basename(self.input_file),
            "Sheet": sheet_name,
            "Rows Read": rows_read,
            "Rows Retained": rows_retained,
            "Plasticizer": plasticizer,
            "Status": status
        })
        self.logger.info(f"Sheet '{sheet_name}' processed. Status: {status}. Rows: {rows_read}.")

    def convert(self):
        ext = os.path.splitext(self.input_file)[1].lower()
        self.logger.info(f"Starting conversion for {self.input_file}")
        
        output_files = []
        try:
            if ext == '.csv':
                df = pd.read_csv(self.input_file)
                out_path = os.path.join(self.raw_csv_dir, f"{os.path.basename(self.input_file)}")
                df.to_csv(out_path, index=False)
                self.log_conversion("CSV", len(df), len(df), "Unknown", "Success")
                output_files.append(out_path)
            elif ext in ['.xlsx', '.xls']:
                engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
                xls = pd.ExcelFile(self.input_file, engine=engine)
                sheets = xls.sheet_names
                self.logger.info(f"Sheets detected: {sheets}")
                
                sheets_to_process = sheets
                if self.target_sheet:
                    if self.target_sheet in sheets:
                        sheets_to_process = [self.target_sheet]
                    else:
                        self.logger.warning(f"Target sheet '{self.target_sheet}' not found.")
                        return []

                for sheet in sheets_to_process:
                    df = pd.read_excel(xls, sheet_name=sheet)
                    base_name = os.path.splitext(os.path.basename(self.input_file))[0]
                    safe_sheet = str(sheet).replace(" ", "_").replace("/", "_")
                    out_path = os.path.join(self.raw_csv_dir, f"{base_name}_{safe_sheet}.csv")
                    
                    # Add a temporary metadata column for plasticizer based on sheet name if applicable
                    plasticizer = "Unknown"
                    sheet_lower = sheet.lower()
                    if "sorbitol" in sheet_lower:
                        plasticizer = "Sorbitol"
                        df["_Sheet_Plasticizer"] = "Sorbitol"
                    elif "gliserol" in sheet_lower or "glycerol" in sheet_lower:
                        plasticizer = "Gliserol"
                        df["_Sheet_Plasticizer"] = "Gliserol"
                        
                    df.to_csv(out_path, index=False)
                    self.log_conversion(sheet, len(df), len(df), plasticizer, "Success")
                    output_files.append(out_path)
            else:
                self.logger.error(f"Unsupported file extension: {ext}")
                
            # Write conversion report
            if self.report_data:
                pd.DataFrame(self.report_data).to_csv(self.report_file, index=False)
                
            return output_files
        except Exception as e:
            self.logger.error(f"Error during conversion: {e}")
            return []
