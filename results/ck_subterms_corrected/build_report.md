# Ck subterms — build report

Source profiles: `/p1-swell/danilocs/paper_energy_patterns/data/corrected/vertical_phase_means_corrected_partial.parquet`
Energy cache lineage: `data/energy_cache.parquet (LEGACY - superseded)`

## Coverage

| Energy Pattern | cyclones | rows (cyclone x phase) |
|---|---|---|
| EP1 | 92 | 368 |
| EP2 | 176 | 704 |
| EP3 | 532 | 2128 |
| **all** | **800** | **3200** |

## Validation

- Worst relative closure residual `|sum(Ck_i) - Ck| / |Ck|`: 3.127e-10
- Tolerance: 1e-06
- Verdict: PASS

## Dominant subterm during intensification

| Energy Pattern | Ck_A | Ck_B | Ck_C | Ck_D | Ck_E |
|---|---|---|---|---|---|
| EP1 | 29.3% | 58.7% | 1.1% | 9.8% | 1.1% |
| EP2 | 23.9% | 40.3% | 3.4% | 29.0% | 3.4% |
| EP3 | 28.0% | 28.6% | 3.0% | 31.0% | 9.4% |
