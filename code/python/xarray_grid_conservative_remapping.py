import xarray_regrid
import xarray as xr
lon_min, lon_max = -20, 55
lat_min, lat_max = -40, 40

CROP_MASK_PATH = '/home/chc-shrad/DATA/Crop_yield_forecasting/Crop_masks/lu_et_al/Global-cropland-percentage-map.nc'
CROP_MASK_VAR = 'crop_mask'
REMAPPED_PATH = '/home/chc-source/shrad/Scripts/Funded_projects/2026/crop_yield_forecasting/data/crop_mask_fraction_on_sif_grid_conservative_xarray_grid.nc'
fine_ds = xr.open_dataset(CROP_MASK_PATH)
ds_grid = xr.open_dataset(f'/home/chc-shrad/DATA/SIF/fusion_SCIAMACHY_GOME-2/SIF_SCIAMACHY_GOME2_Harmonized.sif005_201703_subsetted.nc4')
ds_grid = ds_grid.rename({'lon': 'longitude', 'lat': 'latitude'})
fine_crop_pct = fine_ds[CROP_MASK_VAR].sel(longitude=slice(lon_min, lon_max), latitude=slice(lat_min, lat_max))
# or, for example:
remap_ds = fine_ds.regrid.conservative(ds_grid.sel(longitude=slice(lon_min, lon_max), latitude=slice(lat_min, lat_max)))
print ("Writing remapped crop mask to netcdf file:", REMAPPED_PATH)
remap_ds.to_netcdf(REMAPPED_PATH)