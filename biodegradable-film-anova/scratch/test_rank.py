import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols

df = pd.DataFrame({
    "CMC": [1, 1, 2, 2, 3, 3],
    "PVA": [1, 1, 1, 1, 1, 1],
    "Plasticizer": ["Gliserol"] * 6,
    "Replicate": [1, 2, 1, 2, 1, 2],
    "Resp": [10, 11, 12, 13, 14, 15]
})

formula = "Resp ~ C(CMC) * C(PVA) * C(Plasticizer)"
model = ols(formula, data=df).fit()
rank = model.model.exog.shape[1]
actual_rank = __import__('numpy').linalg.matrix_rank(model.model.exog)
print(f"n_columns={rank}, actual_rank={actual_rank}")
