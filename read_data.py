from netCDF4 import Dataset
rootgrp = Dataset(r"data\S3A_SR_2_LAN_HY_20241020T203045_20241020T203859_20241116T003153_0494_118_171______PS1_O_NT_005.SEN3\standard_measurement.nc", "r", format="NETCDF4")
# print(rootgrp.data_model)
# print("-------------------")
# print(rootgrp.variables.keys())

# Relevante Variablen extrahieren
range_ku = rootgrp.variables['range_water_20_ku'][:]
wet_cor = rootgrp.variables['mod_wet_tropo_cor_meas_altitude_01'][:]
dry_cor = rootgrp.variables['mod_dry_tropo_cor_meas_altitude_01'][:]
iono_cor = rootgrp.variables['iono_cor_gim_01_ku'][:]

print(range_ku.shape)
print(wet_cor.shape)
print(dry_cor.shape)
print(iono_cor.shape)

print(rootgrp.variables['range_water_20_ku'].dimensions)
print(rootgrp.variables['mod_wet_tropo_cor_meas_altitude_01'].dimensions)
print(rootgrp.variables['mod_dry_tropo_cor_meas_altitude_01'].dimensions)
print(rootgrp.variables['iono_cor_gim_01_ku'].dimensions)