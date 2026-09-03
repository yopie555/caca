import pandas as pd
from src.preprocessing import Preprocessor

prep = Preprocessor("data/pengujian (ANOVA).xlsx", "output")
df = prep.process_file("output/raw_csv/pengujian (ANOVA)_WVTR.csv")
print("Process file columns:", df.columns)
print("Process file head:")
print(df.head())
