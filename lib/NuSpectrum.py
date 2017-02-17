#g!

import rdbparse as rp
import GetNRCDailyInfo as nrc
import SNOdist as sd
import dailyparse as dp
import numpy as np

DEBUG = False
ADD_SYSTEMATICS = False

#FIXME: Is hardcoded here and in main.py; would like to isolate to main
DATE = '11/20/2016'

RUNTIME = 8760*5   #One year in hours
EFFICIENCY = 1  #Assume 100% signal detection efficiency

MWHTOMEV = 2.247E22 #One MW*h equals this many MeV
NP = 1E32   #Need to approximate SNO+'s number of proton targets

LF_VAR = 10 #Variance in all load factors

hbarc = 1.9733E-16 #in MeV * km
MWHTOMEV = 2.247E22 #One MW*h equals this many MeV
NP = 1E32   #Need to approximate SNO+'s number of proton targets


SINSQT13 = 0.0219 
SINSQTWO13 = 0.0851 #calculated from SINSQT13
COS4THT13 = 0.9570  #calculated from SINSQT13
#Approximate DELTAMSQ31 = DELTAMSQ32 for now
DELTAMSQ31 = 2.5E-3
DELTAMSQ32 = 2.5E-3

def setDebug(debug):
    globals()["DEBUG"] = debug

USList = nrc.getUSList(DATE)

#-----CROSS-SECTION CONSTANTS------#
DELTA = 1.293   #in MeV; neutron mass - proton mass
Me = 0.511 #in MeV
A1 = -0.07056
A2 = 0.02018
A3 = -0.001953

#Takes in an array of unoscillated spectra (and the spectra's energy values for each entry)
#And returns the dNdE function that results from them
def build_dNdE(unosc_spectra,energy_array,oscParams):
    Total_Spectra = np.zeros(len(energy_array))
    for ReacSpectra in unosc_spectra:
        if ADD_SYSTEMATICS:
            #Adds systematic fluctuations to each core
            ReacSpectra.AddCoreSystematics()
        ReacOscSpecGen = OscSpecGen(ReacSpectra, oscParams)
        Total_Spectra += ReacOscSpecGen.Summed_Spectra
    return dNdE(energy_array,Total_Spectra)

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
        exp_term = np.sum(poly_terms)
        sl = np.exp(exp_term)
        return sl

    def defineBigLambda(self):
        if DEBUG == True:
            print("SMALL LAMBDAS AND ISOTOPE FRACTIONS FED TO THIS BIGLAMBDA:" )
            print(self.sl_array)
            print(self.isofracs)
        bl_terms = []
        for i,sl in enumerate(self.sl_array):
            bl_term = self.isofracs[i] * sl
            bl_terms.append(bl_term)
        bl = np.sum(bl_terms) #Not a functional: just a function now
        if DEBUG == True:
            print("Big Lambda built. Output value for energy " + str(self.E) + "MeV" + \
                    " is " + str(bl))     
        self.value = bl

    def polyTerm(self, a, e, c):
        return a * (e**c)

#Class takes in permanent details for a reactor plant (ReacDetails RATDB entry)
#And the reactor's status (ReacStatus RATDB entry), and the RATDB entries of 
#isotopes to use, and the energys to calculate the spectrum at
#and builds an array of spectra arrays (self.Unosc_Spectra) evaluated at the
#given energies.  There is one array for each core of the plant.
class UnoscSpecGen(object):
    def __init__(self,ReacDetails,ReacStatus,iso_array,energy_array):
        self.E_arr = energy_array
        self.ReacDetails = ReacDetails
        self.ReacStatus = ReacStatus
        self.iso_array = iso_array

        self.__core_check()
        self.no_cores = self.ReacStatus.no_cores

        self.Core_Distances = []
        self.__CoreDistancesFromSNO()
        self.Unosc_Spectra = []
        self.__calcSpectra()

        #Now, incorporate Power information from daily_update database
        self.CoreSpecs = coreGen(ReacStatus,self.Unosc_Spectra)
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
            coreDistance = sd.getDistFromSNOLAB([longitude,latitude,altitude])
            self.Core_Distances.append(coreDistance)
        if DEBUG == True:
            print("Core distances calculated! In km... " + str(self.Core_Distances))

    def calcSpectra(self):
        self.Unosc_Spectra = []  #Refresh array before adding spectrums
        for i in np.arange(0,self.no_cores):
            coreType = self.ReacStatus.core_types[i]
            coreMWt = self.ReacStatus.core_powers[i]
            coreDistance = self.Core_Distances[i]
            isotope_composition = rp.Reactor_Spectrum(coreType).param_composition
            #loop over energies, calculate spectra's values
            coreSpectrum = []
            for E in self.E_arr:
                LambdaFunction = Lambda(self.iso_array, isotope_composition,E).value
                coreLambda = LambdaFunction / self.spectrumDenom(isotope_composition)
                coreSpectrum.append( coreLambda / \
                        (4*np.pi * (coreDistance**2)))
            self.Unosc_Spectra.append(np.array(coreSpectrum))

    def spectrumDenom(self,isocomp):
        denominator = 0.0
        for i,iso in enumerate(self.iso_array):
            denominator += isocomp[i] * self.iso_array[i].Eperfission
        return denominator
       
    def AddCoreSystematics(self):
        '''
        If called, the spectra from each core is scaled according to the
        average load factor.  Basically, sample from a gaussian of 
        mu=LF and sigma = 10% for now.  Can make a function of LF later.
        '''
        sysSigmas = LF_VAR * np.ones(len(self.AvgLFs))
        sysFlucs = np.randShoot(self.AvgLFs,sysSigmas,len(self.AvgLFs))
        Unosc_Spectra_wSys = []
        for i,coreSpectrum in enumerate(self.Unosc_Spectra):
            coreSpectrum = coreSpectrum * sysFlucs[i]
            self.Unosc_Spectra_wSys.append(coreSpectrum)
        self.Unosc_Spectra = self.Unosc_Spectra_wSys

    #Make private copies of the public methods
    __core_check = core_check
    __calcSpectra = calcSpectra
    __CoreDistancesFromSNO = CoreDistancesFromSNO


#Class takes in the unoscillated spectra associated with a reactor plant.
#generates each core's operation details based on the number of days ran
#in an experiment and the load factor of a reactor for each day. Builds the
#unoscillated spectra with power and load factor values included.
class coreGen(object):
    def __init__(self,ReacStatus,Unosc_Spectra):

        self.ReacName = ReacStatus.index
        self.core_powers = ReacStatus.core_powers #Core powers as in RAT
        self.Unosc_Spectra = Unosc_Spectra

        #Number of days of data collected from the daily_updates DB
        self.numdays_ofdata = 0

        #Sum of licensed MWts grabbed for each day and sum of load factors
        self.TotMWts = []
        self.TotLFs = []

        #These are calculated as the total divided by the numdays_ofdata
        self.AvgMWts = []
        self.AvgMWts = []

        #Spectra with power corrections
        self.Unosc_Spectra_wP = []

        #if self.ReacDetails.index is in CAList, use RATDB core powers with no
        #statistical fluctuations
        if self.ReacName not in USList:
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
            coreSpectrum = coreSpectrum * RUNTIME * MWHTOMEV * \
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
        self.AvgLFs = (self.TotLFs/self.numdays_ofdata) / 100.0 #Shown in DB as percentage 

        #now, use the average values to rescale the spectrums
        
        for i,coreSpectrum in enumerate(self.Unosc_Spectra):
            coreSpectrum = coreSpectrum * RUNTIME * MWHTOMEV * \
                    self.AvgMWts[i] * self.AvgLFs[i]
            self.Unosc_Spectra_wP.append(coreSpectrum)

    __Power_Perfect = Power_Perfect
    __Power_AvgAvailable = Power_AvgAvailable


#Class takes a coreGen class (contains spectrums for each core of one reactor)
#and outputs the the oscillated Spectrums.  oscParams should have two entries: 
#[delta m-squared, sin^2(theta12)]
class OscSpecGen(object):
    def __init__(self, UnoscSpecGen, oscParams):
        self.Unosc_Spectra = UnoscSpecGen.Unosc_Spectra
        self.ReacDetails = UnoscSpecGen.ReacDetails
        self.ReacStatus = UnoscSpecGen.ReacStatus
        self.E_arr = UnoscSpecGen.E_arr
        self.Core_Distances = UnoscSpecGen.Core_Distances 

        #define your variable oscillation paramaters;
        self.SINSQT12 = oscParams[1]
        self.DELTAMSQ21 = oscParams[0]
        #calculate needed fixed oscillation parameters
        self.SINSQTWO12 = self.calcSINSQTWO(self.SINSQT12)
        self.COSSQT12 = self.calcCOSSQ(self.SINSQT12)

        #Oscillate each core spectra, then sum them
        self.Osc_Spectra = []
        self.__oscillateSpectra()
        self.Summed_Spectra = []
        self.__sumSpectra()

    def oscillateSpectra(self):
        self.Osc_Spectra = [] #Refresh array before adding spectrums
        for i,spectrum in enumerate(self.Unosc_Spectra):
             self.Osc_Spectra.append(np.product([spectrum,self.Pee(self.E_arr, \
                     self.Core_Distances[i])],axis=0))

    def calcSINSQTWO(self, sst12):
        st12 = np.sqrt(sst12)
        t12 = np.arcsin(st12)
        return (np.sin(2 * t12))**2

    def calcCOSSQ(self, sst12):
        st12 = np.sqrt(sst12)
        t12 = np.arcsin(st12)
        return (np.cos(t12))**2

    def Pee(self,E,L):
        #Takes in an array of energies and one length and returns an array
        #of the Pee spectrum.
        #L must be given in kilometers, energy in MeV
        #USING THE EQN. FROM SVOBODA/LEARNED
        term1 = COS4THT13*self.SINSQTWO12*(np.sin(1E-12 * \
                self.DELTAMSQ21 * L /(4 * E * hbarc))**2)
        term2 = self.COSSQT12*SINSQTWO13*(np.sin(1E-12 * \
                DELTAMSQ31 * L /(4 * E * hbarc))**2)
        term3 = self.SINSQT12*SINSQTWO13*(np.sin(1E-12 * \
            DELTAMSQ32 * L /(4 * E * hbarc))**2)
        result = 1 - (term1 + term2 + term3)
        #OR, USING 2-PARAMETER APPROXIMATION USED BY KAMLAND
        #result = 1 - SINSQTWO12 * np.sin((1.27 * DELTAMSQ21*L)/(E/1000))**2

        return result

    def sumSpectra(self):
        summed_spectra = np.sum(self.Osc_Spectra, axis=0)
        self.Summed_Spectra = summed_spectra


    #Make private copies of the public methods; important to let
    #subclasses override methods without breaking intraclass method calls.
    __sumSpectra = sumSpectra
    __oscillateSpectra = oscillateSpectra

#Class takes in a reactor spectrum array (oscillated or unoscillated) and the
#relative x-axis array (Energy_Array in the class) and calculates the
#dNdE function for the spectrum. Total Runtime and Thermal power associated
#with the spectrum's core must already be factored into the spectrum.
class dNdE(object):
    def __init__(self,Energy_Array,Spectrum):
        self.Energy_Array = Energy_Array
        self.Spectrum = Spectrum

        self.Array_Check()

        self.dNdE = []
        self.evaldNdE()

    def evaldNdE(self):
        self.dNdE = [] #Remove any previous values in dNdE
        self.dNdE = EFFICIENCY * NP * \
            self.XC(self.Energy_Array) * self.Spectrum

    def Array_Check(self):
        if len(self.Energy_Array) != len(self.Spectrum):
            raise UserWarning("WARNING: Energy array length does not equal" + \
                    "length of spectrum given.  Check your entries.")

    #takes in an array of energies and returns an array of cross-section values
    #as a function of energy
    def XC(self, E):
        Ee = (E - DELTA)
        pe = np.sqrt((Ee**2) - (Me**2))
        poly = E**(A1 + (A2 * np.log(E)) + (A3 * ((np.log(E))**3)))
        return (1E-53) * pe * Ee * poly #1E-53, instead of -43, for km^2 units

