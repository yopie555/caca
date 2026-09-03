import pandas as pd
import numpy as np
import os
from src.utils import get_output_dir

class DescriptiveStats:
    def __init__(self, output_base_dir):
        self.output_dir = get_output_dir(output_base_dir, "descriptive")
        
    def run_response(self, df, response_name):
        groups = [
            ["CMC"],
            ["PVA"],
            ["Plasticizer"],
            ["Formulation"],
            ["Formulation", "Plasticizer"],
            ["CMC", "PVA", "Plasticizer"]
        ]
        
        results = []
        if response_name not in df.columns:
            return None
            
        for group in groups:
            if set(group).issubset(df.columns):
                grouped = df.groupby(group)[response_name]
                
                stats = grouped.agg(
                    N='count',
                    Mean='mean',
                    SD='std',
                    Min='min',
                    Max='max'
                ).reset_index()
                
                stats['SE'] = stats['SD'] / np.sqrt(stats['N'])
                stats['CI_Lower'] = stats['Mean'] - 1.96 * stats['SE']
                stats['CI_Upper'] = stats['Mean'] + 1.96 * stats['SE']
                
                stats['Variable'] = response_name
                stats['Group_By'] = " x ".join(group)
                stats['Group_Levels'] = stats[group].apply(lambda x: "_".join(x.astype(str)), axis=1)
                
                cols = ['Variable', 'Group_By', 'Group_Levels', 'N', 'Mean', 'SD', 'SE', 'Min', 'Max', 'CI_Lower', 'CI_Upper']
                results.append(stats[cols])
                
        if results:
            final_df = pd.concat(results, ignore_index=True)
            out_path = os.path.join(self.output_dir, f"{response_name}_descriptive.csv")
            final_df.to_csv(out_path, index=False)
            return out_path
        return None
