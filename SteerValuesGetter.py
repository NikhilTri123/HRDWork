import numpy as np
import pandas as pd
import UsefulFunctions as uf

hours = np.array([0, 24, 48, 60, 72, 84, 96, 108, 120])

for model in ["default", "tiedtke", "analysis"]:
    members = range(0, 31)
    if model == 'analysis':
        members = range(0, 1)    

    magnitudes, directions, depths = [], [], []
    for member in members:
        print(f"ARGHHHHHHHHHHHHHHHHHHHHHHH: {member}")
        hourMags, hourDirs, hourDepths = [], [], []
        for forecastHour in hours:
            atcfData = uf.getAtcfData(model, [member], hours)[0]
            atcfTimeStamp = atcfData.iloc[np.where(hours == forecastHour)[0][0]]
            centerLat = atcfTimeStamp["latitude"]
            centerLon = atcfTimeStamp["longitude"]

            zonalData = uf.getMemberData(model, "zonal wind", [member], forecastHour)
            meridionalData = uf.getMemberData(model, "meridional wind", [member], forecastHour)
            if model == 'analysis':
                centeredZonal = zonalData.sel(latitude=slice(centerLat+2.5, centerLat-2.5), longitude=slice(centerLon-2.5, centerLon+2.5))
                centeredMeridional = meridionalData.sel(latitude=slice(centerLat+2.5, centerLat-2.5), longitude=slice(centerLon-2.5, centerLon+2.5)) 
            else:
                centeredZonal = zonalData.sel(latitude=slice(centerLat-2.5, centerLat+2.5), longitude=slice(centerLon-2.5, centerLon+2.5))
                centeredMeridional = meridionalData.sel(latitude=slice(centerLat-2.5, centerLat+2.5), longitude=slice(centerLon-2.5, centerLon+2.5))
            centeredData = np.sqrt(centeredZonal**2 + centeredMeridional**2)

            radAvgData = uf.getRadAvgWinds(centeredData, atcfTimeStamp, model)
            vortexBottom, vortexTop, vortexLeft, vortexRight = uf.getDynamicVortex(radAvgData, atcfTimeStamp)
            hourDepths.append(vortexBottom - vortexTop)
            
            # calculate the average steering flow on the vortex
            newLevels = radAvgData.level.sel(level=slice(vortexBottom, vortexTop)).values
            weights = []
            for newLevel in newLevels:
                weights.append(newLevel / 1000)
            zonalAvg = centeredZonal.sel(isobaricInhPa=newLevels).mean(dim=["latitude", "longitude"]).values
            zonalAvg = np.average(zonalAvg, weights=weights) * 1.94384
            meridionalAvg = centeredMeridional.sel(isobaricInhPa=newLevels).mean(dim=["latitude", "longitude"]).values
            meridionalAvg = np.average(meridionalAvg, weights=weights) * 1.94384
            magnitude = np.round(np.sqrt(zonalAvg**2 + meridionalAvg**2), 1)
            direction = np.round((90 - np.rad2deg(np.arctan2(meridionalAvg, zonalAvg))) % 360, 1)
            hourMags.append(magnitude)
            hourDirs.append(direction)
            
        magnitudes.append(hourMags)
        directions.append(hourDirs)
        depths.append(hourDepths)
    magnitudes = np.array(magnitudes)
    directions = np.array(directions)
    depths = np.array(depths)
    np.savetxt(f'./SteerValues/{model}_steerSpeed.txt', magnitudes, fmt='%.1f')
    np.savetxt(f'./SteerValues/{model}_steerDirection.txt', directions, fmt='%.1f')
    np.savetxt(f'./SteerValues/{model}_vortexDepth.txt', depths, fmt='%d')
