anom = z_ep - z_all
anom = pct_ep - pct_all
dog = smooth_small - smooth_large
z_ep = zscore_normalize_positive(density_ep)
# Alternative Approaches to Visualize EP Relative Contribution

## Context

Figure 6 aims to highlight spatial regions where each Energy Pattern (EP)
contributes more or less to cyclone genesis relative to the overall climatology.
Challenges include:
- **EP3** dominates absolute frequency (62.7% of cyclones)
- Plotting absolute densities hides patterns for EP1 and EP2
- Dividing by the total density amplifies noise in low-density areas

## Implemented Approach: Min-Max Normalization

### Formula
```text
norm(x) = (x - min(x)) / (max(x) - min(x))  for x > 0
Δ_EP = norm(density_EP) - norm(density_All)
```

### Advantages
- Removes scale differences before comparison
- Preserves spatial structure
- Clear interpretation: negative/positive indicates under-/over-representation
- Robust to differences in EP frequency

### Disadvantages
- Loses absolute magnitude information
- Sensitive to outliers (min/max define the scale)
- Dimensionless (no physical units)

---

## Alternative Methods Considered

### 1. Z-Score Standardization

Normalize using mean and standard deviation:

```python
def zscore_normalize(arr):
    """Standardize to mean=0, std=1 for positive values"""
    pos = arr[arr > 0]
    if len(pos) == 0:
        return np.zeros_like(arr)
    mean = pos.mean()
    std = pos.std()
    out = np.zeros_like(arr)
    out[arr > 0] = (arr[arr > 0] - mean) / std
    return out

z_all = zscore_normalize(density_all)
z_ep = zscore_normalize(density_ep)
anom = z_ep - z_all
```

**Advantages:**
- Statistically grounded
- Indicates how many standard deviations a value is from the mean
- Useful to identify outliers

**Disadvantages:**
- Less intuitive interpretation than Min-Max
- Sensitive to non-Gaussian distributions

---

### 2. Fractional Weighted Anomaly

Accounts for the expected frequency of each EP:

```python
frac_ep = n_ep / n_total  # e.g., EP3 = 0.627

# Convert total density to a probability distribution
prob_all = density_all / density_all.sum()
prob_ep = density_ep / density_ep.sum()

# Fractional anomaly
anom = (prob_ep / prob_all) - frac_ep
```

**Advantages:**
- Considers expected frequency
- Values near zero indicate proportional distribution

**Disadvantages:**
- Division by small values can amplify noise

---

### 3. Kullback–Leibler (KL) Divergence

Pointwise KL measures the information divergence between EP and total:

```python
prob_all = density_all / density_all.sum()
prob_ep = density_ep / density_ep.sum()
epsilon = 1e-10
kl = prob_ep * np.log((prob_ep + epsilon) / (prob_all + epsilon))
```

**Advantages:**
- Theoretically founded in information theory

**Disadvantages:**
- Values are small and hard to visualize
- Interpretation is less intuitive for spatial maps

---

### 4. Rank-Based (Percentile) Normalization

Convert values to percentile ranks [0,1]:

```python
from scipy.stats import rankdata

def percentile_normalize(arr):
    out = np.zeros_like(arr)
    mask = arr > 0
    if np.any(mask):
        ranks = rankdata(arr[mask], method='average')
        out[mask] = (ranks - 1) / (len(ranks) - 1)
    return out

pct_all = percentile_normalize(density_all)
pct_ep = percentile_normalize(density_ep)
anom = pct_ep - pct_all
```

**Advantages:**
- Robust to extreme outliers

**Disadvantages:**
- Loses information about magnitude

---

### 5. Difference of Gaussians (DoG)

Spatial filter to highlight local structures:

```python
from scipy.ndimage import gaussian_filter
smooth_large = gaussian_filter(density_ep, sigma=2.0)
smooth_small = gaussian_filter(density_ep, sigma=0.5)
dog = smooth_small - smooth_large
```

**Advantages:**
- Highlights intermediate-scale features

**Disadvantages:**
- Requires choice of filter scales

---

### 6. Centered Log-Ratio (CLR)

Compositional transformation using geometric mean:

```python
stack = np.stack([d for d in densities_dict.values()], axis=0)
geom_mean = np.exp(np.mean(np.log(stack + epsilon), axis=0))
clr_ep = np.log((density_ep + epsilon) / (geom_mean + epsilon))
```

**Advantages:**
- Appropriate for compositional data

**Disadvantages:**
- Interpretation is more technical

---

## Summary Comparison

| Method | Interpretation | Robustness | Complexity | Recommendation |
|--------|----------------|-----------:|-----------:|---------------:|
| Min-Max | Intuitive | Low–Medium | Low | Recommended |
| Z-Score | Statistical | High | Medium | Alternative |
| Fractional | Frequency-aware | Low | Medium | Possible |
| KL | Information-theoretic | Medium | High | Not recommended |
| Percentile | Robust to outliers | High | Medium | Possible |
| DoG | Spatial filter | Medium | Medium | Complementary |
| CLR | Compositional | High | High | Specialized |

---

## Final Recommendation

Min-Max normalization is recommended for the main figure because it provides
an intuitive, publication-friendly visualization that highlights spatial
preferences independent of EP frequency. Use Z-Score as a supplemental
validation if statistical framing is desired.

---

## References

- Aitchison, J. (1986). The Statistical Analysis of Compositional Data.
- Hoskins, B. J., & Hodges, K. I. (2005). A new perspective on Southern Hemisphere storm tracks. Journal of Climate.
- Silverman, B. W. (1986). Density Estimation for Statistics and Data Analysis.

---

Author: Danilo Couto de Souza
Date: 12 February 2026
