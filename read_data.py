from netCDF4 import Dataset
import numpy as np

# Variables:
# range_water_20_ku
# mod_wet_tropo_cor_meas_altitude_01
# mod_dry_tropo_cor_meas_altitude_01
# iono_cor_gim_01_ku

ds = Dataset(r".\data\S3A_SR_2_LAN_HY_20160324T195805_20160324T203026_20230907T175812_1941_002_171______LN3_R_NT_005.SEN3\standard_measurement.nc")

def to_list(var):
    # Grab the data (returns a NumPy ndarray or MaskedArray)
    a = ds.variables[var][:]

    # If it’s a MaskedArray, replace masked values with NaN
    if np.ma.isMaskedArray(a):
        a = a.filled(np.nan)

    # Convert the ndarray to a (possibly nested) Python list
    return a.tolist()


range_w_temp = to_list("range_water_20_ku")
range_w = []

# What should we do with NaN cases? I will pop them from the list for now...
for i in range(len(range_w_temp)):
    if str(range_w_temp[i]) != "nan":
        range_w.append(range_w_temp[i])


wet_cor = to_list("mod_wet_tropo_cor_meas_altitude_01")
dry_cor = to_list("mod_dry_tropo_cor_meas_altitude_01")
iono_cor = to_list("iono_cor_gim_01_ku")

cycle_size = len(range_w)
step_size = len(wet_cor)

num_steps = np.(cycle_size / step_size)
