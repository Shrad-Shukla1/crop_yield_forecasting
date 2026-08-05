# Current Plan: Disaggregating Sub-National Yield with SIF

## Objective
Disaggregate reported sub-national maize yield (admin-1) to grid scale using SIF spatial patterns, while keeping crop extent physically consistent with a conservative crop-mask remap to the SIF grid.

## Current Workflow (as implemented)

### 1) Build crop mask on SIF grid (area-conservative)
Implemented in:
- `python/conservative_cropmask_remap.py`
- Verified in `notebook/verify_conservative_cropmask_remap.ipynb`

Process:
1. Read fine crop mask (`crop_mask`) and SIF target grid (`lat`, `lon`).
2. Compute fine-cell area using spherical Earth geometry.
3. Convert fine crop fraction to fine crop area.
4. Aggregate fine crop area to coarse SIF cells using center-in-cell binning (`np.digitize`).
5. Convert coarse crop area back to coarse crop fraction and save NetCDF.

Output currently used by notebook:
- `/home/chc-source/shrad/Scripts/Funded_projects/2026/crop_yield_forecasting/data/crop_mask_fraction_on_sif_grid_conservative.nc`

### 2) Prepare SIF and yield inputs
Implemented in:
- `notebook/downscale_yield_with_SIF.ipynb`

Inputs:
- Monthly SIF stack (2003-2017)
- Admin boundaries (`hvstat_boundary.gpkg`)
- Reported harvest/yield table (`hvstat_africa_data_v1.0_20250212.csv`)
- Conservative crop mask on SIF grid (from Step 1)

Process:
1. Load SIF files and assign monthly time coordinate.
2. Subset by admin polygon using `salem.subset`.
3. Focus on JFM seasonal signal and compute yearly max SIF.
4. Mask SIF with crop fraction and remove non-positive values.

### 3) Check signal relevance against reported yield
Implemented in:
- `notebook/downscale_yield_with_SIF.ipynb`

Process:
1. For each South Africa admin-1 region, aggregate crop-masked SIF over grid cells.
2. Align with reported maize yield years (2003-2017).
3. Compute Spearman correlation between aggregated SIF and reported yield.
4. Compare with a rainfall-based baseline (CHIRPS seasonal accumulation).

Purpose:
- Confirm SIF carries yield-relevant interannual information before disaggregation.

### 4) Downscale admin yield to pixels using SIF weights
Implemented in:
- `notebook/downscale_yield_with_SIF.ipynb` (current active method)

Process:
1. Build year-aligned yield vector as an xarray `DataArray` (`year` dimension).
2. Compute max-normalized SIF weight:
   - `sif_weight = sif_yearly_max_masked / max_over_grid(sif_yearly_max_masked)`
3. Apply weight to admin-year yield to create pixel yield map.

Two variants currently in notebook:
- **Variant A (max-normalized)**
  - Preserves relative pattern where highest-SIF pixel gets admin yield level.
  - Does not guarantee spatial mean equals reported admin yield.

- **Variant B (sum-normalized / production-conserving mean)**
  - Normalize weights by grid-cell sum and scale by valid-pixel count.
  - Produces a pixel map whose spatial mean matches reported admin yield for each year.

## Role of Additional Script
- `python/xarray_grid_conservative_remapping.py` is an alternative remapping experiment using `xarray_regrid` conservative remapping over a subset domain.
- Current operational path appears to be `conservative_cropmask_remap.py` + verification notebook.

## What Is Already Established
1. Conservative crop-mask remap is in place and verified.
2. Admin-level SIF-yield relationship checks are implemented.
3. Pixel-level downscaling logic is implemented with both relative and mean-conserving options.

## Immediate Next Steps
1. Decide and lock one downscaling objective:
   - Relative productivity mapping (Variant A), or
   - Mean-conserving yield disaggregation (Variant B).
2. Wrap the per-admin workflow into a loop to generate all admin-1 yearly pixel-yield outputs.
3. Export annual gridded yield products to NetCDF with metadata (admin, year, method).
4. Add validation diagnostics:
   - Per-admin/year mean check (for Variant B),
   - Range checks and no-negative-yield checks,
   - Optional comparison against SPAM yield spatial pattern.
5. Standardize season definition (currently JFM in notebook) for reproducibility.

## Practical Notes
- The notebook currently uses `crop_fraction` from the conservative remap output as intended.
- Ensure temporal alignment between `harvest_year` and SIF `year` is explicit before final batch export.
- Keep one canonical script/notebook for production runs to avoid divergence between experimental variants.
