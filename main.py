#:ython script for building the expected number of events per day as a function
#of energy at SNO+.

import sys,time,optparse

import lib.GetNRCDailyInfo as nrc
import lib.rdbbuild as rb
import lib.rdbparse as rp
import lib.SNOdist as sd
import lib.NuSpectrum as ns
import lib.chi2ML_Utils as cmu
import lib.NuToPos as ntp

import tools.graph.SpectraPlots as splt
import tools.graph.OscPlot as oplt
import tools.graph.ChiSquaredPlots as cplt

import lib.Histogram as h
import lib.playDarts as pd

import lib.config.config as c

import numpy as np

import json
import os.path

#Controls location to save output fit results
basepath = os.path.dirname(__file__)
outpath = os.path.abspath(os.path.join(basepath, "output"))


#Oscillation variables that will be measured by SNO+/vary
#between SuperK and KamLAND; fixed parameters are found hard-coded in
#./lib/NuSPectrum.py
oscParams = []
def setOscParams(parameter_choice):
    if parameter_choice == "SK":
        print("USING SUPERKAMIOKANDE OSCILLATION PARAMETERS")
        sst12 = 0.308
        dmsq = 4.85E-05
        globals()["oscParams"] = [dmsq, sst12]

    elif parameter_choice == "KAMLAND":
        print("USING KAMLAND OSCILLATION PARAMETERS")
        sst12 = 0.316
        dmsq = 7.54E-05
        globals()["oscParams"] = [dmsq, sst12]

    elif parameter_choice == "PDG":
        print("USING PDG 2016 OSCILLATION PARAMETERS")
        sst12 = 0.297
#        dmsq = 7.37E-05
        dmsq = 1.75E-04
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
                  type="string",default="WORLD",
                  help="Specify what set of reactors to use (US, WORLD, CA, or USCA)")
parser.add_option("-j", "--jobnum",action="store",dest="jobnum",
                  type="string",default="0",
                  help="Specify a jobnumber to save onto the end of the generated data")
parser.add_option("-s", "--seed", action="store_true", dest="seed",
                  default="False",help="Runs feeds in a DMS value to minuit" + \
                  "found by doing a rough global minimization across DMS at fixed SST")
(options,args) = parser.parse_args()

DEBUG = options.debug
#Set which parameters to call when building neutrino spectrums
setOscParams(options.parameters)
ns.setDebug(options.debug)
JNUM = options.jobnum
DMSSEED = options.seed

print("SPECTRUM VARIATIONS SET IN CONFIG: " + str(c.SYSTEMATICS))

def getBruceSpectra():
    print("#----- AN EXERCISE IN CALCULATING AN UNOSC. SPECTRA FOR BRUCE --#")
    #Build array containing details for each isotope found in reactors
    Isotope_Information = []
    lambda_values = []
    for isotope in c.ISOTOPES:
        Isotope_Information.append(rp.Reactor_Isotope_Info(isotope))

    BruceDetails = rp.ReactorDetails("BRUCE")
    BruceStatus = rp.ReactorStatus("BRUCE")
    BruceUnoscSpecGen = ns.UnoscSpecGen(BruceDetails,BruceStatus,Isotope_Information, \
            c.NU_ENERGY_ARRAY,c.RUNTIME)
    BruceOscSpecGen = ns.OscSysGen(BruceUnoscSpecGen,oscParams)
    for CORENUM in np.arange(1,BruceUnoscSpecGen.no_cores+1):
        print("GRAPHING OSC SPECTRA FOR " + str(CORENUM) + " NOW...")
        splt.plotCoreOscSpectrum((CORENUM-1),BruceOscSpecGen)
    print("Graphing sum of oscillated spectra for BRUCE:")
    splt.plotSumOscSpectrum(BruceOscSpecGen)
    oplt.plotCoreSurvivalProb(1,BruceOscSpecGen)
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
        if i == 0:
            integral += y_array[i] * (x_array[i+1]-x_array[i])
        elif i == len(y_array)-1:
            print("At end of array.  Result: " + str(integral))
            return int(integral)
        else:
            integral += y_array[i] * (((x_array[i]-x_array[i-1]) + \
                    (x_array[i+1]-x_array[i]))/2.)

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
    #Build array containing details for each isotope found in reactors
    Isotope_Information = []
    lambda_values = []
    for isotope in c.ISOTOPES:
        Isotope_Information.append(rp.Reactor_Isotope_Info(isotope))
    #Use List and isotope information to build spectra
    unosc_spectra = []
    for reactor in List:
        ReacDetails = rp.ReactorDetails(reactor)
        ReacStatus = rp.ReactorStatus(reactor)
        ReacUnoscSpecGen = ns.UnoscSpecGen(ReacDetails,ReacStatus, \
                Isotope_Information, c.NU_ENERGY_ARRAY,c.RUNTIME)
        unosc_spectra.append(ReacUnoscSpecGen)
    return unosc_spectra


if __name__ == '__main__':
    if DEBUG == "True":
        print("IN DEBUG MODE")

    #Get the list of reactors to use in simulation
    WorldList = rp.getRLIndices()
    List_Dictionary = {'US':c.USList, 'WORLD':WorldList, 'CA':c.CAList}
    if DEBUG == True:
        showReactors()
    List = setListType(List_Dictionary)
    #if DEBUG == True:
    #    getBruceSpectra()

    #construct unoscillated spectra of all cores in List
    #CORE SYSTEMATICS NOT ADDED HERE YET
    #unosc_spectra = build_unoscSpectra(List)
    unosc_spectra = build_unoscSpectra(List)
    #Debugging the new Event builder function
    if DEBUG == True:
        NoCoreSys_dNdE = ns.build_Theory_dNdE(unosc_spectra,oscParams)
        print("SHOWING SOME PLOTS OF dNdE's REBINNING")
        #build the dNdE function with systematic fluctuations
        Varied_dNdE = ns.build_Theory_dNdE_wCoreSys(unosc_spectra, oscParams)
        TotEvents = RoughIntegrate(Varied_dNdE.Pos_dNdE,Varied_dNdE.Pos_Energy_Array)
        nuTot = RoughIntegrate(Varied_dNdE.Nu_dNdE,Varied_dNdE.Nu_Energy_Array)
        print("EVENTS IN NEUTRINO ENERGY SPECTRUM: " + str(nuTot))
        print("TOTEVENTS BEFORE SMEAR: " + str(TotEvents))
        splt.dNdEPlot_line_TNU(Varied_dNdE.Nu_Energy_Array, \
            Varied_dNdE.Nu_dNdE, oscParams[1], oscParams[0])
        if "DETECTOR_RESP" in c.SYSTEMATICS:
            Varied_dNdE.setResolution(c.RESOLUTION)
            Varied_dNdE.smear()
        print("TOTEVENTS AFTER SMEAR: " + str(TotEvents))
        splt.dNdEPlot_line(Varied_dNdE.Pos_Energy_Array,Varied_dNdE.Pos_dNdE, oscParams[1],\
                oscParams[0])
        #form histograms in 3-7 MeV region
        dNdEHistperf = h.dNdE_Hist(NoCoreSys_dNdE,c.NUMBINS,c.HMIN,c.HMAX)
        
        perfect_numeventsinhist = np.sum(dNdEHistperf.bin_values)
        stat_eventsinhist = int(pd.RandShoot(perfect_numeventsinhist, \
                np.sqrt(perfect_numeventsinhist), 1))
        dNdEHistvar = h.dNdE_Hist(Varied_dNdE,c.NUMBINS,c.HMIN,c.HMAX)
        dNdEHistvar = pd.playDarts_h(stat_eventsinhist,dNdEHistvar)
        splt.dNdEPlot_pts(dNdEHistperf.bin_centers,dNdEHistperf.bin_values, \
                dNdEHistperf.bin_lefts,dNdEHistperf.bin_rights, \
                oscParams[1], oscParams[0])
        #plots your histogram with smearing, core systematics, statistics
        splt.dNdEPlot_pts(dNdEHistvar.bin_centers,dNdEHistvar.bin_values, \
                dNdEHistvar.bin_lefts,dNdEHistvar.bin_rights, \
                oscParams[1], oscParams[0])
        TheoryEventNum = int(pd.RoughIntegrate(Varied_dNdE.Nu_dNdE,Varied_dNdE.Nu_Energy_Array))

        #Statistically fluctuate from theoretical average to build histogram
        events_in_experiment = int(pd.RandShoot(TheoryEventNum, np.sqrt(TheoryEventNum),1))
        print("SHOOTING AN EXPERIMENT WITH STATISTICS INCLUDED NOW")
        nu_energies = pd.playDarts(events_in_experiment,Varied_dNdE.Nu_dNdE,c.NU_ENERGY_ARRAY)
        NuPosConverter = ntp.NuToPosConverter()
        pos_energies = NuPosConverter.ConvertToPositronKE_0ord(nu_energies)
        if "DETECTOR_RESP" in c.SYSTEMATICS:
            pos_energies = NuPosConverter.Smear(pos_energies,c.RESOLUTION)
        Stat_EventHist = h.Event_Hist(pos_energies,c.NUMBINS,c.HMIN,c.HMAX)
        splt.dNdEPlot_pts(Stat_EventHist.bin_centers,Stat_EventHist.bin_values, \
                Stat_EventHist.bin_lefts, Stat_EventHist.bin_rights, \
                oscParams[1], oscParams[0])
        #Calculate the chi-squared test results (fixed dms, vary sst)
        sst_array = np.arange(0.01, 1.00, 0.01)
        chi2_results = cmu.GetChi2dmsFixed(unosc_spectra, oscParams, sst_array)
        cplt.chi2vssst(chi2_results, sst_array,oscParams)


    #Use the unosc_spectra and applied SYSTEMATICS to create
    #statistically varied experiments.  Use the NegML minimization to find
    #the best fit oscillation parameters assuming no systematics or statistic
    #variation.
    num_experiments = 100
    if DMSSEED == True:
        dms_fits, sst_fits, negML_results = cmu.GetNegMLStatSpread_dmsseed(num_experiments, \
                unosc_spectra,oscParams)
    else:
        dms_fits, sst_fits, negML_results = cmu.GetNegMLStatSpread(num_experiments, \
                unosc_spectra,oscParams)
    print(dms_fits)
    print(sst_fits)
    print(negML_results)
    result_dict = {"Params": options.parameters, "ROI":[c.HMIN,c.HMAX], \
            "nbins": c.NUMBINS, "Reactors": options.reactors, \
            "dms": dms_fits, "sst": sst_fits, "negML": negML_results}
    with open(outpath + "/result_" + JNUM + ".json","w") as outfile:
        json.dump(result_dict,outfile,sort_keys=True,indent=4)
    if DEBUG == True:
        cplt.chi2scatter(dms_fits,sst_fits,oscParams)
