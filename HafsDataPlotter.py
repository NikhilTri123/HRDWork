"""
Name: HAFS/GFS Analysis Data Plotter
Author: Nikhil Trivedi
Description:
This script simply plots the data from any of the available HAFS configurations or GFS analysis. It can plot either the control member or
an ensemble mean, and can plot a variety of variables. Below is a namelist with parameters that can be modified to whatever is of interest. 
Descriptions of each of the parameters are commented to the right of them.
Last modified July 31, 2024
"""

###################################################################################################################################
variable = "vector wind"  # variable to plot (check varDict in UsefulFunctions for supported variables)
year, month, day, hour = 2022, 9, 24, 0  # initialization date
level = 200 # atmospheric level to plot for (if applicable)
forecastHour = 24 # forecast hour to use
model = "HFSB_tiedtke" # HFSA_default  HFSB_default  HFSB_progsigma  HFSB_ras  HFSB_tiedtke  GFS_analysis
runType = "control" # control or mean
###################################################################################################################################

import xarray as xr
import cfgrib
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import UsefulFunctions as uf

# dictionaries for conversions
monthsDict = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August",
              9: "September", 10: "October", 11: "November", 12: "December"}

# determine what members to use
if runType == "control":
    members = range(0, 1)
elif runType == "mean":
    members = range(0, 31)

# download and open variable data
if variable == "vector wind":
    zonalData = uf.getMemberData(model, "zonal wind", members, forecastHour, level)
    meridionalData = uf.getMemberData(model, "meridional wind", members, forecastHour, level)
    varData = np.sqrt(zonalData**2 + meridionalData**2)
else:
    varData = uf.getMemberData(model, variable, members, forecastHour, level)

newcmp = LinearSegmentedColormap.from_list("", [
(0 / 20, "#FF8C89"),
(5 / 20, "#E12309"),
(7.5 / 20, "#FEC024"),
(10 / 20, "#FFFFFF"),
(12.5 / 20, "#22B2FF"),
(15 / 20, "#104CE1"),
(20 / 20, "#B885FF")])
newcmp = newcmp.reversed()

if variable == 'mslp':
    varData /= 100
    mainTitle = f"{model} {str(variable).upper()} at Forecast Hour {forecastHour}"
    subTitle = f"\nInitialized at {hour:02}Z {monthsDict[month]} {day:02} {year}"
    levelsContour = np.arange(983, 1043, 2)
    levelsContourf = np.arange(983, 1043, 1)

elif variable == 'height':
    varData /= 10
    mainTitle = f"{model} {level}mb {str(variable).upper()} at Forecast Hour {forecastHour}"
    subTitle = f"\nInitialized at {hour:02}Z {monthsDict[month]} {day:02} {year}"
    levelsContour = np.arange(492, 600, 4)
    levelsContourf = np.arange(492, 600, 1)
    newcmp = LinearSegmentedColormap.from_list("", [
    (0 / 108, "#AF75FE"),
    (18 / 108, "#104CE1"),
    (48 / 108, "#288DFF"),
    (48 / 108, "#0cf0b7"),
    (60 / 108, "#029916"),
    (78 / 108, "#e8d505"),
    (95 / 108, "#e85202"),
    (95 / 108, "#e30202"),
    (97 / 108, "#cc0202"),
    (97 / 108, "#b80202"),
    (108 / 108, "#6b0602")])
    
elif variable == 'shum':
    mainTitle = f"{model} {level}mb {str(variable).upper()} at Forecast Hour {forecastHour}"
    subTitle = f"\nInitialized at {hour:02}Z {monthsDict[month]} {day:02} {year}"
    levelsContour = np.arange(492, 600, 4)
    levelsContourf = np.arange(492, 600, 1)

elif variable == 'refl':
    mainTitle = f"{model} {str(variable).upper()} at Forecast Hour {forecastHour}"
    subTitle = f"\nInitialized at {hour:02}Z {monthsDict[month]} {day:02} {year}"
    levelsContourf = np.arange(0, 60, 1)
    newcmp = LinearSegmentedColormap.from_list("", [
    (0 / 60, "#ffffff"),
    (10 / 60, "#0ae302"),
    (30 / 60, "#068201"),
    (30 / 60, "#d7eb02"),
    (40 / 60, "#d7eb02"),
    (50 / 60, "#d40d02"),
    (60 / 60, "#f002dc")])

elif variable == 'vector wind':
    mainTitle = f"{model} {level}mb Vector Wind at Forecast Hour {forecastHour}"
    subTitle = f"\nInitialized at {hour:02}Z {monthsDict[month]} {day:02} {year}"
    levelsContourf = np.arange(0, 80, 2)
    newcmp = LinearSegmentedColormap.from_list("", [
    (0 / 25, "#FFFFFF"),
    (2 / 25, "#1ED7E7"),
    (6 / 25, "#19E742"),
    (9 / 25, "#F5FC4B"),
    (12 / 25, "#F9A114"),
    (15 / 25, "#EE1A1A"),
    (19 / 25, "#E009DC"),
    (25 / 25, "#FBC7FA")])

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

# add data and colormap
if variable in ["height", "mslp", "shum"]:
    plt.contour(varData.longitude, varData.latitude, varData, levelsContour, transform=ccrs.PlateCarree(), colors='black', linewidths=0.5)
plt.contourf(varData.longitude, varData.latitude, varData, levelsContourf, extend='both',
             transform=ccrs.PlateCarree(), cmap=newcmp)
cbar = plt.colorbar(pad=0.015, aspect=27, shrink=0.8)
cbar.ax.tick_params(labelsize=8)
if variable == "vector wind":
    plt.streamplot(varData.longitude, varData.latitude, zonalData, meridionalData, color='#4B4B4B', linewidth=0.5,
                   transform=ccrs.PlateCarree())

# add titling
plt.title(mainTitle + subTitle, fontsize=9, weight='bold', loc='left')

# save and display map
plt.savefig(f"./BasicPlots/{variable}_{runType}_plot_{model}.png", dpi=300, bbox_inches='tight')
plt.show()

