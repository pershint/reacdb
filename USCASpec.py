#Python script for building the expected number of events per day as a function
#of energy at SNO+.  Bins are in 50 keV increments.

import lib.GetNRCDailyInfo as nrc
import lib.rdbbuild as rb
import lib.rdbparse as rp
import lib.func.FF as ff
import lib.SNOdist as sd
import numpy as np

import inspect as ins

DATE = '11/20/2016' #Date queried on NRC.gov to get operating US reactor names
EFFICIENCY = 0.8
NP = 10e32   #Need to approximate SNO+'s number of proton targets
ISOTOPES = ['235U', '238U', '239Pu', '241Pu']
ENERGIES_TO_EVALUATE_AT = [2.0, 2.25, 2.5, 2.75, 3, 3.25, 3.5, 3.75, 4.0, \
        4.25, 4.5, 4.75, 5.0, 5.25, 5.5, 5.75, 6.0]



#Class takes in four RATDB type Isotope Info entries, one
#Spectrum entry (has the isotope compositions), and an energy to evaulate at.
#The class evaluates Isotope's associated small lambda, combines with the isotope
#fractions to make the reactor's Lambda function
#Isotopes should be fed as follows: iso_array[0] = 235U RATDB entry, iso_array[1]=238U,
#iso_array[2]=239Pu, iso_array[3]=241Pu
class Lambda(object):
    def __init__(self,iso_array,isofracs, E):
        self.E = E

        self.value = 'none'

        self.sl_array = []
        for iso in iso_array:
            print(iso.index)
            self.sl_array.append(self.smallLambda(iso))
        self.isofracs = isofracs
        self.defineBigLambda()

    def smallLambda(self,iso):
        poly_terms = []
        print(iso.poly_coeff)
        for i in np.arange(0,len(iso.poly_coeff)):
            print(i)
            term = self.polyTerm(iso.poly_coeff[i], self.E, i)
            poly_terms.append(term)
        print(poly_terms)
        #FIXME: the way numpy sums lambdas, functionals get defined into functions.
        #Need to somehow write the sum to keep all elements in the array as a
        #functional
        exp_term = np.sum(poly_terms) #Not a functional: just a function now
        #sl = ff.FunctionalFunction(lambda x: np.exp(exp_term))
        sl = np.exp(exp_term)
        return sl

    def defineBigLambda(self):
        if __debug__:
            print("SMALL LAMBDAS AND ISOTOPE FRACTIONS FED TO THIS BIGLAMBDA:" )
            print(self.sl_array)
            print(self.isofracs)
        bl_terms = []
        for i,sl in enumerate(self.sl_array):
            bl_term = self.isofracs[i] * sl
            bl_terms.append(bl_term)
        bl = np.sum(bl_terms) #Not a functional: just a function now
        if __debug__:
            print("Big Lambda built. Output value for energy " + str(self.E) + "MeV" + \
                    " is " + str(bl))     
        self.value = bl

    def polyTerm(self, c, x, a):
        return c * (x**a)

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
        self.Core_Spectra = []
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
        if __debug__:
            print("Core distances calculated! In km... " + str(self.Core_Distances))

    def calcSpectra(self):
        self.Core_Spectra = []  #Refresh array before adding spectrums
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
                coreSpectrum.append( coreMWt * EFFICIENCY * coreLambda / \
                        (4*np.pi * (coreDistance**2)))
            self.Core_Spectra.append(coreSpectrum)

    def spectrumDenom(self,isocomp):
        denominator = 0.0
        for i,iso in enumerate(self.iso_array):
            denominator += isocomp[i] * self.iso_array[i].Eperfission
        return denominator

#Class takes an array of unoscillated spectrums and outputs the functions for
#The oscillated Spectrums.
class OscSpectra(object):
    def __init__(self, UnoscSpectra):
        print("The init area")
        self.unosc_spectra = UnoscSpectra
        self.osc_spectrums = []
        self.Pee = ff.FunctionalFunction(lambda x: 0) #FIXME: PUT IN OSCILLATION FN. HERE
        
    def oscillateSpectra(self):
        self.osc_spectrums = [] #Refresh array before adding spectrums
        for spectrum in unosc_spectra:
            osc_spectra = lambda x: spectrum(x) * self.Pee(x)
            self.osc_spectrums.append(osc_spectra)


def getUSList():
    NRClist = nrc.NRCDayList()
    NRClist.getDateReacStatuses(DATE)
    NRClist.fillDateNames()
    USlist = NRClist.date_reacs
    USlist = rb.USListToRATDBFormat(USlist)
    return USlist

if __name__ == '__main__':
    WorldList = rp.getRLIndices()
    #Could make a US REACTOR LIST entry in REACTORS.ratdb and read it later
    USList = getUSList()
    CAList = ["BRUCE","DARLINGTON", "PICKERING","POINT LEPREAU"]
    USCAList = USList + CAList

    #Build array containing details for each isotope found in reactors
    Isotope_Information = []
    lambda_values = []
    for isotope in ISOTOPES:
        Isotope_Information.append(rp.Reactor_Isotope_Info(isotope))

    if __debug__:
#        print("#------ AN EXERCIES IN CALCULATING A LARGE LAMBDA ------#")
#        for energy in ENERGIES_TO_EVALUATE_AT:
#            lamb_value= Lambda(Isotope_Information, \
#                rp.Reactor_Spectrum("PHWR").param_composition, energy).value
#            lambda_values.append(lamb_value)
#        print("EXERCISE RESULT:" + str(lambda_values))
    
        print("#----- AN EXERCISE IN CALCULATING AN UNOSC. SPECTRA FOR BRUCE --#")
        BruceDetails = rp.ReactorDetails("BRUCE")
        BruceStatus = rp.ReactorStatus("BRUCE")
        BruceSpectra = UnoscSpectra(BruceDetails,BruceStatus,Isotope_Information, \
                ENERGIES_TO_EVALUATE_AT)
        print("EXERCISE RESULT: " + str(BruceSpectra.Core_Spectra))
