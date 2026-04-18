"""
Statistical significance testing utilities for inter-EP comparisons.

Implements a documented decision tree for variable-by-variable testing
of whether EP1, EP2, and EP3 differ:

    1. Normality check  → Shapiro-Wilk per group
    2. Homogeneity      → Levene (center='median')
    3. Global test      → ANOVA / Welch ANOVA / Kruskal-Wallis
    4. Post-hoc         → Tukey HSD / Welch t-tests / Dunn
    5. Effect size      → eta²/omega² (parametric), epsilon² (non-param)
    6. Multiple-comp    → Holm or Benjamini-Hochberg (via statsmodels)

Dunn's test is implemented from scratch following Dunn (1964) because
``scikit_posthocs`` is not available in the current environment.

Author: Danilo Couto de Souza
Date: April 2026
"""

import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from scipy.stats import rankdata
from statsmodels.stats.multitest import multipletests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ALPHA = 0.05
MIN_SAMPLE_SIZE = 8         # Minimum per-group N to proceed
SHAPIRO_MAX_N = 5000        # scipy.stats.shapiro practical limit


# ===================================================================
# 1. NORMALITY
# ===================================================================

def test_normality_group(x: np.ndarray, alpha: float = ALPHA) -> dict:
    """
    Shapiro-Wilk test for one group.

    For N > SHAPIRO_MAX_N a random subsample of size SHAPIRO_MAX_N
    is used, with a documented caution that Shapiro-Wilk almost
    always rejects for large samples regardless of actual normality.

    Returns
    -------
    dict with keys: statistic, p_value, is_normal, n, note
    """
    x = x[np.isfinite(x)]
    n = len(x)

    if n < 3:
        return dict(statistic=np.nan, p_value=np.nan, is_normal=False,
                     n=n, note=f"n={n} < 3, insufficient")
    if np.ptp(x) == 0:
        return dict(statistic=np.nan, p_value=np.nan, is_normal=False,
                     n=n, note="zero variance (constant)")

    if n > SHAPIRO_MAX_N:
        rng = np.random.default_rng(42)
        x_sub = rng.choice(x, size=SHAPIRO_MAX_N, replace=False)
        stat, p = stats.shapiro(x_sub)
        return dict(
            statistic=float(stat), p_value=float(p),
            is_normal=p > alpha, n=n,
            note=(f"Subsampled to {SHAPIRO_MAX_N} (original n={n}). "
                  "Shapiro-Wilk over-rejects at large N; interpret cautiously."),
        )

    stat, p = stats.shapiro(x)
    return dict(statistic=float(stat), p_value=float(p),
                is_normal=p > alpha, n=n, note="")


def test_normality_groups(groups: List[np.ndarray],
                          labels: List[str],
                          alpha: float = ALPHA) -> List[dict]:
    """Run normality tests on every group and attach the label."""
    results = []
    for g, lab in zip(groups, labels):
        res = test_normality_group(g, alpha=alpha)
        res["group"] = lab
        results.append(res)
    return results


# ===================================================================
# 2. HOMOGENEITY OF VARIANCE
# ===================================================================

def test_homogeneity(groups: List[np.ndarray],
                     alpha: float = ALPHA) -> dict:
    """
    Levene's test with center='median' (Brown-Forsythe variant).

    Returns dict with: statistic, p_value, is_homogeneous, note
    """
    clean = [g[np.isfinite(g)] for g in groups]
    if any(len(g) < 2 for g in clean):
        return dict(statistic=np.nan, p_value=np.nan,
                    is_homogeneous=False,
                    note="Insufficient data in ≥1 group")
    stat, p = stats.levene(*clean, center="median")
    return dict(statistic=float(stat), p_value=float(p),
                is_homogeneous=p > alpha, note="")


# ===================================================================
# 3. GLOBAL TESTS
# ===================================================================

def _one_way_anova(groups: List[np.ndarray]) -> dict:
    clean = [g[np.isfinite(g)] for g in groups]
    stat, p = stats.f_oneway(*clean)
    return dict(test_name="One-way ANOVA", statistic=float(stat),
                p_value=float(p))


def _welch_anova(groups: List[np.ndarray]) -> dict:
    """
    Welch's ANOVA F* (Welch 1951).

    Unlike classic ANOVA, does not assume equal variances.
    """
    clean = [g[np.isfinite(g)] for g in groups]
    k = len(clean)
    ns = np.array([len(g) for g in clean], dtype=float)
    means = np.array([np.mean(g) for g in clean])
    variances = np.array([np.var(g, ddof=1) for g in clean])

    # Guard against zero-variance groups
    variances = np.where(variances == 0, 1e-30, variances)

    w = ns / variances
    W = w.sum()
    X_w = (w * means).sum() / W

    # F* numerator
    numerator = (w * (means - X_w) ** 2).sum() / (k - 1)

    # Lambda correction
    Lambda = ((1 - w / W) ** 2 / (ns - 1)).sum()

    denominator = 1 + 2 * (k - 2) / (k ** 2 - 1) * Lambda
    F_star = numerator / denominator

    df1 = k - 1
    df2 = (k ** 2 - 1) / (3 * Lambda) if Lambda > 0 else np.inf
    p = 1 - stats.f.cdf(F_star, df1, df2) if np.isfinite(df2) else np.nan

    return dict(test_name="Welch ANOVA", statistic=float(F_star),
                p_value=float(p), df1=df1, df2=float(df2))


def _kruskal_wallis(groups: List[np.ndarray]) -> dict:
    clean = [g[np.isfinite(g)] for g in groups]
    stat, p = stats.kruskal(*clean)
    return dict(test_name="Kruskal-Wallis", statistic=float(stat),
                p_value=float(p))


# ===================================================================
# 4. EFFECT SIZES — GLOBAL
# ===================================================================

def _eta_squared(groups: List[np.ndarray]) -> float:
    """η² = SS_between / SS_total."""
    clean = [g[np.isfinite(g)] for g in groups]
    all_vals = np.concatenate(clean)
    grand_mean = np.mean(all_vals)
    ss_total = ((all_vals - grand_mean) ** 2).sum()
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in clean)
    return float(ss_between / ss_total) if ss_total > 0 else 0.0


def _omega_squared(groups: List[np.ndarray]) -> float:
    """ω² — less biased estimator of explained variance."""
    clean = [g[np.isfinite(g)] for g in groups]
    all_vals = np.concatenate(clean)
    N = len(all_vals)
    k = len(clean)
    grand_mean = np.mean(all_vals)
    ss_total = ((all_vals - grand_mean) ** 2).sum()
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in clean)
    ms_within = (ss_total - ss_between) / (N - k) if N > k else 0
    omega2 = (ss_between - (k - 1) * ms_within) / (ss_total + ms_within)
    return float(max(0.0, omega2))


def _epsilon_squared_kw(H: float, N: int, k: int) -> float:
    """
    ε² for Kruskal-Wallis.

    ε² = (H − k + 1) / (N − k)

    Interpretation (Rea & Parker 1992):
      negligible < 0.01 < small < 0.06 < medium < 0.14 < large
    """
    denom = N - k
    return float(max(0.0, (H - k + 1) / denom)) if denom > 0 else 0.0


# ===================================================================
# 5. POST-HOC: Tukey HSD
# ===================================================================

def _tukey_hsd(groups: List[np.ndarray],
               labels: List[str]) -> List[dict]:
    """Tukey HSD via ``scipy.stats.tukey_hsd``."""
    clean = [g[np.isfinite(g)] for g in groups]
    result = stats.tukey_hsd(*clean)

    pairs = []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            p_val = float(result.pvalue[i][j])
            stat_val = float(result.statistic[i][j])
            d = _cohens_d(clean[i], clean[j])
            direction = _direction_str(clean[i], clean[j], labels[i], labels[j])

            pairs.append(dict(
                contrast=f"{labels[i]} vs {labels[j]}",
                test_name="Tukey HSD",
                statistic=stat_val,
                p_value_raw=p_val,
                p_value_adjusted=p_val,      # Tukey already controls FWER
                effect_size=d,
                effect_size_name="Cohen's d",
                mean_1=float(np.mean(clean[i])),
                mean_2=float(np.mean(clean[j])),
                median_1=float(np.median(clean[i])),
                median_2=float(np.median(clean[j])),
                direction=direction,
                n_1=len(clean[i]),
                n_2=len(clean[j]),
            ))
    return pairs


# ===================================================================
# 6. POST-HOC: Pairwise Welch t-tests (Games-Howell substitute)
# ===================================================================

def _welch_t_posthoc(groups: List[np.ndarray],
                     labels: List[str],
                     correction: str = "holm") -> List[dict]:
    """
    Pairwise Welch t-tests with Holm correction.

    Used as post-hoc after Welch ANOVA when ``pingouin`` (Games-Howell)
    is not available.  Methodologically equivalent when combined with
    a familywise-error-rate correction.
    """
    clean = [g[np.isfinite(g)] for g in groups]
    raw_pvals: List[float] = []
    pair_results: List[dict] = []

    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            t_stat, p_val = stats.ttest_ind(
                clean[i], clean[j], equal_var=False)
            d = _cohens_d(clean[i], clean[j])
            direction = _direction_str(clean[i], clean[j],
                                       labels[i], labels[j])

            raw_pvals.append(float(p_val))
            pair_results.append(dict(
                contrast=f"{labels[i]} vs {labels[j]}",
                test_name="Welch t-test (Holm)",
                statistic=float(t_stat),
                p_value_raw=float(p_val),
                p_value_adjusted=np.nan,     # filled below
                effect_size=d,
                effect_size_name="Cohen's d",
                mean_1=float(np.mean(clean[i])),
                mean_2=float(np.mean(clean[j])),
                median_1=float(np.median(clean[i])),
                median_2=float(np.median(clean[j])),
                direction=direction,
                n_1=len(clean[i]),
                n_2=len(clean[j]),
            ))

    if raw_pvals:
        _, adj, _, _ = multipletests(raw_pvals, method=correction)
        for k, res in enumerate(pair_results):
            res["p_value_adjusted"] = float(adj[k])

    return pair_results


# ===================================================================
# 7. POST-HOC: Dunn test (after Kruskal-Wallis)
# ===================================================================

def _dunn_test(groups: List[np.ndarray],
               labels: List[str],
               correction: str = "holm") -> List[dict]:
    """
    Dunn's test for pairwise comparisons after Kruskal-Wallis.

    Implemented from Dunn (1964) with tie adjustment.

    Steps
    -----
    1. Rank all observations jointly (average ties).
    2. For each pair (i, j):
       z = (R̄_i − R̄_j) / σ_ij
       σ_ij = sqrt( [N(N+1)/12  −  Σ(t³−t)/(12(N−1))] × (1/n_i + 1/n_j) )
    3. Two-tailed p-value from standard normal.
    4. Correction via Holm (default) or BH.

    Effect size: rank-biserial r via Mann-Whitney U.
    """
    clean = [g[np.isfinite(g)] for g in groups]
    all_data = np.concatenate(clean)
    N = len(all_data)

    ranks = rankdata(all_data, method="average")

    # Split ranks back
    group_ranks: List[np.ndarray] = []
    idx = 0
    for g in clean:
        n = len(g)
        group_ranks.append(ranks[idx : idx + n])
        idx += n

    # Tie correction
    _, counts = np.unique(ranks, return_counts=True)
    tie_adj = (counts ** 3 - counts).sum() / (12 * (N - 1)) if N > 1 else 0
    sigma_base = N * (N + 1) / 12 - tie_adj

    raw_pvals: List[float] = []
    pair_results: List[dict] = []

    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            ni, nj = len(clean[i]), len(clean[j])
            Ri = group_ranks[i].mean()
            Rj = group_ranks[j].mean()
            se = np.sqrt(sigma_base * (1 / ni + 1 / nj))
            z = (Ri - Rj) / se if se > 0 else 0.0
            p_val = float(2 * stats.norm.sf(abs(z)))

            # Rank-biserial r = 1 − 2U/(n1*n2)
            U, _ = stats.mannwhitneyu(
                clean[i], clean[j], alternative="two-sided")
            r_rb = float(1 - 2 * U / (ni * nj))

            diff_med = float(np.median(clean[i]) - np.median(clean[j]))
            direction = _direction_str(clean[i], clean[j],
                                       labels[i], labels[j],
                                       use_median=True)

            raw_pvals.append(p_val)
            pair_results.append(dict(
                contrast=f"{labels[i]} vs {labels[j]}",
                test_name="Dunn",
                statistic=float(z),
                p_value_raw=p_val,
                p_value_adjusted=np.nan,
                effect_size=r_rb,
                effect_size_name="rank-biserial r",
                mean_1=float(np.mean(clean[i])),
                mean_2=float(np.mean(clean[j])),
                median_1=float(np.median(clean[i])),
                median_2=float(np.median(clean[j])),
                direction=direction,
                n_1=ni,
                n_2=nj,
            ))

    if raw_pvals:
        _, adj, _, _ = multipletests(raw_pvals, method=correction)
        for k, res in enumerate(pair_results):
            res["p_value_adjusted"] = float(adj[k])

    return pair_results


# ===================================================================
# HELPERS
# ===================================================================

def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Pooled-variance Cohen's d."""
    na, nb = len(a), len(b)
    var_a, var_b = np.var(a, ddof=1), np.var(b, ddof=1)
    pooled = np.sqrt(((na - 1) * var_a + (nb - 1) * var_b) / (na + nb - 2))
    return float((np.mean(a) - np.mean(b)) / pooled) if pooled > 0 else 0.0


def _direction_str(a: np.ndarray, b: np.ndarray,
                   lab_a: str, lab_b: str,
                   use_median: bool = False) -> str:
    """'EP1 > EP2' style string based on mean or median."""
    if use_median:
        va, vb = np.median(a), np.median(b)
    else:
        va, vb = np.mean(a), np.mean(b)
    return f"{lab_a} > {lab_b}" if va > vb else f"{lab_b} > {lab_a}"


# ===================================================================
# MAIN ENTRY POINT: FULL DECISION TREE
# ===================================================================

def run_decision_tree(groups: List[np.ndarray],
                      labels: List[str],
                      alpha: float = ALPHA) -> dict:
    """
    Execute the full diagnostic decision tree for one variable.

    Parameters
    ----------
    groups : list of 1-D arrays
        One array per EP (already filtered, may contain NaN).
    labels : list of str
        Group names, same order as *groups* (e.g. ["EP1", "EP2", "EP3"]).
    alpha : float
        Significance level.

    Returns
    -------
    dict with keys:
        normality        — list of per-group normality dicts
        homogeneity      — dict
        global_test      — dict
        global_effect    — dict (name, value)
        pairwise         — list of pairwise result dicts
        decision         — str summarising the outcome
        notes            — list of str
    """
    clean = [g[np.isfinite(g)] for g in groups]
    k = len(clean)
    ns = [len(g) for g in clean]
    N = sum(ns)
    notes: List[str] = []

    # --- Degenerate checks ---
    if any(n < MIN_SAMPLE_SIZE for n in ns):
        return _degenerate_result(
            groups, labels, ns,
            f"At least one group has n < {MIN_SAMPLE_SIZE}; skipping.")

    if any(np.ptp(g) == 0 for g in clean):
        return _degenerate_result(
            groups, labels, ns,
            "At least one group has zero variance (constant); skipping.")

    # --- 1. Normality ---
    normality = test_normality_groups(groups, labels, alpha=alpha)
    all_normal = all(r["is_normal"] for r in normality)

    # Large-sample caveat
    for r in normality:
        if r["n"] > 500 and not r["is_normal"]:
            notes.append(
                f"{r['group']}: n={r['n']}; Shapiro-Wilk may over-reject "
                "at large N.  Visual QQ inspection recommended.")

    # Flag when all groups are large
    if all(n > 500 for n in ns):
        notes.append(
            "All groups have N > 500.  Shapiro-Wilk is overpowered; "
            "minor deviations from normality are detected regardless "
            "of practical relevance.  The non-parametric route is "
            "used conservatively, but ANOVA is generally robust at "
            "these sample sizes via the CLT.")

    # --- 2. Homogeneity ---
    homogeneity = test_homogeneity(groups, alpha=alpha)

    # --- 3 & 4.  Select global test + post-hoc ---
    if all_normal and homogeneity["is_homogeneous"]:
        # Classic ANOVA → Tukey HSD
        global_test = _one_way_anova(groups)
        global_test["decision_path"] = ("Normal + homogeneous variances "
                                        "→ One-way ANOVA")
        effect = dict(name="omega²", value=_omega_squared(groups))
        pairwise = (_tukey_hsd(groups, labels)
                    if global_test["p_value"] < alpha else [])
        posthoc_name = "Tukey HSD"

    elif all_normal and not homogeneity["is_homogeneous"]:
        # Welch ANOVA → Pairwise Welch t
        global_test = _welch_anova(groups)
        global_test["decision_path"] = ("Normal + heterogeneous variances "
                                        "→ Welch ANOVA")
        effect = dict(name="omega²", value=_omega_squared(groups))
        pairwise = (_welch_t_posthoc(groups, labels)
                    if global_test["p_value"] < alpha else [])
        posthoc_name = "Welch t-tests (Holm)"
        notes.append(
            "Games-Howell not available (pingouin not installed).  "
            "Pairwise Welch t-tests with Holm correction are used "
            "as a methodologically equivalent alternative.")

    else:
        # Non-normal → Kruskal-Wallis → Dunn
        global_test = _kruskal_wallis(groups)
        global_test["decision_path"] = ("Non-normal distribution "
                                        "→ Kruskal-Wallis")
        H = global_test["statistic"]
        effect = dict(name="epsilon²",
                      value=_epsilon_squared_kw(H, N, k))
        pairwise = (_dunn_test(groups, labels)
                    if global_test["p_value"] < alpha else [])
        posthoc_name = "Dunn (Holm)"

    # --- Decision summary ---
    sig = global_test["p_value"] < alpha
    pairs_sig = sum(1 for pw in pairwise
                    if pw["p_value_adjusted"] < alpha)
    decision = (
        f"{'Significant' if sig else 'Not significant'} "
        f"({global_test['test_name']}, "
        f"p = {global_test['p_value']:.2e}, "
        f"{effect['name']} = {effect['value']:.4f})"
    )
    if sig and pairwise:
        decision += f"; {pairs_sig}/{len(pairwise)} pairs significant ({posthoc_name})"

    return dict(
        normality=normality,
        homogeneity=homogeneity,
        global_test=global_test,
        global_effect=effect,
        pairwise=pairwise,
        decision=decision,
        notes=notes,
    )


def _degenerate_result(groups, labels, ns, reason):
    """Return a skeleton result for degenerate cases."""
    normality = [dict(group=lab, n=n, statistic=np.nan,
                      p_value=np.nan, is_normal=False, note=reason)
                 for lab, n in zip(labels, ns)]
    return dict(
        normality=normality,
        homogeneity=dict(statistic=np.nan, p_value=np.nan,
                         is_homogeneous=False, note=reason),
        global_test=dict(test_name="SKIPPED", statistic=np.nan,
                         p_value=np.nan, decision_path=reason),
        global_effect=dict(name="N/A", value=np.nan),
        pairwise=[],
        decision=f"SKIPPED: {reason}",
        notes=[reason],
    )


# ===================================================================
# GLOBAL MULTIPLE-COMPARISON CORRECTION
# ===================================================================

def adjust_global_pvalues(pvalues: List[float],
                          method: str = "fdr_bh") -> np.ndarray:
    """
    Apply multiple-comparison correction across ALL variables.

    Parameters
    ----------
    pvalues : list of float
        Raw p-values from global tests across variables.
    method : str
        'holm' or 'fdr_bh' (Benjamini-Hochberg).

    Returns
    -------
    np.ndarray of adjusted p-values (same order).
    """
    # Handle NaN gracefully
    valid_mask = np.isfinite(pvalues)
    adjusted = np.full(len(pvalues), np.nan)
    if valid_mask.sum() == 0:
        return adjusted
    _, adj, _, _ = multipletests(
        np.array(pvalues)[valid_mask], method=method)
    adjusted[valid_mask] = adj
    return adjusted
