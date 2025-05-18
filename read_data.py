from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt

# Variables:
# range_water_20_ku
# mod_wet_tropo_cor_meas_altitude_01
# mod_dry_tropo_cor_meas_altitude_01
# iono_cor_gim_01_ku

ds = Dataset(r"M:\CODING\GeodErdbeobachtung\uebung1_geo\Data\S3A_SR_2_LAN_HY_20160324T195805_20160324T203026_20230907T175812_1941_002_171______LN3_R_NT_005.SEN3\standard_measurement.nc")

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

wet_cor_01 = to_list("mod_wet_tropo_cor_meas_altitude_01")
dry_cor_01 = to_list("mod_dry_tropo_cor_meas_altitude_01")
iono_cor_01 = to_list("iono_cor_gim_01_ku")

# Problem: range is in 20GHz, all other variables in 1GHz
# -> Add missing points through linear regression

cycle_size = len(range_w)
step_size = len(wet_cor_01)

num_steps = int(np.round((cycle_size/step_size), decimals=0))

# x1 = 1
# x2 = steps
# x = current point
def linear_interpolation(y1, y2, steps):
    
    y_vals = []
    x = 1
    x1 = 1
    x2 = steps

    for i in range(steps - 1):
        y = y1 + ((x - x1)/(x2 - x1))*(y2 - y1)
        y_vals.append(y)
        x += 1
    
    return y_vals

def fill_points(data):

    data_size = len(data)
    iterator = 0
    data_20 = []
    
    for i in range(data_size - 1):
        
        data_20.append(data[iterator])
        
        first_val = data[iterator]
        second_val = data[iterator+1]
        insertion_vals = linear_interpolation(first_val, second_val, num_steps)
        
        data_20.extend(insertion_vals)
        # data_20.append(1111111)
        iterator += 1
    
    return data_20

# the algorithm above is not great, and the resulting lists aren't exactly the same size. I will pop the extra values from the interpolated list
def interpolate20(data):

    data20_temp = fill_points(data)

    overshoot = len(data20_temp) - len(range_w)

    data20 = data20_temp[:len(data20_temp)-overshoot]

    return data20

# First calculation: Corrected range = Range + Wet Tropo Correction + Dry Tropo Correction + Iono Correction

wet_cor_20 = interpolate20(wet_cor_01)
dry_cor_20 = interpolate20(dry_cor_01)
iono_cor_20 = interpolate20(iono_cor_01)

range_cor = []

for i in range(len(range_w)):
    range_cor.append(range_w[i] + wet_cor_20[i] + dry_cor_20[i] + iono_cor_20[i])

# plot:
x_axis = list(range(len(range_w)))

plt.plot(x_axis, range_w, label="Range")
plt.plot(x_axis, range_cor, label="Corrected Range")

plt.show()