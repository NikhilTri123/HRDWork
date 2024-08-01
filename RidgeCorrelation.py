"""
Name: Correlation Plotter
Author: Nikhil Trivedi
Description:
This script is still a little messy, but currently calculates two types of correlations. The first (corrType = variable) correlates
the strength of the ridge in the Gulf to 500mb heights. The second (corrType = steering) correlates the meridional component of environmental
steering to 500mb heights. I want to make this so it's more flexible in the future, but for now it's a little messy. Below is a namelist 
with parameters that can be modified to whatever is of interest. Descriptions of each of the parameters are commented to the right of them.
Last modified July 31, 2024
"""

###################################################################################################################################
# adjust these parameters based on your needs
members = range(0, 31) # ensemble members to include (range(0, 31) indicates all members)
model = "HFSB_default" # HFSA_default  HFSB_default  HFSB_progsigma  HFSB_ras  HFSB_tiedtke
forecastHour = 24 # forecast hour to use
corrType = "steering" # type of correlation to do (variable or steering)
hours = [0, 24, 48, 60, 72, 84, 96, 108, 120] # hours to pull from ATCF file
year, month, day, hour = 2022, 9, 24, 0  # initialization date
###################################################################################################################################

import numpy as np
import xarray as xr
import cfgrib
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import pearsonr
import UsefulFunctions as uf

varDict = {"sst": "sst", "mslp": "prmsl", "height": "gh", "zonal wind": "u", "shum": "q", "temp": "t", "stab": "ss", "refl": "refc"}

monthsDict = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August",
              9: "September", 10: "October", 11: "November", 12: "December"}
hours = np.array(hours)


def getCorrelation(varData, aceVals):
    """
    Calculates a global correlation map between a given variable and list of ACE values for a given month. E.g. if the
    variable is SST data, the aceVals are for September only, and the month is June, a correlation map between June
    SST's and September ACE will be calculated
    :param varData: xarray dataset for a variable
    :param aceVals: List of ACE values for a given month and time period
    :param varMonth: month that the correlation map is calculated for
    :return: a global correlation map
    """
    # each element in switchedData is a list data from each year for a given pixel
    allFlattenedData = np.reshape(varData.flatten(), (len(members), -1))
    switchedData = np.nan_to_num(allFlattenedData.T)

    # each element is a correlation for a given pixel
    corrList = np.array([pearsonr(pixelData, aceVals) for pixelData in switchedData])
    rawList = corrList[:, 0]
    sigList = corrList[:, 1]
    sigList = np.where(sigList <= 0.05, 1, 0)

    # list of correlations is reshaped to map of correlations
    rawList = np.reshape(rawList, varData.shape[1:])
    rawList = np.nan_to_num(rawList)
    sigList = np.reshape(sigList, varData.shape[1:])

    return rawList, sigList


print("starting...")
if corrType == "variable":
    # get a list of average heights for the sliced region of interest
    heights = []
    for member in members:
        path = f"/work2/noaa/aoml-hafs1/nikhil/ian_grb2_files/HFSB_{model}/00l.2022092400.hfsb.parent.atm.f{forecastHour:03}.HFSB_{model}_{member:02}.grb2"
        hgtDataset = xr.open_dataset(path, engine='cfgrib', filter_by_keys={'typeOfLevel': 'isobaricInhPa'}, backend_kwargs={'indexpath': f'{path}.idx'})
        hgtData = hgtDataset[varDict["height"]]
        hgtData = hgtData.sel(isobaricInhPa=500)
        hgtPoint = hgtData.sel(latitude=slice(20, 26), longitude=slice(263, 275)).mean()
        heights.append(hgtPoint)

elif corrType == "steering":
    heights, lonlatPoints = [], []
    for member in members:
        print(member)
        atcfData = uf.getAtcfData(model, [member], hours)[0]
        atcfTimeStamp = atcfData.iloc[np.where(hours == forecastHour)[0][0]]
        centerLat = atcfTimeStamp["latitude"]
        centerLon = atcfTimeStamp["longitude"]

        zonalData = uf.getMemberData(model, "zonal wind", [member], forecastHour)
        meridionalData = uf.getMemberData(model, "meridional wind", [member], forecastHour)
        centeredZonal = zonalData.sel(latitude=slice(centerLat-2.5, centerLat+2.5), longitude=slice(centerLon-2.5, centerLon+2.5))
        centeredMeridional = meridionalData.sel(latitude=slice(centerLat-2.5, centerLat+2.5), longitude=slice(centerLon-2.5, centerLon+2.5))
        centeredData = np.sqrt(centeredZonal**2 + centeredMeridional**2)
        
        # calculate the average steering flow on the vortex
        newLevels = centeredData.isobaricInhPa.sel(isobaricInhPa=slice(600, 400)).values
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
        heights.append(meridionalAvg)
        lonlatPoints.append([centerLon, centerLat])
print(heights)

# get the MSLP data for the sliced region of interest
files = []
for member in members:
    varData = uf.getMemberData(model, "height", [member], forecastHour)
    varData = varData.coarsen(latitude=4, longitude=4, boundary="trim").mean()
    files.append(varData)

corrData, sigData = getCorrelation(np.array(files), heights)

# plot cartopy map and various features
plt.figure(figsize=(10, 6))
ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
ax.add_feature(cf.LAND)
ax.add_feature(cf.STATES, linewidth=0.2, edgecolor="gray")
ax.add_feature(cf.BORDERS, linewidth=0.3)
ax.coastlines(linewidth=0.5, resolution='50m')
if corrType == "variable":
    ax.plot([263, 275, 275, 263, 263], [20, 20, 26, 26, 20], transform=ccrs.PlateCarree(), color='black')
elif corrType == "steering":
    lonlatPoints = np.array(lonlatPoints)
    meanLon = lonlatPoints[:, 0].mean()
    meanLat = lonlatPoints[:, 1].mean()
    ax.plot(meanLon, meanLat, marker='x', markersize=15, transform=ccrs.PlateCarree(), color='black', markeredgewidth=3)

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
plt.contourf(varData.longitude, varData.latitude, corrData, np.arange(-1, 1, 0.05), extend='both',
             transform=ccrs.PlateCarree(), cmap=newcmp)
cbar = plt.colorbar(pad=0.015, aspect=25, shrink=0.72)
cbar.ax.tick_params(labelsize=8)
contour = plt.contour(varData.longitude, varData.latitude, sigData, [0.5], transform=ccrs.PlateCarree(), colors='black', linewidths=0.5, zorder=5)
contour.collections[0].set_hatch('///')


# add titling
title = f"HFSB_{model} Meridional Steering Correlated to 500mb Heights"
subTitle = f"\nForecast Hour {forecastHour}, Initialized at {hour:02}Z {monthsDict[month]} {day:02} {year}"
plt.title(title + subTitle, fontsize=9, weight='bold', loc='left')

# save and display map
plt.savefig(f"./BasicPlots/correlation_plot_{model}.png", dpi=300, bbox_inches='tight')
plt.show()

