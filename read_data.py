import xarray as xr
import os

# Path to the .SEN3 product directory
sen3_path = r'data\S3A_SR_2_LAN_HY_20240923T195824_20240923T203042_20241019T233137_1938_117_171______PS1_O_NT_005.SEN3'

# Path to a specific NetCDF file within the product
nc_file = os.path.join(sen3_path, 'standard_measurement.nc')  # or 'geophysical_corrections.nc', etc.

# Open the NetCDF dataset
ds = xr.open_dataset(nc_file)

# Show dataset structure
print(ds)

# Example: Access and print 'alt' or any variable of interest
print(ds.data_vars)  # List available variables
