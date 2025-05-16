from netCDF4 import Dataset
import numpy as np

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

    for i in range(steps):
        y = y1 + ((x - x1)/(x2 - x1))*(y2 - y1)
        y_vals.append(y)
        x += 1
    
    print(y_vals)
    return y_vals

# only works when adding values at the end of the list:
def insert_after_value(main_list, insert_list, start_value):
    try:
        index = main_list.index(start_value)
        return (
            main_list[:index + 1] +
            insert_list +
            main_list[index + 1:]
        )
    except ValueError:
        print(f"Value {start_value} not found in list.")
        return main_list

def fill_points(data):

    data_size = len(data)
    iterator = 0
    iterator_20 = 0
    data_20 = []

    for i in range(data_size - 1):

        data_20[iterator_20].append(data[iterator])
        
        first_val = data[iterator]
        second_val = data[iterator+1]
        insertion_vals = linear_interpolation(first_val, second_val, num_steps)
        
        iterator_20 += 1
        insert_after_value(data_20, insertion_vals, iterator_20)

        iterator += 1
        iterator_20 += num_steps
    
    print(data_20)
    return data_20

fill_points(dry_cor_01)
