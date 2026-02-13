# 🎯 Summary: Normalization Methods Comparison

## ✅ What Was Generated

Nine figures were created in:
`figures/exploratory/normalization_comparison/`

---

## 📊 Individual Figures (7 methods)

Each figure contains 4 panels: **(a) All Cyclones + (b) EP1 + (c) EP2 + (d) EP3**

### 1️⃣ Min-Max Normalization ⭐ **RECOMMENDED**
**File:** `1_minmax_genesis_density.png` (645 KB)  
**Range:** EP1: ±0.13 | EP2: ±0.36 | EP3: ±0.11  
**Interpretation:** Normalized difference on a 0–1 scale (intuitive)  
✅ **Best for the main figure**

### 2️⃣ Z-Score (Standardization) 📈 **ALSO RECOMMENDED**
**File:** `2_zscore_genesis_density.png` (611 KB)  
**Range:** EP1: ±3.04σ | EP2: ±5.35σ | EP3: ±2.14σ  
**Interpretation:** Deviations in standard-deviation units (statistical)  
✅ **Good for supplementary material**  
💡 **Insight:** EP2 shows the largest spatial variability (5.35σ)

### 3️⃣ Fractional Weighted Anomaly
**File:** `3_fractional_weighted_genesis_density.png` (597 KB)  
**Range:** EP1: ±2.39 | EP2: ±2.75 | EP3: ±0.71  
**Interpretation:** (P_EP / P_All) - expected_fraction

### 4️⃣ Kullback–Leibler Divergence
**File:** `4_kl_divergence_genesis_density.png` (619 KB)  
**Range:** very small values; hard to visualize

### 5️⃣ Rank-Based (Percentile)
**File:** `5_percentile_genesis_density.png` (688 KB)  
**Range:** compressed; patterns less visible

### 6️⃣ Difference of Gaussians
**File:** `6_dog_filter_genesis_density.png` (578 KB)  
**Range:** amplified; highlights spatial structure

### 7️⃣ CLR (Compositional Data)
**File:** `7_clr_compositional_genesis_density.png` (572 KB)  
**Range:** specialized interpretation

---

## 🔬 Comparative Figure (Side-by-side)

### Direct comparison: Min-Max vs Z-Score
**File:** `COMPARISON_minmax_vs_zscore.png` (1.16 MB)  
**Layout:** 3 rows × 2 columns (EP1, EP2, EP3)  
✅ **Use this to choose the preferred method**

**Notes:**
- Spatial patterns are identical between methods
- The only difference is the colorbar scale
- Min-Max: intuitive 0–1 scale; Z-Score: σ units

---

## 📋 Documentation Files

1. `README_comparison.txt` — brief summary
2. `ANALYSIS_RESULTS.md` — detailed analysis

---

## 🎯 Recommendation

### For the main manuscript figure (Fig. 6): 🏆 Min-Max

**Use:** `1_minmax_genesis_density.png`

**Why:**
1. Intuitive and easy to explain
2. Appropriate visual contrast
3. Accessible to a broad readership

### For supplementary material: 📊 Z-Score

**Why:**
- Adds statistical rigor and confirms robustness
- Highlights that **EP2 has larger spatial dispersion**

---

## 📊 Key Scientific Insight

### EP2 has the highest spatial variability

Evidence across methods:
- Min-Max range: 0.36
- Z-Score range: 5.35σ
- DoG: high spatial variability

**Interpretation:** EP2 (balanced energy conversions) arises in more varied
environmental contexts, while EP3 is concentrated in the primary hotspot.

---

## ✅ Immediate Actions

1. Visually inspect `1_minmax_genesis_density.png` and `COMPARISON_minmax_vs_zscore.png`.
2. Choose Min-Max for the main figure (optionally include Z-Score in Supplementary).
3. Regenerate Fig. 6 (script already updated):
```bash
source activate.sh
python scripts/main/06_figure_genesis_density_kde.py
```
4. Update manuscript text to note robustness across methods and the EP2 insight.

---

**Author:** Danilo Couto de Souza  
**Scripts:**
- `scripts/exploratory/figure_genesis_density_relative_kde.py`
- `scripts/exploratory/figure_minmax_vs_zscore_comparison.py`
