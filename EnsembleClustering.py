"""
Name: Ensemble Clustering Script
Author: Nikhil Trivedi
Description:
This script creates a 5 panel cluster plot. The top 2 panels are clusters for the HFSB_default scheme, the next 2 are for the HFSB_tiedtke scheme,
and the last panel is GFS analysis. Each panel shows the storm tracks associated with the members within the cluster, with an average of the variable
of choice underlayed (e.g. average 500mb heights for the 5 members). Below is a namelist with parameters that can be modified to whatever is of
interest. Descriptions of each of the parameters are commented to the right of them.
Last modified July 31, 2024
"""

###################################################################################################################################
# adjust these parameters based on your needs
forecastHour = 24 # forecast hour to use
clusterMembers = 3 # number of members to include in each cluster
variable = "height" # variable to plot under ATCF tracks (check varDict in UsefulFunctions for supported variables)
clusterType = "track" # track, MSLP, R34, speed, direction, steerSpeed, steerDirection, vortexDepth
level = 500 # atmospheric level to plot for (if applicable)
year, month, day, hour = 2022, 9, 24, 0  # initialization date

hours = [0, 24, 48, 60, 72, 84, 96, 108, 120] # hours to pull from ATCF file
members = range(0, 31) # ensemble members to include (range(0, 31) indicates all members)
###################################################################################################################################

import pandas as pd
import numpy as np
import xarray as xr
import cfgrib
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import UsefulFunctions as uf

# dictionaries for conversions
hours = np.array(hours)
typeDict = {"track": ["SW", "NE"], "MSLP": ["Weak", "Strong"], "R34": ["R34 Small", "R34 Large"], "speed": ["Slow", "Fast"],
            "direction": ["West", "North"], "steerSpeed": ["Slow", "Fast"], "steerDirection": ["West", "North"], 
            "vortexDepth": ["Shallow", "Deep"]}

# gather ATCF and variable data for convective schemes
clusters = []
for model in ["HFSB_default", "HFSB_tiedtke"]:
    schemeFramesList = uf.getAtcfData(model, members, hours)
    schemeRanks = uf.getClusterRanks(schemeFramesList, hours, forecastHour, clusterType)
    schemeOrder = np.array(schemeRanks).argsort()

    atcfCluster1 = np.array(schemeFramesList)[schemeOrder][:clusterMembers]
    atcfCluster2 = np.array(schemeFramesList)[schemeOrder][clusterMembers * -1:]    

    dataCluster1 = uf.getMemberData(model, variable, schemeOrder[:clusterMembers], forecastHour, level)
    dataCluster2 = uf.getMemberData(model, variable, schemeOrder[clusterMembers * -1:], forecastHour, level)
    
    dataCluster3 = uf.getMemberData(model, "height", schemeOrder[:clusterMembers], forecastHour, level)
    dataCluster4 = uf.getMemberData(model, "height", schemeOrder[clusterMembers * -1:], forecastHour, level)  
    
    clusterAvg1 = np.array(schemeRanks)[schemeOrder][:clusterMembers].mean()
    clusterAvg2 = np.array(schemeRanks)[schemeOrder][clusterMembers * -1:].mean()

    clusters.append([atcfCluster1, dataCluster1, clusterAvg1, f"HFSB {model} {typeDict[clusterType][0]} Cluster"])
    clusters.append([atcfCluster2, dataCluster2, clusterAvg2, f"HFSB {model} {typeDict[clusterType][1]} Cluster"])

# gather ATCF and variable data for best track and GFS analysis
bTrackFrame = uf.getAtcfData("GFS_analysis", range(0, 1), hours)
gfsData = uf.getMemberData("GFS_analysis", variable, range(0, 1), forecastHour, level)
bTrackAvg = uf.getClusterRanks(bTrackFrame, hours, forecastHour, clusterType)[0]

gfsData2 = uf.getMemberData("GFS_analysis", "height", range(0, 1), forecastHour, level)
clusters.append([np.array(bTrackFrame), gfsData, bTrackAvg, "GFS Analysis"])

fig, axes = plt.subplots(3, 2, subplot_kw={'projection': ccrs.PlateCarree(central_longitude=180)}, figsize=(9, 10))
axes = axes.flatten()
fig.delaxes(axes[5])

for i in range(len(clusters)):
    atcfData, gribData, avgData, model = clusters[i][0], clusters[i][1], clusters[i][2], clusters[i][3]    
    ax = axes[i]

    # plot cartopy map and various features
    ax.add_feature(cf.LAND)
    ax.add_feature(cf.STATES, linewidth=0.2, edgecolor="gray")
    ax.add_feature(cf.BORDERS, linewidth=0.3)
    ax.coastlines(linewidth=0.5, resolution='50m')

    # plot gridlines
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = {'size': 7, 'weight': 'bold', 'color': 'gray'}
    gl.ylabel_style = {'size': 7, 'weight': 'bold', 'color': 'gray'}
    if variable == "height":
        gribData = gribData / 10
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
        contours = ax.contour(gribData.longitude, gribData.latitude, gribData, levelsContour, transform=ccrs.PlateCarree(), colors='black', linewidths=0.5)
        ax.clabel(contours, levelsContour, inline=True, fontsize=8)

    elif variable == "refl":
        levelsContourf = np.arange(0, 60, 1)
        newcmp = LinearSegmentedColormap.from_list("", [
        (0 / 60, "#ffffff"),
        (10 / 60, "#0ae302"),
        (30 / 60, "#068201"),
        (30 / 60, "#d7eb02"),
        (40 / 60, "#d7eb02"),
        (50 / 60, "#d40d02"),
        (60 / 60, "#f002dc")])
    
    else:
        levelsContourf = 60
        newcmp = LinearSegmentedColormap.from_list("", [
        (0 / 20, "#FF8C89"),
        (5 / 20, "#E12309"),
        (7.5 / 20, "#FEC024"),
        (10 / 20, "#FFFFFF"),
        (12.5 / 20, "#22B2FF"),
        (15 / 20, "#104CE1"),
        (20 / 20, "#B885FF")])
        newcmp = newcmp.reversed()

        if variable == "zwind":
            levelsContourf = np.arange(-7, 7, 0.25)

    # plot title and data
    title = f"500mb Heights and Ensemble Tracks\n{model} at Hour {forecastHour}"
    if clusterType in ["intensity", "R34"]:
        if clusterType == "intensity":
            avgData *= -1
        title += f"\nCluster Average: {avgData}"
    ax.set_title(title, fontsize=9, weight='bold', loc='left')
    contourf = ax.contourf(gribData.longitude, gribData.latitude, gribData, levelsContourf, extend='both',
                           transform=ccrs.PlateCarree(), cmap=newcmp)
    cbar = plt.colorbar(contourf, pad=0.015, aspect=20, shrink=0.8, ax=ax)
    cbar.ax.tick_params(labelsize=8)

    index = np.where(hours == forecastHour)[0][0]
    for data in atcfData:
        ax.plot(data[:, 1], data[:, 0], transform=ccrs.PlateCarree(), color='black')
        ax.scatter(data[:, 1][index], data[:, 0][index], transform=ccrs.PlateCarree(), color='blue', zorder=100, s=15)

plt.savefig(rf"/work2/noaa/aoml-hafs1/nikhil/ClusterMaps/{variable}_{clusterType}_clusters_{forecastHour}.png", dpi=300, bbox_inches='tight')
plt.show()
