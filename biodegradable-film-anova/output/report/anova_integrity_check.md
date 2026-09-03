# ANOVA Integrity Check

## Data Integrity
- source response correctly mapped: YES
- no synthetic data: YES
- no imputation: YES
- no unexpected cells: YES

## ANOVA Integrity

Response: FTL
N: 72
Model: FTL ~ C(CMC) * C(PVA) * C(Plasticizer)
SS available: YES
MS available: YES
F available: YES
p-value available: YES
Effect size available: YES

Response: Kelarutan
N: 72
Model: Kelarutan ~ C(CMC) * C(PVA) * C(Plasticizer)
SS available: YES
MS available: YES
F available: YES
p-value available: YES
Effect size available: YES

Response: Solubilitas
N: 51
Model: Solubilitas ~ C(CMC) + C(PVA) + C(Plasticizer)
SS available: YES
MS available: YES
F available: YES
p-value available: YES
Effect size available: YES

Response: Opasitas
N: 51
Model: Opasitas ~ C(CMC) + C(PVA) + C(Plasticizer)
SS available: YES
MS available: YES
F available: YES
p-value available: YES
Effect size available: YES

Response: WVTR
N: 51
Model: WVTR ~ C(CMC) + C(PVA) + C(Plasticizer)
SS available: YES
MS available: YES
F available: YES
p-value available: YES
Effect size available: YES

Response: UTS
N: 51
Model: UTS ~ C(CMC) + C(PVA) + C(Plasticizer)
SS available: YES
MS available: YES
F available: YES
p-value available: YES
Effect size available: YES

Response: Elongasi
N: 51
Model: Elongasi ~ C(CMC) + C(PVA) + C(Plasticizer)
SS available: YES
MS available: YES
F available: YES
p-value available: YES
Effect size available: YES

## FTL vs Kelarutan Matriks

IDENTICAL BY MATHEMATICAL TRANSFORMATION
Verified that `FTL + Kelarutan = 100` exactly (std dev of sum = 5.593547979721084e-15). This linear transformation causes the ANOVA F-statistics and p-values to be mathematically identical.