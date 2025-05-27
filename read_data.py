from netCDF4 import Dataset
import numpy as np
from numpy import array2string
import matplotlib.pyplot as plt

np.set_printoptions(threshold=np.inf)

# Variables:
# lat_20_ku (lat range: 52.334067 to 52.471998)
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

def create_list_20(data_01, total_len):
    
    # create empty list with correct size, to be fille with real AND interpolated data
    empty_20 = np.linspace(0, 0, total_len)
    # calculate how many points need to interpolated -> length20GHz/length1GHz
    num_steps = int(np.round(total_len/len(data_01), decimals=0))

    counter = 0
    selector = 0

    # loop through every entry in the empty list
    for i in range(len(empty_20)):
        counter += 1


        # copy 1GHz (real) data into the empty list in the correct places
        if (counter == num_steps) or (i == 0):

            if selector >= len(data_01):
                break
            empty_20[i] = data_01[selector]
            selector += 1
            counter = 0

        npdata = np.array(empty_20)
        # find indices where the values are non-zero
        nonzero_indices = np.nonzero(npdata)[0]

        # perform interpolation
        interpolated = np.copy(npdata)
        interpolated = np.interp(np.arange(len(npdata)), nonzero_indices, npdata[nonzero_indices])
        
    return interpolated

range_w_20 = to_list("range_water_20_ku")
lat_20 = to_list("lat_20_ku")
wet_cor_01 = to_list("mod_wet_tropo_cor_meas_altitude_01")
dry_cor_01 = to_list("mod_dry_tropo_cor_meas_altitude_01")
iono_cor_01 = to_list("iono_cor_gim_01_ku")

wet_cor_20 = create_list_20(wet_cor_01, len(range_w_20))
dry_cor_20 = create_list_20(dry_cor_01, len(range_w_20))
iono_cor_20 = create_list_20(iono_cor_01, len(range_w_20))
