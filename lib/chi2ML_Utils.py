
import numpy as np
import scipy.optimize as spo
import scipy.misc as sm

import config.config as c

import iminuit as im
import NuSpectrum as ns
import NuToPos as ntp
import Histogram as h
import playDarts as pd


#builds the chi-squared between the expected SNO+ spectrum with
#systematics included and an oscillated spectrum with no systematics
#that is oscillated with a (sine-squared theta12) and b
#(Delta m-squared). In this case, an unoscillated spectra is
#passed in to be oscillated with a,b.
#Check your bin sizes; don't want to feed in an un-scaled true spectrum

#Function returns a histogram with binned event energies resulting from the
#expected neutrino flux at SNO+.  Events are generated by sampling neutrino
#energies from the expected neutrino dNdE, converting to prompt energy, then
#smearing with the resolution defined in config.py
def getExpt_wstats(oscParams, All_unosc_spectra):
    VarieddNdE = ns.build_Theory_dNdE_wCoreSys(All_unosc_spectra, oscParams)
    if "DETECTOR_RESP" in c.SYSTEMATICS:
        VarieddNdE.setResolution(c.RESOLUTION)
        VarieddNdE.smear()
    #DO A ROUGH INTEGRATE TO GET EVENTS IN EXPERIMENT TIME
    TheoryEventNum = int(pd.RoughIntegrate(VarieddNdE.Nu_dNdE,VarieddNdE.Nu_Energy_Array))
    #Statistically fluctuate from theoretical average
    events_in_experiment = int(pd.RandShoot(TheoryEventNum, np.sqrt(TheoryEventNum),1))
    nu_energies = pd.playDarts(events_in_experiment,VarieddNdE.Nu_dNdE,c.NU_ENERGY_ARRAY)
    NuPosConverter = ntp.NuToPosConverter()
    pos_energies = NuPosConverter.ConvertToPositronKE_0ord(nu_energies)
    if "DETECTOR_RESP" in c.SYSTEMATICS:
        pos_energies = NuPosConverter.Smear(pos_energies,c.RESOLUTION)
    Stat_EventHist = h.Event_Hist(pos_energies,c.NUMBINS,c.HMIN,c.HMAX)
    return Stat_EventHist

## ------------ BEGIN FUNCTIONS/CLASSES FOR CHI-SQUARED TESTS ---------- ##
## --------------------------------------------------------------------- ##

def GetChi2dmsFixed(unosc_spectra, oscParams, sst_array):
    '''
    Calculates an array of chi-squared results for a spectra with parameters
    oscParams.  The seed for the fit is fixed delta-m squared, and each sst
    value in the sst_array.
    '''
    EventHist_wstats = getExpt_wstats(oscParams, unosc_spectra)
    chi2 = ExperimentChi2(unosc_spectra,c.SYSTEMATICS, \
            c.RESOLUTION, EventHist_wstats)
    chi2_results = []
    for sst in sst_array:
        chi2_results.append(chi2(sst, oscParams[0]))
    return chi2_results

def Getchi2StatSpread(num_experiments, unosc_spectra,oscParams):
    '''
    Function returns three arrays that have the best fit oscillation parameters
    And chi-squared results for the best fit of a statistically fluctuated
    SNO+ Antineutrino spectrum against a non-fluctuated spectrum with the
    input oscillation parameters.
    '''
    dms_fits=[]
    sst_fits=[]
    chi2_results = []
    experiment = 0
    while experiment < num_experiments:
        EventHist_wstats = getExpt_wstats(oscParams,unosc_spectra)
        print("CHISQUARE BEING CALCULATED NOW FOR A RANDOM EXPERIMENT...")
        chi2 = ExperimentChi2(unosc_spectra,c.SYSTEMATICS, \
                c.RESOLUTION, EventHist_wstats)
        im.describe(chi2)
        m = im.Minuit(chi2, limit_dms = (1e-07, 1e-03), limit_sst=(0.0,1.0), sst = (oscParams[1]), dms = oscParams[0])
        m.migrad()
        dms_fits.append(m.values['dms'])
        sst_fits.append(m.values['sst'])
        chi2_results.append(m.fval)
        experiment += 1
    return dms_fits, sst_fits, chi2_results

## ----------- END OF FUNCTIONS USED IN MAIN FOR CHI-SQUARED TESTS ---------- ##
## --------------------------------------------------------------------- ##


## ----- BEGIN FUNCTIONS/CLASSES FOR NEGATIVE MAX LIKELIHOOD TESTS ----- ##
## --------------------------------------------------------------------- ##
def GetNegMLStatSpread_dmsseed(num_experiments, unosc_spectra,oscParams):
    '''
    Function returns three arrays that have the best fit oscillation parameters
    And minimized neg. ML results for best fitting a statistically fluctuated
    SNO+ Antineutrino spectrum against a non-fluctuated spectrum with the
    input oscillation parameters.
    '''
    dms_fits=[]
    sst_fits=[]
    negML_results = []
    experiment = 0
    while experiment < num_experiments:
        EventHist_wstats = getExpt_wstats(oscParams,unosc_spectra)
        print("CHISQUARE BEING CALCULATED NOW FOR A RANDOM EXPERIMENT...")
        negML = ExperimentNegML(unosc_spectra,c.SYSTEMATICS, \
                c.RESOLUTION, EventHist_wstats)
        im.describe(negML)
        #First, get delta-m squared's profile at the seed sst.  This will be our
        #Delta-m squared seed.
        mseed = im.Minuit(negML, limit_dms = (1e-07, 1e-03), limit_sst=(0.0,1.0), sst = (oscParams[1]), dms = (oscParams[0]), fix_sst=True)
        dmspoint,negMLval = mseed.profile(dms,bins=100,bound=(1E-05,1E-04))
        dmsseed = negMLval.index(np.min(negMLval))
        print("DMS SEED IS: " + str(dmsseed))
        #Get the global minimum in range of 1E-05 to 1E-04
        m = im.Minuit(negML, limit_dms = (1e-07, 1e-03), limit_sst=(0.0,1.0), sst = (oscParams[1]), dms = dmsseed)
        m.migrad()
        print("MINIMIZATION OUTPUT: " + str(m.values))
        print("MINIMUM VALUE: " + str(m.fval))
        dms_fits.append(m.values['dms'])
        sst_fits.append(m.values['sst'])
        negML_results.append(m.fval)
        experiment += 1
    return dms_fits, sst_fits, negML_results

def GetNegMLStatSpread(num_experiments, unosc_spectra,oscParams):
    '''
    Function returns three arrays that have the best fit oscillation parameters
    And minimized neg. ML results for best fitting a statistically fluctuated
    SNO+ Antineutrino spectrum against a non-fluctuated spectrum with the
    input oscillation parameters.
    '''
    dms_fits=[]
    sst_fits=[]
    negML_results = []
    experiment = 0
    while experiment < num_experiments:
        EventHist_wstats = getExpt_wstats(oscParams,unosc_spectra)
        print("CHISQUARE BEING CALCULATED NOW FOR A RANDOM EXPERIMENT...")
        negML = ExperimentNegML(unosc_spectra,c.SYSTEMATICS, \
                c.RESOLUTION, EventHist_wstats)
        im.describe(negML)
        m = im.Minuit(negML, limit_dms = (1e-07, 1e-03), limit_sst=(0.0,1.0), sst = (oscParams[1]), dms = oscParams[0])
        m.migrad()
        print("MINIMIZATION OUTPUT: " + str(m.values))
        print("MINIMUM VALUE: " + str(m.fval))
        dms_fits.append(m.values['dms'])
        sst_fits.append(m.values['sst'])
        negML_results.append(m.fval)
        experiment += 1
    return dms_fits, sst_fits, negML_results

# ------------------ END NEGATIVE MAX LIKELIHOOD FUNCTIONS USED IN MAIN -----#
# ---------------------------------------------------------------------------#

# ------------------- BASE CLASSES ------------------------------------------#
# ---------------------------------------------------------------------------#


#INPUTS: oscillation parameter array [Delta m-squared, sst12], Unoscilated
#spectra used to generate the event histograms, Event histogram with statistical
#fluctuation, Event histogram without statistical fluctuation
class ExperimentChi2(object):
    def __init__(self, unosc_spectra, Systematics,Res,Stat_EventHist):
        self.Resolution = Res
        self.Systematics = Systematics
        self.unosc_spectra = unosc_spectra
        self.Stat_EventHist = Stat_EventHist
        self.numbins = self.Stat_EventHist.numbins
        self.hmin = Stat_EventHist.hmin
        self.hmax = Stat_EventHist.hmax

    def __call__(self, sst, dms):
        print("OSC PARAMS FED IN: " + str([dms,sst]))
        PerfectdNdE = ns.build_Theory_dNdE(self.unosc_spectra, [dms,sst])
        if "DETECTOR_RESP" in self.Systematics:
            PerfectdNdE.setResolution(self.Resolution)
            PerfectdNdE.smear()
       #Build your histogram for the input oscillation parameters
        FitHist = h.dNdE_Hist(PerfectdNdE, self.numbins, self.hmin, self.hmax)
        chisquare = np.sum(((FitHist.bin_values - 
            self.Stat_EventHist.bin_values)**2)/ FitHist.bin_values)
        #self.NoStat_EventHist.bin_values)
        #use uncertainty of a bin in the "theoretically expected event rate"
        #(i.e. the Spectrum for the input oscillation parameters) for denom
        print("CHISQ RESULT: " + str(chisquare))
        return chisquare


class ExperimentNegML(object):
    def __init__(self, unosc_spectra,Systematics,Res,Stat_EventHist):
        self.Resolution = Res
        self.Systematics = Systematics
        self.unosc_spectra = unosc_spectra
        self.Stat_EventHist = Stat_EventHist
        self.numbins = self.Stat_EventHist.numbins
        self.hmin = Stat_EventHist.hmin
        self.hmax = Stat_EventHist.hmax

    def __call__(self, sst, dms):
        PerfectdNdE = ns.build_Theory_dNdE(self.unosc_spectra, [dms,sst])
        if "DETECTOR_RESP" in self.Systematics:
            PerfectdNdE.setResolution(self.Resolution)
            PerfectdNdE.smear()
        #Build your histogram for the input oscillation parameters
        FitHist = h.dNdE_Hist(PerfectdNdE, self.numbins, self.hmin, self.hmax)
        x = self.Stat_EventHist.bin_values
        if np.max(x) > 170:
            print("WARNING: BIN VALUE GREATER THAN FACTORIAL FUNCTION" + \
                    "CAN DO IN SCIPY.  PERHAPS DO A CHI SQUARED FIT?")
        mu = FitHist.bin_values
        negML = -np.sum((x*np.log(mu) - mu) - np.log(sm.factorial(x)))
        #self.NoStat_EventHist.bin_values)
        #use uncertainty of a bin in the "theoretically expected event rate"
        #(i.e. the Spectrum for the input oscillation parameters) for denom
        return negML


