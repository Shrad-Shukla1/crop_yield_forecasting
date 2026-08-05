#!/usr/bin/env python3
from __future__ import annotations

"""Conservative remapping of fine crop-mask fraction to a coarse SIF grid.

Phase 1-5 implementation from the project plan:
1) Load and inspect fine/coarse grids.
2) Convert fine crop fraction -> fine crop area.
3) Aggregate fine crop area onto coarse grid (center-in-cell binning).
4) Convert coarse crop area -> coarse crop fraction.
5) Save a NetCDF output compatible with lat/lon workflows.
"""
"""
Running the script
python conservative_cropmask_remap.py --crop-mask-path Global-cropland-percentage-map.nc --sif-sample-path /home/chc-shrad/DATA/SIF/fusion_SCIAMACHY_GOME-2/SIF_SCIAMACHY_GOME2_Harmonized.YYYYMM_subsetted.nc4 --output-path /home/chc-source/shrad/Scripts/Funded_projects/2026/crop_yield_forecasting/code/notebook/code/crop_mask_fraction_on_sif_grid_conservative.nc
"""

import argparse
import glob
from pathlib import Path

import numpy as np
import xarray as xr

EARTH_RADIUS_KM = 6371.0


def infer_grid_step_deg(coord: xr.DataArray) -> float:
    """Infer representative grid spacing from a 1-D coordinate array."""
    values = np.asarray(coord.values, dtype=float)
    diffs = np.diff(values)
    if diffs.size == 0:
        raise ValueError(f"Coordinate '{coord.name}' must contain at least two points.")
    return float(np.abs(np.median(diffs)))


def compute_edges_from_centers(centers: np.ndarray) -> np.ndarray:
    """Compute coordinate edges from center coordinates.

    Returns monotonically increasing edges (required by np.digitize).
    """
    centers = np.asarray(centers, dtype=float)
    if centers.ndim != 1 or centers.size < 2:
        raise ValueError("Need at least 2 center points to compute cell edges.")

    if centers[0] > centers[-1]:
        centers = centers[::-1]

    mid = 0.5 * (centers[:-1] + centers[1:])
    first = centers[0] - 0.5 * (centers[1] - centers[0])
    last = centers[-1] + 0.5 * (centers[-1] - centers[-2])
    edges = np.concatenate(([first], mid, [last]))
    return edges


def compute_cell_area(lat_centers: xr.DataArray, delta_lon_deg: float, delta_lat_deg: float) -> xr.DataArray:
    """Compute grid-cell area (km^2) on a spherical Earth for each latitude row.

    area = R^2 * |dlon_rad| * |sin(lat_N) - sin(lat_S)|
    """
    lat_vals = np.asarray(lat_centers.values, dtype=float)
    dlon_rad = np.deg2rad(abs(delta_lon_deg))
    half_dlat = 0.5 * abs(delta_lat_deg)

    lat_n = np.deg2rad(lat_vals + half_dlat)
    lat_s = np.deg2rad(lat_vals - half_dlat)

    area_1d = (EARTH_RADIUS_KM**2) * dlon_rad * np.abs(np.sin(lat_n) - np.sin(lat_s))
    return xr.DataArray(area_1d, coords={"lat": lat_centers}, dims=("lat",), name="cell_area_km2")


def open_crop_mask(crop_path: str, var_name: str = "crop_mask") -> xr.DataArray:
    ds = xr.open_dataset(crop_path)
    if var_name not in ds:
        raise KeyError(f"Variable '{var_name}' not found in {crop_path}.")

    da = ds[var_name]
    rename_map = {}
    if "latitude" in da.coords:
        rename_map["latitude"] = "lat"
    if "longitude" in da.coords:
        rename_map["longitude"] = "lon"
    if rename_map:
        da = da.rename(rename_map)

    if "lat" not in da.coords or "lon" not in da.coords:
        raise KeyError("Crop mask must have latitude/longitude coordinates.")

    return da


def open_sif_coords(sif_sample_path: str, lat_name: str = "lat", lon_name: str = "lon") -> tuple[xr.DataArray, xr.DataArray]:
    ds = xr.open_dataset(sif_sample_path)
    if lat_name not in ds.coords or lon_name not in ds.coords:
        raise KeyError(f"SIF file must have coordinates '{lat_name}' and '{lon_name}'.")
    return ds[lat_name], ds[lon_name]


def aggregate_fine_area_to_coarse(
    fine_crop_area: xr.DataArray,
    coarse_lat: xr.DataArray,
    coarse_lon: xr.DataArray,
) -> xr.DataArray:
    """Aggregate fine crop area onto coarse grid by center-in-cell binning."""
    coarse_lat_vals = np.asarray(coarse_lat.values, dtype=float)
    coarse_lon_vals = np.asarray(coarse_lon.values, dtype=float)

    lat_reverse = coarse_lat_vals[0] > coarse_lat_vals[-1]
    lon_reverse = coarse_lon_vals[0] > coarse_lon_vals[-1]

    coarse_lat_for_bins = coarse_lat_vals[::-1] if lat_reverse else coarse_lat_vals
    coarse_lon_for_bins = coarse_lon_vals[::-1] if lon_reverse else coarse_lon_vals

    coarse_lat_edges = compute_edges_from_centers(coarse_lat_for_bins)
    coarse_lon_edges = compute_edges_from_centers(coarse_lon_for_bins)

    flat = fine_crop_area.stack(cell=("lat", "lon"))
    flat_vals = np.asarray(flat.values, dtype=float)
    fine_lat = np.asarray(flat["lat"].values, dtype=float)
    fine_lon = np.asarray(flat["lon"].values, dtype=float)

    lat_idx = np.digitize(fine_lat, coarse_lat_edges) - 1
    lon_idx = np.digitize(fine_lon, coarse_lon_edges) - 1

    nlat = coarse_lat_for_bins.size
    nlon = coarse_lon_for_bins.size

    valid = (
        np.isfinite(flat_vals)
        & (lat_idx >= 0)
        & (lat_idx < nlat)
        & (lon_idx >= 0)
        & (lon_idx < nlon)
    )

    coarse_sum = np.zeros((nlat, nlon), dtype=np.float64)
    np.add.at(coarse_sum, (lat_idx[valid], lon_idx[valid]), flat_vals[valid])

    if lat_reverse:
        coarse_sum = coarse_sum[::-1, :]
    if lon_reverse:
        coarse_sum = coarse_sum[:, ::-1]

    return xr.DataArray(
        coarse_sum,
        coords={"lat": coarse_lat, "lon": coarse_lon},
        dims=("lat", "lon"),
        name="coarse_crop_area_km2",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Conservative fine->coarse crop mask remapping")
    parser.add_argument(
        "--crop-mask-path",
        default="/home/chc-shrad/DATA/Crop_yield_forecasting/Crop_masks/lu_et_al/Global-cropland-percentage-map.nc",
        help="Path to fine-resolution crop mask NetCDF",
    )
    parser.add_argument(
        "--crop-mask-var",
        default="crop_mask",
        help="Variable name for crop fraction",
    )
    parser.add_argument(
        "--sif-sample-path",
        default="",
        help="Path to one SIF NetCDF file used as coarse target grid",
    )
    parser.add_argument(
        "--sif-glob",
        default="/home/chc-shrad/DATA/SIF/fusion_SCIAMACHY_GOME-2/SIF_SCIAMACHY_GOME2_Harmonized.*_subsetted.nc4",
        help="Glob to locate SIF files if --sif-sample-path is not provided",
    )
    parser.add_argument(
        "--output-path",
        default=str(Path(__file__).with_name("crop_mask_fraction_on_sif_grid_conservative.nc")),
        help="Output NetCDF path",
    )

    args = parser.parse_args()

    if args.sif_sample_path:
        sif_sample_path = args.sif_sample_path
    else:
        matches = sorted(glob.glob(args.sif_glob))
        if not matches:
            raise FileNotFoundError(f"No SIF files matched: {args.sif_glob}")
        sif_sample_path = matches[0]

    crop_pct = open_crop_mask(args.crop_mask_path, args.crop_mask_var)
    sif_lat, sif_lon = open_sif_coords(sif_sample_path)

    # Phase 1: inspect grid spacing
    fine_dlat = infer_grid_step_deg(crop_pct["lat"])
    fine_dlon = infer_grid_step_deg(crop_pct["lon"])
    coarse_dlat = infer_grid_step_deg(sif_lat)
    coarse_dlon = infer_grid_step_deg(sif_lon)

    print(f"Fine grid step:   dlat={fine_dlat:.6f} deg, dlon={fine_dlon:.6f} deg")
    print(f"Coarse grid step: dlat={coarse_dlat:.6f} deg, dlon={coarse_dlon:.6f} deg")

    # Phase 2: fine crop area
    fine_row_area = compute_cell_area(crop_pct["lat"], fine_dlon, fine_dlat)
    fine_cell_area = fine_row_area.broadcast_like(crop_pct)

    crop_fraction_fine = (crop_pct).clip(0.0, 1.0).rename("fine_crop_fraction")
    fine_crop_area = (crop_fraction_fine * fine_cell_area).rename("fine_crop_area_km2")

    # Phase 3: aggregate fine crop area to coarse grid
    coarse_crop_area = aggregate_fine_area_to_coarse(fine_crop_area, sif_lat, sif_lon)

    # Phase 4: coarse crop fraction
    coarse_row_area = compute_cell_area(sif_lat, coarse_dlon, coarse_dlat)
    coarse_cell_area = coarse_row_area.broadcast_like(coarse_crop_area).rename("coarse_cell_area_km2")

    coarse_crop_fraction = (coarse_crop_area / coarse_cell_area).clip(0.0, 1.0)
    coarse_crop_fraction = coarse_crop_fraction.rename("crop_fraction")

    # Phase 5: output
    fine_total_crop_area = float(fine_crop_area.sum(skipna=True).values)
    coarse_total_crop_area = float((coarse_crop_fraction * coarse_cell_area).sum(skipna=True).values)

    out_ds = xr.Dataset(
        data_vars={
            "crop_fraction": coarse_crop_fraction,
            "coarse_crop_area_km2": coarse_crop_area,
            "coarse_cell_area_km2": coarse_cell_area,
        },
        coords={"lat": sif_lat, "lon": sif_lon},
        attrs={
            "title": "Conservatively remapped crop fraction on SIF grid",
            "source_crop_mask": args.crop_mask_path,
            "source_sif_grid_sample": sif_sample_path,
            "method": "fine crop fraction -> fine crop area -> coarse summed crop area -> coarse crop fraction",
            "fine_grid_step_deg": f"dlat={fine_dlat}, dlon={fine_dlon}",
            "coarse_grid_step_deg": f"dlat={coarse_dlat}, dlon={coarse_dlon}",
            "fine_total_crop_area_km2": fine_total_crop_area,
            "coarse_total_crop_area_km2": coarse_total_crop_area,
            "area_conservation_ratio": coarse_total_crop_area / fine_total_crop_area if fine_total_crop_area > 0 else np.nan,
            "earth_radius_km": EARTH_RADIUS_KM,
        },
    )

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_ds.to_netcdf(output_path)

    print(f"Saved: {output_path}")
    print(f"Fine total crop area   (km^2): {fine_total_crop_area:.6f}")
    print(f"Coarse total crop area (km^2): {coarse_total_crop_area:.6f}")
    if fine_total_crop_area > 0:
        print(f"Conservation ratio coarse/fine: {coarse_total_crop_area / fine_total_crop_area:.8f}")


if __name__ == "__main__":
    main()
