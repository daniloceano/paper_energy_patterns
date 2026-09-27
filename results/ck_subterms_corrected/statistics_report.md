# Ck subterms — statistics across Energy Patterns

Energy cache lineage: `/p1-swell/danilocs/paper_energy_patterns/data/corrected/energy_cache_corrected.parquet`

Sign convention: `C_K < 0` means K_Z -> K_E (the mean flow feeds the
eddy). The dominant subterm is the most negative one; cases in which
all five subterms are positive are reported separately.

## 1. Intensification-phase magnitudes

| Energy Pattern | term | mean (W m-2) | median | share of mean C_K |
|---|---|---|---|---|
| EP1 | Ck_total | -6.715 | -4.520 | — |
| EP1 | Ck_A | -3.814 | -3.032 | 56.8% |
| EP1 | Ck_B | -5.816 | -4.234 | 86.6% |
| EP1 | Ck_C | 0.386 | 0.328 | -5.8% |
| EP1 | Ck_D | 0.532 | 0.415 | -7.9% |
| EP1 | Ck_E | 1.996 | 1.625 | -29.7% |
| EP2 | Ck_total | 3.119 | 2.729 | — |
| EP2 | Ck_A | 0.042 | 0.109 | 1.4% |
| EP2 | Ck_B | 0.497 | 0.355 | 15.9% |
| EP2 | Ck_C | 0.486 | 0.391 | 15.6% |
| EP2 | Ck_D | 0.148 | 0.062 | 4.7% |
| EP2 | Ck_E | 1.946 | 1.645 | 62.4% |
| EP3 | Ck_total | -0.087 | 0.121 | — |
| EP3 | Ck_A | -0.357 | -0.138 | 410.2% |
| EP3 | Ck_B | -0.439 | -0.172 | 504.3% |
| EP3 | Ck_C | 0.190 | 0.134 | -217.9% |
| EP3 | Ck_D | 0.126 | 0.061 | -145.0% |
| EP3 | Ck_E | 0.393 | 0.299 | -451.6% |
| EPALL | Ck_total | -0.316 | 0.096 | — |
| EPALL | Ck_A | -0.763 | -0.282 | 241.5% |
| EPALL | Ck_B | -1.000 | -0.414 | 316.3% |
| EPALL | Ck_C | 0.285 | 0.202 | -90.1% |
| EPALL | Ck_D | 0.189 | 0.094 | -59.9% |
| EPALL | Ck_E | 0.973 | 0.588 | -307.8% |

## 2. Dominance during intensification

| Energy Pattern | Ck_A | Ck_B | Ck_C | Ck_D | Ck_E | None (all positive) |
|---|---|---|---|---|---|---|
| EP1 | 32.3% | 60.0% | 0.2% | 4.4% | 1.6% | 1.5% |
| EP2 | 20.3% | 32.4% | 0.5% | 32.7% | 3.0% | 11.0% |
| EP3 | 28.2% | 32.5% | 0.5% | 23.5% | 8.4% | 6.9% |
| EPALL | 27.0% | 36.4% | 0.5% | 22.8% | 6.2% | 7.0% |

## 3. Energy Pattern contrasts (intensification)

Benjamini-Hochberg FDR at q = 0.05, family = all pairwise tests
of the phase. Effect size is the rank-biserial correlation.

| subterm | contrast | median left | median right | p (FDR) | effect | magnitude |
|---|---|---|---|---|---|---|
| Ck_A | EP1 vs EP2 | -3.032 | 0.109 | **1.68e-74** | -0.578 | large |
| Ck_A | EP1 vs EP3 | -3.032 | -0.138 | **1.89e-106** | -0.600 | large |
| Ck_A | EP2 vs EP3 | 0.109 | -0.138 | **3.81e-05** | +0.095 | negligible |
| Ck_B | EP1 vs EP2 | -4.234 | 0.355 | **5.1e-81** | -0.603 | large |
| Ck_B | EP1 vs EP3 | -4.234 | -0.172 | **1.77e-127** | -0.658 | large |
| Ck_B | EP2 vs EP3 | 0.355 | -0.172 | **1.67e-07** | +0.121 | small |
| Ck_C | EP1 vs EP2 | 0.328 | 0.391 | **5.92e-06** | -0.144 | small |
| Ck_C | EP1 vs EP3 | 0.328 | 0.134 | **2.46e-34** | +0.335 | medium |
| Ck_C | EP2 vs EP3 | 0.391 | 0.134 | **6.48e-107** | +0.505 | large |
| Ck_D | EP1 vs EP2 | 0.415 | 0.062 | **6.59e-14** | +0.238 | small |
| Ck_D | EP1 vs EP3 | 0.415 | 0.061 | **1.13e-23** | +0.275 | small |
| Ck_D | EP2 vs EP3 | 0.062 | 0.061 | 0.821 | -0.005 | negligible |
| Ck_E | EP1 vs EP2 | 1.625 | 1.645 | 0.755 | +0.012 | negligible |
| Ck_E | EP1 vs EP3 | 1.625 | 0.299 | **8.27e-133** | +0.672 | large |
| Ck_E | EP2 vs EP3 | 1.645 | 0.299 | **5.15e-181** | +0.660 | large |
