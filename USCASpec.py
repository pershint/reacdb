#:ython script for building the expected number of events per day as a function
#of energy at SNO+.  Bins are in 50 keV increments.

import sys

import lib.GetNRCDailyInfo as nrc
import lib.rdbbuild as rb
import lib.rdbparse as rp
import lib.SNOdist as sd
import lib.NuSpectrum as ns
import tools.graph.SpectraPlots as splt
import tools.graph.OscPlot as oplt
import tools.hist.binning as hb
import lib.playDarts as pd
import numpy as np

import time
import inspect as ins
import optparse


#DATE = '11/20/2016' #Date queried on NRC.gov to get operating US reactor names
#RUNTIME = 8760   #One year in hours
#EFFICIENCY = 1  #Assume 100% signal detection efficiency
#LF = 0.8    #Assume all power plants operate at 80% of licensed MWt
#MWHTOMEV = 2.247E22 #One MW*h equals this many MeV
#NP = 1E32   #Need to approximate SNO+'s number of proton targets
ISOTOPES = ['235U', '238U', '239Pu', '241Pu']
ENERGIES_TO_EVALUATE_AT = np.arange(1.82,9,0.01)
DATE = '11/20/2016' #Date queried on NRC.gov to get operating US reactor names



#Oscillation variables that will be measured by SNO+/vary
#between SuperK and KamLAND; others are found hard-coded in
#./lib/NuSPectrum.py
oscParams = []
def setOscParams(parameter_choice):
    if parameter_choice == "SK":
        print("USING SUPERKAMIOKANDE OSCILLATION PARAMETERS")
        sst12 = 0.334
        dmsq = 4.85E-05
        globals()["oscParams"] = [dmsq, sst12]

    if parameter_choice == "KAMLAND":
        print("USING KAMLAND OSCILLATION PARAMETERS")
        sst12 = 0.316
        dmsq = 7.54E-05
        globals()["oscParams"] = [dmsq, sst12]

    if parameter_choice == "none":
        print("NO OSCILLATION PARAMETERS SET.  NOOOO")



parser = optparse.OptionParser()
parser.add_option("--debug",action="store_true",default="False")
parser.add_option("-p", "--parameters",action="store",dest="parameters",
                  type="string",default="KAMLAND",
                  help="Specify which experiment's oscillation parameters to use")
parser.add_option("-r", "--reactors",action="store",dest="reactors",
                  type="string",default="USCA",
                  help="Specify what set of reactors to use (US, CA, or USCA)")
(options,args) = parser.parse_args()

DEBUG = options.debug
#Set which parameters to call when building neutrino spectrums
setOscParams(options.parameters)
ns.setDebug(options.debug)
print(options.debug)


def GaussRand(mu, sigma, n):
    """
    Returns an array of n random values sampled from a gaussian of
    average mu and variance sigma.
    """
    return mu + sigma * np.random.randn(n)

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
#FIXME: If there's no online connection, need to
#Default to some hard-coded list
def getUSList():
    NRClist = nrc.NRCDayList()
    NRClist.getDateReacStatuses(DATE)
    NRClist.fillDateNames()
    USlist = NRClist.date_reacs
    USlist = rb.USListToRATDBFormat(USlist)
    return USlist

#Uses whatever type is set in the arguments for -r to pick a reactor name list
def setListType():
    if options.reactors == "WORLD":
        WorldList = rp.getRLIndices()
        return WorldList
    if options.reactors == "US":
        USList = getUSList()
        return USList
    if options.reactors == ("CA"):
        CAList = ["BRUCE","DARLINGTON", "PICKERING","POINT LEPREAU"]
        return CAList
    if options.reactors == ("USCA"):
        USList = getUSList()
        CAList = ["BRUCE","DARLINGTON", "PICKERING","POINT LEPREAU"]
        USCAList = USList + CAList
        return USCAList

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
#FIXME: want the return of this to be the final spectrum.

def build_unoscSpectra(List):
    All_unosc_spectra = []
    for reactor in List:
        ReacDetails = rp.ReactorDetails(reactor)
        ReacStatus = rp.ReactorStatus(reactor)
        ReacUnoscSpectra = ns.UnoscSpectra(ReacDetails,ReacStatus, \
                Isotope_Information, ENERGIES_TO_EVALUATE_AT)
        All_unosc_spectra.append(ReacUnoscSpectra)
    return All_unosc_spectra

def build_dNdE(All_unosc_spectra,oscParams):
    Total_Spectra = np.zeros(len(ENERGIES_TO_EVALUATE_AT))
    for unoscSpectrum in All_unosc_spectra:
        ReacOscSpectra = ns.OscSpectra(unoscSpectrum, oscParams)
        Total_Spectra += ReacOscSpectra.Summed_Spectra
    splt.CAspectrumPlot(ENERGIES_TO_EVALUATE_AT,Total_Spectra)
    return ns.dNdE(ENERGIES_TO_EVALUATE_AT,Total_Spectra)

if __name__ == '__main__':
    List = setListType()
    
    #Build array containing details for each isotope found in reactors
    Isotope_Information = []
    lambda_values = []
    for isotope in ISOTOPES:
        Isotope_Information.append(rp.Reactor_Isotope_Info(isotope))


    if DEBUG == True:
        print("IN")
        time.sleep(5)
#        print("#------ AN EXERCIES IN CALCULATING A LARGE LAMBDA ------#")
#        for energy in ENERGIES_TO_EVALUATE_AT:
#            lamb_value= Lambda(Isotope_Information, \
#                rp.Reactor_Spectrum("PHWR").param_composition, energy).value
#            lambda_values.append(lamb_value)
#        print("EXERCISE RESULT:" + str(lambda_values))
    
        print("#----- AN EXERCISE IN CALCULATING AN UNOSC. SPECTRA FOR BRUCE --#")


        BruceDetails = rp.ReactorDetails("BRUCE")
        BruceStatus = rp.ReactorStatus("BRUCE")
        BruceUnoscSpectra = ns.UnoscSpectra(BruceDetails,BruceStatus,Isotope_Information, \
                ENERGIES_TO_EVALUATE_AT)
        BruceOscSpectra = ns.OscSpectra(BruceUnoscSpectra)
        for CORENUM in np.arange(1,BruceUnoscSpectra.no_cores+1):
#            print("UNOSC RESULT: " + str(BruceUnoscSpectra.Unosc_Spectra))
#            print("GRAPHING UNOSC SPECTRA FOR " + str(CORENUM) + " NOW...")
 #           splt.plotCoreUnoscSpectrum((CORENUM-1),BruceUnoscSpectra)
#            print("OSC RESULT: " + str(BruceOscSpectra.Osc_Spectra))
            print("GRAPHING OSC SPECTRA FOR " + str(CORENUM) + " NOW...")
            splt.plotCoreOscSpectrum((CORENUM-1),BruceOscSpectra)
#            print("Graphing Survival Probability of electron antineutrio now...")
#            oplt.plotCoreSurvivalProb((CORENUM-1),BruceOscSpectra)
        print("Graphing sum of oscillated spectra for BRUCE:")
        splt.plotSumOscSpectrum(BruceOscSpectra)

        print("#---- END EXERCISES FOR BRUCE -----#")
    print(" ")
    showReactors()
    unosc_spectra = build_unoscSpectra(List)
    USCA_dNdE = build_dNdE(unosc_spectra,oscParams)

    RoughIntegrate(USCA_dNdE.dNdE,ENERGIES_TO_EVALUATE_AT)
    splt.dNdEPlot_line(ENERGIES_TO_EVALUATE_AT,USCA_dNdE.dNdE, oscParams[1],\
            oscParams[0])
    spec, bin_centers, bin_lefts, bin_rights = hb.reBin_EW(USCA_dNdE.dNdE, \
            ENERGIES_TO_EVALUATE_AT,25)
    splt.dNdEPlot_pts(bin_centers,spec,bin_lefts,bin_rights, oscParams[1], \
            oscParams[0])
    events_per_year = RoughIntegrate(spec,bin_lefts)
    #----- RUN 100 RANDOM EXPERIMENTS, SEE WHAT YOU GET ----#
    #----- ASSUME EVENTS PER YEAR AS GIVEN WITH 250 KEV BINNING ----#
    experiments = []
    num_experiments = 100
    experiment = 0
    while experiment < num_experiments:
        n = pd.RandShoot(events_per_year, np.sqrt(events_per_year),1)
        random_exp_spec = pd.playDarts(n,spec,bin_lefts,bin_rights,bin_centers)
        experiments.append(random_exp_spec)
        if experiment < 5:
            splt.dNdEPlot_pts(bin_centers,random_exp_spec,bin_lefts,bin_rights, \
                    oscParams[1], oscParams[0])
        experiment += 1
    exp_avg_spec, bin_stdevs = pd.arr_average(experiments)
    splt.dNdEPlot_pts(bin_centers,exp_avg_spec, bin_lefts,bin_rights, \
            oscParams[1], oscParams[0])
