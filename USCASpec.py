#Python script for building the expected number of events per day as a function
#of energy at SNO+.  Bins are in 50 keV increments.

import lib.GetNRCDailyInfo as nrc
import lib.rdbbuild as rb
import lib.rdbparse as rp
import lib.func.FF as ff
imoport lib.SNODist as sd
import numpy as np

import inspect as ins

DATE = '11/20/2016' #Date queried on NRC.gov to get operating US reactor names
EFFICIENCY = 0.8
NP = 10e32   #Need to approximate SNO+'s number of proton targets
ISOTOPES = ['235U', '238U', '239Pu', '241Pu']

#Class takes in four RATDB type Isotope Info entries and one
#Spectrum entry (has the isotope compositions).  The class builds each
#Isotope's associated small lambda.  These are combined with the isotope
#fractions to make the reactor's Lambda function
#Isotopes should be fed as follows: iso_array[0] = 235U RATDB entry, iso_array[1]=238U,
#iso_array[2]=239Pu, iso_array[3]=241Pu
class Lambda(object):
    def __init__(self,iso_array,isofracs):
        self.sl_array = []
        for iso in iso_array:
            self.sl_array.append(self.smallLambda(iso))
        self.isofracs = isofracs
        self.function = 'none'
        self.defineBigLambda()


    def smallLambda(self,iso):
        poly_terms = []
        for i in np.arange(0,len(iso.poly_coeff)):
            term = ff.FunctionalFunction(lambda x: iso.poly_coeff[i]*(x**i))
            poly_terms.append(term)
        exp_term = np.sum(poly_terms) #Not a functional: just a function now
        #sl = ff.FunctionalFunction(lambda x: np.exp(exp_term))
        sl = lambda x: np.exp(exp_term(x))
        return sl

    def defineBigLambda(self):
        bl = ff.FunctionalFunction(lambda x: 0)
        bl_terms = []
        for i,sl in enumerate(self.sl_array):
            bl_term = ff.FunctionalFunction(lambda x: self.isofracs[i] * sl(x))
            bl_terms.append(bl_term)
        bl = np.sum(bl_terms) #Not a functional: just a function now
        print("Big Lambda built. Function is" + str(ins.getsource(bl)))     
        self.function = bl

    def evaluate(self, energy):
        if self.function != 'none':
            return self.function(energy)
        else:
            print("No Lambda function present.  Check your isotope inputs" + \
                    "and isotope composition for errors.")

#Class takes in permanent details for a reactor plant (ReacDetails RATDB entry)
#And the reactor's status (ReacStatus RATDB entry), and the RATDB entries of 
#isotopes to use. returns an array of spectrum functions (one for each core).
class UnoscSpectra(object):
    def __init__(self,ReacDetails,ReacStatus,iso_array):
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
        if ReacDetails.no_cores != ReacStatus.no_cores:
            raise UserWarning("WARNING: Number of cores in REACTOR" + \
                    "RATDB entry does not match REACTOR_STATUS entry. Using" + \
                    "number of cores put in REACTOR STATUS entry.")

    def CoreDistancesFromSNO(self):
        self.Core_Distances = [] #Refresh array before adding core distances
        for i in np.arange(0,no_cores):
            longitude = self.ReacDetails.core_longitudes[i]
            latitude = self.ReacDetails.core_latitudes[i]
            altitude = self.ReacDetails.core_altitudes[i]
            coreDistance = sd.SNODistance(longitude,latitude,altitude)
            self.Core_Distances.append(coreDistance)
        print("Core distances calculated! In km... " + str(self.Core_Distances))

    def calcSpectra(self):
        self.Core_Spectra = []  #Refresh array before adding spectrums
        for i in np.arange(0,self.no_cores):
            coreType = self.ReacStatus.core_type[i]
            coreMWt = self.ReacStatus.core_power[i]
            coreDistance = self.Core_Distances[i]
            isotope_composition = rp.Reactor_Spectrum(coretype).param_composition
            LambdaFunction = Lambda(self.iso_array, isotope_composition).function
            coreLambda = lambda x: LambdaFunction(x) / spectrumDenom(isotope_composition)
            coreSpectrum = lambda x: coreMWt * EFFICIENCY * coreLambda(x) / \
                    (4*np.pi * (coreDist**2))
            self.Core_Spectra.append(coreSpectrum)

    def spectrumDenom(self,isocomp):
        denominator = 0.0
        for i,iso in enumerate(iso_array):
            denominator += isocomp[i] * iso_array[i].Eperfission
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
    USList = NRCDayList.date_reacs
    USList = rb.USListToRATDBFormat(USList)
    return USList

if __name__ == '__main__':
    WorldList = rp.getRLIndices()
    #Could make a US REACTOR LIST entry in REACTORS.ratdb and read it later
    USList = getUSList()
    CAList = ["BRUCE","DARLINGTON", "PICKERING","POINT LEPREAU"]
    USCAList = USList + CAList

    #Build array containing details for each isotope found in reactors
    Isotope_Information = []
    for isotope in ISOTOPES:
        Isotope_Information.append(rp.Reactor_Isotope_Info(isotope))

