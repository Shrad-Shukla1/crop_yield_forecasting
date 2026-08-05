#!/usr/bin/env python3
"""convert_GOSIF_v2_tiff_monthly_to_netcdf.py

Convert monthly single‑band GeoTIFFs for the GOSIF_v2 dataset into yearly NetCDF files.

The script performs the following steps:
1. Enumerates all GeoTIFFs in ``--data-dir``.
2. Groups them by year based on the filename pattern ``GOSIF_<YEAR>.<MON>.tif``.
3. Loads each month with rioxarray, masks water (32767) and snow/ice (32766),
   applies a scaling factor of 0.0001, and builds a 3‑D DataArray (time, lat, lon).
4. Writes one NetCDF per year to ``--out-dir`` using the filename
   ``GOSIF_v2_<YEAR>.nc``.

No compression is applied; only the raw data and source metadata (CRS, bounds, no‑data
value) are preserved.
"""

from __future__ import annotations

import argparse
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import xarray as xr
import rioxarray

__all__ = ["main"]

# -----------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------

def collect_files(data_dir: Path) -> Dict[int, List[Path]]:
    """Return a mapping of year → list of month file paths.

    The function looks for filenames matching ``GOSIF_*.tif``.  The year is
    extracted from the first part after the underscore and before the dot.
    """
    pattern = str(data_dir / "GOSIF_*.tif")
    files = sorted(glob.glob(pattern))
    year_map: Dict[int, List[Path]] = {}
    for f in files:
        p = Path(f)
        stem = p.stem  # e.g., GOSIF_2000.M03
        try:
            year_part = stem.split("_")[1]
            year = int(year_part.split(".")[0])
        except Exception:
            # Skip files that do not match the expected pattern
            continue
        year_map.setdefault(year, []).append(p)
    return year_map


def load_year(year: int, files: List[Path]) -> xr.DataArray:
    """Load monthly rasters for a single year and concatenate along time.

    Each file is assumed to be a single‑band GeoTIFF.
    """
    rasters: List[xr.DataArray] = []
    times: List[datetime] = []
    for f in sorted(files):
        da = rioxarray.open_rasterio(f, masked=True)
        # rioxarray returns a 3‑D array (band, y, x).  For single band we
        # squeeze the first dimension.
        da = da.squeeze()
        # Mask water bodies (32767) and lands under snow/ice (32766)
        da = da.where((da != 32767) & (da != 32766), drop=False)
        # Apply scaling factor of 0.0001
        da = da * 0.0001
        # Determine month from filename: e.g., M03 → 3
        month_str = f.stem.split(".")[1]  # 'M03'
        month = int(month_str.lstrip("M"))
        times.append(datetime(year, month, 15))  # mid‑month representative
        # Attach the time coordinate to the 2‑D DataArray
        da = da.expand_dims(time=[times[-1]])
        rasters.append(da)
    # Concatenate along the time dimension (now present in each DataArray)
    return xr.concat(rasters, dim="time")

# -----------------------------------------------------------------------
# Main CLI
# -----------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Convert GOSIF_v2 monthly GeoTIFFs to yearly NetCDFs.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(
            "/home/chc-shrad/DATA/SIF/GOSIF_v2/tiff/GOSIF_v2/monthly"
        ),
        help="Directory containing monthly GOSIF GeoTIFFs.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(
            "/home/chc-shrad/DATA/SIF/GOSIF_v2/netcdf/monthly"
        ),
        help="Directory to store yearly NetCDF files.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print extra debug information.")

    args = parser.parse_args()

    # Ensure output directory exists
    args.out_dir.mkdir(parents=True, exist_ok=True)

    year_map = collect_files(args.data_dir)
    if args.verbose:
        print(f"Found {len(year_map)} years in {args.data_dir}")

    for year, files in sorted(year_map.items()):
        if args.verbose:
            print(f"Processing year {year} ({len(files)} month(s))")
        da_year = load_year(year, files)
        out_path = args.out_dir / f"GOSIF_v2_{year}.nc"
        da_year.to_netcdf(out_path, format="NETCDF4", engine="netcdf4")
        print(f"Wrote {out_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
