#Python script for building the expected number of events per day as a function
#of energy at SNO+.  Bins are in 50 keV increments.

import lib.GetNRCDailyInfo as nrc
import lib.rdbbuild as rb
import lib.rdbparse as rp
import lib.func.FF as ff
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
    def __init__(self,iso_array,spec):
        self.sl_array = []
        for iso in iso_array:
            self.sl_array.append(self.smallLambda(iso))
        self.isofracs = spec.param_composition
        self.function = 'none'
        self.defineBigLambda()


    def smallLambda(self,iso):
        poly_terms = []
        for i in np.arange(0,len(iso.poly_coeff)):
            term = ff.FunctionalFunction(lambda x: iso.poly_coeff[i]*(x**i))
            poly_terms.append(term)
        exp_term = np.sum(poly_terms)
        sl = ff.FunctionalFunction(lambda x: np.exp(exp_term))
        return sl

    def defineBigLambda(self):
        bl = ff.FunctionalFunction(lambda x: 0)
        scaled_sls = []
        for i,sl in enumerate(self.sl_array):
            scaled_sls.append(lambda x: self.isofracs[i] * sl(x))
        bl = np.sum(scaled_sls)
        print("Big Lambda built. Function is" + str(ins.getsource(bl)))     
        self.function = bl

    def evaluate(self, energy):
        if self.function != 'none':
            return self.function(energy)
        else:
            print("No Lambda function present.  Check your isotope inputs" + \
                    "and isotope composition for errors.")


class Spectrum(object):
    def __init__(self,Lambda,ReacSpec,ReacStatus,iso_array):
        self.denom = 0.0
        print("initialization going down here. yee")

    def denomScale(self):
        for i,iso in iso_array:
        
    def defineSpectrum(self):

    def 
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

