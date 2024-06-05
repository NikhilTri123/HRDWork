import cdsapi
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

variable = "height"  # variable to be downloaded
year, month, day, hour = 2022, 9, 28, 12  # date to be plotted
level = 500

# dictionaries for conversions
eraDict = {"sst": "sea_surface_temperature",
           "mslp": "mean_sea_level_pressure",
           "height": "geopotential",
           "zonal wind": "u_component_of_wind",
           "specific humidity": "specific_humidity",
           "temp": "temperature"}

varDict = {"sst": "sst", "mslp": "msl", "height": "z", "zonal wind": "u", "shummid": "q", "temp": "t", "stab": "ss"}

monthsDict = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August",
              9: "September", 10: "October", 11: "November", 12: "December"}


def downloadDailyData():
    c = cdsapi.Client()
    if variable in ['sst', 'mslp', ]:
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'grib',
                'variable': eraDict[variable],
                'year': year,
                'month': month,
                'day': day,
                'time': hour,
            },
            'download.grib')

    else:
        c.retrieve(
            'reanalysis-era5-pressure-levels',
            {
                'product_type': 'reanalysis',
                'format': 'grib',
                'pressure_level': f"{level}",
                'variable': eraDict[variable],
                'year': year,
                'month': f"{month}",
                'day': f"{day}",
                'time': f"{hour:02}:00",
            },
            'download.grib')


# download and open variable data
downloadDailyData()
varDataset = xr.open_dataset('download.grib', engine='cfgrib')
varData = varDataset[varDict[variable]]
varData = varData.coarsen(latitude=2, longitude=2, boundary="trim").mean()
varData = varData.sel(latitude=slice(60, 0), longitude=slice(240, 320))
if variable == 'mslp':
    varData /= 100
if variable in ['hgtmid', 'hgtup']:
    varData /= 9.81

# plot cartopy map and various features
plt.figure(figsize=(10, 6))
ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
ax.add_feature(cf.LAND)
ax.add_feature(cf.STATES, linewidth=0.2, edgecolor="gray")
ax.add_feature(cf.BORDERS, linewidth=0.3)
ax.coastlines(linewidth=0.5, resolution='50m')

# plot gridlines
gl = ax.gridlines(crs=ccrs.PlateCarree(central_longitude=180), draw_labels=True, linewidth=1, color='gray', alpha=0.5,
                  linestyle='--')
gl.top_labels = gl.right_labels = False
gl.xlabel_style = {'size': 7, 'weight': 'bold', 'color': 'gray'}
gl.ylabel_style = {'size': 7, 'weight': 'bold', 'color': 'gray'}

newcmp = LinearSegmentedColormap.from_list("", [
    [0 / 20, "#FF8C89"],
    (5 / 20, "#E12309"),
    (7.5 / 20, "#FEC024"),
    (10 / 20, "#FFFFFF"),
    (12.5 / 20, "#22B2FF"),
    (15 / 20, "#104CE1"),
    (20 / 20, "#B885FF")])
newcmp = newcmp.reversed()

# add data and colormap
plt.contourf(varData.longitude, varData.latitude, varData, 60, extend='both',
             transform=ccrs.PlateCarree(), cmap=newcmp)
cbar = plt.colorbar(pad=0.015, aspect=27, shrink=0.8)
cbar.ax.tick_params(labelsize=8)

# add titling
mainTitle = f"ERA5 {level} MB {str(variable).upper()} for {hour:02}Z {monthsDict[month]} {day:02} {year}"
plt.title(mainTitle, fontsize=9, weight='bold', loc='left')
plt.title("DCAreaWx", fontsize=9, weight='bold', loc='right', color='gray')

# save and display map
plt.show()
