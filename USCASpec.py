#Python script for building the expected number of events per day as a function
#of energy at SNO+.  Bins are in 50 keV increments.

import sys

import lib.GetNRCDailyInfo as nrc
import lib.rdbbuild as rb
import lib.rdbparse as rp
import lib.SNOdist as sd
import tools.graph.SpectraPlots as splt
import tools.graph.OscPlot as oplt
import numpy as np

import inspect as ins


DATE = '11/20/2016' #Date queried on NRC.gov to get operating US reactor names
RUNTIME = 8760   #One year in hours
EFFICIENCY = 1  #Assume 100% signal detection efficiency
LF = 0.8    #Assume all power plants operate at 80% of licensed MWt
MWHTOMEV = 2.247E22 #One MW*h equals this many MeV
NP = 1E32   #Need to approximate SNO+'s number of proton targets
ISOTOPES = ['235U', '238U', '239Pu', '241Pu']
ENERGIES_TO_EVALUATE_AT = np.arange(1.82,9,0.01)


SK_PARAMS = False
KAMLAND_PARAMS = True

#-----OSCILLATION PARAMETERS-----#
#-----ALL PARAMETERS PULLED FROM Abe, K., Haga, Y. et al. "Solar Neutrino" ---#
#-----Measurements in Super-Kamiokande-IV", arXiv:1606.07538v1 [hep-ex] ------#
#-----24 Jun 2016 ------------------------------------------------------------#

hbarc = 1.9733E-16 #in MeV * km
SINSQT13 = 0.0219 
SINSQTWO13 = 0.0851 #calculated from SINSQT13
COS4THT13 = 0.9570  #calculated from SINSQT13
#Approximate DELTAMSQ31 = DELTAMSQ32 for now
DELTAMSQ31 = 2.5E-3
DELTAMSQ32 = 2.5E-3
if SK_PARAMS:
    SINSQT12 = 0.334
    COSSQT12 = 0.666
    SINSQTWO12 = 0.890 #calculated from SINSQT12
    DELTAMSQ21 = 4.85E-05  #in ev^2
if KAMLAND_PARAMS:
    SINSQT12 = 0.316
    COSSQT12 = 0.684
    SINSQTWO12 = 0.865 #calculated from SINSQT12
    DELTAMSQ21 = 7.54E-05


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
        if __debug__:
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
#The oscillated Spectrums.
class OscSpectra(object):
    def __init__(self, UnoscSpectra):
        self.Unosc_Spectra = UnoscSpectra.Unosc_Spectra
        self.ReacDetails = UnoscSpectra.ReacDetails
        self.ReacStatus = UnoscSpectra.ReacStatus
        self.E_arr = UnoscSpectra.E_arr
        self.Core_Distances = UnoscSpectra.Core_Distances 

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

    def Pee(self,E,L):
        #L must be given in kilometers, energy in MeV
        #term = (1 - (SINSQTWO12 * \
        #        (np.sin(1E-12 * DELTAMSQ21 * L /(4 * E * hbarc))**2)))
        #result = (COS4THT13 * term) + (SINSQT13**2)
        #USING THE EQN. FROM SVOBODA/LEARNED
        term1 = COS4THT13*SINSQTWO12*(np.sin(1E-12 * DELTAMSQ21 * L /(4 * E * hbarc))**2)
        term2 = COSSQT12*SINSQTWO13*(np.sin(1E-12 * DELTAMSQ31 * L /(4 * E * hbarc))**2)
        term3 = SINSQT12*SINSQTWO13*(np.sin(1E-12 * DELTAMSQ32 * L /(4 * E * hbarc))**2)
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
            print(self.Summed_Spectra)[0]

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
        print(E)
        Ee = (E - DELTA)
        pe = np.sqrt((Ee**2) - (Me**2))
        poly = E**(A1 + (A2 * np.log(E)) + (A3 * ((np.log(E))**3)))
        return (1E-53) * pe * Ee * poly #1E-53, instead of -43, for km^2 units

#FIXME: Need to make a class that can take in the unoscilated spectrum info.
#for a reactor, and uses scipy to integrate over that function times
#The survival probability function times the cross-section.  Right now, how
#The classes are written, you can't use the individual pieces cleanly, so we
#May have to restructure a bit.

def RoughIntegrate(y_array,x_array):
    """
    Returns the area under the y_array given from range (a,b) in the
    x_array.  The bin width for y_array[i] is defined here as
    x_array[i+1] - x_array[i].
    """
#    if not a or b:
#        print("no range given, integratine entire array.")
#        a_bin = x_array[0]
#        b_bin = x_array[len(x_array)-1]
#    if a>b:
#        return ValueError("CHOOSE AN INTEGRATION RANGE WHERE a<b")
#    if a<x_array[0] or b>x_array[len(x_array)-1]:
#        print("range given is outside of array's endpoints." + \
#                "stopping at endpoints of defined array.")
#    for x,i in enumerate(x_array):
#        if a>x_array[i-1] and a<x_array[i]:
#            a_bin = i
#        if b>x_array[i-1] and b<x_array[i]:
#            b_bin = i
    #strips y_array to the range to be integrated over
#    y_array = y_array[a:b]
    print("NOTE: Final endpoint of array is not considered in integral.")
    integral = 0.0
    for i,y in enumerate(y_array):
        if i == len(y_array)-1:
            print("At end of array.  Result: " + str(integral))
            return integral
        integral += y_array[i] * (x_array[i+1]-x_array[i])

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
        BruceUnoscSpectra = UnoscSpectra(BruceDetails,BruceStatus,Isotope_Information, \
                ENERGIES_TO_EVALUATE_AT)
        BruceOscSpectra = OscSpectra(BruceUnoscSpectra)
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
    print("GRAPHING THE SUM OF CANADIAN REACTORS")
    Total_Spectra = np.zeros(len(ENERGIES_TO_EVALUATE_AT))
    if "US" in (sys.argv):
        List = USList
    elif "CA" in (sys.argv):
        List = CAList
    elif "USCA" in (sys.argv):
        List = USCAList
    else:
        print("Please write US, CA, or USCA as a flag for what reactors to use")
        exit()
    for reactor in List:
        ReacDetails = rp.ReactorDetails(reactor)
        ReacStatus = rp.ReactorStatus(reactor)
        ReacUnoscSpectra = UnoscSpectra(ReacDetails,ReacStatus, \
                Isotope_Information, ENERGIES_TO_EVALUATE_AT)
        ReacOscSpectra = OscSpectra(ReacUnoscSpectra)
        Total_Spectra += ReacOscSpectra.Summed_Spectra
    splt.CAspectrumPlot(ENERGIES_TO_EVALUATE_AT,Total_Spectra)
    USCA_dNdE = dNdE(ENERGIES_TO_EVALUATE_AT,Total_Spectra)
    RoughIntegrate(USCA_dNdE.dNdE,ENERGIES_TO_EVALUATE_AT)
    splt.dNdEPlot(ENERGIES_TO_EVALUATE_AT,USCA_dNdE.dNdE, SINSQT12, DELTAMSQ21)

