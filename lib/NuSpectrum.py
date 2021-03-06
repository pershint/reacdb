import sys
import ctypes as ct
import os.path
import config.config as c

import NuToPos as ntp
import rdbparse as rp
import playDarts as pd
import GetNRCDailyInfo as nrc
import distance as sd
import dailyparse as dp
import numpy as np

import ArgParser as p
import PhysicsConstants as pc

basepath = os.path.dirname(__file__)
clibpath = os.path.abspath(os.path.join(basepath,"ctypes_libs"))

DEBUG = p.debug #False


#Takes in an array of UnoscSpecGen classes (assume all have same energy points on y-axis)
#And returns the dNdE function that results from them (neutrino energy)
def build_Theory_dNdE(unosc_spectra,oscParams):
    energy_array = unosc_spectra[0].energy_array
    Total_PerfectSpectra = np.zeros(len(energy_array))
    for ReacSpectra in unosc_spectra:
        PerfectOscSpec = Osc_CoreSysGen(ReacSpectra, oscParams,[None])
        Total_PerfectSpectra += PerfectOscSpec.Summed_Spectra
    return dNdE(energy_array,Total_PerfectSpectra)

def build_Theory_dNdE_wCoreSys(unosc_spectra,oscParams):
    energy_array = unosc_spectra[0].energy_array
    Total_VariedSpectra = np.zeros(len(energy_array))
    for ReacSpectra in unosc_spectra:
        VariedOscSpec = Osc_CoreSysGen(ReacSpectra,oscParams,c.SYSTEMATICS)
        Total_VariedSpectra += VariedOscSpec.Summed_Spectra
    return dNdE(energy_array, Total_VariedSpectra)


#Class takes in four RATDB type Isotope Info entries, one
#Spectrum entry (has the isotope compositions), and an energy to evaulate at.
#The class evaluates Isotope's associated small lambda, combines with the isotope
#fractions to make the reactor's Lambda function
#Isotopes should be fed as follows: iso_array[0] = 235U RATDB entry, iso_array[1]=238U,
#iso_array[2]=239Pu, iso_array[3]=241Pu
class Lambda(object):
    def __init__(self,iso_array,isofracs, E):
        self.E = E

        self.iso_arr = iso_array
        self.sl_array = []
        for iso in self.iso_arr:
            self.sl_array.append(self.smallLambda(iso))
        self.isofracs = isofracs

        self.value = 'none'
        self.defineBigLambda()

    def smallLambda(self,iso):
        poly_terms = []
        for i in np.arange(0,len(iso.poly_coeff)):
            term = self.polyTerm(iso.poly_coeff[i], self.E, i)
            poly_terms.append(term)
        exp_term = np.sum(poly_terms,axis=0)
        sl = np.exp(exp_term)
        return sl

    def defineBigLambda(self):
        bl_terms = []
        for i,sl in enumerate(self.sl_array):
            bl_term = self.isofracs[i] * sl
            bl_terms.append(bl_term)
        bl = np.sum(bl_terms,axis=0)
        self.value = bl

    def polyTerm(self, a, e, c):
        return a * (e**c)

#Class takes in permanent details for a reactor plant (ReacDetails RATDB entry)
#And the reactor's status (ReacStatus RATDB entry), and the RATDB entries of 
#isotopes to use, and the energys to calculate the spectrum at
#and builds an array of spectra arrays (self.Unosc_Spectra) evaluated at the
#given energies.  There is one array for each core of the plant.
class UnoscSpecGen(object):
    def __init__(self,ReacDetails,ReacStatus,iso_array,energy_array,Uptime):
        self.energy_array = energy_array
        self.ReacDetails = ReacDetails
        self.ReacStatus = ReacStatus
        self.iso_array = iso_array
        self.Uptime = Uptime

        self.__core_check()
        self.no_cores = self.ReacStatus.no_cores

        self.Core_Distances = []
        self.__CoreDistancesFromSNO()
        self.Unosc_Spectra = []
        self.__calcSpectra()

        #Now, incorporate Power information from daily_update database
        self.CoreSpecs = coreGen(ReacStatus,self.Unosc_Spectra,self.Uptime)
        self.Unosc_Spectra = self.CoreSpecs.Unosc_Spectra_wP


    def core_check(self):
        if self.ReacDetails.no_cores != self.ReacStatus.no_cores:
            raise UserWarning("WARNING: Number of cores in REACTOR" + \
                    "RATDB entry does not match REACTOR_STATUS entry. Using" + \
                    "number of cores put in REACTOR STATUS entry.")

    def CoreDistancesFromSNO(self):
        self.Core_Distances = [] #Refresh array before adding core distances
        for i in np.arange(0,self.no_cores):
            longitude = self.ReacDetails.core_longitudes[i]
            latitude = self.ReacDetails.core_latitudes[i]
            altitude = self.ReacDetails.core_altitudes[i]
            coreDistance = sd.distance(c.LONGLATALT,[longitude,latitude,altitude])
            self.Core_Distances.append(coreDistance)
        if DEBUG == True:
            print("For core " + self.ReacStatus.index + "...")
            print("Core distances calculated! In km... " + str(self.Core_Distances))

    def calcSpectra(self):
        self.Unosc_Spectra = []  #Refresh array before adding spectrums
        for i in np.arange(0,self.no_cores):
            coreType = self.ReacStatus.core_types[i]
            coreDistance = self.Core_Distances[i]
            isotope_composition = rp.Reactor_Spectrum(coreType).param_composition
            #loop over energies, calculate spectra's values
            LambdaFunction = Lambda(self.iso_array, isotope_composition,self.energy_array).value
            coreLambda = LambdaFunction / self.spectrumDenom(isotope_composition)
            coreSpectrum = ( coreLambda / \
                    (4.*np.pi * (coreDistance**2)))
            self.Unosc_Spectra.append(np.array(coreSpectrum))

    def spectrumDenom(self,isocomp):
        denominator = 0.0
        for i,iso in enumerate(self.iso_array):
            denominator += isocomp[i] * self.iso_array[i].Eperfission
        return denominator
    #Make private copies of the public methods
    __core_check = core_check
    __calcSpectra = calcSpectra
    __CoreDistancesFromSNO = CoreDistancesFromSNO


#Class takes in the unoscillated spectra associated with a reactor plant.
#generates each core's operation details based on the number of days ran
#in an experiment and the load factor of a reactor for each day. Builds the
#unoscillated spectra with power and load factor values included.
class coreGen(object):
    def __init__(self,ReacStatus,Unosc_Spectra,Uptime):
        self.Uptime = Uptime
        self.ReacName = ReacStatus.index
        self.core_powers = ReacStatus.core_powers #Core powers as in RAT
        self.Unosc_Spectra = Unosc_Spectra

        #Number of days of data collected from the daily_updates DB
        self.numdays_ofdata = 0

        #Sum of licensed MWts grabbed for each day and sum of load factors
        self.TotMWts = []
        self.TotLFs = []

        #These are calculated as the total divided by the numdays_ofdata
        self.AvgLFs = []
        self.AvgMWts = []

        #Spectra with power corrections
        self.Unosc_Spectra_wP = []

        #if self.ReacDetails.index is in c.CAList, use RATDB core powers with no
        #statistical fluctuations
        if self.ReacName not in c.USList:
            self.__Power_Perfect()
        else:
            self.__Power_AvgAvailable()

    def Power_Perfect(self):
        '''
        Assumes all reactors run at 2015 averaged thermal power, no statistical
        fluctuations.  Ends up scaling each reactor core's spectra by the
        approproate thermal power, time, and MeV conversion factor.
        '''
        for i,coreSpectrum in enumerate(self.Unosc_Spectra):
            coreSpectrum = coreSpectrum * self.Uptime * pc.MWHTOMEV * \
                    self.core_powers[i] 
            self.Unosc_Spectra_wP.append(coreSpectrum)

    def Power_AvgAvailable(self):
        '''
        Grabs all of the load factors and licensed MWts available for this reactors
        cores from the daily database, averages the licensed MWts and load
        factors, and uses these with the hard-coded runtime to generate each core
        power.
        '''
        self.numdays_ofdata, AllReacEntries = dp.getAllEntriesInDailyUpdates(self.ReacName)
        allLicensedMWts = []
        allLoadFactors = []
        for entry in AllReacEntries:
            allLicensedMWts.append(np.array(entry["lic_core_powers"]))
            allLoadFactors.append(np.array(entry["capacities"]))
        #Now, average over all values for each core
        self.TotMWts = np.sum(allLicensedMWts, axis=0)
        self.TotLFs = np.sum(allLoadFactors, axis=0)
        self.AvgMWts = self.TotMWts/self.numdays_ofdata
        self.AvgLFs = (self.TotLFs/self.numdays_ofdata) #Shown in DB as percentage 

        #now, use the average values to rescale the spectrums
        
        for i,coreSpectrum in enumerate(self.Unosc_Spectra):
            coreSpectrum = coreSpectrum * self.Uptime * pc.MWHTOMEV * \
                    self.AvgMWts[i] * (self.AvgLFs[i] / 100.0)
            self.Unosc_Spectra_wP.append(coreSpectrum)

    __Power_Perfect = Power_Perfect
    __Power_AvgAvailable = Power_AvgAvailable


#Class takes an UnoscSpecGen class (contains spectrums for each core of one reactor)
#and outputs the the oscillated Spectrums.  oscParams should have two entries: 
#[delta m-squared, sin^2(theta12)]
class Osc_CoreSysGen(object):
    def __init__(self, UnoscSpecGen, oscParams,Systematics):
        self.Systematics = Systematics
        self.Unosc_Spectra = UnoscSpecGen.Unosc_Spectra
        self.ReacDetails = UnoscSpecGen.ReacDetails
        self.ReacStatus = UnoscSpecGen.ReacStatus
        self.energy_array = UnoscSpecGen.energy_array
        self.Core_Distances = UnoscSpecGen.Core_Distances 

        #define your variable oscillation paramaters;
        self.SINSQT12 = oscParams[1]
        self.DELTAMSQ21 = oscParams[0]
        #calculate needed fixed oscillation parameters
        self.SINSQTWO12 = self.calcSINSQTWO(self.SINSQT12)
        self.COSSQT12 = self.calcCOSSQ(self.SINSQT12)

        self.AvgLFs = UnoscSpecGen.CoreSpecs.AvgLFs
        #Adds systematic fluctuations to each core
        self.__addCoreSystematics()

        #Oscillate each core spectra, then sum them
        self.Osc_Spectra = []
        self.__oscillateSpectra()

        self.Summed_Spectra = []
        self.__sumSpectra()


    def addCoreSystematics(self):
        '''
        If called, the spectra from each core is scaled according to the
        average load factor.  Basically, sample from a gaussian of 
        mu=LF and sigma = 25% for now.  Can make a function of LF later.
        '''
        if ("USSYS" in self.Systematics) and \
                (self.ReacDetails.index in c.USList):
            sysSigmas = c.US_LF_VAR * np.ones(len(self.AvgLFs))
            #Get the fluctuation from each core's avg LF, in percentage
            sysFlucs = pd.RandShoot(self.AvgLFs,sysSigmas, \
                    len(self.AvgLFs)) - self.AvgLFs
            Unosc_Spectra_wSys = []
            #For each spectrum, vary by the fluctuation calculated in sysFlucs
            for i,coreSpectrum in enumerate(self.Unosc_Spectra):
                coreSpectrum = coreSpectrum * (1 + (sysFlucs[i]/100.0))
                Unosc_Spectra_wSys.append(coreSpectrum)
            self.Unosc_Spectra = Unosc_Spectra_wSys
        #Vary each Canadian reactor core's flux around it's thermal power
        elif ("CASYS" in self.Systematics) and \
                (self.ReacDetails.index in c.CAList):
            numcores = len(self.ReacStatus.core_powers)
            #Thermal MWts for CA reactors already have LFs factored in
            #ReacStatus entries
            coreAvgs = 100.0 * np.ones(numcores)
            coreSigmas = (c.CA_LF_VAR) * np.ones(numcores)
            core_SysVar = pd.RandShoot(coreAvgs,coreSigmas, numcores)
            print(core_SysVar)
            Unosc_Spectra_wSys = []
            #For each spectrum, vary by the fluctuation calculated in sysFlucs
            for i,coreSpectrum in enumerate(self.Unosc_Spectra):
                coreSpectrum = coreSpectrum * (core_SysVar[i] / 100.0)
                Unosc_Spectra_wSys.append(coreSpectrum)
            self.Unosc_Spectra = Unosc_Spectra_wSys

    def oscillateSpectra(self):
        self.Osc_Spectra = [] #Refresh array before adding spectrums
        for i,spectrum in enumerate(self.Unosc_Spectra):
             self.Osc_Spectra.append(np.product([spectrum,self.Pee(self.energy_array, \
                     self.Core_Distances[i])],axis=0))

    def calcSINSQTWO(self, sst12):
        result = 4. * sst12 * (1. - sst12)
        return result

    def calcCOSSQ(self, sst12):
        result = 1. - sst12
        return result

    def Pee(self,E,L):
        #Takes in an array of energies and one length and returns an array
        #of the Pee spectrum.
        #L must be given in kilometers, energy in MeV
        #USING THE EQN. FROM SVOBODA/LEARNED
        term1 = pc.COS4THT13*self.SINSQTWO12*(np.sin(1E-12 * \
                self.DELTAMSQ21 * L /(4 * E * pc.hbarc))**2)
        result = (1. - term1) # + term2 + term3)
        #OR, USING 2-PARAMETER APPROXIMATION USED BY KAMLAND
#        result = 1 - (self.SINSQTWO12 * np.sin((1.27 * \
#                DELTAMSQ21*L)/(E/1000))**2)

        return result

    def sumSpectra(self):
        summed_spectra = np.sum(self.Osc_Spectra, axis=0)
        self.Summed_Spectra = summed_spectra


    #Make private copies of the public methods; important to let
    #subclasses override methods without breaking intraclass method calls.
    __sumSpectra = sumSpectra
    __oscillateSpectra = oscillateSpectra
    __addCoreSystematics = addCoreSystematics


#Class takes in a reactor spectrum array (oscillated or unoscillated) and the
#relative x-axis array (Energy_Array in the class) and calculates the
#dNdE function for the spectrum. Total Runtime and Thermal power associated
#with the spectrum's core must already be factored into the spectrum.
class dNdE(object):
    def __init__(self,Energy_Array,Spectrum):
        self.Nu_Energy_Array = Energy_Array
        self.Spectrum = Spectrum

        self.Array_Check()

        self.resolution = None

        self.Nu_dNdE = []
        self.evalNudNdE()

        self.Pos_Energy_Array = self.getPositronEnergyArr()
        self.Pos_dNdE = self.NuToPos_dNdE(0)


    def getPositronEnergyArr(self):
        Converter = ntp.NuToPosConverter()
        pos_energies = Converter.ConvertToPositronKE_0ord(self.Nu_Energy_Array)
        return pos_energies

    #Makes room for a jacobian factor; isn't one for 0order, just multiplies by 1
    def NuToPos_dNdE(self,order):
        Converter = ntp.NuToPosConverter()
        if order == 0:
            Pos_dNdE = self.Nu_dNdE
        else:
            print("order 1 not implemented!")
        return Pos_dNdE

    def evalNudNdE(self):
        self.Nu_dNdE = [] #Remove any previous values in dNdE
        self.Nu_dNdE = c.EFFICIENCY * c.NP * \
            self.XC_Vogel_0ord(self.Nu_Energy_Array) * self.Spectrum

    def Array_Check(self):
        if len(self.Nu_Energy_Array) != len(self.Spectrum):
            raise UserWarning("WARNING: Energy array length does not equal" + \
                    "length of spectrum given.  Check your entries.")

    #takes in an array of energies and returns an array of cross-section values
    #as a function of energy. Source: A. Strumia and F. Vissani, Physics Letters
    #B 564, 42
    def XC(self, E):
        Ee = (E - pc.DELTA)
        pe = np.sqrt((Ee**2) - (pc.Me**2))
        poly = E**(pc.A1 + (pc.A2 * np.log(E)) + (pc.A3 * ((np.log(E))**3)))
        return (1E-53) * pe * Ee * poly #1E-53, instead of -43, for km^2 units

    #takes in an array of energies and returns the scattering angle-averaged
    #cross-section for neutrino IBD interactions.
    def XC_Vogel_0ord(self, E):
        Ee0 = (E - pc.DELTA)
        pe0 = np.sqrt((Ee0**2 - pc.Me**2))
#        f,g=1,1.26  #vector axial coupling constants
#        gFERM = 1.16639E-11  #in MeV ^ -2
#        cosTC = 0.974
#        RCinner = 0.024  #inner radiative correction
#        sig0 = (gFERM**2) * (cosTC**2) * (1 + RCinner) / np.pi
#        sigtot_0th = sig0 * (f**2 + 3*(g**2)) * pe0 * Ee0 * 1E-10 #cm^2->km^2
        sigtot_0th = 0.0952 * pe0 * Ee0 * 1E-52
        return sigtot_0th


    def setResolution(self, res):
        '''
        Takes in a detector resolution percentage.  For example, KamLAND is
        7.5%/sqrt(E).  Input would be res = 0.075
        '''
        self.resolution = res

    def smear(self):
        '''
        Smears the current dNdE by the defined detector resolution.
        NOTE: Smearing only valid when dNdE is now as a function of
        Positron energy.
        '''
        if self.resolution is None:
            print("Define your resolution first!  Exiting...")
            sys.exit(0)
        numpoints = len(self.Pos_dNdE)
        #call library you're going to use, and get the function from it
        libns = ct.CDLL(os.path.join(clibpath,'libNuSpectrum.so'))
        specsmearer= libns.convolveWER
    
        #Define the ctypes you will be feeding into the function
        pdub = ct.POINTER(ct.c_double)
        cint = ct.c_int
        cdub = ct.c_double
        specsmearer.argtypes = [pdub, pdub, cint, cdub]
        specsmearer.restype = pdub
    
        #cast inputs as numpy arrays (just in case they were a list)
        spec = np.array(self.Pos_dNdE)
        e_arr = np.array(self.Pos_Energy_Array)

        #use the np.array.ctypes function call to cast data as needed for ctypes
        spec_in = spec.ctypes.data_as(pdub)
        e_arr_in = e_arr.ctypes.data_as(pdub)
    
        #Allocate space for the function's output to be stored in
        indata = (ct.c_double * numpoints)()
    
        #actually run the function
        indata = specsmearer(spec_in,e_arr_in,numpoints,self.resolution)
        #go back to a python-usable numpy array
        smearedspec = np.array(np.fromiter(indata, dtype=np.float64, count=numpoints))
        libns.freeMalloc(indata)

        self.Pos_dNdE = smearedspec
        return

