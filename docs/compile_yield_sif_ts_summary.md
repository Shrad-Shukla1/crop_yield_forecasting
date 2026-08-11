# Methodology for compiling seasonal SIF and crop yield for each of the sub-national units 

1. **Setup**
   - Imports the required libraries and defines directories for SIF outputs, crop mask, crop data, and administrative boundaries.
   - Loads crop production CSV and its GeoPackage boundary file.

2. **Load SIF data**
   - Creates a monthly‑end date range from 2003‑01‑01 to 2017‑12‑31.
   - Opens the netCDF SIF files as a multi‑dataset and aligns the `time` coordinate.
   - Loads the crop‑mask raster dataset.

3. **Loop over crops** (Maize, Wheat, Rice, Sorghum, Millet)
   - Filters crop data each of the crop type, QC flag 0, and harvest years 2003‑2017 (consistent with SIF data availability).
   - Deduplicates on relevant columns to get unique crop subsets. This is needed because for the same crop and administrative unit, there can be different types of crop production systems (e.g. rainfed and irrigated) and season name (e.g. summer and winter)
   - For each subset:
     * Detects changes in `fnid` (fnid is a code for administrative unit) and, if changed, subsets both SIF and crop mask rasters to the corresponding administrative polygon for that fnid using `salem.subset`.
     * Determines the planting/harvest dates and builds a time slice from the first day of planting month to the last day of harvest month.
     * Extracts the SIF time series for the season based on the time slice build above. For example, for Maize crop type over South Africa, the growing season spans from October to April, so for each harvest year (the growing season remains constant) and we select extract a temporal slice of October-April data from SIF for each year. 
     * After extracting time slice of SIF for a given growing season, "seasonal SIF" is calculated using the following approach:
       - **Mean SIF** over the growing season → multiplied by crop fraction mask, zero values masked → spatial mean over the administrative boundary → stored as `sif_mean`
       - **Max SIF** over the growing season → multiplied by crop fraction mask, zero values masked → spatial mean over the administrative boundary → stored as `sif_max`.
     * Appends a dictionary with metadata and the two versions of spatially aggregated SIF values to `results`.

4. **Finalize**
   - Converts `results` into a DataFrame and saves it as a CSV file in `datadir`, named to reflect the year range and crop type.

The script combines crop‑production records with spatially sub‑sampled SIF data to compute, per unique administrative unit, the mean and maximum SIF values over the growing season, and records these alongside yield and metadata for downstream analysis.
