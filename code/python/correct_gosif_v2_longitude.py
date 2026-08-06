import xarray as xr
import glob

files = sorted(glob.glob('/home/chc-shrad/DATA/SIF/GOSIF_v2/netcdf/monthly/GOSIF_v2_*.nc'))

# Open first file as reference to get x and y coordinates
with xr.open_dataset(files[0]) as ds_ref:
    x_ref = ds_ref.x.values
    y_ref = ds_ref.y.values

# Use preprocess to impose reference coordinates on all files
def preprocess(ds):
    ds["x"] = x_ref
    ds["y"] = y_ref
    return ds

# Now open all files
ds_combined = xr.open_mfdataset(
    files,
    combine="by_coords",
    preprocess=preprocess
)

outfile = '/home/chc-shrad/DATA/SIF/GOSIF_v2/netcdf/monthly/GOSIF_v2_combined_longitude_corrected.nc'
print (f"Writing {outfile}")
ds_combined.to_netcdf(outfile)