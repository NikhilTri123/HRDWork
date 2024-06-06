import cdsapi
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

variable = "vector wind"  # variable to be downloaded
year, month, day, hour = 2022, 9, 28, 12  # date to be plotted
level = 200

# dictionaries for conversions
eraDict = {"sst": "sea_surface_temperature",
           "mslp": "mean_sea_level_pressure",
           "height": "geopotential",
           "zonal wind": "u_component_of_wind",
           "meridional wind": "v_component_of_wind",
           "specific humidity": "specific_humidity",
           "temp": "temperature"}

varDict = {"sst": "sst", "mslp": "msl", "height": "z", "zonal wind": "u", "shummid": "q", "temp": "t", "stab": "ss",
           "meridional wind": "v"}

monthsDict = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August",
              9: "September", 10: "October", 11: "November", 12: "December"}


def downloadDailyData(var):
    c = cdsapi.Client()
    if var in ['sst', 'mslp', ]:
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'grib',
                'variable': eraDict[var],
                'year': year,
                'month': month,
                'day': day,
                'time': hour,
            },
            f'{var}.grib')

    else:
        c.retrieve(
            'reanalysis-era5-pressure-levels',
            {
                'product_type': 'reanalysis',
                'format': 'grib',
                'pressure_level': f"{level}",
                'variable': eraDict[var],
                'year': year,
                'month': f"{month}",
                'day': f"{day}",
                'time': f"{hour:02}:00",
            },
            f'{var}.grib')


# downloadDailyData("zonal wind")
# downloadDailyData("meridional wind")

zonalDataset = xr.open_dataset(f'{"zonal wind"}.grib', engine='cfgrib')
zonalData = zonalDataset[varDict["zonal wind"]]
zonalData = zonalData.coarsen(latitude=2, longitude=2, boundary="trim").mean()
zonalData = zonalData.sel(latitude=slice(60, 0), longitude=slice(240, 320))

meridionalDataset = xr.open_dataset(f'{"meridional wind"}.grib', engine='cfgrib')
meridionalData = meridionalDataset[varDict["meridional wind"]]
meridionalData = meridionalData.coarsen(latitude=2, longitude=2, boundary="trim").mean()
meridionalData = meridionalData.sel(latitude=slice(60, 0), longitude=slice(240, 320))

magnitudeData = np.sqrt(zonalData**2 + meridionalData**2)
print(magnitudeData)

# plot cartopy map and various features
plt.figure(figsize=(10, 6))
ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
ax.add_feature(cf.LAND)
ax.add_feature(cf.STATES, linewidth=0.2, edgecolor="gray")
ax.add_feature(cf.BORDERS, linewidth=0.3)
ax.coastlines(linewidth=0.5, resolution='50m')

# plot gridlines
gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.5, linestyle='--')
gl.top_labels = gl.right_labels = False
gl.xlabel_style = {'size': 7, 'weight': 'bold', 'color': 'gray'}
gl.ylabel_style = {'size': 7, 'weight': 'bold', 'color': 'gray'}

# add titling
if variable in ['sst', 'mslp', ]:
    mainTitle = f"ERA5 {str(variable).upper()} for {hour:02}Z {monthsDict[month]} {day:02} {year}"
else:
    mainTitle = f"ERA5 {level} MB {str(variable).upper()} for {hour:02}Z {monthsDict[month]} {day:02} {year}"
plt.title(mainTitle, fontsize=9, weight='bold', loc='left')
plt.title("DCAreaWx", fontsize=9, weight='bold', loc='right', color='gray')

newcmp = LinearSegmentedColormap.from_list("", [
    (0 / 25, "#FFFFFF"),
    (2 / 25, "#1ED7E7"),
    (6 / 25, "#19E742"),
    (9 / 25, "#F5FC4B"),
    (12 / 25, "#F9A114"),
    (15 / 25, "#EE1A1A"),
    (19 / 25, "#E009DC"),
    (25 / 25, "#FBC7FA")])

# add data and colormap
plt.contourf(magnitudeData.longitude, magnitudeData.latitude, magnitudeData, 60, extend='both',
             transform=ccrs.PlateCarree(), cmap=newcmp)
cbar = plt.colorbar(pad=0.015, aspect=27, shrink=0.8)
cbar.ax.tick_params(labelsize=8)
plt.streamplot(zonalData.longitude, zonalData.latitude, zonalData, meridionalData, color='#4B4B4B', linewidth=0.5,
               transform=ccrs.PlateCarree())

# save and display map
plt.savefig("vector_wind_plot.png", dpi=300, bbox_inches='tight')
plt.show()
