"""
Spherical KDE density machinery shared by the CPS density maps.

The estimator is the one already used for the manuscript's genesis-density
figure (`scripts/main/07_figure_genesis_density_kde.py`), transcribed here so
that the CPS maps and the manuscript figure are the same calculation:

    Hoskins, B. J., & Hodges, K. I. (2005). A new perspective on Southern
    Hemisphere storm tracks. J. Climate, 18(20), 4108-4129.
    doi:10.1175/JCLI3570.1

Method
------
A Gaussian kernel with a haversine metric is fitted to the (lat, lon) positions
in radians, with bandwidth 0.05 rad (~318 km), and evaluated on the regular
2.5-degree grid of Hoskins and Hodges (128 x 64 global). The KDE integrates to
one over the sphere, so

    density = kde * n_points * (1e6 / R^2) / n_years * weight

is a count per 10^6 km^2 per year (R = 6369.345 km, the WGS-84 radius at 40 S).

`weight` is what makes the two map kinds comparable in their own units:

    genesis density   weight = 1                 -> cyclogenesis events / 10^6 km^2 / year
    track density     weight = dt / 24 = 3/24    -> cyclone DAYS / 10^6 km^2 / year

i.e. the whole-life maps count each 3-hourly position as an eighth of a cyclone
day, which is the standard way of stating residence-time density and keeps the
number independent of the sampling cadence.

Departure from `07_figure_genesis_density_kde.py`
-------------------------------------------------
The KDE is evaluated only on the grid points inside the plotted domain (plus a
one-cell halo so the contours reach the frame) rather than on the whole globe.
The values are identical - the estimator is pointwise - but it is ~30x cheaper,
which matters because the whole-life maps evaluate against up to 2.1 x 10^5
positions. The consequence is that the min-max normalisation used for the
anomaly panels is taken over the plotted domain instead of the globe. For
genesis this is no change at all (every genesis point is inside the domain);
for the track maps it means the normalisation reference is the plotted region.

Author: Danilo Couto de Souza
Date: August 2026
"""

from dataclasses import dataclass
from typing import Optional, Tuple

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from sklearn.neighbors import KernelDensity

# --- Estimator settings (Hoskins and Hodges 2005; as in scripts/main/07) -----
GRID_K = 64                     # global grid is GRID_K x 2*GRID_K -> 2.5 deg
KDE_BANDWIDTH = 0.05            # radians, ~318 km
EARTH_RADIUS_KM = 6369.345      # WGS-84 radius at 40 S

# Cadence of the CPS series. Used to turn a timestep count into cyclone days.
TRACK_TIMESTEP_HOURS = 3.0

# Below this many CYCLONES a KDE is not an estimate of anything: the positions
# are drawn as points instead. The gate is on cyclones, not on positions,
# because the 3-hourly positions of one cyclone are not independent samples.
MIN_KDE_CYCLONES = 10


@dataclass(frozen=True)
class Domain:
    """Plotted map domain, in degrees."""
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float

    @property
    def extent(self):
        return [self.lon_min, self.lon_max, self.lat_min, self.lat_max]

    @property
    def aspect(self) -> float:
        """Height / width in degrees, for laying panels out at true shape."""
        return ((self.lat_max - self.lat_min) /
                (self.lon_max - self.lon_min))


# Genesis: the catalogue's cyclogenesis boxes, same frame as the manuscript's
# genesis-density figure.
GENESIS_DOMAIN = Domain(-75.0, -20.0, -55.0, -20.0)

# Whole life: the tracks run far east and far south of the genesis boxes. This
# frame holds 96.1% of all 3-hourly positions in the catalogue.
TRACK_DOMAIN = Domain(-80.0, 60.0, -70.0, -15.0)

# Colour maps, matching the manuscript's genesis figure.
CMAP_ABSOLUTE = "YlOrRd"
CMAP_ANOMALY = "RdBu_r"


# =============================================================================
# GRID AND DENSITY
# =============================================================================

def global_grid() -> Tuple[np.ndarray, np.ndarray]:
    """The 2.5-degree global grid of Hoskins and Hodges (2005)."""
    longrd = np.linspace(-180.0, 180.0, 2 * GRID_K)
    latgrd = np.linspace(-87.863, 87.863, GRID_K)
    return longrd, latgrd


def domain_grid(domain: Domain) -> Tuple[np.ndarray, np.ndarray]:
    """The global grid restricted to `domain`, with a one-cell halo.

    The halo keeps the filled contours running to the frame instead of
    stopping one grid cell short of it.
    """
    longrd, latgrd = global_grid()
    dlon = longrd[1] - longrd[0]
    dlat = latgrd[1] - latgrd[0]
    lon_sel = ((longrd >= domain.lon_min - dlon) &
               (longrd <= domain.lon_max + dlon))
    lat_sel = ((latgrd >= domain.lat_min - dlat) &
               (latgrd <= domain.lat_max + dlat))
    return longrd[lon_sel], latgrd[lat_sel]


def compute_density(lat, lon, num_years: float, domain: Domain,
                    weight: float = 1.0):
    """Spherical KDE density of the positions (lat, lon), in counts/10^6 km^2/year.

    Args:
        lat, lon: position arrays in degrees. NaNs must already be removed.
        num_years: number of years the sample spans, for the time normalisation.
        domain: the map domain to evaluate on.
        weight: multiplies the count. 1 for events (genesis), dt/24 for
            residence time (whole-life maps, giving cyclone days).

    Returns:
        (density, longrd, latgrd) with density of shape (n_lat, n_lon), or
        (None, longrd, latgrd) if there are no positions.
    """
    longrd, latgrd = domain_grid(domain)
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    if lat.size == 0:
        return None, longrd, latgrd

    tx, ty = np.meshgrid(longrd, latgrd)
    mesh = np.vstack((ty.ravel(), tx.ravel())).T * (np.pi / 180.0)

    sample = np.vstack([lat, lon]).T * (np.pi / 180.0)
    kde = KernelDensity(bandwidth=KDE_BANDWIDTH, metric="haversine",
                        kernel="gaussian", algorithm="ball_tree").fit(sample)
    v = np.exp(kde.score_samples(mesh)).reshape(len(latgrd), len(longrd))

    factor = 1e6 / (EARTH_RADIUS_KM ** 2)
    density = v * lat.size * factor * weight / num_years
    return density, longrd, latgrd


def minmax_normalize_positive(arr: np.ndarray) -> np.ndarray:
    """Scale the positive values of `arr` to [0, 1]; zeros stay zero.

    Same helper as the manuscript's genesis figure. It is what makes the
    anomaly panels a comparison of SHAPE rather than of sample size: two
    subsets with very different cyclone counts are put on the same footing
    before being differenced.
    """
    out = np.zeros(arr.shape, dtype=float)
    pos = arr > 0
    if not np.any(pos):
        return out
    lo, hi = arr[pos].min(), arr[pos].max()
    out[pos] = 1.0 if hi == lo else (arr[pos] - lo) / (hi - lo)
    return out


# =============================================================================
# MAP PANELS
# =============================================================================

def setup_map_axes(ax, domain: Domain, left_labels: bool = False,
                   bottom_labels: bool = False):
    """Coastlines, borders and gridlines, with labels only where asked."""
    ax.set_extent(domain.extent, crs=ccrs.PlateCarree())
    ax.coastlines(resolution="50m", linewidth=0.6, color="black")
    ax.add_feature(cfeature.BORDERS, linewidth=0.35, edgecolor="0.35",
                   linestyle=":")
    gl = ax.gridlines(draw_labels=True, linewidth=0.4, color="gray",
                      alpha=0.45, linestyle="--")
    gl.top_labels = False
    gl.right_labels = False
    gl.left_labels = left_labels
    gl.bottom_labels = bottom_labels
    gl.xlabel_style = {"size": 7.5}
    gl.ylabel_style = {"size": 7.5}
    return gl


def draw_density(ax, density, longrd, latgrd, vmax: float, n_levels: int = 11):
    """Filled contours of an absolute density field. Returns the mappable."""
    levels = np.linspace(0.0, vmax, n_levels)
    cf = ax.contourf(longrd, latgrd, density, levels=levels,
                     cmap=CMAP_ABSOLUTE, transform=ccrs.PlateCarree(),
                     extend="max", alpha=0.9)
    ax.contour(longrd, latgrd, density, levels=levels[::3], colors="black",
               linewidths=0.35, alpha=0.55, transform=ccrs.PlateCarree())
    return cf


def draw_anomaly(ax, anomaly, longrd, latgrd, maxabs: float,
                 n_levels: int = 13):
    """Filled contours of a normalised anomaly field. Returns the mappable."""
    norm = TwoSlopeNorm(vcenter=0.0, vmin=-maxabs, vmax=maxabs)
    levels = np.linspace(-maxabs, maxabs, n_levels)
    cf = ax.contourf(longrd, latgrd, np.ma.masked_invalid(anomaly),
                     levels=levels, cmap=CMAP_ANOMALY, norm=norm,
                     transform=ccrs.PlateCarree(), extend="both", alpha=0.9)
    ax.contour(longrd, latgrd, np.ma.masked_invalid(anomaly),
               levels=[0.0], colors="0.25", linewidths=0.5,
               transform=ccrs.PlateCarree())
    return cf


def draw_points(ax, lat, lon, color: str, size: float = 12.0,
                alpha: float = 0.85):
    """Raw positions, for subsets too small for a density estimate."""
    ax.scatter(lon, lat, s=size, c=color, alpha=alpha, linewidths=0.4,
               edgecolors="white", transform=ccrs.PlateCarree(), zorder=5)


def panel_note(ax, text: str, color: str = "0.30"):
    """Centred note over an empty or point-only panel."""
    ax.text(0.5, 0.5, text, transform=ax.transAxes, ha="center", va="center",
            fontsize=8.5, color=color, style="italic",
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=2.0), zorder=6)


def robust_vmax(fields, percentile: float = 98.0) -> Optional[float]:
    """Upper colour limit shared by a group of absolute density fields."""
    vals = []
    for field in fields:
        if field is None:
            continue
        pos = field[field > 0]
        if pos.size:
            vals.append(np.percentile(pos, percentile))
    if not vals:
        return None
    return float(max(vals))


def symmetric_max(fields) -> Optional[float]:
    """Symmetric colour limit shared by a group of anomaly fields."""
    vals = [np.nanmax(np.abs(f)) for f in fields if f is not None]
    vals = [v for v in vals if np.isfinite(v) and v > 0]
    if not vals:
        return None
    return float(max(vals))
