#Here, we can configure a few parameters that are used throughout the
#Code.
import numpy as np

#Defines what isotopes we include in our flux parameterization
ISOTOPES = ['235U', '238U', '239Pu', '241Pu']

#Defines our energy range for our spectra/dNdE and the resoultion
#unites are in MeV.
ENERGY_ARRAY = np.arange(1.82,9,0.01)

#TODO: Make a list of all cores that have been online since start of 2016
#FIXME: is hardcoded in NuSpectrum.py also.  Would be good to not.
DATE = '11/20/2016' #Tells GetUSList from which day to grab US operating reactors

#Set the number of bins that your histograms will be binned into
NUMBINS = 30

#Sets the Canadian reactors to be incorporated in CA spectrum contribution
CAList = ["BRUCE","DARLINGTON","PICKERING","POINT LEPREAU"]

#Sets which systematics to include in the generated Spectrum at SNO+
#Current options: "USSYS", "CASYS", and "DETECTOR_RESP"
SYSTEMATICS = ["DETECTOR_RESP"]

#Specifies the detector resolution to use for the detector.
#KamLAND's quoted value: 7.5%/sqrt(E)
RESOLUTION = 0.075


