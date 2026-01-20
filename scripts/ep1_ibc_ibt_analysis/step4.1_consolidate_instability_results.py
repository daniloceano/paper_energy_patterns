"""
Consolidate individual instability results into summary table.

Combines all *_instabilities.csv files into a single dataframe with
summary statistics for publication.
"""
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_DIR = BASE_DIR / "results" / "ep1_vertical" / "instabilities"
OUTPUT_DIR = BASE_DIR / "results" / "ep1_vertical"

print("\n" + "="*80)
print("CONSOLIDATING INSTABILITY RESULTS")
print("="*80)

# Load all individual files
files = sorted(INPUT_DIR.glob("*_instabilities.csv"))
print(f"\nFound {len(files)} result files")

df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
print(f"Combined data: {len(df)} cases\n")

# Save consolidated
output_file = OUTPUT_DIR / "instabilities_all.csv"
df.to_csv(output_file, index=False)
print(f"✓ Saved: {output_file}")

# Summary statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

print("\n--- Eady Growth Rate (day⁻¹) ---")
domain_sizes = {'local': 5, 'mesoscale': 15, 'synoptic': 30}
for domain in ['local', 'mesoscale', 'synoptic']:
    col_mean = f'egr_{domain}_mean'
    col_max = f'egr_{domain}_max'
    size = domain_sizes[domain]
    print(f"\n{domain.upper()} ({size}°):")
    print(f"  Mean EGR: {df[col_mean].mean():.3f} ± {df[col_mean].std():.3f} day⁻¹")
    print(f"  Range:    [{df[col_mean].min():.3f}, {df[col_mean].max():.3f}] day⁻¹")
    print(f"  Max EGR:  {df[col_max].mean():.3f} ± {df[col_max].std():.3f} day⁻¹")

print("\n--- Rayleigh-Kuo Criterion ---")
print("\n2D Field (full spatial structure):")
for domain in ['local', 'mesoscale', 'synoptic']:
    col = f'rk_{domain}_satisfied'
    n_satisfied = df[col].sum()
    pct = 100 * n_satisfied / len(df)
    print(f"  {domain:12s}: {n_satisfied}/{len(df)} cases ({pct:.0f}%)")

print("\nZonal Mean (meridional structure):")
for domain in ['local', 'mesoscale', 'synoptic']:
    col = f'rk_{domain}_satisfied_zonal'
    n_satisfied = df[col].sum()
    pct = 100 * n_satisfied / len(df)
    print(f"  {domain:12s}: {n_satisfied}/{len(df)} cases ({pct:.0f}%)")

print("\n--- Static Stability (Brunt-Väisälä, s⁻¹) ---")
for domain in ['local', 'mesoscale', 'synoptic']:
    col = f'N_{domain}'
    print(f"{domain:12s}: {df[col].mean():.4f} ± {df[col].std():.4f} s⁻¹")

print("\n--- Vertical Wind Shear (s⁻¹) ---")
for domain in ['local', 'mesoscale', 'synoptic']:
    col = f'shear_{domain}'
    print(f"{domain:12s}: {df[col].mean():.4f} ± {df[col].std():.4f} s⁻¹")

# Summary table for publication
summary = []
for domain in ['local', 'mesoscale', 'synoptic']:
    summary.append({
        'Domain': domain,
        'Domain_size_deg': {'local': 5, 'mesoscale': 15, 'synoptic': 30}[domain],
        'EGR_mean': df[f'egr_{domain}_mean'].mean(),
        'EGR_std': df[f'egr_{domain}_mean'].std(),
        'EGR_max_mean': df[f'egr_{domain}_max'].mean(),
        'N_mean': df[f'N_{domain}'].mean(),
        'Shear_mean': df[f'shear_{domain}'].mean(),
        'RK_2D_satisfied_pct': 100 * df[f'rk_{domain}_satisfied'].sum() / len(df),
        'RK_zonal_satisfied_pct': 100 * df[f'rk_{domain}_satisfied_zonal'].sum() / len(df)
    })

summary_df = pd.DataFrame(summary)
summary_file = OUTPUT_DIR / "instabilities_summary.csv"
summary_df.to_csv(summary_file, index=False)
print(f"\n✓ Summary table: {summary_file}")

print("\n" + "="*80 + "\n")
