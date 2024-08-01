"""
Name: Ensemble Line Plots Script
Author: Nikhil Trivedi
Description:
This script creates a line plot with time for all ensemble members from both convective schemes, along with a line for best track. The
quantity that it being analyzed is shown on the y-axis. Below is a namelist with parameters that can be modified to whatever is of interest. 
Descriptions of each of the parameters are commented to the right of them. 
Last modified July 31, 2024
"""

###################################################################################################################################
# adjust these parameters based on your needs
clusterType = "MSLP" # track, MSLP, R34, speed, direction, steerSpeed, steerDirection, vortexDepth
hours = np.array([0, 24, 48, 60, 72, 84, 96, 108, 120]) # hours to pull from ATCF file
year, month, day, hour = 2022, 9, 24, 0  # initialization date
###################################################################################################################################

import pandas as pd
import numpy as np
import xarray as xr
import cfgrib
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
import UsefulFunctions as uf

# dictionaries for conversions
monthsDict = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August",
              9: "September", 10: "October", 11: "November", 12: "December"}

typeDict = {"track": "Location (lat + lon)", "MSLP": "MSLP (hPa)", "R34": "Radius (km)", "speed": "Speed (kts)", "direction": "Direction (deg)",
            "steerSpeed": "Speed (kts)", "steerDirection": "Direction (deg)", "vortexDepth": "Bottom - Top (hPa)"}

colors = ["red", "blue", "black"]
hours = np.array(hours)

# get ATCF data for convective schemes and best track
bTrackFrames  = uf.getAtcfData("GFS_analysis", range(0, 1), hours)
defaultFrames = uf.getAtcfData("HFSB_default", range(0, 31), hours)
tiedtkeFrames = uf.getAtcfData("HFSB_tiedtke", range(0, 31), hours)

dataLists = [defaultFrames, tiedtkeFrames, bTrackFrames]
if clusterType in ["steerSpeed", "steerDirection", "vortexDepth"]:
    models = ["default", "tiedtke", "analysis"]
    for i in range(len(dataLists)):    
        steerData = np.loadtxt(f"/work2/noaa/aoml-hafs1/nikhil/SteerValues/{models[i]}_{clusterType}.txt")
        members = range(0, 31)
        if models[i] == "analysis":
            members = range(0, 1)
            steerData = [steerData]
        for member in members:
            dataLists[i][member][clusterType] = steerData[member]

# plot cartopy map and various features
plt.figure(figsize=(10, 6))
capClusterType = clusterType[0].upper() + clusterType[1:]
title = f"Ensemble Members {capClusterType} By Convective Scheme"
subTitle = f"\nInitialized at {hour:02}Z {monthsDict[month]} {day:02} {year}"
plt.title(title + subTitle, fontsize=9, weight='bold', loc='left');
plt.xlabel('Time in Hours', fontsize=9, weight='bold')
plt.ylabel(typeDict[clusterType], fontsize=9, weight='bold')
custom_markers = [
    Line2D([0], [0], marker='o', color='red', markersize=10, linestyle='None'),
    Line2D([0], [0], marker='o', color='blue', markersize=10, linestyle='None'),
    Line2D([0], [0], marker='o', color='black', markersize=10, linestyle='None')
]
default_steerDirection.txtdefault_steerDirection.txtplt.legend(custom_markers, ['HFSB-Default', 'HFSB-Tiedtke', 'Best Track'])

# plot lines based on property of interest
for i in range(len(dataLists)):
    data = dataLists[i]
    if i == 2:
        dotSize = 60
        lineThickness = 4
        opacity = 1
        if clusterType in ["speed", "direction", "steerSpeed", "steerDirection", "vortexDepth"]:
            break
    else:
        dotSize = 15
        lineThickness = 0.8
        opacity = 0.5
    end = -2
    for memberData in data:
        if clusterType in ["direction", "steerDirection"]:
            memberData[clusterType] = np.where(memberData[clusterType] < 90, memberData[clusterType] + 360, memberData[clusterType])
        plt.plot(hours[:end], memberData[clusterType][:end], color=colors[i], linewidth=lineThickness, alpha=opacity)
        plt.scatter(hours[:end], memberData[clusterType][:end], color=colors[i], s=dotSize, alpha=opacity)
    
    index = data[0].columns.get_loc(clusterType)
    ensembleMean = np.array(data).mean(axis=0)[:, index]
    plt.plot(hours[:end], ensembleMean[:end], color=colors[i], linewidth=4, zorder=5)
    plt.scatter(hours[:end], ensembleMean[:end], color=colors[i], zorder=5, s=60)

plt.savefig(rf"./LinePlots/{clusterType}_line_plot.png", dpi=300, bbox_inches='tight')
plt.show()

