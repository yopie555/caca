# STATISTICAL ROBUSTNESS AUDIT

## 1. Experimental Design Overview
The complete theoretical design specifies 72 observations (3 CMC × 4 PVA × 2 Plasticizer × 3 Replicates). However, only 'matrix-level' variables (FTL, Kelarutan Matriks) were tested on all 72 combinations. Downstream mechanical and physical properties were only evaluated on formulations that successfully formed a biofilm, resulting in a structurally reduced (conditional) design of N=51.

## 2. Confounding Discussion
Because treatment eligibility (N=51) is deterministic (e.g., PVA=0 completely fails formability), factors are confounded with formulation viability. Specifically, Main Effects evaluated downstream must be interpreted as *conditional associations within viable formulations*, NOT universal independent causal effects. Variations in CMC cannot be fully isolated from PVA since only certain CMC/PVA pairings survive the selection step.

## 3. Final Model Recommendations

### FTL
- **Final model:** FULL FACTORIAL
- **Reason:** Design is complete (N=72, 24 cells). Valid for full main effects and interactions.
- **Limitations:** None for experimental domain.

### Kelarutan
- **Final model:** FULL FACTORIAL
- **Reason:** Design is complete (N=72, 24 cells). Valid for full main effects and interactions.
- **Limitations:** None for experimental domain.

### Solubilitas
- **Final model:** MAIN EFFECTS (Conditional)
- **Reason:** Full factorial is rank deficient due to structural missingness (biofilm formability failure for PVA=0 and Formulation F with Sorbitol).
- **Limitations:** Interpretations are strictly conditional. We cannot claim independent causal effects of CMC/PVA universally; findings apply ONLY to formulations capable of forming biofilms.

### Opasitas
- **Final model:** MAIN EFFECTS (Conditional)
- **Reason:** Full factorial is rank deficient due to structural missingness (biofilm formability failure for PVA=0 and Formulation F with Sorbitol).
- **Limitations:** Interpretations are strictly conditional. We cannot claim independent causal effects of CMC/PVA universally; findings apply ONLY to formulations capable of forming biofilms.

### WVTR
- **Final model:** MAIN EFFECTS (Conditional)
- **Reason:** Full factorial is rank deficient due to structural missingness (biofilm formability failure for PVA=0 and Formulation F with Sorbitol).
- **Limitations:** Interpretations are strictly conditional. We cannot claim independent causal effects of CMC/PVA universally; findings apply ONLY to formulations capable of forming biofilms.

### UTS
- **Final model:** MAIN EFFECTS (Conditional)
- **Reason:** Full factorial is rank deficient due to structural missingness (biofilm formability failure for PVA=0 and Formulation F with Sorbitol).
- **Limitations:** Interpretations are strictly conditional. We cannot claim independent causal effects of CMC/PVA universally; findings apply ONLY to formulations capable of forming biofilms.

### Elongasi
- **Final model:** MAIN EFFECTS (Conditional)
- **Reason:** Full factorial is rank deficient due to structural missingness (biofilm formability failure for PVA=0 and Formulation F with Sorbitol).
- **Limitations:** Interpretations are strictly conditional. We cannot claim independent causal effects of CMC/PVA universally; findings apply ONLY to formulations capable of forming biofilms.

## 4. Overall Methodological Conclusion
The current ANOVA pipeline is statistically valid under a **Conditional Inferential Framework**. By falling back to Main Effects for downstream variables, we avoid attempting to estimate unidentifiable interactions (Rank Deficiency). However, researchers MUST NOT claim universal independent causal effects of CMC/PVA across all configurations. The analysis is structurally confounded with formulation viability. All conclusions must be strictly prefaced with: *'For formulations that successfully formed a biofilm...'*.
