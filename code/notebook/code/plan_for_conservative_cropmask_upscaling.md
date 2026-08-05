# Plan: Conservative Crop Mask Upscaling (Fine → Coarse)

**TL;DR**: Upscale the Lu et al. crop fraction mask to the SIF grid using a physically correct area-conservative approach: convert fine crop fraction → crop area → aggregate to coarse cells → convert back to fraction.

---

## Files

- **Crop mask (fine)**: `/home/chc-shrad/DATA/Crop_yield_forecasting/Crop_masks/lu_et_al/Global-cropland-percentage-map.nc`
  — variable: `crop_mask`, coords: `latitude` / `longitude`, values 0–100 (percentage)
- **SIF data (coarse / target)**: `/home/chc-shrad/DATA/SIF/fusion_SCIAMACHY_GOME-2/SIF_SCIAMACHY_GOME2_Harmonized.*_subsetted.nc4`
  — coords: `lat` / `lon`

---

## Phase 1 — Load & inspect grids

1. Load the crop mask with `xr.open_dataset`, extract the `crop_mask` DataArray; rename coords to `lat`/`lon` for consistency.
2. Load one SIF file (single month) with `xr.open_dataset` to get the target coarse `lat`/`lon` grid.
3. Print Δlat / Δlon of each grid to confirm fine vs. coarse resolution.

---

## Phase 2 — Compute fine-resolution crop area

4. Write a helper `compute_cell_area(lat, delta_lon_deg, delta_lat_deg)` using the spherical Earth formula:

   ```
   area = R² × |Δlon_rad| × |sin(lat_N_rad) − sin(lat_S_rad)|
   ```

   where R = 6371 km and lat_N / lat_S are the northern/southern edges of each cell.

5. Apply the helper over the fine crop mask `lat` coordinate to produce a 2-D DataArray `fine_cell_area` (km²).
6. Convert crop percentage to fraction: `crop_fraction = crop_mask' (range 0–1).
7. Compute **fine crop area**: `fine_crop_area = crop_fraction × fine_cell_area` (km²).

---

## Phase 3 — Aggregate fine crop area onto the coarse SIF grid

8. Compute SIF cell edges from the SIF lat/lon center arrays (half-step offsets).
9. For each coarse SIF cell, sum all `fine_crop_area` values whose centers fall within that cell's bounding box.
   - Use `np.digitize` to assign each fine cell a coarse-cell bin index along lat and lon.
   - Use `xarray.DataArray.groupby` (or a `pandas`-style aggregation) to sum within each bin → `coarse_crop_area` (km²) on the SIF grid.
   - No xESMF required — pure numpy/xarray approach.

---

## Phase 4 — Compute coarse-resolution crop fraction

10. Compute **coarse cell area** using the same helper over the SIF `lat` coordinate → `coarse_cell_area` DataArray (km²).
11. Divide: `coarse_crop_fraction = coarse_crop_area / coarse_cell_area` (range 0–1).
12. Clip to [0, 1] to remove any floating-point noise.

---

## Phase 5 — Output & integration

13. Rename output dimensions to `lat`/`lon` to match the SIF data (for `.salem.subset()` and `.where()` compatibility).
14. Use as a drop-in replacement for the current `crop_mask_regrid` (which uses `interp(method='nearest')` and does **not** conserve area).
15. Save the result to NetCDF for reuse.

---

## Verification

1. **Area conservation**: `coarse_crop_fraction × coarse_cell_area` summed globally should ≈ `fine_crop_area` summed globally.
2. **Visual check**: side-by-side plots of the fine and coarse masks over Africa to confirm spatial patterns are preserved.
3. **Spot check**: manually sum fine fractions × fine areas within one coarse cell and compare to the regridded value.

---

## Key decisions

| Decision | Choice |
|---|---|
| Area formula | Spherical Earth, R = 6371 km (sufficient for 0.05° → 0.5°) |
| Aggregation | Sum of fine crop areas per coarse cell (flux-preserving) |
| Library | Pure numpy / xarray — no xESMF assumed |
| Scope | Crop mask regridding only; SIF data itself is unchanged |
