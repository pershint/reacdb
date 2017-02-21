#:ython script for building the expected number of events per day as a function
#of energy at SNO+.

import sys,time,optparse

import lib.GetNRCDailyInfo as nrc
import lib.rdbbuild as rb
import lib.rdbparse as rp
import lib.SNOdist as sd
import lib.NuSpectrum as ns
import lib.chi2ML_Utils as cmu

import tools.graph.SpectraPlots as splt
import tools.graph.OscPlot as oplt
import tools.graph.ChiSquaredPlots as cplt

import tools.hist.binning as hb
import lib.Histogram as h
import lib.playDarts as pd

import numpy as np
import scipy.optimize as spo

import iminuit as im


#DATE = '11/20/2016' #Date queried on NRC.gov to get operating US reactor names
ISOTOPES = ['235U', '238U', '239Pu', '241Pu']
ENERGY_ARRAY = np.arange(1.82,9,0.01)

#TODO: Make a list of all cores that have been online since start of 2016
#FIXME: is hardcoded in NuSpectrum.py also.  Would be good to not.
DATE = '11/20/2016' #Tells GetUSList from which day to grab US operating reactors

CAList = ["BRUCE","DARLINGTON", "PICKERING","POINT LEPREAU"]

NUMBINS = 30 #Number of bins for the discretized dNdE spectrum

#Oscillation variables that will be measured by SNO+/vary
#between SuperK and KamLAND; fixed parameters are found hard-coded in
#./lib/NuSPectrum.py
oscParams = []
def setOscParams(parameter_choice):
    if parameter_choice == "SK":
        print("USING SUPERKAMIOKANDE OSCILLATION PARAMETERS")
        sst12 = 0.334
        dmsq = 4.85E-05
        globals()["oscParams"] = [dmsq, sst12]

    elif parameter_choice == "KAMLAND":
        print("USING KAMLAND OSCILLATION PARAMETERS")
        sst12 = 0.316
        dmsq = 7.54E-05
        globals()["oscParams"] = [dmsq, sst12]

    elif parameter_choice == "none":
        print("NO OSCILLATION PARAMETERS SET.  NOOOO")

    else:
        print("CHOOSE A VALID OSCILLATION PARAMETER SET (SK or KAMLAND).")
        sys.exit(0)

parser = optparse.OptionParser()
parser.add_option("--debug",action="store_true",default="False")
parser.add_option("-p", "--parameters",action="store",dest="parameters",
                  type="string",default="KAMLAND",
                  help="Specify which experiment's oscillation parameters to use")
parser.add_option("-r", "--reactors",action="store",dest="reactors",
                  type="string",default="USCA",
                  help="Specify what set of reactors to use (US, WORLD, CA, or USCA)")
(options,args) = parser.parse_args()

DEBUG = options.debug
#Set which parameters to call when building neutrino spectrums
setOscParams(options.parameters)
ns.setDebug(options.debug)

def GetBruceSpectra(List,Isotope_Information):
    print("#----- AN EXERCISE IN CALCULATING AN UNOSC. SPECTRA FOR BRUCE --#")
    BruceDetails = rp.ReactorDetails("BRUCE")
    BruceStatus = rp.ReactorStatus("BRUCE")
    BruceUnoscSpecGen = ns.UnoscSpecGen(BruceDetails,BruceStatus,Isotope_Information, \
            ENERGY_ARRAY)
    BruceOscSpecGen = ns.OscSpecGen(BruceUnoscSpecGen)
    for CORENUM in np.arange(1,BruceUnoscSpecGen.no_cores+1):
        print("GRAPHING OSC SPECTRA FOR " + str(CORENUM) + " NOW...")
        splt.plotCoreOscSpectrum((CORENUM-1),BruceOscSpecGen)
    print("Graphing sum of oscillated spectra for BRUCE:")
    splt.plotSumOscSpectrum(BruceOscSpecGen)
    print("#---- END EXERCISES FOR BRUCE -----#")

def RoughIntegrate(y_array,x_array):
    """
    Returns the area under the y_array for the range of the
    x_array.  The bin width for y_array[i] is defined here as
    x_array[i+1] - x_array[i].
    """
    print("NOTE: Final endpoint of array is not considered in integral.")
    integral = 0.0
    for i,y in enumerate(y_array):
        if i == len(y_array)-1:
            print("At end of array.  Result: " + str(integral))
            return int(integral)
        integral += y_array[i] * (x_array[i+1]-x_array[i])

#Uses whatever type is set in the arguments for -r to pick a reactor name list
def setListType(List_Dictionary):
    if options.reactors == ("USCA"):
        USCAList = List_Dictionary['US'] + List_Dictionary['CA']
        return USCAList
    else:
        try:
            return List_Dictionary[options.reactors]
        except KeyError:
            print("Choose a valid reactor list option.  see python main.py --help" + \
                    "for choices")
            raise

def showReactors():
    if options.reactors == "CA":
        print("GRAPHING THE SUM OF CANADIAN REACTORS")
    if options.reactors == "US":
        print("GRAPHING THE SUM OF US REACTORS")
    if options.reactors == "USCA":
        print("GRAPHING THE SUM OF US AND CA REACTORS")
    if options.reactors == "WORLD":
        print("GRAPHING SUM OF WORLD'S REACTORS AT SNO+")

#Takes in a list of reactor names from REACTORS.ratdb and
#Returns the dNdE class from all the reactor's operational
#cores

def build_unoscSpectra(List):
    unosc_spectra = []
    for reactor in List:
        ReacDetails = rp.ReactorDetails(reactor)
        ReacStatus = rp.ReactorStatus(reactor)
        ReacUnoscSpecGen = ns.UnoscSpecGen(ReacDetails,ReacStatus, \
                Isotope_Information, ENERGY_ARRAY)
        unosc_spectra.append(ReacUnoscSpecGen)
    return unosc_spectra


if __name__ == '__main__':
    WorldList = rp.getRLIndices()
    print(WorldList)
    USList = nrc.getUSList(DATE)
    List_Dictionary = {'US':USList, 'WORLD':WorldList, 'CA':CAList}
    showReactors()
    List = setListType(List_Dictionary)
    #Build array containing details for each isotope found in reactors
    Isotope_Information = []
    lambda_values = []
    for isotope in ISOTOPES:
        Isotope_Information.append(rp.Reactor_Isotope_Info(isotope))


    if DEBUG == True:
        print("IN DEBUG MODE")
        time.sleep(1)
        getBruceSpectra(List, Isotope_Information)

    print(" ")
    unosc_spectra = build_unoscSpectra(List)
    #First, show the dNdE function
    USCA_dNdE = ns.build_dNdE(unosc_spectra,ENERGY_ARRAY,oscParams)
    RoughIntegrate(USCA_dNdE.dNdE,ENERGY_ARRAY)
    splt.dNdEPlot_line(ENERGY_ARRAY,USCA_dNdE.dNdE, oscParams[1],\
            oscParams[0])
    if DEBUG == True:
        splt.dNdEPlot_line(ENERGY_ARRAY,USCA_dNdE.dNdE, oscParams[1],\
                oscParams[0])

    #Calculate the chi-squared test results (fixed dms, vary sst)
    #sst_array = np.arange(0.01, 1.00, 0.01)
    #chi2_results = cmu.GetChi2dmsFixed(unosc_spectra, oscParams, sst_array, \
    #        ENERGY_ARRAY,NUMBINS)
    #cplt.chi2vssst(chi2_results, sst_array,oscParams)
    #Now, create your "perfect" event histogram, events binned into 30 bins
    #EventHist_wstats, EventHist = cu.getExpt_wstats(oscParams, unosc_spectra, \
    #        ENERGY_ARRAY,NUMBINS)

    #----- TRY THE MINIMIZATION OF THE CHISQUARE FUNCTION FOR -----#
    #----- THE TRUE SPECTRA AT SNO+ AND A FLUX WITH EXPERIMENTAL --#
    #----- UNCERTAINTY                                       ------#
    #TODO: RUN THIS WITH SUPERK VALUES, 5YEARS
    #
    num_experiments = 1000
    dms_fits, sst_fits, negML_results = cmu.GetNegMLStatSpread(num_experiments, \
            unosc_spectra,oscParams,ENERGY_ARRAY,NUMBINS)
    print(dms_fits)
    print(sst_fits)
    print(negML_results)
    cplt.chi2scatter(dms_fits,sst_fits,oscParams)
