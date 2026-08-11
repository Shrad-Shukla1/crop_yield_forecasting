# `compile_yield_sif_ts.py` Methodology

1. **Setup**
   - Imports the required libraries and defines directories for SIF outputs, crop mask, crop data, and administrative boundaries.
   - Loads crop production CSV and its GeoPackage boundary file.

2. **Load SIF data**
   - Creates a monthly‑end date range from 2003‑01‑01 to 2017‑12‑31.
   - Opens the netCDF SIF files as a multi‑dataset and aligns the `time` coordinate.
   - Loads the crop‑mask raster dataset.

3. **Loop over crops** (Maize, Wheat, Rice, Sorghum, Millet)
   - Filters crop data for the current product, QC flag 0, and harvest years 2003‑2017.
   - Deduplicates on relevant columns to get unique crop subsets.
   - For each subset:
     * Detects changes in `fnid` and, if changed, subsets both SIF and crop mask rasters to the corresponding administrative polygon using `salem.subset`.
     * Determines the planting/harvest dates and builds a time slice from the first day of planting month to the last day of harvest month.
     * Extracts the SIF time series for the season and computes:
       - **Mean SIF** over the season → multiplied by crop fraction mask, zero values masked → stored as `sif_mean`.
       - **Max SIF** over the season → multiplied by crop fraction mask, zero values masked → stored as `sif_max`.
     * Appends a dictionary with metadata and the two computed metrics to `results`.

4. **Finalize**
   - Converts `results` into a DataFrame and saves it as a CSV file in `datadir`, named to reflect the year range and crop type.

The script combines crop‑production records with spatially sub‑sampled SIF data to compute, per unique administrative unit, the mean and maximum SIF values over the growing season, and records these alongside yield and metadata for downstream analysis.
