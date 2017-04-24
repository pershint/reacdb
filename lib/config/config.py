#Here, we can configure a few parameters that are used throughout the
#Code.
import numpy as np
import sys
import os.path

basepath = os.path.dirname(__file__)

sys.path.append(os.path.abspath(os.path.join(basepath, "..")))
import GetNRCDailyInfo as nrc
sys.path.remove(os.path.abspath(os.path.join(basepath, "..")))


#Defines what isotopes we include in our flux parameterization
ISOTOPES = ['235U', '238U', '239Pu', '241Pu']

#Defines our energy range for our spectra/dNdE and the resoultion
#unites are in MeV.
NU_ENERGY_ARRAY = np.arange(1.82,9.02,0.011)

#Set the number of bins that your histograms will be binned into
#Want len(ENERGY_ARRAY) to be divisible by NUMBINS.
NUMBINS = 30
HMIN = 1.02
HMAX = 8.82

RUNTIME = 8760*5   #Run years in hours

EFFICIENCY = 1  #Assume 100% signal detection efficiency
NP = (1E32 * 0.5929)   #Number of protons on target (1E32 = 1 TNU)

#TODO: Make a list of all cores that have been online since start of 2016 
DATE = '11/20/2016' #Tells GetUSList from which day to grab US operating reactors

#Sets the Canadian reactors to be incorporated in CA spectrum contribution
CAList = ["BRUCE","DARLINGTON","PICKERING","POINT LEPREAU"]
USList = nrc.getUSList(DATE)

#Sets which systematics to include in the generated Spectrum at SNO+
#Current options: "USSYS", "CASYS", and "DETECTOR_RESP"
SYSTEMATICS = ["DETECTOR_RESP"]

#To activate, add "USSYS" to SYSTEMATICS
US_LF_VAR = 25 #Variance in all US load factors as a percentage

#To incorporate, add "CASYS" to SYSTEMATICS
CA_LF_VAR = 25 #Variance in all CA core thermal powers as a percentage

#To incorporate, add "DETECTOR_RESP" to SYSTEMATICS
#Specifies the detector resolution to use for the detector.
#KamLAND's quoted value: 7.5%/sqrt(E)
RESOLUTION = 0.075


