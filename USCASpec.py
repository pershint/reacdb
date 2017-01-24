#:ython script for building the expected number of events per day as a function
#of energy at SNO+.

import sys,time,optparse

import lib.GetNRCDailyInfo as nrc
import lib.rdbbuild as rb
import lib.rdbparse as rp
import lib.SNOdist as sd
import lib.NuSpectrum as ns
import tools.graph.SpectraPlots as splt
import tools.graph.OscPlot as oplt
import tools.hist.binning as hb
import tools.graph.ChiSquaredGrid as csg
import lib.Histogram as h
import lib.playDarts as pd

import numpy as np
import scipy.optimize as spo

import iminuit as im


#DATE = '11/20/2016' #Date queried on NRC.gov to get operating US reactor names
#RUNTIME = 8760   #One year in hours
#EFFICIENCY = 1  #Assume 100% signal detection efficiency
#LF = 0.8    #Assume all power plants operate at 80% of licensed MWt
#MWHTOMEV = 2.247E22 #One MW*h equals this many MeV
#NP = 1E32   #Need to approximate SNO+'s number of proton targets
ISOTOPES = ['235U', '238U', '239Pu', '241Pu']
ENERGIES_TO_EVALUATE_AT = np.arange(1.82,9,0.01)
DATE = '11/20/2016' #Date queried on NRC.gov to get operating US reactor names

OSCPARAM_BOUNDS = ((1.0E-05, 3.0E-04),(0.000000001,0.999999999999))
MIN_METHOD = 'TNC'

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

def GetBruceSpectra(List,Isotope_Information):
#    print("#------ AN EXERCIES IN CALCULATING A LARGE LAMBDA ------#")
#    for energy in ENERGIES_TO_EVALUATE_AT:
#        lamb_value= Lambda(Isotope_Information, \
#            rp.Reactor_Spectrum("PHWR").param_composition, energy).value
#       lambda_values.append(lamb_value)
#    print("EXERCISE RESULT:" + str(lambda_values))

    print("#----- AN EXERCISE IN CALCULATING AN UNOSC. SPECTRA FOR BRUCE --#")

    BruceDetails = rp.ReactorDetails("BRUCE")
    BruceStatus = rp.ReactorStatus("BRUCE")
    BruceUnoscSpectra = ns.UnoscSpectra(BruceDetails,BruceStatus,Isotope_Information, \
            ENERGIES_TO_EVALUATE_AT)
    BruceOscSpectra = ns.OscSpectra(BruceUnoscSpectra)
    for CORENUM in np.arange(1,BruceUnoscSpectra.no_cores+1):
#        print("UNOSC RESULT: " + str(BruceUnoscSpectra.Unosc_Spectra))
#        print("GRAPHING UNOSC SPECTRA FOR " + str(CORENUM) + " NOW...")
#        splt.plotCoreUnoscSpectrum((CORENUM-1),BruceUnoscSpectra)
#        print("OSC RESULT: " + str(BruceOscSpectra.Osc_Spectra))
        print("GRAPHING OSC SPECTRA FOR " + str(CORENUM) + " NOW...")
        splt.plotCoreOscSpectrum((CORENUM-1),BruceOscSpectra)
#        print("Graphing Survival Probability of electron antineutrio now...")
#        oplt.plotCoreSurvivalProb((CORENUM-1),BruceOscSpectra)
    print("Graphing sum of oscillated spectra for BRUCE:")
    splt.plotSumOscSpectrum(BruceOscSpectra)

    print("#---- END EXERCISES FOR BRUCE -----#")

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

def build_unoscSpectra(List):
    unosc_spectra = []
    for reactor in List:
        ReacDetails = rp.ReactorDetails(reactor)
        ReacStatus = rp.ReactorStatus(reactor)
        ReacUnoscSpectra = ns.UnoscSpectra(ReacDetails,ReacStatus, \
                Isotope_Information, ENERGIES_TO_EVALUATE_AT)
        unosc_spectra.append(ReacUnoscSpectra)
    return unosc_spectra

def build_dNdE(unosc_spectra,oscParams):
    Total_Spectra = np.zeros(len(ENERGIES_TO_EVALUATE_AT))
    for unoscSpectrum in unosc_spectra:
        ReacOscSpectra = ns.OscSpectra(unoscSpectrum, oscParams)
        Total_Spectra += ReacOscSpectra.Summed_Spectra
    return ns.dNdE(ENERGIES_TO_EVALUATE_AT,Total_Spectra)

#builds the chi-squared between the expected SNO+ spectrum with
#systematics included and an oscillated spectrum with no systematics
#that is oscillated with a (sine-squared theta12) and b
#(Delta m-squared). In this case, an unoscillated spectra is
#passed in to be oscillated with a,b.
#Check your bin sizes; don't want to feed in an un-scaled true spectrum

#Function returns an oscillated SNO+ antineutrino spectrum with statistical
#Fluctuation generated using the PlayDarts library.  Also returns the
#Spectrum without statistical fluctuation
def getExpt_wstats(oscParams, All_unosc_spectra,numBins):
    dNdE = build_dNdE(All_unosc_spectra, oscParams)
    NoStat_EventHist = h.dNdE_Hist(dNdE, numBins)
    events_per_year = sum(NoStat_EventHist.bin_values)
    n = pd.RandShoot(events_per_year, np.sqrt(events_per_year),1)
    print("NUMBER OF EVENTS FIRED:" + str(n))
    Stat_EventHist = pd.playDarts_h(n,NoStat_EventHist)
    return Stat_EventHist, NoStat_EventHist

#INPUTS: oscillation parameter array [Delta m-squared, sst12], Unoscilated
#spectra used to generate the event histograms, Event histogram with statistical
#fluctuation, Event histogram without statistical fluctuation
class ExperimentChi2(object):
    def __init__(self, unosc_spectra, Stat_EventHist,NoStat_EventHist):
        self.unosc_spectra = unosc_spectra
        self.Stat_EventHist = Stat_EventHist
        self.NoStat_EventHist = NoStat_EventHist
    def __call__(self, dms, sst):
        print("OSC PARAMS FED IN: " + str([dms,sst]))
        dNdE = build_dNdE(self.unosc_spectra, [dms,sst])
        #Build your histogram for the input oscillation parameters
        FitHist = h.dNdE_Hist(dNdE, 30)
        chisquare = np.sum(((FitHist.bin_values - 
            self.Stat_EventHist.bin_values)**2)/ self.NoStat_EventHist.bin_values)
        #use uncertainty of the no-statistics event histogram spectrum; that is, 
        #variance =NoStat_EventHist.bin_values)
        print("CHISQ RESULT: " + str(chisquare))
        return chisquare


def chisquared(test,true):
    return np.sum(((true-test)**2)/true)

if __name__ == '__main__':
    List = setListType()
    
    #Build array containing details for each isotope found in reactors
    Isotope_Information = []
    lambda_values = []
    for isotope in ISOTOPES:
        Isotope_Information.append(rp.Reactor_Isotope_Info(isotope))


    if DEBUG == True:
        print("IN DEBUG MODE")
        time.sleep(5)
        getBruceSpectra(List, Isotope_Information)

    print(" ")
    showReactors()
    unosc_spectra = build_unoscSpectra(List)
    
    #First, show the dNdE function
    USCA_dNdE = build_dNdE(unosc_spectra,oscParams)
    RoughIntegrate(USCA_dNdE.dNdE,ENERGIES_TO_EVALUATE_AT)
    splt.dNdEPlot_line(ENERGIES_TO_EVALUATE_AT,USCA_dNdE.dNdE, oscParams[1],\
            oscParams[0])
    
    #Now, create your "perfect" event histogram, events binned into 30 bins
    EventHist_wstats, EventHist = getExpt_wstats(oscParams, unosc_spectra,30)
    splt.plot_hist(EventHist, oscParams[1], oscParams[0])
    events_per_year = sum(EventHist.bin_values)
    print("EVENTS PER YEAR FOR STAT-FLUCTUATED HIST: " + str(events_per_year))

    #----- TRY THE MINIMIZATION OF THE CHISQUARE FUNCTION FOR -----#
    #----- THE TRUE SPECTRA AT SNO+ AND A FLUX WITH EXPERIMENTAL --#
    #----- UNCERTAINTY                                       ------#
    x0 = np.array(oscParams)
    print("CHISQUARE BEING CALCULATED NOW FOR A RANDOM EXPERIMENT...")
    print("FED IN SPEC:" + str(EventHist.bin_values))
    print("LET'S TRY TO MINIMIZE THE CHI-SQUARED WITH MINUIT...")
    chi2 = ExperimentChi2(unosc_spectra,EventHist_wstats,EventHist)
    print("CHI-SQUARED RESULT WITH TRUE OSCILLATION PARAMETERS: \n")
    chi2(x0[0], x0[1])
    im.describe(chi2)
    m = im.Minuit(chi2, limit_sst=(0.0,1.0),limit_dms = (1e-07, 1e-03),dms = 4e-05, sst = .334)
    m.migrad()
    print("MINIMIZATION OUTPUT: " + str(m.values))

    #----- HEAT PLOT OF CHISQUARES AROUND SK AND KL VALUES -----#
    dms_array = np.arange(1E-06,1E-04, 0.000001)
    sst_array = np.arange(0.300,0.400, 0.001)
    chisq_array = []
    dms_value = []
    sst_value = []
    for dms in dms_array:
        for sst in sst_array:
            chisq_array.append(chi2(dms,sst))
            dms_value.append(dms)
            sst_value.append(sst)
    csg.chi2grid(dms_value,sst_value,chisq_array)

    #----- RUN 100 RANDOM EXPERIMENTS, SEE WHAT YOU GET ----#
    #----- ASSUME EVENTS PER YEAR AS GIVEN WITH 250 KEV BINNING ----#
    RandExpHists = []
    RandExpHists_binVals = []
    num_experiments = 100
    experiment = 0
    while experiment < num_experiments:
        n = pd.RandShoot(events_per_year, np.sqrt(events_per_year),1)
        RandExpHist  = pd.playDarts_h(n,EventHist)
        RandExpHists_binVals.append(RandExpHist.bin_values)
        RandExpHists.append(RandExpHist)
        if experiment < 5:
            splt.plot_hist(RandExpHist, oscParams[1], oscParams[0])
        experiment += 1
        
    exp_avg_hist, bin_stdev_hist = pd.hist_average(RandExpHists)
    splt.plot_hist(exp_avg_hist, oscParams[1], oscParams[0])
    print("CHECK: THE CHI-SQUARED BETWEEN THE AVERAGE OF ALL AND THE" + \
            "EXPECTED SPECTRUM AT SNO+")
    print(chisquared(exp_avg_hist.bin_values,EventHist.bin_values))