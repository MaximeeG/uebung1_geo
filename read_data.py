from netCDF4 import Dataset
rootgrp = Dataset(r"data\S3A_SR_2_LAN_HY_20241020T203045_20241020T203859_20241116T003153_0494_118_171______PS1_O_NT_005.SEN3\standard_measurement.nc", "r", format="NETCDF4")
print(rootgrp.data_model)
print("-------------------")
print(rootgrp.variables.keys())
