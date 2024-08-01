"""
Name: Vortex Averaged Steering Script
Author: Nikhil Trivedi
Description:
This script calculates mass-weighted steering in a 5x5 degree box centered at the center of the TC, using objectively estimated bounds for vortex
depth. It averages the steering along the depth of the vortex to generate a steering vector. Magnitude and direction are plotted, and 500mb heights
are underlayed. Below is a namelist with parameters that can be modified to whatever is of interest. Descriptions of each of the parameters are 
commented to the right of them.
Last modified August 1, 2024
"""

###################################################################################################################################
# adjust these parameters based on your needs
forecastHour = 24 # forecast hour to use
hours = [0, 6, 12, 18, 24, 48, 60, 72, 84, 96, 108, 120] # hours to pull from ATCF file
model = "HFSB_default" # HFSA_default  HFSB_default  HFSB_progsigma  HFSB_ras  HFSB_tiedtke  GFS_analysis
member = 0 # ensemble member to calculate steering for (0 indicates the control)
###################################################################################################################################

import xarray as xr
import numpy as np
import pandas as pd
from scipy import interpolate
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as PathEffects
import UsefulFunctions as uf

hours = np.array(hours)
atcfData = uf.getAtcfData(model, [member], hours)[0]
atcfTimeStamp = atcfData.iloc[np.where(hours == forecastHour)[0][0]]
centerLat = atcfTimeStamp["latitude"]
centerLon = atcfTimeStamp["longitude"]

zonalData = uf.getMemberData(model, "zonal wind", [member], forecastHour)
meridionalData = uf.getMemberData(model, "meridional wind", [member], forecastHour)
centeredZonal = zonalData.sel(latitude=slice(centerLat-2.5, centerLat+2.5), longitude=slice(centerLon-2.5, centerLon+2.5))
centeredMeridional = meridionalData.sel(latitude=slice(centerLat-2.5, centerLat+2.5), longitude=slice(centerLon-2.5, centerLon+2.5))
centeredData = np.sqrt(centeredZonal**2 + centeredMeridional**2)

radAvgData = uf.getRadAvgWinds(centeredData, atcfTimeStamp, model)
vortexBottom, vortexTop, vortexLeft, vortexRight = uf.getDynamicVortex(radAvgData, atcfTimeStamp)

# plot the radially averaged data
plt.figure(figsize=(10, 6))
newcmp = LinearSegmentedColormap.from_list("", [
    (0 / 50, "#FFFFFF"),
    (2 / 50, "#FFFFFF"),
    (2 / 50, "#65E8F7"),
    (10 / 50, "#0E97A7"),
    (10 / 50, "#14B937"),
    (15 / 50, "#E6EF23"),
    (21 / 50, "#B50204"),
    (21 / 50, "#C103C1"),
    (33 / 50, "#FEEFFE"),
    (50 / 50, "#FA8F83")])
plt.contourf(radAvgData.radial_distance, radAvgData.level, radAvgData, levels=np.arange(0, 150, 2),
             cmap=newcmp, extend='both')
plt.gca().invert_yaxis()
# plt.yscale('symlog')
plt.plot([vortexLeft, vortexRight, vortexRight, vortexLeft, vortexLeft], [vortexBottom, vortexBottom, vortexTop, vortexTop, vortexBottom], color='black')
cbar = plt.colorbar(pad=0.015, aspect=27, shrink=0.8)
cbar.ax.tick_params(labelsize=8)
plt.xlabel("Distance from Center (km)")
plt.ylabel("Pressure Level (hPa)")

# add titling
mainTitle = f"HFSB-{model} Radial Averaged Vector Winds for Ensemble {member}"
subTitle = f"\nForecast Hour {forecastHour}"
plt.title(mainTitle + subTitle, fontsize=9, weight='bold', loc='left')

plt.savefig(f"./SteeringPlots/radial_winds_{model}_hour_{forecastHour}.png", dpi=300, bbox_inches='tight')
plt.show()

# calculate the average steering flow on the vortex
# level = input("What is level is the top of the vortex (in hPa)? ")
newLevels = radAvgData.level.sel(level=slice(vortexBottom, vortexTop)).values
print(newLevels)
weights = []
for newLevel in newLevels:
    weights.append(newLevel / 1000)
zonalAvg = centeredZonal.sel(isobaricInhPa=newLevels).mean(dim=["latitude", "longitude"]).values
zonalAvg = np.average(zonalAvg, weights=weights) * 1.94384
meridionalAvg = centeredMeridional.sel(isobaricInhPa=newLevels).mean(dim=["latitude", "longitude"]).values
meridionalAvg = np.average(meridionalAvg, weights=weights) * 1.94384
magnitude = np.round(np.sqrt(zonalAvg**2 + meridionalAvg**2), 1)
direction = np.round((90 - np.rad2deg(np.arctan2(meridionalAvg, zonalAvg))) % 360, 1)

# plot cartopy map and various features
plt.figure(figsize=(10, 6))
ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
ax.add_feature(cf.LAND)
ax.add_feature(cf.STATES, linewidth=0.2, edgecolor="gray")
ax.add_feature(cf.BORDERS, linewidth=0.3)
ax.coastlines(linewidth=0.5, resolution='50m')
ax.plot([centerLon-2.5, centerLon+2.5, centerLon+2.5, centerLon-2.5, centerLon-2.5], [centerLat-2.5, centerLat-2.5, centerLat+2.5, centerLat+2.5, centerLat-2.5], 
        transform=ccrs.PlateCarree(), color='black')

# plot gridlines
gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.5, linestyle='--')
gl.top_labels = gl.right_labels = False
gl.xlabel_style = {'size': 7, 'weight': 'bold', 'color': 'gray'}
gl.ylabel_style = {'size': 7, 'weight': 'bold', 'color': 'gray'}

hgtData = uf.getMemberData(model, "height", [member], forecastHour, 500)
hgtData = hgtData / 10
levelsContour = np.arange(586, 592, 2)
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
contours = ax.contour(hgtData.longitude, hgtData.latitude, hgtData, levelsContour, transform=ccrs.PlateCarree(), colors='black', linewidths=0.5)
ax.clabel(contours, levelsContour, inline=True, fontsize=8)
plt.contourf(hgtData.longitude, hgtData.latitude, hgtData, levelsContourf, extend='both',
             transform=ccrs.PlateCarree(), cmap=newcmp)
cbar = plt.colorbar(pad=0.015, aspect=27, shrink=0.8)
cbar.ax.tick_params(labelsize=8)

# add titling
mainTitle = f"HFSB-{model} {vortexTop}-{vortexBottom}mb Steering Flow for Ensemble {member}"
subTitle = f"\n500mb Heights, Forecast Hour {forecastHour}"
plt.title(mainTitle + subTitle, fontsize=9, weight='bold', loc='left')

plt.quiver(np.array([centerLon]), np.array([centerLat]), np.array([zonalAvg]), np.array([meridionalAvg]), transform=ccrs.PlateCarree(),
           scale_units='xy', scale=3)
txt = plt.text(centerLon + 0.7, centerLat, f"Speed: {magnitude} kts\nDirection: {direction} deg", transform=ccrs.PlateCarree())
txt.set_path_effects([PathEffects.withStroke(linewidth=1, foreground='w')])

# actualU = atcfTimeStamp['speed'] * np.cos(np.radians(90 - atcfTimeStamp['direction']))
# actualV = atcfTimeStamp['speed'] * np.sin(np.radians(90 - atcfTimeStamp['direction']))
# plt.quiver(np.array([centerLon]), np.array([centerLat]), np.array([actualU]), np.array([actualV]), transform=ccrs.PlateCarree(),
#            scale_units='xy', scale=3, color='blue')
# 
# deviantU = actualU - zonalAvg
# deviantV = actualV - meridionalAvg
# plt.quiver(np.array([centerLon]), np.array([centerLat]), np.array([deviantU]), np.array([deviantV]), transform=ccrs.PlateCarree(),
#            scale_units='xy', scale=3, color='red')

plt.savefig(f"./SteeringPlots/steering_{model}_hour_{forecastHour}.png", dpi=300, bbox_inches='tight')
plt.show()

