import os
import re
from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# === CONFIGURATION ===
write_complete_cycle = False  # True = full orbit, False = Müggelsee and Virtual Station
show_plots = False            # Toggle to control whether plots are shown

# === DATA FOLDER ===
base_dir = r"C:\Users\bruno\Documents\Sentinel-3A Data"

def extract_start_time(folder_name):
    match = re.search(r"_(\d{8}T\d{6})_", folder_name)
    return match.group(1) if match else ""

sen3_dirs = [
    os.path.join(base_dir, d)
    for d in os.listdir(base_dir)
    if d.endswith(".SEN3") and os.path.isdir(os.path.join(base_dir, d))
]
sen3_dirs.sort(key=lambda x: extract_start_time(os.path.basename(x)))

# === Müggelsee ===
LATITUDE_MIN = 52.33
LATITUDE_MAX = 52.47
LONGITUDE_MIN = 13.60
LONGITUDE_MAX = 13.70

# === Virtual Station ===
station_lat = (52.4266 + 52.3996) / 2
station_lon = (13.6435 + 13.6566) / 2
# Define a small radius around the point
station_delta = 0.01

def get_variable(name):
    var = ds.variables[name][:]
    return var.filled(np.nan) if np.ma.isMaskedArray(var) else var

# === ACCUMULATORS ===
all_latitudes = []
all_longitudes = []
all_time_20ghz = []
all_range_20ghz = []
all_wet_20ghz = []
all_dry_20ghz = []
all_iono_20ghz = []
all_corrected_range = []
all_altitude_20ghz = []
all_solid_earth_tide = []
all_pole_tide = []
all_llh = []
all_corrected_llh = []
all_geoid = []
all_orthometric_height = []

for sen3_folder in sen3_dirs:
    print(f"Processing: {os.path.basename(sen3_folder)}")
    nc_path = os.path.join(sen3_folder, "standard_measurement.nc")
    if not os.path.isfile(nc_path):
        print(f"Missing file in {sen3_folder}, skipping.")
        continue

    ds = Dataset(nc_path)

    def get_variable(name):
        var = ds.variables[name][:]
        return var.filled(np.nan) if np.ma.isMaskedArray(var) else var

    latitudes = get_variable("lat_20_ku")
    longitudes = get_variable("lon_20_ku")
    time_1ghz = get_variable("time_01")
    time_20ghz = get_variable("time_20_ku")

    range_20ghz = get_variable("range_water_20_ku")
    wet_1ghz = get_variable("mod_wet_tropo_cor_meas_altitude_01")
    dry_1ghz = get_variable("mod_dry_tropo_cor_meas_altitude_01")
    iono_1ghz = get_variable("iono_cor_gim_01_ku")

    altitude_20ghz = get_variable("alt_20_ku")
    solid_earth_tide_1ghz = get_variable("solid_earth_tide_01")
    pole_tide_1ghz = get_variable("pole_tide_01")
    geoid_1ghz = get_variable("geoid_01")

    def interpolate(data): return np.interp(time_20ghz, time_1ghz, data)
    wet_20ghz = interpolate(wet_1ghz)
    dry_20ghz = interpolate(dry_1ghz)
    iono_20ghz = interpolate(iono_1ghz)
    solid_earth_tide_20ghz = interpolate(solid_earth_tide_1ghz)
    pole_tide_20ghz = interpolate(pole_tide_1ghz)
    geoid_20ghz = interpolate(geoid_1ghz)

    corrected_range = range_20ghz + wet_20ghz + dry_20ghz + iono_20ghz
    llh = altitude_20ghz - corrected_range
    corrected_llh = llh - solid_earth_tide_20ghz - pole_tide_20ghz
    orthometric_height = corrected_llh - geoid_20ghz

    # === Append all data ===
    all_latitudes.append(latitudes)
    all_longitudes.append(longitudes)
    all_time_20ghz.append(time_20ghz)
    all_range_20ghz.append(range_20ghz)
    all_wet_20ghz.append(wet_20ghz)
    all_dry_20ghz.append(dry_20ghz)
    all_iono_20ghz.append(iono_20ghz)
    all_corrected_range.append(corrected_range)
    all_altitude_20ghz.append(altitude_20ghz)
    all_solid_earth_tide.append(solid_earth_tide_20ghz)
    all_pole_tide.append(pole_tide_20ghz)
    all_llh.append(llh)
    all_corrected_llh.append(corrected_llh)
    all_geoid.append(geoid_20ghz)
    all_orthometric_height.append(orthometric_height)

    ds.close()

latitudes = np.concatenate(all_latitudes)
longitudes = np.concatenate(all_longitudes)
time_20ghz = np.concatenate(all_time_20ghz)
range_20ghz = np.concatenate(all_range_20ghz)
wet_20ghz = np.concatenate(all_wet_20ghz)
dry_20ghz = np.concatenate(all_dry_20ghz)
iono_20ghz = np.concatenate(all_iono_20ghz)
corrected_range = np.concatenate(all_corrected_range)
altitude_20ghz = np.concatenate(all_altitude_20ghz)
solid_earth_tide_20ghz = np.concatenate(all_solid_earth_tide)
pole_tide_20ghz = np.concatenate(all_pole_tide)
llh = np.concatenate(all_llh)
corrected_llh = np.concatenate(all_corrected_llh)
geoid_20ghz = np.concatenate(all_geoid)
orthometric_height = np.concatenate(all_orthometric_height)

# === FILTER TO MÜGGELSEE AREA AND VIRTUAL STATION AREA ===
if not write_complete_cycle:
    
    # === FILTER TO VIRTUAL STATION AREA ===
    station_mask = (
        (latitudes >= station_lat - station_delta) & (latitudes <= station_lat + station_delta) &
        (longitudes >= station_lon - station_delta) & (longitudes <= station_lon + station_delta)
    )
    
    station_time = time_20ghz[station_mask]
    station_latitudes = latitudes[station_mask]
    station_longitudes = longitudes[station_mask]
    station_range = range_20ghz[station_mask]
    station_corr_range = corrected_range[station_mask]
    station_llh = llh[station_mask]
    station_corrected_llh = corrected_llh[station_mask]
    station_ortho = orthometric_height[station_mask]
    
    # === FILTER TO MÜGGELSEE AREA ===
    mueggelsee_mask = (  (latitudes >= LATITUDE_MIN) & (latitudes <= LATITUDE_MAX) &
                    (longitudes >= LONGITUDE_MIN) & (longitudes <= LONGITUDE_MAX))
    time_20ghz = time_20ghz[mueggelsee_mask]
    latitudes = latitudes[mueggelsee_mask]
    longitudes = longitudes[mueggelsee_mask]
    range_20ghz = range_20ghz[mueggelsee_mask]
    wet_20ghz = wet_20ghz[mueggelsee_mask]
    dry_20ghz = dry_20ghz[mueggelsee_mask]
    iono_20ghz = iono_20ghz[mueggelsee_mask]
    corrected_range = corrected_range[mueggelsee_mask]
    altitude_20ghz = altitude_20ghz[mueggelsee_mask] # altitude above the reference ellipsoid
    solid_earth_tide_20ghz = solid_earth_tide_20ghz[mueggelsee_mask]
    pole_tide_20ghz = pole_tide_20ghz[mueggelsee_mask]
    llh = llh[mueggelsee_mask]
    corrected_llh = corrected_llh[mueggelsee_mask]
    geoid_20ghz = geoid_20ghz[mueggelsee_mask]
    orthometric_height = orthometric_height[mueggelsee_mask]

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

if not write_complete_cycle:
    # === EXPORT STATION DATA TO CSV ===
    with open("station.csv", "w") as f_station:
        f_station.write("Time,Latitude,Longitude,Range,CorrectedRange,LLH,CorrectedLLH,OrthometricHeight\n")
        skipped_station = 0
        for t, lat, lon, rng, corr_rng, h, corr_h, ortho in zip(
            station_time, station_latitudes, station_longitudes,
            station_range, station_corr_range,
            station_llh, station_corrected_llh, station_ortho
        ):
            if any(np.isnan([rng, corr_rng, h, corr_h, ortho])):
                skipped_station += 1
                continue
            f_station.write(f"{t},{lat},{lon},{rng:.4f},{corr_rng:.4f},{h:.4f},{corr_h:.4f},{ortho:.4f}\n")



print("\n===== INFO =====")
print(f"Entire cycle: {write_complete_cycle}")
print("Calculation finished")
print(f"{skipped_rng} Range/LLH entries were skipped due to NaN.")
# print(f"{skipped_llh} LLH entries were skipped due to NaN.")
if not write_complete_cycle:
    print(f"{skipped_station} station entries skipped due to NaNs.\n")



# === Save always and show when selected ===
def save_and_optionally_show(fig, filename):
    # Save as SVG
    fig.savefig(f"plots/{filename}.svg", format="svg")
    if show_plots:
        plt.show()
    else:
        plt.close(fig)

# TAI to UTC conversion
def tai_to_utc(tai_seconds):
    tai_epoch = datetime(2000, 1, 1)
    leap_seconds = 37  # as of June 2025
    return [tai_epoch + timedelta(seconds=t - leap_seconds) for t in tai_seconds]

# Convert time array to UTC datetime
utc_time_20ghz = tai_to_utc(time_20ghz)
utc_station_time = tai_to_utc(station_time)

# === PLOT RANGE ORIGINAL vs. CORRECTED ===
fig = plt.figure(figsize=(6, 4))
plt.plot(utc_time_20ghz, range_20ghz, label="Original Range")
plt.plot(utc_time_20ghz, corrected_range, label="Corrected Range", linestyle="--")
plt.xlabel("Time (UTC)")
plt.ylabel("Range (20GHz) [m]")
plt.title("Original vs. Corrected Range")
plt.legend()
plt.grid(True)
plt.tight_layout()
save_and_optionally_show(fig, "range_original_vs_corrected")

# === PLOT RANGE DIFFERENCE ===
range_diff = range_20ghz - corrected_range
fig = plt.figure(figsize=(6, 4))
plt.plot(utc_time_20ghz, range_diff, label="Difference: Original - Corrected")
plt.xlabel("Time (UTC)")
plt.ylabel("Range Difference (20GHz) [m]")
plt.title("Difference Between Original and Corrected Range")
plt.legend()
plt.grid(True)
plt.tight_layout()
save_and_optionally_show(fig, "range_difference")

# === PLOT RANGE CORRECTIONS ===
fig = plt.figure(figsize=(6, 4))
plt.gca().invert_yaxis()
plt.plot(utc_time_20ghz, wet_20ghz+dry_20ghz+iono_20ghz, label="All Corrections", linestyle='dotted', color='black')
plt.plot(utc_time_20ghz, dry_20ghz, label="Dry Tropospheric Correction", color='orange')
plt.plot(utc_time_20ghz,wet_20ghz, label="Wet Tropospheric Correction", color='blue')
plt.plot(utc_time_20ghz, iono_20ghz, label="Ionospheric Correction")
plt.xlabel("Time (UTC)")
plt.ylabel("Correction (20GHz) [m]")
plt.title("Atmospheric Corrections")
plt.legend()
plt.grid(True)
plt.tight_layout()
save_and_optionally_show(fig, "atmospheric_corrections")

# === PLOT LLH vs. CORRECTED ===
fig = plt.figure(figsize=(6, 4))
# plt.plot(llh, label="LLH")  # Uncomment if you want to include
plt.plot(utc_time_20ghz, corrected_llh, label="Corrected LLH")
plt.xlabel("Time (UTC)")
plt.ylabel("Height above Ellipsoid (20GHz) [m]")
plt.title("LLH Relative to Reference Ellipsoid")
plt.grid(True)
plt.legend()
plt.tight_layout()
save_and_optionally_show(fig, "corrected_llh")

# === PLOT TIDAL CORRECTIONS ===
fig = plt.figure(figsize=(6, 4))
plt.plot(utc_time_20ghz, solid_earth_tide_20ghz + pole_tide_20ghz, label="Total Tidal Correction", linestyle='dotted', color='black')
plt.plot(utc_time_20ghz, solid_earth_tide_20ghz, label="Solid Earth Tide Correction")
plt.plot(utc_time_20ghz, pole_tide_20ghz, label="Pole Tide Correction")
plt.xlabel("Time (UTC)")
plt.ylabel("Correction (20GHz) [m]")
plt.title("Tidal Corrections")
plt.legend()
plt.grid(True)
plt.tight_layout()
save_and_optionally_show(fig, "tidal_corrections")

# === PLOT ORTHOMETRIC HEIGHT ===
fig = plt.figure(figsize=(6, 4))
plt.plot(utc_time_20ghz, orthometric_height, label="Orthometric Height")
plt.xlabel("Time (UTC)")
plt.ylabel("Orthometric Height (20GHz) [m]")
plt.title("Orthometric Height")
plt.grid(True)
plt.legend()
plt.tight_layout()
save_and_optionally_show(fig, "orthometric_height")

if not write_complete_cycle:
    # === PLOT CORRECTED VIRTUAL STATION LLH ===
    fig = plt.figure(figsize=(6, 4))
    # plt.plot(station_llh, label="LLH")  # Uncomment if you want to include
    plt.plot(utc_station_time, station_corrected_llh, label="Corrected LLH")
    plt.xlabel("Time (UTC)")
    plt.ylabel("Height above Ellipsoid (20GHz) [m]")
    plt.title("LLH of Virtual Station Relative to Reference Ellipsoid")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    save_and_optionally_show(fig, "station_corrected_llh")



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