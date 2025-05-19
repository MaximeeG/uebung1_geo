from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt

# Load dataset
ds = Dataset(r"data\S3A_SR_2_LAN_HY_20241020T203045_20241020T203859_20241116T003153_0494_118_171______PS1_O_NT_005.SEN3\standard_measurement.nc")

# Function to get variable data
def get_variable(name):
    var = ds.variables[name][:]
    return var.filled(np.nan) if np.ma.isMaskedArray(var) else var

# Load variables
range_20ghz = get_variable("range_water_20_ku")
wet_1ghz = get_variable("mod_wet_tropo_cor_meas_altitude_01")
dry_1ghz = get_variable("mod_dry_tropo_cor_meas_altitude_01")
iono_1ghz = get_variable("iono_cor_gim_01_ku")

# Remove NaNs from range (and keep only valid range entries)
valid_mask = ~np.isnan(range_20ghz)
range_20ghz = range_20ghz[valid_mask]
n_range = len(range_20ghz)

# Interpolation setup
n_steps = len(wet_1ghz)
x_interp = np.linspace(0, n_steps - 1, n_range)

def interpolate_to_20ghz(data_1ghz):
    x_orig = np.arange(len(data_1ghz))
    return np.interp(x_interp, x_orig, data_1ghz)

# Interpolate correction terms to 20GHz
wet_20ghz = interpolate_to_20ghz(wet_1ghz)
dry_20ghz = interpolate_to_20ghz(dry_1ghz)
iono_20ghz = interpolate_to_20ghz(iono_1ghz)

# Calculate corrected range
corrected_range = range_20ghz + wet_20ghz + dry_20ghz + iono_20ghz

# Plot
plt.figure(figsize=(10, 5))
plt.plot(range_20ghz, label="Original Range (20GHz)")
plt.plot(corrected_range, label="Corrected Range", linestyle="--")
plt.xlabel("Measurement Index")
plt.ylabel("Range (m)")
plt.title("Original vs Corrected Range")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Calculate the difference between original and corrected range
range_diff = range_20ghz - corrected_range

# Plot the difference
plt.figure(figsize=(10, 5))
plt.plot(range_diff, label="Difference of Range (Original - Corrected)")
plt.xlabel("Measurement Index")
plt.ylabel("Difference in Range (m)")
plt.title("Difference Between Original and Corrected Range")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
