#:ython script for building the expected number of events per day as a function
#of energy at SNO+.

import sys,time

import lib.GetNRCDailyInfo as nrc
import lib.rdbbuild as rb
import lib.rdbparse as rp
import lib.NuSpectrum as ns
import lib.chi2ML_Utils as cmu
import lib.NuToPos as ntp

import tools.graph.SpectraPlots as splt
import tools.graph.OscPlot as oplt
import tools.graph.ChiSquaredPlots as cplt

import lib.Histogram as h
import lib.playDarts as pd

import lib.config.config as c
import lib.ArgParser as p

import numpy as np

import json
import os.path

#Controls location to save output fit results
basepath = os.path.dirname(__file__)
outpath = os.path.abspath(os.path.join(basepath, "output"))

DEBUG = p.debug
#Set which parameters to call when building neutrino spectrums
oscParams = p.oscParams
#ns.setDebug(p.debug)
JNUM = p.jobnum
DMSSEED = p.seed

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
        p.showReactors()
    List = p.setListType(List_Dictionary)
    #if DEBUG == True:
    #    getBruceSpectra()

    #construct unoscillated spectra of all cores in List
    #CORE SYSTEMATICS NOT ADDED HERE YET
    unosc_spectra = build_unoscSpectra(List)
    
    if DEBUG == True:
        NoCoreSys_dNdE = ns.build_Theory_dNdE(unosc_spectra,oscParams)
        print("SHOWING SOME PLOTS OF dNdE's REBINNING")
        #build the dNdE function with systematic fluctuations
        Varied_dNdE = ns.build_Theory_dNdE_wCoreSys(unosc_spectra, oscParams)
        TotEvents = pd.RoughIntegrate(Varied_dNdE.Pos_dNdE,Varied_dNdE.Pos_Energy_Array)
        nuTot = pd.RoughIntegrate(Varied_dNdE.Nu_dNdE,Varied_dNdE.Nu_Energy_Array)
        print("EVENTS IN NEUTRINO ENERGY SPECTRUM: " + str(nuTot))
        print("TOTEVENTS BEFORE SMEAR: " + str(TotEvents))
        splt.dNdEPlot_line_TNU(Varied_dNdE.Nu_Energy_Array, \
            Varied_dNdE.Nu_dNdE, oscParams[1], oscParams[0],PID='nu')
        if "DETECTOR_RESP" in c.SYSTEMATICS:
            Varied_dNdE.setResolution(c.RESOLUTION)
            Varied_dNdE.smear()
        print("TOTEVENTS AFTER SMEAR: " + str(TotEvents))
        splt.dNdEPlot_line(Varied_dNdE.Pos_Energy_Array,Varied_dNdE.Pos_dNdE, oscParams[1],\
                oscParams[0],PID='pos')
        #form histograms in 3-7 MeV region
        dNdEHistperf = h.dNdE_Hist(NoCoreSys_dNdE,c.NUMBINS,c.HMIN,c.HMAX)
        
        perfect_numeventsinhist = np.sum(dNdEHistperf.bin_values)
        stat_eventsinhist = int(pd.RandShoot(perfect_numeventsinhist, \
                np.sqrt(perfect_numeventsinhist), 1))
        dNdEHistvar = h.dNdE_Hist(Varied_dNdE,c.NUMBINS,c.HMIN,c.HMAX)
        dNdEHistvar = pd.playDarts_h(stat_eventsinhist,dNdEHistvar)
        print("SHOWING THEORETICAL ANTINEUTRINO ENERGY SPECTRUM NOW")
        splt.dNdEPlot_pts(dNdEHistperf.bin_centers,dNdEHistperf.bin_values, \
                dNdEHistperf.bin_lefts,dNdEHistperf.bin_rights, \
                oscParams[1], oscParams[0],PID='nu')
        print("SHOWING NEUTRINO ENERGY HISTOGRAM WITH STATISTICAL UNCERTAINTIES NOW")
        splt.dNdEPlot_pts(dNdEHistvar.bin_centers,dNdEHistvar.bin_values, \
                dNdEHistvar.bin_lefts,dNdEHistvar.bin_rights, \
                oscParams[1], oscParams[0],PID='nu')
        TheoryEventNum = int(pd.RoughIntegrate(Varied_dNdE.Nu_dNdE,Varied_dNdE.Nu_Energy_Array))

        #Statistically fluctuate from theoretical average to build histogram
        events_in_experiment = int(pd.RandShoot(TheoryEventNum, np.sqrt(TheoryEventNum),1))
        print("CONVERTING TO POSITRON ENERGY AND ADDING ENERGY SMEARING IF DEFINED")
        nu_energies = pd.playDarts(events_in_experiment,Varied_dNdE.Nu_dNdE,c.NU_ENERGY_ARRAY)
        NuPosConverter = ntp.NuToPosConverter()
        pos_energies = NuPosConverter.ConvertToPositronKE_0ord(nu_energies)
        if "DETECTOR_RESP" in c.SYSTEMATICS:
            pos_energies = NuPosConverter.Smear(pos_energies,c.RESOLUTION)
        Stat_EventHist = h.Event_Hist(pos_energies,c.NUMBINS,c.HMIN,c.HMAX)
        splt.dNdEPlot_pts(Stat_EventHist.bin_centers,Stat_EventHist.bin_values, \
                Stat_EventHist.bin_lefts, Stat_EventHist.bin_rights, \
                oscParams[1], oscParams[0],PID='pos')
        #Calculate the chi-squared test results (fixed dms, vary sst)
        print("SHOWING CHI-SQUARED DISTRIBUTION FOR FIXED DMS") 
        sst_array = np.arange(0.01, 1.00, 0.01)
        chi2_results = cmu.GetChi2dmsFixed(unosc_spectra, oscParams, sst_array)
        cplt.chi2vssst(chi2_results, sst_array,oscParams)


    #Use the unosc_spectra and applied SYSTEMATICS to create
    #statistically varied experiments.  Use the NegML minimization to find
    #the best fit oscillation parameters assuming no systematics or statistic
    #variation.
    num_experiments = 1000
    if DMSSEED == True:
        dms_fits, sst_fits, negML_results = cmu.GetNegMLStatSpread_dmsseed(num_experiments, \
                unosc_spectra,oscParams)
    else:
        dms_fits, sst_fits, negML_results = cmu.GetNegMLStatSpread(num_experiments, \
                unosc_spectra,oscParams)
    print(dms_fits)
    print(sst_fits)
    print(negML_results)
    result_dict = {"Params": p.parameters, "ROI":[c.HMIN,c.HMAX], \
            "nbins": c.NUMBINS, "Reactors": p.reactors, \
            "dms": dms_fits, "sst": sst_fits, "negML": negML_results}
    with open(outpath + "/result_" + JNUM + ".json","w") as outfile:
        json.dump(result_dict,outfile,sort_keys=True,indent=4)
    if DEBUG == True:
        cplt.chi2scatter(result_dict)
