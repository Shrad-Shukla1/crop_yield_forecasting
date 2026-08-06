## Methodology for downscaling reported subnational yields with gridded SIF data
Note that the following is currently implemented only over South Africa and for the maize crop. In future, I will expand to other countries and other crops. 

### 1) Regrid the Lu crop mask onto the crop mask on the SIF grid (area-conservative)
Implemented in:
- `python/conservative_cropmask_remap.py`
- Verified in `notebook/verify_conservative_cropmask_remap.ipynb`
Process:
1. Read fine crop mask (`crop_mask`) and SIF target grid (`lat`, `lon`).
2. Compute fine-cell area using spherical Earth geometry.
3. Convert fine crop fraction to fine crop area.
4. Aggregate fine crop area to coarse SIF cells using center-in-cell binning.
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
1. Read SIF data and apply the remapped crop mask.
2. Using the polygon for each admin unit in South Africa (SA), we subset crop mask and SIF data for that polygon using `salem.subset`
3. We then simply multiply the subset of crop mask and SIF from the previous step. In other words, we weight SIF grid cells based on the crop fraction in that grid cell.
   Another option of doing the above could be to mask our SIF values from the grid cells where crop fraction is below a certain threshold (say 10% or 25%)  Using the subset crop mask and subset of SIF data we then 
4. For each admin unit in SA, we select reported crop yield data for Maize crop for the main season (referred to as the "summer season" in the harveststat data), and from that also extract planting month, planting year, harvest month and harvest year information.
5. Using the planting and harvest date information, we then subset SIF data for those months that fall in the growing season.
6. Next, for each grid cell we calculate maximum SIF (sif_yearly_max) values during the growing season in each year (this usually occurs within the last 2-3 months before the harvest). We use the sif_yearly_max value as a "seasonal" representation of SIF.
6. Mask SIF with crop fraction and remove non-positive values.

### 3) Downscale admin yield to pixels using SIF weights
Implemented in:
- `notebook/downscale_yield_with_SIF.ipynb` (current active method)
Process:
1. Build year-aligned subnational yield vector as an xarray `DataArray` (`year` dimension).
2. Compute max-normalized SIF weight:
   - `sif_weight = sif_yearly_max / max_over_grid(sif_yearly_max)`
3. Now we normalize SIF weights by grid-cell sum and scale by valid-pixel count.
4. We then multiply the normalized weights by the reported yield.
The above produces disaggregated yield values whose spatial mean matches reported admin yield for each year.

## Results
The results below show some how SIF data compares with the yield data and how SIF disaggregated yield data compares with the SPAM 2020 v2.2 Global yield data that are updated every 5 years or so and represent the spatial variability in yield during the last 5 years. 
SPAM data were downloaded from here: https://www.mapspam.info/data/

> Figure 1: The following figure shows the correlation between seasonal SIF and reported sub-national Maize yield, and the same with seasonal rainfall. The crop fraction used for the analysis is also provided. 
![png](downscale_yield_with_SIF_files/downscale_yield_with_SIF_6_1.png)
> 
> Figure 2: The following figure compares the normalized values of spatially aggregated seasonal SIF with normalized values of reported Maize yield for the Free State province in South Africa. Both datasets were normalized based on the maximum value during the 2003-2018 period.
> 
![png](downscale_yield_with_SIF_files/downscale_yield_with_SIF_7_1.png)
> 
> Figure 3: The following figure compares disaggregated yield based on weights that come from gridded seasonal SIF max data for the growing season ending in the harvest year shown below. As per production reports 2015 harvest year experienced a moderate drought, 2016 experienced a major drought whereas 2017 was a major surplus production year. The SIF disaggregated yields depict the same variability as well. 
> 
![png](downscale_yield_with_SIF_files/downscale_yield_with_SIF_8_1.png)


> Figure 4: The following figure compares SPAM- 2020-based maize yield in South Africa (this uses FAO national yield data to disaggregate to a gridded scale) with SIF-based gridded yield. In general, there is a good agreement but in some provinces the difference is substantial. I wonder if the source of the difference is the crop mask that I am using. Could it be that the crop mask that I am using is more representative of all crops vs Maize crop only, which is what SPAM uses. I could decide to use a common crop mask which might increase the similarities in the SIF disaggretaed yields with SPAM yield.
> 
![png](downscale_yield_with_SIF_files/downscale_yield_with_SIF_12_1.png)
    

