"""
Name: Useful Functions
Author: Nikhil Trivedi
Description:
This script simply contains a list of functions that are repeatedly used by many of the other scripts in this "library". They are stored in here
so they can just be written once, rather than being repeated and cluttering the other scripts. A list of these functions and a brief description of
each of them will now be provided:
1) getAtcfData: retrieves raw ATCF data for the given model and processes it into a Pandas DataFrame for each member, returning a list of these DataFrames
2) getClusterRanks: ranks the members within the processed list of ATCF data based on a provided attribute
3) getMemberData: returns an averaged xarray DataArray for the provided members, using the specified model, variable, and pressure level
4) getRadAvgWinds: converts a cartesian coordinate system centered on a TC to a radial-averaged system, returning an xarray DataArray with this data
5) getDynamicVortex: uses a radial-averaged DataArray to objectively estimate both the width and depth of a TC's vortex, returning its bounds
Last modified July 31, 2024
"""

import pandas as pd
import xarray as xr
import cfgrib
import numpy as np

# dictionaries for conversions
varDict = {"mslp": "prmsl", "height": "gh", "shum": "q", "refl": "refc", "zonal wind": "u", "meridional wind": "v", "vert wind": "w", "temp": "t"}

keysDict = {"mslp": {'typeOfLevel': 'meanSea'}, 
            "height": {'typeOfLevel': 'isobaricInhPa'},
            "shum": {'typeOfLevel': 'isobaricInhPa'},
            "refl": {'stepType': 'instant', 'typeOfLevel': 'atmosphereSingleLayer'},
            "zonal wind": {'typeOfLevel': 'isobaricInhPa'},
            "meridional wind": {'typeOfLevel': 'isobaricInhPa'},
            "vert wind": {'typeOfLevel': 'isobaricInhPa'},
            "temp": {'typeOfLevel': 'isobaricInhPa'}}

typeDict = {"track": ["SW", "NE"], "intensity": ["Weak", "Strong"], "R34": ["R34 Small", "R34 Large"], "speed": ["Slow", "Fast"]}

datesDict = {0: "2022092400", 6: "2022092406", 12: "2022092412", 18: "2022092418", 24: "2022092500", 48: "2022092600", 60: "2022092612", 72: "2022092700", 
             84: "2022092712", 96: "2022092800", 108: "2022092812", 120: "2022092900"}


def getAtcfData(model, members, hours):
    # this function processes each ensemble's ATCF data into a list of DataFrames that's easy to work with
    frames  = []
    for member in members:
        # choose which data path to use
        if model == "GFS_analysis":
            atcfPath = f"/work2/noaa/aoml-hafs1/nikhil/bal092022.dat"
        else:
            atcfPath = f"/work2/noaa/aoml-hafs1/nikhil/ian_ensemble_tracks/{model}/2022092400/ian09l.2022092400.hfsb-h223-ens-cloud.{member:02}.trak.atcfunix"

        # create dataframe from ATCF file
        data = pd.read_csv(atcfPath, sep=",", header=None)
        parameters = ["BASIN","CY","YYYYMMDDHH","TECHNUM/MIN","TECH","TAU","latitude","longitude","VMAX","MSLP","TY","RAD","WINDCODE",
                      "RAD1","RAD2","RAD3","RAD4","RADP","RRP","MRD","GUSTS","EYE","SUBREGION","MAXSEAS","INITIALS","direction","speed"]
        if model != "GFS_analysis":
            parameters.insert(24, "bruh")
        data = data[range(len(parameters))]
        data.columns = parameters

        # adjust latitude/longitude values to be consistent with plotting
        data['latitude'] = data['latitude'].map(lambda x: float(x[:-1]) / 10)
        data['longitude'] = 360 - data['longitude'].map(lambda x: float(x[:-1]) / 10)
        data['speed'] = data['speed'] / 10

        # select only time values of interest
        indices = []
        if model == "GFS_analysis":
            for hour in hours:
                index = data[data['YYYYMMDDHH'].astype(str) == datesDict[hour]].index[0]
                indices.append(index)
        else:
            for hour in hours:
                index = data[data['TAU'].astype(int) == hour].index[0]
                indices.append(index)
        data = data.iloc[indices]

        # select only parameters of interest
        data['R34'] = data[["RAD1", "RAD2", "RAD3", "RAD4"]].mean(axis=1)
        data['track'] = data['latitude'] + data['longitude']
        frames.append(data[['latitude', 'longitude', 'MSLP', 'R34', 'track', 'direction', 'speed']])

    return frames


def getClusterRanks(atcfData, hours, forecastHour, clusterType):
    # this function returns the values that will be used for clustering for each ensemble member
    index = np.where(hours == forecastHour)[0][0]

    positions = []
    for memberData in atcfData:
        # choose which data to select base on clustering type
        if clusterType == "intensity":
            positions.append(memberData['MSLP'].iloc[index] * -1)
        else:
            positions.append(memberData[clusterType].iloc[index])
    return positions


def getMemberData(model, variable, members, forecastHour, level=-999):
    print(members)
    # this function returns a DataArray of the specificed variable averaged over the provided ensemble members
    files = []
    for member in members:
        # select the correct path and type of level
        global keysDict
        if model == "GFS_analysis":
            path = f"/work2/noaa/aoml-hafs1/nikhil/IanGFSAnalysis/00l.2022092400.gfs.f{forecastHour:03}.GFS_analysis.grb2"
            if variable == "refl":
                keysDict = {"refl": {'stepType': 'instant', 'typeOfLevel': 'atmosphere'}, "height": {'typeOfLevel': 'isobaricInhPa'}}
        else:
            path = f"/work2/noaa/aoml-hafs1/ahazelto/student_data/ian_grb2_files/{model}/2022092400/00l.2022092400.hfsb.parent.atm.f{forecastHour:03}.{model}_{member:02}.grb2"

        # open variable data
        varDataset = xr.open_dataset(path, engine='cfgrib', filter_by_keys=keysDict[variable], backend_kwargs={'indexpath': f'{path}.idx'})
        varData = varDataset[varDict[variable]]
        if 'isobaricInhPa' in varData.dims and level != -999:
            varData = varData.sel(isobaricInhPa=level)

        # select the lat/lon bounds and append variable data to a list
        if model == "GFS_analysis":
            varData = varData.sel(latitude=slice(45, 10), longitude=slice(260, 310))
        else:
            varData = varData.sel(latitude=slice(10, 45), longitude=slice(260, 310))
        files.append(varData)

    # take the mean of the members and return the resulting DataArray
    varData = xr.concat(files, dim='member').mean(dim='member')
    return varData


def getRadAvgWinds(centeredData, atcfTimeStamp, model):
    xCentered = centeredData['longitude'].values - atcfTimeStamp['longitude']
    yCentered = centeredData['latitude'].values - atcfTimeStamp['latitude']
    xCentered, yCentered = np.meshgrid(xCentered, yCentered)

    r = np.sqrt(xCentered**2 + yCentered**2)
    radialBins = np.linspace(0, 2.5, 40)

    levels = centeredData.isobaricInhPa.values
    levelAverages = []
    # get polar data for each level
    for level in levels:
        levelData = centeredData.sel(isobaricInhPa=level)
        radialAverages = []

        # add wind data to bin if it's within the specified radial bounds
        for i in range(len(radialBins) - 1):
            mask = (r >= radialBins[i]) & (r < radialBins[i + 1])
            maskedWinds = levelData.values[mask]
            radialAverages.append(np.mean(maskedWinds))
        levelAverages.append(radialAverages)

    levelAverages = np.array(levelAverages)
    radialDistance = 0.5 * (radialBins[:-1] + radialBins[1:])  # Use bin centers as coordinates
    crossSectionData = xr.DataArray(levelAverages,
                                    dims=['level', 'radial_distance'],
                                    coords={'level': levels, 'radial_distance': radialDistance})
    return crossSectionData


def getDynamicVortex(crossSectionData, atcfTimeStamp):
    # dynamically calculate the height of the vortex
    minPres = atcfTimeStamp['MSLP']
    for level in crossSectionData.level.values.astype(int):
        if level < minPres:
            break
    bottomLevel = level

    maxIdx = crossSectionData.sel(level=slice(bottomLevel, bottomLevel - 200)).mean(dim="level").argmax().item()
    if maxIdx < 3:
        maxIdx = 3
    vortexSlice = crossSectionData.isel(radial_distance=slice(0, maxIdx * 2))
    vortexMean = vortexSlice.mean(dim="radial_distance")
    maxValue = vortexMean.sel(level=slice(bottomLevel, bottomLevel - 200)).max()
    vortexMean = vortexMean.sel(level=slice(bottomLevel - 200, None))

    dvDr = vortexSlice.differentiate("radial_distance")
    dvDrMean = dvDr.isel(radial_distance=slice(0, maxIdx)).mean("radial_distance")

    for level in vortexMean.level.values.astype(int):
        if minPres < 990:
            threshold = maxValue * 0.5
        else:
            threshold = maxValue * 0.75
        if vortexMean.sel(level=level).item() <= threshold or dvDrMean.sel(level=level).item() < 0:
            break

    leftEdge = vortexSlice.radial_distance.values[0]
    rightEdge = vortexSlice.radial_distance.values[-1]
    return bottomLevel, level, leftEdge, rightEdge

