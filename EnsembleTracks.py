"""
Name: Colored Ensemble Tracks Script
Author: Nikhil Trivedi
Description:
This script creates a 2 panel plot, where each panel shows the spatial tracks for an ensemble suite colored for a certain attribute. This 
can be used to analyze how track is affected by differences in the quantity. Below is a namelist with parameters that can be modified to 
whatever is of interest. Descriptions of each of the parameters are commented to the right of them.
Last modified July 31, 2024
"""

###################################################################################################################################
# adjust these parameters depending on your needs
forecastHour = 48 # forecast hour to use
clusterType = "MSLP" # track, MSLP, R34, speed, direction, steerSpeed, steerDirection, vortexDepth
hours = [0, 24, 48, 60, 72, 84, 96, 108, 120] # hours to pull from ATCF file
members = range(0, 31) # ensemble members to include
year, month, day, hour = 2022, 9, 24, 0  # date to be plotted
###################################################################################################################################

import pandas as pd
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import UsefulFunctions as uf

# dictionaries for conversions
monthsDict = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August",
              9: "September", 10: "October", 11: "November", 12: "December"}

typeDict = {"track": ["SW", "NE"], "MSLP": ["Weak", "Strong"], "R34": ["R34 Small", "R34 Large"], "speed": ["Slow", "Fast"],
            "direction": ["West", "North"], "steerSpeed": ["Slow", "Fast"], "steerDirection": ["West", "North"],
            "vortexDepth": ["Shallow", "Deep"]}
hours = np.array(hours)


def mapping(ax, model):
    # plot cartopy map and various features
    ax.set_extent([270, 295, 12, 32])
    ax.add_feature(cf.LAND)
    ax.add_feature(cf.STATES, linewidth=0.2, edgecolor="gray")
    ax.add_feature(cf.BORDERS, linewidth=0.3)
    ax.coastlines(linewidth=0.5, resolution='50m')

    # plot gridlines
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = {'size': 7, 'weight': 'bold', 'color': 'gray'}
    gl.ylabel_style = {'size': 7, 'weight': 'bold', 'color': 'gray'}

    # plot title
    capClusterType = clusterType[0].upper() + clusterType[1:]
    title = f"HAFS {model} Ensembles by {capClusterType} at Hour {forecastHour}"
    subTitle = f"\nInitialized at {hour:02}Z {monthsDict[month]} {day:02} {year}"
    ax.set_title(title + subTitle, fontsize=9, weight='bold', loc='left')

    colors = plt.cm.viridis(np.linspace(0, 1, 31))
    custom_markers = [
        Line2D([0], [0], marker='o', color=colors[0], markersize=10, linestyle='None'),
        Line2D([0], [0], marker='o', color=colors[-1], markersize=10, linestyle='None'),
    ]
    ax.legend(custom_markers, [typeDict[clusterType][0], typeDict[clusterType][1]])


colors = plt.cm.viridis(np.linspace(0, 1, 31))
defaultFrames, tiedtkeFrames, endLongs = [], [], []

defaultFrames = uf.getAtcfData("HFSB_default", members, hours)
tiedtkeFrames = uf.getAtcfData("HFSB_tiedtke", members, hours)

dataLists = [defaultFrames, tiedtkeFrames]
if clusterType in ["steerSpeed", "steerDirection", "vortexDepth"]:
    models = ["HFSB_default", "HFSB_tiedtke"]
    for i in range(len(dataLists)):
        steerData = np.loadtxt(f"/work2/noaa/aoml-hafs1/nikhil/SteerValues/{models[i]}_{clusterType}.txt")
        members = range(0, 31)
        for member in members:
            dataLists[i][member][clusterType] = steerData[member]

defaultPos = uf.getClusterRanks(defaultFrames, hours, forecastHour, clusterType)
tiedtkePos = uf.getClusterRanks(tiedtkeFrames, hours, forecastHour, clusterType)

defaultOrder = np.array(defaultPos).argsort()
tiedtkeOrder = np.array(tiedtkePos).argsort()

defaultFrames = np.array(defaultFrames)[defaultOrder]
tiedtkeFrames = np.array(tiedtkeFrames)[tiedtkeOrder]

fig, axes = plt.subplots(1, 2, subplot_kw={'projection': ccrs.PlateCarree(central_longitude=180)}, figsize=(10, 6))
index = np.where(hours == forecastHour)[0][0]
for member in members:
    # plot data
    ax = axes[0]
    mapping(ax, "Default")
    ax.plot(defaultFrames[member][:, 1], defaultFrames[member][:, 0], transform=ccrs.PlateCarree(), color=colors[member], linewidth=1.2)
    ax.scatter(defaultFrames[member][:, 1][index], defaultFrames[member][:, 0][index], transform=ccrs.PlateCarree(), color='black', zorder=100, s=20)

for member in members:
    # plot data
    ax = axes[1]
    mapping(ax, "Tiedtke")
    ax.plot(tiedtkeFrames[member][:, 1], tiedtkeFrames[member][:, 0], transform=ccrs.PlateCarree(), color=colors[member], linewidth=1.2)
    ax.scatter(tiedtkeFrames[member][:, 1][index], tiedtkeFrames[member][:, 0][index], transform=ccrs.PlateCarree(), color='black', zorder=100, s=20)

plt.savefig(rf"/work2/noaa/aoml-hafs1/nikhil/LinePlots/ensemble_tracks_{forecastHour}.png", dpi=300, bbox_inches='tight')
plt.show()

