# Ck subterms — statistics across Energy Patterns

Energy cache lineage: `data/energy_cache.parquet (LEGACY - superseded)`

Sign convention: `C_K < 0` means K_Z -> K_E (the mean flow feeds the
eddy). The dominant subterm is the most negative one.

## 1. Intensification-phase magnitudes

| Energy Pattern | term | mean (W m-2) | median | share of mean C_K |
|---|---|---|---|---|
| EP1 | Ck_total | -6.092 | -4.605 | — |
| EP1 | Ck_A | -3.764 | -2.471 | 61.8% |
| EP1 | Ck_B | -5.420 | -4.231 | 89.0% |
| EP1 | Ck_C | 0.353 | 0.295 | -5.8% |
| EP1 | Ck_D | 0.646 | 0.392 | -10.6% |
| EP1 | Ck_E | 2.093 | 1.639 | -34.3% |
| EP2 | Ck_total | 2.042 | 1.190 | — |
| EP2 | Ck_A | -0.324 | -0.332 | -15.9% |
| EP2 | Ck_B | -0.318 | -0.689 | -15.6% |
| EP2 | Ck_C | 0.490 | 0.411 | 24.0% |
| EP2 | Ck_D | 0.254 | 0.116 | 12.5% |
| EP2 | Ck_E | 1.939 | 1.620 | 95.0% |
| EP3 | Ck_total | 0.549 | 0.304 | — |
| EP3 | Ck_A | -0.093 | 0.009 | -16.8% |
| EP3 | Ck_B | 0.040 | -0.008 | 7.2% |
| EP3 | Ck_C | 0.197 | 0.131 | 36.0% |
| EP3 | Ck_D | 0.061 | 0.001 | 11.1% |
| EP3 | Ck_E | 0.343 | 0.282 | 62.5% |
| EPALL | Ck_total | 0.114 | 0.239 | — |
| EPALL | Ck_A | -0.566 | -0.176 | -497.3% |
| EPALL | Ck_B | -0.667 | -0.207 | -586.1% |
| EPALL | Ck_C | 0.280 | 0.205 | 245.9% |
| EPALL | Ck_D | 0.171 | 0.058 | 150.3% |
| EPALL | Ck_E | 0.895 | 0.539 | 787.2% |

## 2. Dominance during intensification

| Energy Pattern | Ck_A | Ck_B | Ck_C | Ck_D | Ck_E |
|---|---|---|---|---|---|
| EP1 | 29.3% | 58.7% | 1.1% | 9.8% | 1.1% |
| EP2 | 23.9% | 40.3% | 3.4% | 29.0% | 3.4% |
| EP3 | 28.0% | 28.6% | 3.0% | 31.0% | 9.4% |
| EPALL | 27.3% | 34.6% | 2.9% | 28.1% | 7.1% |

## 3. Energy Pattern contrasts (intensification)

Benjamini-Hochberg FDR at q = 0.05, family = all pairwise tests
of the phase. Effect size is the rank-biserial correlation.

| subterm | contrast | median left | median right | p (FDR) | effect | magnitude |
|---|---|---|---|---|---|---|
| Ck_A | EP1 vs EP2 | -2.471 | -0.332 | **5.73e-10** | -0.470 | medium |
| Ck_A | EP1 vs EP3 | -2.471 | 0.009 | **6.22e-19** | -0.588 | large |
| Ck_A | EP2 vs EP3 | -0.332 | 0.009 | 0.16 | -0.072 | negligible |
| Ck_B | EP1 vs EP2 | -4.231 | -0.689 | **2e-12** | -0.533 | large |
| Ck_B | EP1 vs EP3 | -4.231 | -0.008 | **2.54e-27** | -0.716 | large |
| Ck_B | EP2 vs EP3 | -0.689 | -0.008 | 0.0602 | -0.098 | negligible |
| Ck_C | EP1 vs EP2 | 0.295 | 0.411 | **0.0036** | -0.224 | small |
| Ck_C | EP1 vs EP3 | 0.295 | 0.131 | **2.62e-06** | +0.313 | medium |
| Ck_C | EP2 vs EP3 | 0.411 | 0.131 | **3.71e-25** | +0.527 | large |
| Ck_D | EP1 vs EP2 | 0.392 | 0.116 | **0.003** | +0.230 | small |
| Ck_D | EP1 vs EP3 | 0.392 | 0.001 | **9.85e-09** | +0.381 | medium |
| Ck_D | EP2 vs EP3 | 0.116 | 0.001 | **0.00866** | +0.136 | small |
| Ck_E | EP1 vs EP2 | 1.639 | 1.620 | 0.543 | +0.045 | negligible |
| Ck_E | EP1 vs EP3 | 1.639 | 0.282 | **2.92e-29** | +0.744 | large |
| Ck_E | EP2 vs EP3 | 1.620 | 0.282 | **4.98e-46** | +0.725 | large |
