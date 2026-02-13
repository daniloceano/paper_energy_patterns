"""
Precompute composites for PV (975 & 250 hPa), 250-hPa wind and EGR for all domains.

Saves a netCDF file at `figures/exploratory/composites_all_domains.nc` with
variables for each domain: pv975, pv250, u250, v250, wind, egr, and coords x,y.

Run once and reuse in plotting to avoid repeated heavy computation.
"""
import sys
from pathlib import Path
import numpy as np
import xarray as xr
import pandas as pd
import warnings

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "era5_ep1"
RESULTS_DIR = BASE_DIR / "results" / "ep1_vertical"
OUT_DIR = BASE_DIR / "figures" / "exploratory"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DOMAIN_SIZES = {'local': 5.0, 'mesoscale': 15.0, 'synoptic': 30.0}
RESOLUTION = 0.25

# Make scripts importable
sys.path.append(str(BASE_DIR / 'scripts'))

from ep1_ibc_ibt_analysis.step4_compute_instabilities import eady_growth_rate, geopotential_height
from metpy.calc import potential_temperature, potential_vorticity_baroclinic
from metpy.units import units


def extract_subdomain(ds, center_lat, center_lon, domain_size):
    half = domain_size / 2.0
    n_points = int(domain_size / RESOLUTION) + 1
    lat_target = np.linspace(center_lat + half, center_lat - half, n_points)
    lon_target = np.linspace(center_lon - half, center_lon + half, n_points)
    ds_sub = ds.sel(
        latitude=slice(center_lat + half + 1, center_lat - half - 1),
        longitude=slice(center_lon - half - 1, center_lon + half + 1)
    )
    ds_interp = ds_sub.interp(latitude=lat_target, longitude=lon_target, method='linear')
    return ds_interp


def compute_pv_all(u_all, v_all, t_all, q_all, plevels_pa, lat_values, lon_values):
    pressure_hpa = plevels_pa / 100.0
    temperature_da = xr.DataArray(
        t_all,
        coords={'level': pressure_hpa, 'latitude': lat_values, 'longitude': lon_values},
        dims=['level', 'latitude', 'longitude']
    ) * units.kelvin
    u_da = xr.DataArray(u_all, coords={'level': pressure_hpa, 'latitude': lat_values, 'longitude': lon_values}, dims=['level','latitude','longitude']) * units('m/s')
    v_da = xr.DataArray(v_all, coords={'level': pressure_hpa, 'latitude': lat_values, 'longitude': lon_values}, dims=['level','latitude','longitude']) * units('m/s')
    pressure_da = xr.DataArray(pressure_hpa, coords={'level': pressure_hpa}, dims=['level']) * units.hPa
    theta = potential_temperature(pressure_da, temperature_da)
    pv = potential_vorticity_baroclinic(theta, pressure_da, u_da, v_da)
    return pv.values


def main():
    cases_file = RESULTS_DIR / "selected_cases.csv"
    if not cases_file.exists():
        raise FileNotFoundError("selected_cases.csv not found")

    cases = pd.read_csv(cases_file)

    # Output container
    ds_out = xr.Dataset()

    for domain_name, domain_size in DOMAIN_SIZES.items():
        print(f'Computing domain: {domain_name} ({domain_size}°)')
        pv_all_list = []
        u_all_list = []
        v_all_list = []
        pv250_list = []
        pv975_list = []
        u250_list = []
        v250_list = []
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
                t_idx = len(ds.valid_time) // 2
                ds_t = ds.isel(valid_time=t_idx)
                ds_sub = extract_subdomain(ds_t, meta['track_center_lat'], meta['track_center_lon'], domain_size)

                plevels = ds_sub.pressure_level.values
                p_pa = plevels * 100.0
                lat_vals = ds_sub.latitude.values
                lon_vals = ds_sub.longitude.values

                u_all = ds_sub['u'].values
                v_all = ds_sub['v'].values
                t_all = ds_sub['t'].values
                q_all = ds_sub['q'].values
                z_all = ds_sub['z'].values

                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore')
                    pv_all = compute_pv_all(u_all, v_all, t_all, q_all, p_pa, lat_vals, lon_vals)

                # indices
                if 250 not in plevels or 975 not in plevels:
                    ds.close()
                    continue
                idx250 = int(np.where(plevels == 250)[0][0])
                idx975 = int(np.where(plevels == 975)[0][0])

                pv250 = pv_all[idx250]
                pv975 = pv_all[idx975]
                u250 = u_all[idx250]
                v250 = v_all[idx250]
                wind = np.sqrt(u250**2 + v250**2)

                # EGR compute using step4 function
                try:
                    lev3_ca = [950, 975, 1000]
                    u3 = ds_sub['u'].sel(pressure_level=lev3_ca).values
                    v3 = ds_sub['v'].sel(pressure_level=lev3_ca).values
                    T3 = ds_sub['t'].sel(pressure_level=lev3_ca).values
                    q3 = ds_sub['q'].sel(pressure_level=lev3_ca).values
                    z3 = geopotential_height(ds_sub['z'].sel(pressure_level=lev3_ca).values)
                    p3 = np.array(lev3_ca) * 100.0
                    _, egr_day_case, _ = eady_growth_rate(u3, v3, T3, q3, p3, z3, np.meshgrid(lat_vals, lon_vals, indexing='ij')[0])
                except Exception:
                    egr_day_case = np.full_like(pv975, np.nan)

                # accumulate full-level arrays for domain-mean composites
                pv_all_list.append(pv_all)
                u_all_list.append(u_all)
                v_all_list.append(v_all)

                pv250_list.append(pv250)
                pv975_list.append(pv975)
                u250_list.append(u250)
                v250_list.append(v250)
                egr_list.append(egr_day_case)

                ds.close()
            except Exception:
                continue

        if len(pv975_list) == 0:
            print(f'  No valid cases for domain {domain_name}, skipping')
            continue

        # compute means
        pv_all_mean = np.nanmean(np.stack(pv_all_list), axis=0) * 1e6  # levels, y, x
        u_all_mean = np.nanmean(np.stack(u_all_list), axis=0)
        v_all_mean = np.nanmean(np.stack(v_all_list), axis=0)

        # convenience level-specific means
        pv975_mean = np.nanmean(np.stack(pv975_list), axis=0) * 1e6
        pv250_mean = np.nanmean(np.stack(pv250_list), axis=0) * 1e6
        u250_mean = np.nanmean(np.stack(u250_list), axis=0)
        v250_mean = np.nanmean(np.stack(v250_list), axis=0)
        wind_mean = np.sqrt(u250_mean**2 + v250_mean**2)
        egr_mean = np.nanmean(np.stack(egr_list), axis=0)

        # coords
        nlat, nlon = pv975_mean.shape
        x = np.linspace(-nlon / 2, (nlon / 2) - 1, nlon) * RESOLUTION
        y = np.linspace(-nlat / 2, (nlat / 2) - 1, nlat) * RESOLUTION

        # store in dataset under domain prefix using domain-specific dimension names
        y_dim = f'y_{domain_name}'
        x_dim = f'x_{domain_name}'

        # store full-level means with domain-specific level dim
        level_dim = f'level_{domain_name}'
        pressure_hpa = plevels

        ds_out[f'{domain_name}_pv_all'] = ((level_dim, y_dim, x_dim), pv_all_mean)
        ds_out[f'{domain_name}_u_all'] = ((level_dim, y_dim, x_dim), u_all_mean)
        ds_out[f'{domain_name}_v_all'] = ((level_dim, y_dim, x_dim), v_all_mean)

        # store convenience single-level fields
        ds_out[f'{domain_name}_pv975'] = ((y_dim, x_dim), pv975_mean)
        ds_out[f'{domain_name}_pv250'] = ((y_dim, x_dim), pv250_mean)
        ds_out[f'{domain_name}_u250'] = ((y_dim, x_dim), u250_mean)
        ds_out[f'{domain_name}_v250'] = ((y_dim, x_dim), v250_mean)
        ds_out[f'{domain_name}_u975'] = ((y_dim, x_dim), u_all_mean[idx975])
        ds_out[f'{domain_name}_v975'] = ((y_dim, x_dim), v_all_mean[idx975])
        ds_out[f'{domain_name}_wind250'] = ((y_dim, x_dim), wind_mean)
        ds_out[f'{domain_name}_egr'] = ((y_dim, x_dim), egr_mean)

        # assign domain-specific coords
        # assign domain-specific coords
        ds_out = ds_out.assign_coords({x_dim: x, y_dim: y, level_dim: pressure_hpa})

    out_file = OUT_DIR / 'composites_all_domains.nc'
    ds_out.to_netcdf(out_file)
    print(f'✓ Saved composites to {out_file}')


if __name__ == '__main__':
    main()
