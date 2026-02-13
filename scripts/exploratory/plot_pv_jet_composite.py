"""
Exploratory: PV (975 & 250 hPa) + 250-hPa jet composite

Produces a composite figure (ensemble mean across selected EP1 cyclones)
showing:
 - PV at 975 hPa as blue contour lines
 - PV at 250 hPa as green contour lines
 - Shaded 250-hPa wind speed (jet) with colorbar (m/s)

Usage:
  python scripts/exploratory/plot_pv_jet_composite.py --domain mesoscale --max-cases 50

Author: GitHub Copilot (as pair-programmer)
"""
import argparse
import sys
from pathlib import Path
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import warnings


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "era5_ep1"
RESULTS_DIR = BASE_DIR / "results" / "ep1_vertical"
OUT_DIR = BASE_DIR / "figures" / "exploratory"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DOMAIN_SIZES = {'local': 5.0, 'mesoscale': 15.0, 'synoptic': 30.0}
RESOLUTION = 0.25

# Ensure scripts package is importable
import sys
sys.path.append(str(BASE_DIR / 'scripts'))

# Barb/vector subsampling per domain (customizable)
BARB_SKIP = {
    'local': 2,
    'mesoscale': 6,
    'synoptic': 12,
}


def compute_baroclinic_pv(u, v, T, q, p, z, lat_2d, lon_2d):
    """Compute baroclinic PV using MetPy (returns array level x lat x lon).
    Expects arrays shaped (nlev, nlat, nlon) and p in Pa.
    Returns PV (same shape) in SI units (K m^2 kg^-1 s^-1).
    """
    from metpy.calc import potential_temperature, potential_vorticity_baroclinic
    from metpy.units import units

    # pressure in hPa for consistent coordinates
    pressure_hpa = (p / 100.0)

    # Build DataArrays
    lat_1d = lat_2d[:, 0]
    lon_1d = lon_2d[0, :]

    temperature_da = xr.DataArray(
        T,
        coords={'level': pressure_hpa, 'latitude': lat_1d, 'longitude': lon_1d},
        dims=['level', 'latitude', 'longitude']
    ) * units.kelvin

    u_da = xr.DataArray(
        u,
        coords={'level': pressure_hpa, 'latitude': lat_1d, 'longitude': lon_1d},
        dims=['level', 'latitude', 'longitude']
    ) * units('m/s')

    v_da = xr.DataArray(
        v,
        coords={'level': pressure_hpa, 'latitude': lat_1d, 'longitude': lon_1d},
        dims=['level', 'latitude', 'longitude']
    ) * units('m/s')

    pressure_da = xr.DataArray(pressure_hpa, coords={'level': pressure_hpa}, dims=['level']) * units.hPa

    theta = potential_temperature(pressure_da, temperature_da)
    pv = potential_vorticity_baroclinic(theta, pressure_da, u_da, v_da)

    # Return as plain numpy array
    try:
        return pv.values
    except Exception:
        return np.array(pv)


def extract_subdomain(ds, center_lat, center_lon, domain_size):
    """Interpolate dataset `ds` (at fixed time) to a regular centered grid.
    Expects variables 'u','v','t','z','q' with dims (pressure_level, latitude, longitude).
    Returns an xarray.Dataset with the target regular grid.
    """
    half = domain_size / 2.0
    n_points = int(domain_size / RESOLUTION) + 1
    lat_target = np.linspace(center_lat + half, center_lat - half, n_points)
    lon_target = np.linspace(center_lon - half, center_lon + half, n_points)

    ds_sub = ds.sel(
        latitude=slice(center_lat + half + 1, center_lat - half - 1),
        longitude=slice(center_lon - half - 1, center_lon + half + 1)
    )

    ds_interp = xr.Dataset()
    ds_interp = ds_sub.interp(latitude=lat_target, longitude=lon_target, method='linear')

    return ds_interp


def build_composite(domain_name='mesoscale', max_cases=None):
    cases_file = RESULTS_DIR / "selected_cases.csv"
    if not cases_file.exists():
        raise FileNotFoundError(f"selected_cases.csv not found at {cases_file}")

    cases = pd.read_csv(cases_file)
    if max_cases is not None:
        cases = cases.head(max_cases)

    domain_size = DOMAIN_SIZES.get(domain_name, 15.0)

    pv975_list = []
    pv250_list = []
    u250_list = []
    v250_list = []
    u975_list = []
    v975_list = []
    egr_list = []

    for _, row in cases.iterrows():
        track_id = row['track_id']
        nc_file = DATA_DIR / f"{track_id}_era5.nc"
        meta_file = DATA_DIR / f"{track_id}_metadata.csv"
        if not nc_file.exists() or not meta_file.exists():
            continue

        try:
            ds = xr.open_dataset(nc_file)
            meta = pd.read_csv(meta_file).iloc[0]
            levels_hpa = eval(meta['pressure_levels_hPa'])
            t_idx = len(ds.valid_time) // 2
            ds_t = ds.isel(valid_time=t_idx)

            ds_sub = extract_subdomain(ds_t, meta['track_center_lat'], meta['track_center_lon'], domain_size)

            # Ensure 250 and 975 available
            if 250 not in ds_sub.pressure_level.values:
                continue
            if 975 not in ds_sub.pressure_level.values:
                continue

            # Build lat/lon 2D
            lat_2d, lon_2d = np.meshgrid(ds_sub.latitude.values, ds_sub.longitude.values, indexing='ij')

            # Get pressure array in Pa
            plevels = ds_sub.pressure_level.values
            # If units are hPa, convert later in compute function by multiplying by 100
            p_pa = plevels * 100.0

            u_all = ds_sub['u'].values
            v_all = ds_sub['v'].values
            t_all = ds_sub['t'].values
            q_all = ds_sub['q'].values
            z_all = ds_sub['z'].values

            with warnings.catch_warnings():
                warnings.filterwarnings('ignore')
                pv_all = compute_baroclinic_pv(u_all, v_all, t_all, q_all, p_pa, z_all, lat_2d, lon_2d)

            # Compute EGR (use step4 function if available)
            try:
                # add scripts path to import step4 helpers
                sys.path.append(str(BASE_DIR))
                from ep1_ibc_ibt_analysis.step4_compute_instabilities import eady_growth_rate, geopotential_height
                lev3_ca = [950, 975, 1000]
                # select lev3_ca from ds_sub
                u3 = ds_sub['u'].sel(pressure_level=lev3_ca).values
                v3 = ds_sub['v'].sel(pressure_level=lev3_ca).values
                T3 = ds_sub['t'].sel(pressure_level=lev3_ca).values
                q3 = ds_sub['q'].sel(pressure_level=lev3_ca).values
                z3 = geopotential_height(ds_sub['z'].sel(pressure_level=lev3_ca).values)
                p3 = np.array(lev3_ca) * 100.0
                _, egr_day_case, _ = eady_growth_rate(u3, v3, T3, q3, p3, z3, lat_2d)
            except Exception:
                egr_day_case = np.full_like(pv_all[0], np.nan)

            plevels_hpa = ds_sub.pressure_level.values
            idx250 = int(np.where(plevels_hpa == 250)[0][0])
            idx975 = int(np.where(plevels_hpa == 975)[0][0])

            pv250 = pv_all[idx250]
            pv975 = pv_all[idx975]

            u250 = u_all[idx250]
            v250 = v_all[idx250]
            u975 = u_all[idx975]
            v975 = v_all[idx975]

            pv250_list.append(pv250)
            pv975_list.append(pv975)
            u250_list.append(u250)
            v250_list.append(v250)
            u975_list.append(u975)
            v975_list.append(v975)
            egr_list.append(egr_day_case)

            ds.close()
        except Exception:
            import traceback
            print(f"Error processing {track_id}: ")
            traceback.print_exc()
            continue

    if len(pv975_list) == 0:
        raise RuntimeError("No valid cases found for composite")

    pv975_mean = np.nanmean(np.stack(pv975_list), axis=0) * 1e6
    pv250_mean = np.nanmean(np.stack(pv250_list), axis=0) * 1e6
    u250_mean = np.nanmean(np.stack(u250_list), axis=0)
    v250_mean = np.nanmean(np.stack(v250_list), axis=0)
    u975_mean = np.nanmean(np.stack(u975_list), axis=0)
    v975_mean = np.nanmean(np.stack(v975_list), axis=0)
    egr_mean = np.nanmean(np.stack(egr_list), axis=0)

    wind_speed = np.sqrt(u250_mean**2 + v250_mean**2)

    nlat, nlon = pv975_mean.shape
    x = np.linspace(-nlon / 2, (nlon / 2) - 1, nlon) * RESOLUTION
    y = np.linspace(-nlat / 2, (nlat / 2) - 1, nlat) * RESOLUTION
    x_2d, y_2d = np.meshgrid(x, y)

    return x_2d, y_2d, pv975_mean, pv250_mean, wind_speed, egr_mean, u250_mean, v250_mean, u975_mean, v975_mean


def plot_and_save(x, y, pv975, pv250, wind_speed, domain_name):
    # kept for backward compatibility; not used by multiplot
    fig, ax = plt.subplots(figsize=(8, 6))

    # Shade baroclinic PV at Ca/975 hPa similar to step5_create_figures.py
    try:
        pv_min = np.nanmin(pv975)
        pv_levels = np.linspace(pv_min, 0, 21)
    except Exception:
        pv_levels = 21
    im = ax.contourf(x, y, pv975, levels=pv_levels, cmap='RdYlBu_r', extend='both')

    # Jet as black contour lines (only contour strong winds)
    try:
        wind_contour = np.where(wind_speed >= 30, wind_speed, np.nan)
        wind_levels = np.arange(30, int(np.nanmax(wind_speed)) + 10, 10)
        csw = ax.contour(x, y, wind_contour, levels=wind_levels, colors='black', linewidths=1.0)
    except Exception:
        pass

    # PV at altitude (250 hPa) as green contour lines
    try:
        levels250 = np.linspace(np.nanpercentile(pv250, 5), np.nanpercentile(pv250, 95), 8)
        csp = ax.contour(x, y, pv250, levels=levels250, colors='green', linewidths=1.2)
        ax.clabel(csp, inline=1, fontsize=8, fmt='%1.0f')
    except Exception:
        pass

    ax.set_aspect('equal')
    ax.set_xlabel('Relative Longitude (°)')
    ax.set_ylabel('Relative Latitude (°)')
    ax.set_title(f'Composite PV (975 blue, 250 green) + 250-hPa wind (shaded) - {domain_name}')

    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='4%', pad=0.1)
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label('PV (10$^{-6}$ K m$^2$ kg$^{-1}$ s$^{-1}$)')

    out_png = OUT_DIR / f'pv_jet_composite_{domain_name}.png'
    out_pdf = OUT_DIR / f'pv_jet_composite_{domain_name}.pdf'
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_pdf)
    plt.close(fig)

    print(f'✓ Saved: {out_png} and {out_pdf}')


def main():
    # Always use all cases and produce a 2x3 multiplot (domains left->right)
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=None, help='output filename (PNG). If omitted writes to figures/exploratory')
    args = parser.parse_args()

    domains = list(DOMAIN_SIZES.keys())
    composites = {}
    comp_file = OUT_DIR / 'composites_all_domains.nc'
    if comp_file.exists():
        print(f'Loading precomputed composites from {comp_file}')
        ds = xr.open_dataset(comp_file)
        for d in domains:
            try:
                y_dim = f'y_{d}'
                x_dim = f'x_{d}'
                pv975 = ds[f'{d}_pv975'].values
                pv250 = ds[f'{d}_pv250'].values
                u250 = ds[f'{d}_u250'].values
                v250 = ds[f'{d}_v250'].values
                # optional 975 hPa winds if present in precomputed file
                if f'{d}_u975' in ds and f'{d}_v975' in ds:
                    u975 = ds[f'{d}_u975'].values
                    v975 = ds[f'{d}_v975'].values
                else:
                    u975 = None
                    v975 = None
                egr = ds[f'{d}_egr'].values
                x1d = ds[x_dim].values
                y1d = ds[y_dim].values
                x2d, y2d = np.meshgrid(x1d, y1d)
                wind = np.sqrt(u250**2 + v250**2)
                composites[d] = (x2d, y2d, pv975, pv250, wind, egr, u250, v250, u975, v975)
            except Exception:
                print(f'  Precomputed composites missing or invalid for {d}, falling back to compute')
                x, y, pv975, pv250, wind, egr, u250m, v250m, u975m, v975m = build_composite(domain_name=d)
                composites[d] = (x, y, pv975, pv250, wind, egr, u250m, v250m, u975m, v975m)
        ds.close()
    else:
        print('No precomputed composites found, building now (this may take a while)')
        for d in domains:
            print(f'  Computing composite for {d}...')
            x, y, pv975, pv250, wind, egr, u250m, v250m, u975m, v975m = build_composite(domain_name=d)
            composites[d] = (x, y, pv975, pv250, wind, egr, u250m, v250m, u975m, v975m)

    # Create multiplot: 2 rows x 3 cols
    fig, axes = plt.subplots(2, 3, figsize=(18, 10), constrained_layout=True)

    # determine wind vmax from available composites
    ws_max = 0.0
    for d in domains:
        try:
            ws = composites[d][4]
            if np.isfinite(ws).any():
                ws_max = max(ws_max, float(np.nanmax(ws)))
        except Exception:
            continue
    vmin = 30
    vmax = ws_max + 10 if ws_max > 0 else 110
    cmap = plt.get_cmap('turbo')

    for col, d in enumerate(domains):
        x, y, pv975, pv250, wind, egr, u250m, v250m, u975m, v975m = composites[d]

        # Row 0: PV (shaded) + 250-hPa barbs + PV(250) green contours
        ax = axes[0, col]
        try:
            pv_min = np.nanmin(pv975)
            pv_levels = np.linspace(pv_min, 0, 21)
        except Exception:
            pv_levels = 21
        im = ax.contourf(x, y, pv975, levels=pv_levels, cmap='RdYlBu_r', extend='both')

        # Jet as barbs (250 hPa) - subsample using BARB_SKIP per domain
        try:
            skip_barb = BARB_SKIP.get(d, max(1, x.shape[0] // 10))
            wsp = np.sqrt(u250m**2 + v250m**2)
            u_barb = np.where(wsp >= 30, u250m, np.nan)
            v_barb = np.where(wsp >= 30, v250m, np.nan)
            ax.barbs(x[::skip_barb, ::skip_barb], y[::skip_barb, ::skip_barb],
                     u_barb[::skip_barb, ::skip_barb], v_barb[::skip_barb, ::skip_barb],
                     length=6, linewidth=0.5, color='black', alpha=0.9)
        except Exception:
            pass

        # PV at altitude (250 hPa) as green contour lines
        try:
            levels250 = np.linspace(np.nanpercentile(pv250, 5), np.nanpercentile(pv250, 95), 8)
            ax.contour(x, y, pv250, levels=levels250, colors='green', linewidths=1.1)
        except Exception:
            pass

        ax.set_title(f'{d} - PV (975 shaded) + Jet (barbs) + PV(250) green')
        ax.set_aspect('equal')

        # Row 1: EGR + 250-hPa barbs (use u250/v250 mean as barbs)
        ax2 = axes[1, col]
        im2 = ax2.contourf(x, y, egr, levels=np.linspace(np.nanpercentile(egr, 1), np.nanpercentile(egr, 99), 21), cmap='YlOrRd', extend='both')
        try:
            skip_vec = BARB_SKIP.get(d, max(1, x.shape[0] // 15))
            # prefer winds at 975 hPa for EGR bars; fallback to 250 hPa if 975 not available
            if u975m is not None and v975m is not None:
                u_barbs = u975m
                v_barbs = v975m
            else:
                u_barbs = u250m
                v_barbs = v250m
            ax2.barbs(x[::skip_vec, ::skip_vec], y[::skip_vec, ::skip_vec],
                      u_barbs[::skip_vec, ::skip_vec], v_barbs[::skip_vec, ::skip_vec],
                      length=6, linewidth=0.5, color='black', alpha=0.8)
        except Exception:
            pass
        ax2.set_title(f'{d} - EGR (day$^{{-1}}$) + 250-hPa barbs')
        ax2.set_aspect('equal')

    # Colorbars: PV (top row) and EGR (bottom row) placed without overlapping plots
    try:
        pv_min_all = min([np.nanmin(composites[d][2]) for d in domains])
    except Exception:
        pv_min_all = -1.0
    pv_max_all = 0.0
    sm_pv = plt.cm.ScalarMappable(cmap='RdYlBu_r', norm=plt.Normalize(vmin=pv_min_all, vmax=pv_max_all))
    fig.colorbar(sm_pv, ax=axes[0, :], orientation='vertical', fraction=0.03, pad=0.02, label='PV (10$^{-6}$ K m$^2$ kg$^{-1}$ s$^{-1}$)')

    try:
        egr_max_all = max([np.nanmax(composites[d][5]) for d in domains if np.isfinite(np.nanmax(composites[d][5]))])
        egr_vmin = 0.0
        egr_vmax = egr_max_all
    except Exception:
        egr_vmin, egr_vmax = 0.0, 4.0
    sm_egr = plt.cm.ScalarMappable(cmap='YlOrRd', norm=plt.Normalize(vmin=egr_vmin, vmax=egr_vmax))
    fig.colorbar(sm_egr, ax=axes[1, :], orientation='vertical', fraction=0.03, pad=0.02, label='EGR (day$^{-1}$)')

    outname = args.out or (OUT_DIR / 'pv_jet_egr_multiplot.png')
    fig.savefig(outname, dpi=300)
    plt.close(fig)
    print(f'✓ Saved multiplot: {outname}')


if __name__ == '__main__':
    main()
