#g!

import rdbparse as rp
import SNOdist as sd
import numpy as np

parameters = 'none'
DEBUG = False

RUNTIME = 8760   #One year in hours
EFFICIENCY = 1  #Assume 100% signal detection efficiency
LF = 0.8    #Assume all power plants operate at 80% of licensed MWt
MWHTOMEV = 2.247E22 #One MW*h equals this many MeV
NP = 1E32   #Need to approximate SNO+'s number of proton targets

hbarc = 1.9733E-16 #in MeV * km

SINSQT13 = 0.0219 
SINSQTWO13 = 0.0851 #calculated from SINSQT13
COS4THT13 = 0.9570  #calculated from SINSQT13
#Approximate DELTAMSQ31 = DELTAMSQ32 for now
DELTAMSQ31 = 2.5E-3
DELTAMSQ32 = 2.5E-3

def setDebug(debug):
    globals()["DEBUG"] = debug

#-----CROSS-SECTION CONSTANTS------#
DELTA = 1.293   #in MeV; neutron mass - proton mass
Me = 0.511 #in MeV
A1 = -0.07056
A2 = 0.02018
A3 = -0.001953

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
#returns an array of spectra arrays evaluated at the given energies.
#There is one array for each core of the plant.
class UnoscSpectra(object):
    def __init__(self,ReacDetails,ReacStatus,iso_array,energy_array):
        self.E_arr = energy_array
        self.ReacDetails = ReacDetails
        self.ReacStatus = ReacStatus
        self.iso_array = iso_array

        self.core_check()
        self.no_cores = self.ReacStatus.no_cores

        self.Core_Distances = []
        self.CoreDistancesFromSNO()
        self.Unosc_Spectra = []
        self.calcSpectra()


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
                coreSpectrum.append( coreMWt * LF * coreLambda / \
                        (4*np.pi * (coreDistance**2)))
            self.Unosc_Spectra.append(coreSpectrum)

    def spectrumDenom(self,isocomp):
        denominator = 0.0
        for i,iso in enumerate(self.iso_array):
            denominator += isocomp[i] * self.iso_array[i].Eperfission
        return denominator

#Class takes an array of unoscillated spectrums and outputs the functions for
#The oscillated Spectrums.  oscParams should have two entries: 
#[delta m-squared, sin^2(theta12)]
class OscSpectra(object):
    def __init__(self, UnoscSpectra, oscParams):
        self.Unosc_Spectra = UnoscSpectra.Unosc_Spectra
        self.ReacDetails = UnoscSpectra.ReacDetails
        self.ReacStatus = UnoscSpectra.ReacStatus
        self.E_arr = UnoscSpectra.E_arr
        self.Core_Distances = UnoscSpectra.Core_Distances 

        #define your oscillation paramaters;
        self.SINSQT12 = oscParams[1]
        self.DELTAMSQ21 = oscParams[0]
        self.SINSQTWO12 = self.calcSINSQTWO(self.SINSQT12)
        self.COSSQT12 = self.calcCOSSQ(self.SINSQT12)
        self.Osc_Spectra = []
        self.oscillateSpectra()

        self.Summed_Spectra = []
        self.sumSpectra()

    def oscillateSpectra(self):
        self.osc_spectrums = [] #Refresh array before adding spectrums
        for i,spectrum in enumerate(self.Unosc_Spectra):
            osc_spectrum = []
            for j,entry in enumerate(spectrum):
                osc_spectrum.append(entry * self.Pee(self.E_arr[j],self.Core_Distances[i]))
            self.Osc_Spectra.append(osc_spectrum)

    def calcSINSQTWO(self, sst12):
        st12 = np.sqrt(sst12)
        t12 = np.arcsin(st12)
        return (np.sin(2 * t12))**2

    def calcCOSSQ(self, sst12):
        st12 = np.sqrt(sst12)
        t12 = np.arcsin(st12)
        return (np.cos(t12))**2

    def Pee(self,E,L):
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
        if self.Osc_Spectra:
            summed_spectra = np.zeros(len(self.E_arr))
            for spectrum in self.Osc_Spectra:
                summed_spectra = np.add(summed_spectra,spectrum)
            self.Summed_Spectra = summed_spectra

class dNdE(object):
    def __init__(self,Energy_Array,Spectrum):
        self.Energy_Array = Energy_Array
        self.Spectrum = Spectrum

        self.Array_Check()

        self.dNdE = []
        self.evaldNdE()

    def evaldNdE(self):
        dNdE = []
        for j,E in enumerate(self.Energy_Array):
            dNdE.append(EFFICIENCY * NP * RUNTIME * MWHTOMEV * \
                    self.XC(E)* self.Spectrum[j])
        self.dNdE = dNdE

    def Array_Check(self):
        if len(self.Energy_Array) != len(self.Spectrum):
            raise UserWarning("WARNING: Energy array length does not equal" + \
                    "length of spectrum given.  Check your entries.")


    def XC(self, E):
        Ee = (E - DELTA)
        pe = np.sqrt((Ee**2) - (Me**2))
        poly = E**(A1 + (A2 * np.log(E)) + (A3 * ((np.log(E))**3)))
        return (1E-53) * pe * Ee * poly #1E-53, instead of -43, for km^2 units

class Histogram(object):
    def __init__(self, spectrum, x_axis, numbins):
        self.spectrum = spectrum
        self.x_axis = x_axis
        self.numbins = numbins
        self.specvals_perbin = self.numbins / len(self.spectrum)
        self.bincheck()

        #Initialize arrays that hold bin end locations
        self.bin_left = []
        self.bin_right = []
        self.bin_center = []
        self.bin_values = []

        #FIXME: FILL IN BIN VALUES USING reBin_EW from tools/hist/binning.py
        #MAYBE MOVE THAT TO BE A METHOD YEAH?

    def bincheck(self):
        '''
        Function that checks the number of bins is not greater than the
        number of spectrum entries.
        '''
        if len(self.numbins) > len(self.spectrum):
            print("ERROR: CANNOT USE MORE BINS THAN SPECTRUM ARRAY ENTRIES." +\
                    "SETTING NUMBER OF BINS TO NUMBER OF SPECTRUM VALUES.")
            self.numbins = self.spectrum

#FIXME: Need to make a class that can take in the unoscilated spectrum info.
#for a reactor, and uses scipy to integrate over that function times
#The survival probability function times the cross-section.  Right now, how
#The classes are written, you can't use the individual pieces cleanly, so we
#May have to restructure a bit.


