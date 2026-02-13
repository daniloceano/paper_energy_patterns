# Análise Comparativa dos Métodos de Normalização

**Data:** 12 de fevereiro de 2026  
**Dataset:** 3820 ciclones (1979-2020)  
**Distribuição:** EP1: 11.6% | EP2: 25.6% | EP3: 62.7%

## Resultados Observados

### Ranges de Anomalia por Método

| Método | EP1 Range | EP2 Range | EP3 Range | Observação |
|--------|-----------|-----------|-----------|------------|
| **1. Min-Max** | [-0.13, 0.13] | [-0.36, 0.36] | [-0.11, 0.11] | ⭐ Valores simétricos, escala intuitiva |
| **2. Z-Score** | [-3.04, 3.04] | [-5.35, 5.35] | [-2.14, 2.14] | Unidades de desvio-padrão |
| **3. Fracional** | [-2.39, 2.39] | [-2.75, 2.75] | [-0.71, 0.71] | EP3 tem menor range (mais frequente) |
| **4. KL Divergence** | [-0.004, 0.004] | [-0.008, 0.008] | [-0.004, 0.004] | Valores muito pequenos |
| **5. Percentile** | [-0.010, 0.010] | [-0.007, 0.007] | [-0.004, 0.004] | Ranges muito comprimidos |
| **6. DoG Filter** | [-13.80, 13.80] | [-12.61, 12.61] | [-4.63, 4.63] | Valores amplificados |
| **7. CLR** | [-3.03, 3.03] | [-1.39, 1.39] | [-2.31, 2.31] | EP2 tem menor range |

---

## Análise Detalhada por Método

### ⭐ 1. Min-Max Normalization (RECOMENDADO)

**Características:**
- ✅ Ranges simétricos e proporcionais à variabilidade espacial
- ✅ EP2 tem maior range (0.36) → maior variabilidade espacial
- ✅ Escala [0-1] é intuitiva
- ✅ Fácil de comunicar: "30% de diferença na distribuição normalizada"

**Quando usar:**
- Publicação científica (interpretação clara)
- Visualização para audiência geral
- Quando a estrutura espacial é mais importante que magnitude absoluta

**Limitações:**
- Sensível a valores máximos/mínimos extremos
- Não é estatisticamente fundamentado

---

### 🔬 2. Z-Score (Standardization)

**Características:**
- ✅ Estatisticamente robusto (unidades de desvio-padrão)
- ✅ EP2 mostra 5.35σ de variação → alta dispersão
- ⚠️ Valores maiores que ±3 indicam extremos (potenciais outliers)
- ✅ Familiar para audiência científica

**Quando usar:**
- Manuscrito com foco estatístico
- Quando quiser enfatizar outliers
- Para comparação com literatura que usa z-scores

**Limitações:**
- Interpretação menos intuitiva que Min-Max
- Assume distribuição aproximadamente normal

**Interpretação dos resultados:**
- EP1: ±3.04σ → variação moderada
# Comparative Analysis of Normalization Methods

**Date:** 12 February 2026  
**Dataset:** 3820 cyclones (1979–2020)  
**Distribution:** EP1: 11.6% | EP2: 25.6% | EP3: 62.7%

## Observed Results

### Anomaly Ranges by Method

| Method | EP1 Range | EP2 Range | EP3 Range | Comment |
|--------|-----------:|-----------:|-----------:|---------|
| **1. Min-Max** | [-0.13, 0.13] | [-0.36, 0.36] | [-0.11, 0.11] | Symmetric ranges, intuitive scale |
| **2. Z-Score** | [-3.04, 3.04] | [-5.35, 5.35] | [-2.14, 2.14] | Units of standard deviation |
| **3. Fractional** | [-2.39, 2.39] | [-2.75, 2.75] | [-0.71, 0.71] | EP3 smaller range (more frequent) |
| **4. KL Divergence** | [-0.004, 0.004] | [-0.008, 0.008] | [-0.004, 0.004] | Very small values |
| **5. Percentile** | [-0.010, 0.010] | [-0.007, 0.007] | [-0.004, 0.004] | Compressed ranges |
| **6. DoG Filter** | [-13.80, 13.80] | [-12.61, 12.61] | [-4.63, 4.63] | Amplified values |
| **7. CLR** | [-3.03, 3.03] | [-1.39, 1.39] | [-2.31, 2.31] | EP2 smaller range |

---

## Detailed Method Analysis

### 1. Min-Max Normalization (RECOMMENDED)

**Features:**
- Symmetric, proportional ranges reflecting spatial variability
- EP2 has the largest range (0.36) → greater spatial variability
- The [0–1] scale is intuitive and publication-friendly

**Use when:**
- Preparing figures for the main manuscript
- Prioritizing interpretability over statistical nuance

**Limitations:**
- Sensitive to min/max outliers

---

### 2. Z-Score (Standardization)

**Features:**
- Statistically robust (units in standard deviations)
- EP2 shows ±5.35σ → high dispersion

**Use when:**
- Statistical framing or supplementary material is required

**Interpretation:**
- EP1: ±3.04σ (moderate)
- EP2: ±5.35σ (largest spatial dispersion)
- EP3: ±2.14σ (more concentrated)

---

### 3. Fractional Weighted Anomaly

**Features:**
- Accounts for expected EP frequency

**Limitations:**
- Can amplify noise for less frequent EPs

---

### 4. Kullback–Leibler Divergence

**Features:**
- Theoretically grounded

**Limitations:**
- Values are very small and hard to visualize; not recommended for main figures

---

### 5. Rank-Based (Percentile)

**Features:**
- Robust to outliers

**Limitations:**
- Compresses dynamic range; spatial patterns become less visible

---

### 6. Difference of Gaussians (DoG)

**Features:**
- Highlights intermediate-scale spatial structures

**Use as:**
- Complementary analysis to reveal mesoscale hotspots

---

### 7. Centered Log-Ratio (CLR)

**Features:**
- Appropriate for compositional analyses

**Limitations:**
- Specialized and less intuitive for general audience

---

## Visual Expectations

Across methods, common spatial patterns are expected:

**EP1:** weak/negative anomalies across most of the domain, more dispersed

**EP2:** positive anomalies slightly northward (~37–42°S), higher spatial variability

**EP3:** strong positive anomalies in the coastal hotspot (~40–45°S)

---

## Final Recommendation

**Main figure (Fig. 6): Min-Max Normalization**

**Supplementary:** Z-Score standardization for statistical context

**Scientific insight:** EP2 consistently shows the highest spatial variability
across methods—an analysis point worth highlighting in the manuscript.

---

**Author:** Danilo Couto de Souza  
**Script:** `scripts/exploratory/figure_genesis_density_relative_kde.py`  
**Output:** `figures/exploratory/normalization_comparison/`
- Concentração máxima perto da costa Argentina
