"""
PREDEP (PREdictive DEPendence) estimator.

Implements the bootstrap-based estimator of the PREDEP measure
following Assunção et al. (2025, arXiv:2501.10815).

PREDEP quantifies the expected relative prediction loss when the
distribution of X is ignored in predicting Y:

    α_{Y|X} = (S_{Y|X} - S_Y) / S_{Y|X}

where:
    S_Y     = E[f_Y(Y)]     = ∫ f_Y²(y) dy   (marginal prediction rate)
    S_{Y|X} = E_X[E_{Y|X} f_{Y|X}(Y|X)]      (conditional prediction rate)

Both quantities are estimated via the convolution-density-at-zero
trick:  E[f(Y)] = f_W(0)  where W = Y₁ − Y₂  (Y₁, Y₂ iid copies).

The conditional component uses hierarchical clustering on X to
define bins, then applies the same bootstrap inside each bin.

Key properties:
    • α ∈ [0, 1]
    • α = 0 ⟺ X ⊥ Y
    • Asymmetric: α_{Y|X} ≠ α_{X|Y}  in general
    • Connected to quadratic Rényi entropy

Author: Danilo Couto de Souza
Date: April 2026
Reference: Assunção et al. (2025), arXiv:2501.10815v1
"""

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.stats import gaussian_kde, spearmanr, pearsonr
from typing import Dict, Optional, Tuple
import warnings


def _kde_at_zero(samples: np.ndarray, bw_method: str = "scott") -> float:
    """
    Estimate the convolution density f_W(0) from bootstrap differences.

    Parameters
    ----------
    samples : array-like
        1D array of W = Y₁ − Y₂ values.
    bw_method : str
        Bandwidth selection method for scipy.stats.gaussian_kde.

    Returns
    -------
    float
        f̂_W(0), the KDE evaluated at zero.
    """
    if len(samples) < 3:
        return np.nan
    try:
        kde = gaussian_kde(samples, bw_method=bw_method)
        return float(kde.evaluate([0.0])[0])
    except (np.linalg.LinAlgError, ValueError):
        return np.nan


def _bootstrap_differences(y: np.ndarray, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    """
    Generate bootstrap sample of W = Y₁ − Y₂.
    """
    idx1 = rng.integers(0, len(y), size=n_boot)
    idx2 = rng.integers(0, len(y), size=n_boot)
    return y[idx1] - y[idx2]


def _compute_bin_edges(x: np.ndarray, n_bins: Optional[int] = None) -> np.ndarray:
    """
    Compute bin edges for X using hierarchical clustering (Ward).

    Parameters
    ----------
    x : np.ndarray
        1D predictor array.
    n_bins : int or None
        Number of bins.  Default: sqrt(len(x)).

    Returns
    -------
    np.ndarray
        Sorted array of bin edges (length n_bins + 1).
    """
    n = len(x)
    if n_bins is None:
        n_bins = max(2, int(np.sqrt(n)))

    # Ward linkage on 1-D data
    Z = linkage(x.reshape(-1, 1), method="ward")
    labels = fcluster(Z, t=n_bins, criterion="maxclust")

    # Build edges from cluster boundaries
    edges = [-np.inf]
    for lbl in sorted(np.unique(labels)):
        mask = labels == lbl
        edges.append(x[mask].max())
    edges[-1] = np.inf
    return np.array(edges)


def predep(
    x: np.ndarray,
    y: np.ndarray,
    n_boot: Optional[int] = None,
    n_bins: Optional[int] = None,
    seed: int = 42,
    min_bin_size: int = 5,
) -> float:
    """
    Estimate PREDEP α_{Y|X} from data.

    Direction convention: X predicts Y.
    A high value means knowing X greatly improves prediction of Y.

    Parameters
    ----------
    x : np.ndarray
        Predictor variable (1D, length N).
    y : np.ndarray
        Response variable (1D, length N).
    n_boot : int or None
        Number of bootstrap pairs.  Default: ceil(N * log(N)).
    n_bins : int or None
        Number of bins for X.  Default: sqrt(N).
    seed : int
        Random seed for reproducibility.
    min_bin_size : int
        Minimum observations in a bin to compute conditional density.

    Returns
    -------
    float
        PREDEP α_{Y|X} ∈ [0, 1], or NaN on failure.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    # Remove paired NaN
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    n = len(x)

    if n < 10:
        return np.nan

    if n_boot is None:
        n_boot = int(np.ceil(n * np.log(n)))

    rng = np.random.default_rng(seed)

    # --- S_Y (marginal) ---
    W_y = _bootstrap_differences(y, n_boot, rng)
    S_Y = _kde_at_zero(W_y)
    if np.isnan(S_Y) or S_Y <= 0:
        return np.nan

    # --- S_{Y|X} (conditional) ---
    edges = _compute_bin_edges(x, n_bins)
    S_YX = 0.0

    for i in range(len(edges) - 1):
        bin_mask = (x >= edges[i]) & (x < edges[i + 1])
        y_bin = y[bin_mask]
        n_bin = len(y_bin)

        if n_bin < min_bin_size:
            continue

        p = n_bin / n  # fraction of data in this bin
        W_cond = _bootstrap_differences(y_bin, n_boot, rng)
        kde_val = _kde_at_zero(W_cond)

        if not np.isnan(kde_val):
            S_YX += p * kde_val

    if S_YX <= 0:
        return np.nan

    alpha = (S_YX - S_Y) / S_YX
    # Clip to [0, 1] to handle numerical noise
    return float(np.clip(alpha, 0.0, 1.0))


def predep_with_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_boot_ci: int = 200,
    confidence: float = 0.95,
    **kwargs,
) -> Dict[str, float]:
    """
    Estimate PREDEP with bootstrap confidence interval.

    Parameters
    ----------
    x, y : np.ndarray
        Predictor and response arrays.
    n_boot_ci : int
        Number of bootstrap resamples for CI.
    confidence : float
        Confidence level (e.g. 0.95).
    **kwargs :
        Passed to predep().

    Returns
    -------
    dict
        {"predep": α, "ci_lower": lo, "ci_upper": hi,
         "n_boot_ci": n_boot_ci}
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    n = len(x)

    if n < 10:
        return {"predep": np.nan, "ci_lower": np.nan, "ci_upper": np.nan, "n_boot_ci": 0}

    rng = np.random.default_rng(kwargs.get("seed", 42))
    alphas = []

    for b in range(n_boot_ci):
        idx = rng.integers(0, n, size=n)
        alpha_b = predep(x[idx], y[idx], seed=b + 1000, **{k: v for k, v in kwargs.items() if k != "seed"})
        if not np.isnan(alpha_b):
            alphas.append(alpha_b)

    if len(alphas) < 5:
        return {"predep": np.nan, "ci_lower": np.nan, "ci_upper": np.nan, "n_boot_ci": len(alphas)}

    alpha_est = float(np.median(alphas))
    q_lo = (1 - confidence) / 2
    q_hi = 1 - q_lo
    ci_lo = float(np.quantile(alphas, q_lo))
    ci_hi = float(np.quantile(alphas, q_hi))

    return {"predep": alpha_est, "ci_lower": ci_lo, "ci_upper": ci_hi, "n_boot_ci": len(alphas)}


def compute_baselines(x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Compute auxiliary (baseline) association measures.

    Returns
    -------
    dict
        {"pearson_r": r, "pearson_p": p, "spearman_rho": rho, "spearman_p": p}
    """
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]

    if len(x) < 5:
        return {
            "pearson_r": np.nan, "pearson_p": np.nan,
            "spearman_rho": np.nan, "spearman_p": np.nan,
        }

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r, rp = pearsonr(x, y)
        rho, sp = spearmanr(x, y)

    return {
        "pearson_r": float(r), "pearson_p": float(rp),
        "spearman_rho": float(rho), "spearman_p": float(sp),
    }
