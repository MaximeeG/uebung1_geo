from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt

# === CONFIGURATION ===
write_complete_cycle = True  # True = full orbit, False = Müggelsee only
show_plots = True            # Toggle to control whether plots are shown

LATITUDE_MIN = 52.33
LATITUDE_MAX = 52.47
LONGITUDE_MIN = 13.60
LONGITUDE_MAX = 13.70

# === LOAD DATASET ===
ds = Dataset(r"data\S3A_SR_2_LAN_HY_20160324T195805_20160324T203026_20230907T175812_1941_002_171______LN3_R_NT_005.SEN3\standard_measurement.nc")
# print(ds.variables.keys())

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
# === LOAD ALTITUDE AND TIDE CORRECTIONS ===
altitude_20ghz = get_variable("alt_20_ku")  # altitude of the satellite above reference ellipsoid
solid_earth_tide_1ghz = get_variable("solid_earth_tide_01")
pole_tide_1ghz = get_variable("pole_tide_01")
# === LOAD GEOID UNDULATION ===
geoid_1ghz = get_variable("geoid_01")

# === INTERPOLATION FUNCTION (by time) ===
def interpolate_to_20ghz_by_time(data_1ghz):
    return np.interp(time_20ghz, time_1ghz, data_1ghz)
# === INTERPOLATE to match 20GHz timestamps ===
wet_20ghz = interpolate_to_20ghz_by_time(wet_1ghz)
dry_20ghz = interpolate_to_20ghz_by_time(dry_1ghz)
iono_20ghz = interpolate_to_20ghz_by_time(iono_1ghz)
solid_earth_tide_20ghz = interpolate_to_20ghz_by_time(solid_earth_tide_1ghz)
pole_tide_20ghz = interpolate_to_20ghz_by_time(pole_tide_1ghz)
geoid_20ghz = interpolate_to_20ghz_by_time(geoid_1ghz)

# === CALCULATE CORRECTED RANGE ===
corrected_range = range_20ghz + wet_20ghz + dry_20ghz + iono_20ghz
# === CALCULATE LLH AND CORRECTED LLH ===
llh = altitude_20ghz - corrected_range
corrected_llh = llh - solid_earth_tide_20ghz - pole_tide_20ghz
# === CALCULATE ORTHOMETRIC HEIGHT ===
orthometric_height = corrected_llh - geoid_20ghz

# === FILTER TO MÜGGELSEE AREA ===
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
    altitude_20ghz = altitude_20ghz[mask_local] # altitude above the reference ellipsoid
    solid_earth_tide_20ghz = solid_earth_tide_20ghz[mask_local]
    pole_tide_20ghz = pole_tide_20ghz[mask_local]
    llh = llh[mask_local]
    corrected_llh = corrected_llh[mask_local]
    geoid_20ghz = geoid_20ghz[mask_local]
    orthometric_height = orthometric_height[mask_local]

# === EXPORT RANGE TO CSV ===
range_csv_name = f"range_{'global' if write_complete_cycle else 'local'}.csv"
with open(range_csv_name, "w") as f_range:
    f_range.write("Time,Latitude,Longitude,Range,CorrectedRange,WetTropoCorrection,DryTropoCorrection,IonoCorrection\n")
    skipped_rng = 0
    for t, lat, lon, rng, corr, wet, dry, iono in zip(time_20ghz, latitudes, longitudes, range_20ghz, corrected_range, wet_20ghz, dry_20ghz, iono_20ghz):
        if any(np.isnan([rng, wet, dry, iono])):
            skipped_rng += 1
            continue
        f_range.write(f"{t},{lat}, {lon},{rng:.4f},{corr:.4f},{wet:.4f},{dry:.4f},{iono:.4f}\n")

# === EXPORT LLH and ORTHO TO CSV ===
llh_ortho_csv_name = f"llh_{'global' if write_complete_cycle else 'local'}.csv"
with open(llh_ortho_csv_name, "w") as f_llh_ortho:
    f_llh_ortho.write("Time,Latitude,Longitude,LLH,CorrectedLLH,OrthometricHeight\n")
    skipped_llh = 0
    for t, lat, lon, h, corh, ortho in zip(time_20ghz, latitudes, longitudes, llh, corrected_llh, orthometric_height):
        if any(np.isnan([h, corh, ortho])):
            skipped_llh += 1
            continue
        f_llh_ortho.write(f"{t},{lat},{lon},{h:.4f},{corh:.4f},{ortho:.4f}\n")

print("===== INFO =====")
print(f"Print entire cycle: {write_complete_cycle}")
print("Calculation finished, file generated.")
print(f"{skipped_rng} Range values were skipped due to NaN.")
print(f"{skipped_llh} LLH entries were skipped due to NaN.\n")



if show_plots:
    # === PLOT RANGE ORIGINAL vs. CORRECTED ===
    plt.figure(figsize=(16, 9))
    plt.plot(range_20ghz, label="Original Range (20GHz)")
    plt.plot(corrected_range, label="Corrected Range", linestyle="--")
    plt.xlabel("Measurement Index")
    plt.ylabel("Range (m)")
    plt.title("Original vs Corrected Range")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # === PLOT RANGE DIFFERENCE ===
    range_diff = range_20ghz - corrected_range

    plt.figure(figsize=(16, 9))
    plt.plot(range_diff, label="Difference: Original - Corrected")
    plt.xlabel("Measurement Index")
    plt.ylabel("Difference in Range (m)")
    plt.title("Difference Between Original and Corrected Range")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # === PLOT RANGE CORRECTIONS ===
    plt.figure(figsize=(16, 9))
    plt.gca().invert_yaxis()
    plt.plot(wet_20ghz+dry_20ghz+iono_20ghz, label="All Corrections", linestyle='dotted', color='black')
    plt.plot(dry_20ghz, label="Dry Tropo Correction", color='orange')
    plt.plot(wet_20ghz, label="Wet Tropo Correction", color='blue')
    plt.plot(iono_20ghz, label="Ionospheric Correction")
    plt.xlabel("Measurement Index")
    plt.ylabel("Correction (m)")
    plt.title("Atmospheric Corrections Along Flight Path")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # === PLOT LLH vs. CORRECTED ===
    plt.figure(figsize=(16, 9))
    # plt.plot(llh, label="LLH")
    plt.plot(corrected_llh, label="Corrected LLH")
    plt.xlabel("Measurement Index")
    plt.ylabel("Height above Ellipsoid (m)")
    plt.title("LLH Relative to Reference Ellipsoid")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # === PLOT TIDAL CORRECTIONS ===
    plt.figure(figsize=(16, 9))
    plt.plot(solid_earth_tide_20ghz + pole_tide_20ghz, label="Total Tidal Correction", linestyle='dotted', color='black')
    plt.plot(solid_earth_tide_20ghz, label="Solid Earth Tide Correction")
    plt.plot(pole_tide_20ghz, label="Pole Tide Correction")
    plt.xlabel("Measurement Index")
    plt.ylabel("Correction (m)")
    plt.title("Tidal Corrections Along Flight Path")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # === PLOT ORTHOMETRIC HEIGHT ===
    plt.figure(figsize=(16, 9))
    plt.plot(orthometric_height, label="Orthometric Height")
    plt.xlabel("Measurement Index")
    plt.ylabel("Height (m)")
    plt.title("Orthometric Height")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()



# === CALCULATE AVERAGE CORRECTIONS ===
valid_mask = ~np.isnan(wet_20ghz) & ~np.isnan(dry_20ghz) & ~np.isnan(iono_20ghz)

wet_avg = np.nanmean(wet_20ghz[valid_mask])
dry_avg = np.nanmean(dry_20ghz[valid_mask])
iono_avg = np.nanmean(iono_20ghz[valid_mask])
total_avg_correction = wet_avg + dry_avg + iono_avg

print("===== AVERAGE RANGE CORRECTIONS =====")
print(f"Wet Tropospheric Correction Avg:   {wet_avg:.4f} m")
print(f"Dry Tropospheric Correction Avg:   {dry_avg:.4f} m")
print(f"Ionospheric Correction Avg:        {iono_avg:.4f} m")
print("------------------------------------------")
print(f"Total Average Range Correction:    {total_avg_correction:.4f} m\n")
