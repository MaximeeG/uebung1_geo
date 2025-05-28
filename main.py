from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt

# === CONFIGURATION ===
write_complete_cycle = False  # True = full orbit, False = Müggelsee only
LATITUDE_MIN = 52.334067
LATITUDE_MAX = 52.471998
LONGITUDE_MIN = 13.600
LONGITUDE_MAX = 13.750

# === LOAD DATASET ===
ds = Dataset(r"data\S3A_SR_2_LAN_HY_20160324T195805_20160324T203026_20230907T175812_1941_002_171______LN3_R_NT_005.SEN3\standard_measurement.nc")
print(ds.variables.keys())

def get_variable(name):
    var = ds.variables[name][:]
    return var.filled(np.nan) if np.ma.isMaskedArray(var) else var

# === LOAD LATITUDE AND LONGITUDE ===
latitudes = get_variable("lat_20_ku")
longitudes = get_variable("lon_20_ku")

# === LOAD TIME VARIABLES ===
time_1ghz = get_variable("time_01")
time_20ghz = get_variable("time_20_ku")

# === LOAD VARIABLES ===
range_20ghz = get_variable("range_water_20_ku")
wet_1ghz = get_variable("mod_wet_tropo_cor_meas_altitude_01")
dry_1ghz = get_variable("mod_dry_tropo_cor_meas_altitude_01")
iono_1ghz = get_variable("iono_cor_gim_01_ku")

# === INTERPOLATION FUNCTION (by time) ===
def interpolate_to_20ghz_by_time(data_1ghz):
    return np.interp(time_20ghz, time_1ghz, data_1ghz)

# === INTERPOLATE to match 20GHz timestamps ===
wet_20ghz = interpolate_to_20ghz_by_time(wet_1ghz)
dry_20ghz = interpolate_to_20ghz_by_time(dry_1ghz)
iono_20ghz = interpolate_to_20ghz_by_time(iono_1ghz)

# === CALCULATE CORRECTED RANGE ===
corrected_range = range_20ghz + wet_20ghz + dry_20ghz + iono_20ghz

# === OPTIONAL: FILTER TO MÜGGELSEE AREA ===
if not write_complete_cycle:
    mask_local = (  (latitudes >= LATITUDE_MIN) & (latitudes <= LATITUDE_MAX) &
                    (longitudes >= LONGITUDE_MIN) & (longitudes <= LONGITUDE_MAX))
    time_20ghz = time_20ghz[mask_local]
    latitudes = latitudes[mask_local]
    longitudes = longitudes[mask_local]
    range_20ghz = range_20ghz[mask_local]
    wet_20ghz = wet_20ghz[mask_local]
    dry_20ghz = dry_20ghz[mask_local]
    iono_20ghz = iono_20ghz[mask_local]
    corrected_range = corrected_range[mask_local]

# === EXPORT TO CSV ===
csv_name = f"range_cor_{'global' if write_complete_cycle else 'local'}.csv"
with open(csv_name, "w") as f:
    f.write("Time,Latitude,Longitude,Range,CorrectedRange,WetTropoCorrection,DryTropoCorrection,IonoCorrection\n")
    skipped = 0
    for t, lat, lon, rng, corr, wet, dry, iono in zip(time_20ghz, latitudes, longitudes, range_20ghz, corrected_range, wet_20ghz, dry_20ghz, iono_20ghz):
        if any(np.isnan([rng, wet, dry, iono])):
            skipped += 1
            continue
        f.write(f"{t},{lat}, {lon},{rng:.4f},{corr:.4f},{wet:.4f},{dry:.4f},{iono:.4f}\n")

print("--------------------------")
print(f"Print entire cycle: {write_complete_cycle}")
print("Calculation finished, file generated.")
print(f"{skipped} values were skipped due to NaN.")
print("--------------------------")

# === PLOT: ORIGINAL vs CORRECTED ===
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

# === PLOT: DIFFERENCE ===
range_diff = range_20ghz - corrected_range

plt.figure(figsize=(10, 5))
plt.plot(range_diff, label="Difference: Original - Corrected")
plt.xlabel("Measurement Index")
plt.ylabel("Difference in Range (m)")
plt.title("Difference Between Original and Corrected Range")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()