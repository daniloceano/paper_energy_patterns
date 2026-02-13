# Vertical Level Selection for EP1 Full Analysis

## Overview

This document explains the rationale for targeted pressure level selection in the EP1 full analysis pipeline.

## Preliminary Analysis

Based on **`ep1_ibc_ibt_analysis/step2_vertical_levels_analysis.py`**:

A comprehensive vertical profile analysis of ~94 EP1 cyclones from the Zenodo LEC dataset (DOI: 10.5281/zenodo.18243447) identified the critical levels where energy conversions are maximized:

### Key Findings

| Energy Term | Level | Physical Interpretation |
|-------------|-------|------------------------|
| **Maximum Ca** | **975 hPa** | Peak baroclinic conversion (temperature gradient × vertical wind shear) |
| **Minimum Ck** | **350 hPa** | Strongest barotropic depletion (vorticity transport by ageostrophic flow) |

**Note:** Ck minimum indicates where barotropic conversion is most **negative**, representing energy extraction from the kinetic energy reservoir.

## Selected Pressure Levels

### Purpose-Driven Level Selection

| Level (hPa) | Purpose | Required For |
|-------------|---------|--------------|
| **1000** | Lower boundary | Vertical derivative at 975 hPa |
| **975** | **Maximum Ca** | ✅ **Eady Growth Rate calculation** |
| **950** | Upper boundary | Vertical derivative at 975 hPa |
| **300** | Lower boundary | Vertical derivative at 350 hPa |
| **350** | **Minimum Ck** | ✅ **Potential Vorticity diagnostics** |
| **400** | Upper boundary | Vertical derivative at 350 hPa |
| **250** | Upper-level jet | ✅ **Plot overlays (PV contours, wind vectors)** |
| **msl** | Surface pressure | ✅ **Plot overlays (SLP contours)** |

**Total: 7 pressure levels + SLP**

### Comparison with Full Tropospheric Coverage

| Approach | Levels | Data Volume | Justification |
|----------|--------|-------------|---------------|
| **Full troposphere** | 14 levels | ~100-200 GB | Downloads unnecessary intermediate levels |
| **Targeted (this analysis)** | 7 levels | **~50-80 GB** | ✅ Includes only levels needed for diagnostics + visualization |

**Efficiency gain: ~50% reduction in data volume** ⚡

## Diagnostic Requirements

### Eady Growth Rate (EGR)

**Formula:**
$$\sigma_{EGR} = 0.31 \frac{|f|}{N} \left|\frac{\partial \vec{V}}{\partial z}\right|$$

**Computation at 975 hPa requires:**
- $|\partial \vec{V}/\partial z|$ → needs u, v at **950, 975, 1000 hPa**
- $N$ (Brunt-Väisälä frequency) → needs T at **950, 975, 1000 hPa**

### Potential Vorticity (PV)

**Computation at 350 hPa requires:**
- Relative vorticity: $\zeta$ from u, v at **350 hPa**
- Vertical derivative terms from **300, 350, 400 hPa**

### Rayleigh-Kuo Criterion

**Criterion:** $\partial(\zeta + f)/\partial y$ changes sign

**Computation at 350 hPa requires:**
- Relative vorticity: $\zeta$ from u, v at **350 hPa**
- Meridional gradient of absolute vorticity

## Visualization Requirements

### Modified Plots (see step5_create_figures.py)

**PV Composite Plots:**
- Shaded: PV at 975 hPa
- Green contours: PV at **250 hPa** (upper-level jet signature)
- Gray vectors: Wind at **250 hPa**

**EGR Composite Plots:**
- Shaded: EGR at 975 hPa
- Black contours: **SLP/MSLP** (cyclone center)
- Black vectors: Wind at 975 hPa

## Alternative: Why Not Download All Levels?

❌ **Disadvantages of full vertical coverage:**
1. **Storage inefficiency**: ~100-120 GB of unused data
2. **Download time**: ~2x longer with CDS API rate limits
3. **Computational overhead**: Processing unnecessary levels
4. **No diagnostic benefit**: Intermediate levels not used in analysis

✅ **Advantages of targeted selection:**
1. **Efficiency**: 50% reduction in storage and download time
2. **Focused**: Only levels that contribute to scientific analysis
3. **Validated**: Based on actual EP1 cyclone vertical structure
4. **Sufficient**: All necessary levels for diagnostics + visualization

## References

1. **Preliminary Analysis**: `ep1_ibc_ibt_analysis/step2_vertical_levels_analysis.py`
2. **Zenodo Dataset**: DOI 10.5281/zenodo.18243447
3. **Scientific Rationale**: `SCIENTIFIC_NOTES.md` Section 2.1-2.2

---

**Document prepared:** February 13, 2026  
**Author:** Danilo Couto de Souza
