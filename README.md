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
EnsembleClustering.py
EnsembleLinePlots.py  
EnsembleTracks.py  
HafsDataPlotter.py  
HafsDiffPlotter.py  
RidgeCorrelation.py  
SteerValuesGetter.py  
UsefulFunctions.py
VortexAvgSteer.py

# Parameters (Repeated in Many Scripts)
forecastHour = 24 # forecast hour to use
clusterMembers = 3 # number of members to include in each cluster
variable = "height" # variable to plot under ATCF tracks (check varDict in UsefulFunctions for supported variables)
clusterType = "track" # track, MSLP, R34, speed, direction, steerSpeed, steerDirection, vortexDepth
level = 500 # atmospheric level to plot for (if applicable)
year, month, day, hour = 2022, 9, 24, 0  # initialization date

hours = [0, 24, 48, 60, 72, 84, 96, 108, 120] # hours to pull from ATCF file
members = range(0, 31) # ensemble members to include (range(0, 31) indicates all members)
