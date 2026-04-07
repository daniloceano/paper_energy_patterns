"""
Exploratory Analysis: Intensification Phase Duration by Energy Pattern

Analyzes the duration of the intensification phase for each Energy Pattern (EP1, EP2, EP3).
Generates PDF distributions and statistics to understand temporal characteristics.

Outputs:
    - figures/exploratory/intensification_duration_pdf_by_ep.png
    - results/exploratory/intensification_duration_stats.csv

Author: Danilo Couto de Souza
Date: April 2026
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scripts.utils.ep_mapping import ALL_EPS, EP_LABELS, EP_COLORS, get_ep_label, get_ep_color

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results" / "ep_structure"
OUTPUT_DIR = PROJECT_ROOT / "results" / "exploratory"
FIGURES_DIR = PROJECT_ROOT / "figures" / "exploratory"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

DPI = 300


def load_ep_cases():
    """Load case files for all EPs."""
    ep_data = {}
    for ep_num in ALL_EPS:
        ep_label = get_ep_label(ep_num)
        case_file = RESULTS_DIR / f"{ep_label.lower()}_cases.csv"
        
        if not case_file.exists():
            print(f"⚠️  Warning: {case_file.name} not found")
            continue
        
        df = pd.read_csv(case_file)
        ep_data[ep_num] = df
        print(f"✓ Loaded {ep_label}: {len(df)} cases")
    
    return ep_data


def compute_duration_stats(ep_data):
    """
    Compute intensification duration statistics for each EP.
    
    Duration is calculated from the intensification_start and intensification_end
    timestamps in hours.
    """
    stats_list = []
    
    for ep_num in sorted(ep_data.keys()):
        df = ep_data[ep_num]
        ep_label = get_ep_label(ep_num)
        
        # Duration in hours (already computed in step1)
        durations = df['duration_hours'].values
        
        # Statistics
        stats_dict = {
            'ep': ep_label,
            'n_cases': len(durations),
            'mean_hours': np.mean(durations),
            'median_hours': np.median(durations),
            'std_hours': np.std(durations),
            'min_hours': np.min(durations),
            'max_hours': np.max(durations),
            'q25_hours': np.percentile(durations, 25),
            'q75_hours': np.percentile(durations, 75),
        }
        
        # Count cases < 12h and < 24h
        n_lt_12h = np.sum(durations < 12)
        n_lt_24h = np.sum(durations < 24)
        pct_lt_12h = 100 * n_lt_12h / len(durations)
        pct_lt_24h = 100 * n_lt_24h / len(durations)
        
        stats_dict['n_lt_12h'] = n_lt_12h
        stats_dict['pct_lt_12h'] = pct_lt_12h
        stats_dict['n_lt_24h'] = n_lt_24h
        stats_dict['pct_lt_24h'] = pct_lt_24h
        
        stats_list.append(stats_dict)
        
        # Print summary
        print(f"\n{ep_label} (n={len(durations)}):")
        print(f"  Duration: {stats_dict['median_hours']:.1f}h (median), "
              f"{stats_dict['mean_hours']:.1f}±{stats_dict['std_hours']:.1f}h (mean±std)")
        print(f"  Range: {stats_dict['min_hours']:.1f}–{stats_dict['max_hours']:.1f}h")
        print(f"  < 12 hours: {n_lt_12h} cases ({pct_lt_12h:.1f}%)")
        print(f"  < 24 hours: {n_lt_24h} cases ({pct_lt_24h:.1f}%)")
    
    return pd.DataFrame(stats_list)


def plot_duration_pdfs(ep_data):
    """
    Create PDF (probability density function) figure for intensification duration.
    
    Shows distributions for EP1, EP2, EP3 with median markers.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for ep_num in sorted(ep_data.keys()):
        df = ep_data[ep_num]
        ep_label = get_ep_label(ep_num)
        color = get_ep_color(ep_num)
        
        durations = df['duration_hours'].values
        median_dur = np.median(durations)
        
        # Compute KDE for smooth PDF
        kde = stats.gaussian_kde(durations)
        x_range = np.linspace(0, 120, 500)  # 0 to 120 hours
        pdf = kde(x_range)
        
        # Plot PDF
        ax.plot(x_range, pdf, color=color, linewidth=2.5, label=ep_label, alpha=0.9)
        
        # Mark median with vertical line
        ax.axvline(median_dur, color=color, linestyle='--', linewidth=1.5, alpha=0.7)
        
        # Annotate median
        y_max = pdf.max()
        ax.text(median_dur, y_max * 1.05, f'{median_dur:.1f}h', 
                ha='center', va='bottom', fontsize=9, color=color, fontweight='bold')
    
    ax.set_xlabel('Intensification Duration (hours)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Probability Density', fontsize=12, fontweight='bold')
    ax.set_title('Intensification Phase Duration by Energy Pattern', 
                 fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', framealpha=0.95, fontsize=11)
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax.set_xlim(0, 100)
    
    # Add reference lines
    ax.axvline(12, color='gray', linestyle=':', linewidth=1, alpha=0.5, label='12h')
    ax.axvline(24, color='gray', linestyle=':', linewidth=1, alpha=0.5, label='24h')
    
    plt.tight_layout()
    
    out_path = FIGURES_DIR / "intensification_duration_pdf_by_ep.png"
    fig.savefig(out_path, dpi=DPI, bbox_inches='tight')
    print(f"\n✓ Saved figure: {out_path.relative_to(PROJECT_ROOT)}")
    plt.close()


def main():
    print("=" * 70)
    print("EXPLORATORY ANALYSIS: INTENSIFICATION DURATION BY ENERGY PATTERN")
    print("=" * 70)
    print()
    
    # Load data
    print("1. Loading EP case files...")
    ep_data = load_ep_cases()
    
    if not ep_data:
        print("❌ No EP case files found. Run step1_select_ep_tracks.py first.")
        return
    
    print()
    print("2. Computing duration statistics...")
    stats_df = compute_duration_stats(ep_data)
    
    # Save statistics
    stats_path = OUTPUT_DIR / "intensification_duration_stats.csv"
    stats_df.to_csv(stats_path, index=False)
    print(f"\n✓ Saved statistics: {stats_path.relative_to(PROJECT_ROOT)}")
    
    print()
    print("3. Generating PDF figure...")
    plot_duration_pdfs(ep_data)
    
    print()
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print()
    print("Summary of cases with short intensification:")
    print()
    for _, row in stats_df.iterrows():
        print(f"  {row['ep']}: {int(row['n_lt_12h'])} cases < 12h ({row['pct_lt_12h']:.1f}%); "
              f"{int(row['n_lt_24h'])} cases < 24h ({row['pct_lt_24h']:.1f}%)")


if __name__ == "__main__":
    main()
