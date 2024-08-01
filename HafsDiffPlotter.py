"""
Name: HAFS Differencing Script
Author: Nikhil Trivedi
Description:
This script differences two HAFS configurations of choice, using the variable and pressure level of choice. The resulting plot is the
first input minus the second input. Below is a namelist with parameters that can be modified to whatever is of interest. Descriptions of 
each of the parameters are commented to the right of them.
Last modified August 1, 2024
"""

###################################################################################################################################
# adjust these parameters based on your needs
forecastHour = 72 # forecast hour to use
variable = "mslp" # variable to plot (check varDict for suuported variables)
year, month, day, hour = 2022, 9, 24, 0  # initialization date
models = ["HFSB_default", "HFSB_tiedtke"] # HFSA_default  HFSB_default  HFSB_progsigma  HFSB_ras  HFSB_tiedtke
type = "control" # control or mean
level = 500 # atmospheric level to plot for (if applicable)
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
if type == "control":
    members = range(0, 1)
elif type == "mean":
    members = range(0, 31)

# download and open variable data
meanData1 = uf.getMemberData(models[0], variable, members, forecastHour, level)
meanData2 = uf.getMemberData(models[1], variable, members, forecastHour, level)
varData = meanData1 - meanData2

if variable == 'mslp':
    varData /= 100
    mainTitle = f"{models[0]} - {models[1]} {str(variable).upper()} at Forecast Hour {forecastHour}"
    subTitle = f"\nInitialized at {hour:02}Z {monthsDict[month]} {day:02} {year}"
    levelsContourf = np.arange(-10, 10.5, 0.5)

if variable in ['height', 'zonal wind']:
    varData /= 10
    mainTitle = f"{models[0]} - {models[1]} {level}mb {str(variable).upper()} at Forecast Hour {forecastHour}"
    subTitle = f"\nInitialized at {hour:02}Z {monthsDict[month]} {day:02} {year}"
    levelsContourf = np.arange(-5, 5.25, 0.25)

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

newcmp = LinearSegmentedColormap.from_list("", [
    (0 / 20, "#FF8C89"),
    (5 / 20, "#E12309"),
    (7.5 / 20, "#FEC024"),
    (10 / 20, "#FFFFFF"),
    (12.5 / 20, "#22B2FF"),
    (15 / 20, "#104CE1"),
    (20 / 20, "#B885FF")])
newcmp = newcmp.reversed()

# add data and colormap
plt.contourf(varData.longitude, varData.latitude, varData, levelsContourf, extend='both',
             transform=ccrs.PlateCarree(), cmap=newcmp)
cbar = plt.colorbar(pad=0.015, aspect=27, shrink=0.8)
cbar.ax.tick_params(labelsize=8)

# add titling
plt.title(mainTitle + subTitle, fontsize=9, weight='bold', loc='left')

# save and display map
plt.savefig(f"./IanDiffPlots/{type}_diff_hour_{forecastHour}.png", dpi=300, bbox_inches='tight')
plt.show()

