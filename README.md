# Convective Schemes Analysis Scripts
Author: Nikhil Trivedi

The scripts listed within this README are what I used to evaluate the various convective schemes that were run with HAFS.
Although I only looked at comparisons between HFSB-default and HFSB-tiedtke and were only evaluated on Hurricane Ian, the scripts
were designed to be flexible enough to be used for any of the convective schemes that were run and any storm that they were run
on. The function of each of these scripts vary greatly, and will be described below. For more detail about the function of any of 
these scripts, visit them and read the detailed description at the top. Additionally, the variables and inputs that the scripts 
currently accept will also be listed below. Because many of the adjustable parameters are used in multiple scripts, I'll just 
independently outline their purposes.

# Scripts
This script is a dependacy for every other script, as it contains a list of functions that are repeatedly used by many of them:
UsefulFunctions.py

These are more basic plotting scripts that specify a particular model and runType:
HafsDataPlotter.py
HafsDiffPlotter.py

These scripts do some sort of ranking process, utilizing the clusterType parameter:
EnsembleClustering.py
EnsembleLinePlots.py  
EnsembleTracks.py  

Kind of miscellaneous scripts, read the descriptions at the top of them to learn more about them:
RidgeCorrelation.py  
SteerValuesGetter.py  
VortexAvgSteer.py

# Repeated Parameters (Doesn't Include All)
year, month, day, hour: This specifies the initialization time and date for the forecast. 

hours: This is a list that specifies all the forecast hours that have grb2 data available. It's used to gather the relevant ATCF data.

forecastHour: This selects the forecast hour that is used when relevant in plotting and/or calculations. 

variable: This specifies the variable that will be spatially plotted from the grb2 data.

level: This specifies the pressure level of the variable data that will be plotted, if necessary. If the variable doesn't have levels, it'll be ignored.

members: This specifies the ensemble members that will be used in a given script. Use range(0, 1) for the control and range(0, 31) for all members.

model: This specifies the model configuration that will be plotted. It can take any of the HAFS configurations and also GFS analysis.

clusterType: This specifies the type of storm attribute that is used for clustering or ranking within ensemble sets.

runType: This specifies whether the control or an ensemble mean should be plotted for the basic plotting scripts.

# Dictionary Info
varDict: Converts the value inputted in the variable parameter to the equivalent name in the grb2 file
Currently available variables are mslp, height, shum, refl, zonal wind, meridional wind, vert wind, temp

keysDict: Retrieves the category that the provided variable is under, as this is needed for xarray to read the grb2 file
The same variables as above are supported, this dictionary pretty much just supports the above one

typeDict: Looks at the value inputted in the clusterType parameter and defines the two groups (displayed in the title)
The clusterTypes supported by this are track, MSLP, R34, speed, direction, steerSpeed, steerDirection, vortexDepth
Note that steerSpeed, steerDepth, and vortexDepth are all quantities derived from vortex-averaged environmental steering

datesDict: Used specifically to convert GFS analysis intialization times to HAFS forecast hours for consistency between ATCF files
The "forecast hours" supported by this are 0, 6, 12, 18, 24, 48, 60, 72, 84, 96, 108, 120
