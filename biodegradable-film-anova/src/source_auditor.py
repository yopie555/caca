import pandas as pd
import os
from src.utils import get_output_dir

class SourceAuditor:
    def __init__(self, output_base_dir):
        self.val_dir = get_output_dir(output_base_dir, "validation")
        
    def run_audit(self, raw_files, response_datasets):
        audit_records = []
        
        import itertools
        expected_cells = list(itertools.product([1, 2, 3], [0, 1, 2, 3], ["Gliserol", "Sorbitol"]))
        
        # Load raw data maps
        raw_dfs = {}
        for rf in raw_files:
            try:
                base = os.path.basename(rf)
                raw_dfs[base] = pd.read_csv(rf)
            except:
                pass
                
        for resp, df_clean in response_datasets.items():
            if df_clean.empty:
                continue
                
            # Find the best raw file for this response
            best_rf = None
            from src.utils import normalize_column_name, RESPONSE_ALIASES
            for base, df_raw in raw_dfs.items():
                normalized = [normalize_column_name(c) for c in df_raw.columns]
                # Is resp in normalized? Or matches aliases?
                aliases = RESPONSE_ALIASES.get(resp, [resp.lower().replace(" ", "_")])
                for a in aliases:
                    if a in normalized:
                        best_rf = base
                        break
                if best_rf:
                    break
                    
            if not best_rf:
                continue
                
            df_raw = raw_dfs[best_rf]
            norm_cols = [normalize_column_name(c) for c in df_raw.columns]
            df_raw.columns = norm_cols
            
            # Create a lookup set for raw and clean
            def create_keys(df):
                keys = set()
                if not set(["cmc", "pva", "plasticizer", "replicate"]).issubset(set(df.columns)):
                    return keys
                for _, row in df.iterrows():
                    try:
                        c = int(row["cmc"])
                        p = int(row["pva"])
                        pl = str(row["plasticizer"]).strip().capitalize()
                        r = int(row["replicate"])
                        keys.add((c, p, pl, r))
                    except:
                        pass
                return keys
                
            raw_keys = create_keys(df_raw)
            clean_keys = set()
            for _, row in df_clean.iterrows():
                try:
                    c = int(row["CMC"])
                    p = int(row["PVA"])
                    pl = str(row["Plasticizer"]).strip().capitalize()
                    r = int(row["Replicate"])
                    clean_keys.add((c, p, pl, r))
                except:
                    pass
                    
            for cell in expected_cells:
                for rep in [1, 2, 3]:
                    key = (cell[0], cell[1], cell[2], rep)
                    
                    found_in_clean = key in clean_keys
                    if not found_in_clean:
                        found_in_raw = key in raw_keys
                        audit_records.append({
                            "Response": resp,
                            "CMC": cell[0],
                            "PVA": cell[1],
                            "Plasticizer": cell[2],
                            "Replicate": rep,
                            "Expected": "YES",
                            "Found_In_Source": "YES" if found_in_raw else "NO",
                            "Found_After_Preprocessing": "NO",
                            "Source_Sheet": best_rf
                        })
                        
        if audit_records:
            pd.DataFrame(audit_records).to_csv(os.path.join(self.val_dir, "source_audit.csv"), index=False)
