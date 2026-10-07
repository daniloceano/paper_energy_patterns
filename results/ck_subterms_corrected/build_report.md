# Ck subterms — build report

Source profiles: `/p1-swell/danilocs/paper_energy_patterns/data/corrected/vertical_phase_means_corrected.parquet`
Energy cache lineage: `/p1-swell/danilocs/paper_energy_patterns/data/corrected/energy_cache_corrected.parquet`

## Coverage

| Energy Pattern | cyclones | rows (cyclone x phase) |
|---|---|---|
| EP1 | 548 | 2192 |
| EP2 | 860 | 3440 |
| EP3 | 2412 | 9648 |
| **all** | **3820** | **15280** |

## Validation

- Worst relative closure residual `|sum(Ck_i) - Ck| / |Ck|`: 3.127e-10
- Tolerance: 1e-06
- Verdict: PASS

## Dominant subterm during intensification

| Energy Pattern | Ck_A | Ck_B | Ck_C | Ck_D | Ck_E | None (all positive) |
|---|---|---|---|---|---|---|
| EP1 | 32.3% | 60.0% | 0.2% | 4.4% | 1.6% | 1.5% |
| EP2 | 20.3% | 32.4% | 0.5% | 32.7% | 3.0% | 11.0% |
| EP3 | 28.2% | 32.5% | 0.5% | 23.5% | 8.4% | 6.9% |
