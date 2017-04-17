#Here, we can configure a few parameters that are used throughout the
#Code.

#Defines what isotopes we include in our flux parameterization
ISOTOPES = ['235U', '238U', '239Pu', '241Pu']

#Defines our energy range for our spectra/dNdE and the resoultion
#unites are in MeV.
ENERGY_ARRAY = np.arange(1.82,9,0.01)

#TODO: Make a list of all cores that have been online since start of 2016
#FIXME: is hardcoded in NuSpectrum.py also.  Would be good to not.
DATE = '11/20/2016' #Tells GetUSList from which day to grab US operating reactors

#FIXME: Should have this just read from the ratdb file
#Defines the list of canadian reactors to use for CAList
CAList = ["BRUCE","DARLINGTON", "PICKERING","POINT LEPREAU"]

NUMBINS = 30 #Number of bins for the discretized dNdE spectrum

#Contains flags that tell the program how to vary the
#Spectrum at SNO+ (options: "DETECTOR_RESP","USSYS","CASYS")
SPECTRUM_VARIATIONS = ["DETECTOR_RESP"]  
