#Here, we can configure a few parameters that are used throughout the
#Code.
import numpy as np
import sys
import os.path
import json

basepath = os.path.dirname(__file__)

sys.path.append(os.path.abspath(os.path.join(basepath, "..")))
import GetNRCDailyInfo as nrc
sys.path.remove(os.path.abspath(os.path.join(basepath, "..")))
dbpath = os.path.abspath(os.path.join(basepath,"..","..","db","static"))

#Defines what isotopes we include in our flux parameterization
ISOTOPES = ['235U', '238U', '239Pu', '241Pu']

#Defines our energy range for our spectra/dNdE and the resoultion
#unites are in MeV.
NU_ENERGY_ARRAY = np.arange(1.805,9.005,0.01)

#Set the number of bins that your histograms will be binned into
#Want len(ENERGY_ARRAY) to be divisible by NUMBINS.
NUMBINS = 20   #30
HMIN = 3.0  #1.02
HMAX = 7.0  #8.82

RUNTIME = 8760.*7   #Run years in hours

EFFICIENCY = 1.0  #Assume 100% signal detection efficiency
NP = (1E32 * 0.57719 * ((5.5**3)/(6.0**3)))   #Number of protons on target (1E32 = 1 TNU)
#NP = 1.0E32     #Number of protons on target (1E32 = 1 TNU)


#Sets the Canadian reactors to be incorporated in CA spectrum contribution
CAList = ["BRUCE","DARLINGTON","PICKERING","POINT LEPREAU"]

UseRemoteUSList = False
if UseRemoteUSList:
    DATE = '04/01/2017' #Decide which day from the NRC database you want the list for
    USList = nrc.getUSList(DATE)
else:
    with open(dbpath + "/USLIST_04012017.json") as l:
        USList = json.load(l)

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


