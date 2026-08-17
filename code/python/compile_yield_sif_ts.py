# %%
# Shrad 2026-08-11
# This script compiles seasonal SIF metrics and crop yield data for different crop types (Maize, Wheat, Rice, Sorghum, Millet) based on the provided crop data and SIF datasets. It subsets the SIF data based on administrative boundaries and calculates mean and maximum SIF values over the growing season for each unique crop subset.
import xarray as xr
import geopandas as gpd
import salem
import pandas as pd
import numpy as np
import os

# %%
## Define data directories and file paths
datadir = '/home/chc-source/shrad/Scripts/Funded_projects/2026/crop_yield_forecasting/data/outputs/sif_vs_yield'
os.makedirs(datadir, exist_ok=True)
crop_mask_dir = '/home/chc-source/shrad/Scripts/Funded_projects/2026/crop_yield_forecasting/data/inputs'
crop_data_dir = '/home/chc-source/shrad/Scripts/Funded_projects/2026/crop_yield_forecasting/data/inputs/hvstat'
crop_data_file = f"{crop_data_dir}/hvstat_africa_data_v1.2.csv"
admin_shapefile = f"{crop_data_dir}/hvstat_africa_boundary_v1.2.gpkg"
crop_data = pd.read_csv(crop_data_file)
admin_shp = gpd.read_file(admin_shapefile)
## Reading SIF data and shape file
syr, eyr = 2003, 2017
date_range = pd.date_range(start=f'{syr}-01-01', end=f'{eyr}-12-31', freq='ME')
sif_data = xr.open_mfdataset(f'/home/chc-shrad/DATA/SIF/fusion_SCIAMACHY_GOME-2/SIF_SCIAMACHY_GOME2_Harmonized.*_subsetted.nc4', 
                            concat_dim='time', combine='nested')
sif_data.coords['time'] = date_range
threshold = 0.1  # Threshold for filtering SIF values

for crop_specific_flag in [False, True]:
    print (f"Processing crop_specific_flag: {crop_specific_flag}")    
    if crop_specific_flag:
        crop_list = ['Maize', 'Wheat', 'Rice', 'Soybean']
    else:
        crop_list = ['Maize', 'Wheat', 'Rice', 'Soybean', 'Sorghum', 'Millet']
    # %%
    for crop_type in crop_list:
        if not crop_specific_flag:
            crop_mask_file = f'{crop_mask_dir}/crop_mask_fraction_on_sif_grid_conservative.nc'
            crop_mask = xr.open_dataset(crop_mask_file)
        else:
            if (crop_type=='Wheat'):
                crop_mask_file = f'{crop_mask_dir}/BEST_remapped_Winter_{crop_type}_crop_fraction.nc'
            else:
                crop_mask_file = f'{crop_mask_dir}/BEST_remapped_{crop_type}_crop_fraction.nc'
        print (f"Reading crop mask for {crop_type} from {crop_mask_file}")
        crop_mask = xr.open_dataset(crop_mask_file)
        # Subsetting crop data for a given crop type, quality control flag, and harvest year range
        sel_crop_data = crop_data[(crop_data['product'] == crop_type) & (crop_data['qc_flag']==0) & (crop_data['harvest_year']>=syr) & (crop_data['harvest_year']<=eyr)]
        # Getting unique subsets of crop data based on relevant columns
        unique_subsets = sel_crop_data[['country', 'fnid', 'product', 'crop_production_system', 'season_name', 'planting_year', 'planting_month', 'harvest_year', 'harvest_month', 'yield']].drop_duplicates()
        fnid = None
        # Loop over unique subsets in crop data to calculate seasonal SIF metrics and store results
        results = []
        for index, subset in unique_subsets.iterrows():
            #print (f"Processing subset: {subset.to_dict()}")

            fnid_new = subset['fnid']
            if fnid_new != fnid:
                fnid = fnid_new
                # Only subset the SIF and crop mask data if the fnid has changed
                print(f"Processing fnid: {fnid} for crop type: {crop_type}")
                fnid_admin_shp = admin_shp[admin_shp['fnid'] == fnid]
                if not fnid_admin_shp.empty:
                    sif_subset = sif_data.salem.subset(shape=fnid_admin_shp, margin=2)
                    crop_mask_subset = crop_mask.salem.subset(shape=fnid_admin_shp, margin=2)
                    flag = True
                else:
                    flag = False
            else:
                pass

            if flag:
                p_year = int(subset['planting_year'])
                p_month = int(subset['planting_month'])
                h_year = int(subset['harvest_year'])
                h_month = int(subset['harvest_month'])
                    
                # Season window: from first day of planting month to end of harvest month
                season_start = pd.Timestamp(p_year, p_month, 1)
                season_end = pd.Timestamp(h_year, h_month, 1) + pd.offsets.MonthEnd(1)
                sif_season = sif_subset.sel(time=slice(season_start, season_end))['SIF_740_daily_corr']

                # Calculating different representation of seasonal SIF
                # Average of SIF over the growing season
                sif_season_mean = sif_season.mean(dim='time', skipna=True)
                sif_season_mean_masked = sif_season_mean.where(crop_mask_subset['crop_fraction']>threshold, other=np.nan)
            
                # Maximum of SIF over the growing season
                sif_season_max = sif_season.max(dim='time', skipna=True)
                sif_season_max_masked = sif_season_max.where(crop_mask_subset['crop_fraction']>threshold, other=np.nan)

                # Append to results
                results.append({
                    'country': subset['country'],
                    'fnid': subset['fnid'],
                    'product':subset['product'],
                    'crop_production_system':subset['crop_production_system'],
                    'season_name':subset['season_name'],
                    'planting_month': subset['planting_month'],
                    'planting_year': subset['planting_year'],
                    'harvest_month': subset['harvest_month'],
                    'harvest_year': subset['harvest_year'],
                    'yield': subset['yield'],
                    'sif_mean': sif_season_mean_masked.mean().values,
                    'sif_max': sif_season_max_masked.mean().values,
                })
                
            else:
                print(f"No shape file found for fnid: {fnid}. Skipping this subset.")
                continue

        results_df = pd.DataFrame(results)

        # Save results to CSV
        if not crop_specific_flag:
            output_file = f"{datadir}/sif_and_yield_{syr}_{eyr}_{crop_type}_using_all_crop_mask.csv"
        else:
            output_file = f"{datadir}/sif_and_yield_{syr}_{eyr}_{crop_type}_using_BEST_crop_specific_mask.csv"
        print (f"Saving results to {output_file}")
        results_df.to_csv(output_file, index=False)


