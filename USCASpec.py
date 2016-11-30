#Python script for building the expected number of events per day as a function
#of energy at SNO+.  Bins are in 50 keV increments.

import lib.GetNRCDailyInfo as nrc
import lib.rdbbuild as rb
import lib.rdbparse as rp
import lib.func.FF as ff
import numpy as np

import inspect as ins

DATE = '11/20/2016'
EFFICIENCY = 0.8
NP = 10e32   #Need to approximate SNO+'s number of proton targets
ISOTOPES = ['235U', '238U', '239Pu', '241Pu']

#Class takes in four RATDB type Isotope Info entries and one
#Spectrum entry (has the isotope compositions).  The class builds each
#Isotope's associated small lambda.  These are combined with the isotope
#fractions to make the reactor's Lambda function
#Isotopes should be fed as follows: iso1 = 235U RATDB entry, iso2=238U,
#iso3=239Pu, iso4=241Pu
class Lambda(object):
    def __init__(self,iso1,iso2,iso3,iso4,spec):
        self.sl_array = [self.smallLambda(iso1), self.smallLambda(iso2) +  
                self.smallLambda(iso3), self.smallLambda(iso4)]
        self.isofracs = spec.param_composition
        self.Lambda = 'none'
        self.calcBigLambda()

        print("Function initialized.  Need any constants?")
    #FIXME: TRY USING THE FUNCTIONALFUNCTION CLASS TO DEFINE THESE FUNCTIONS!
    def smallLambda(self,iso):
        poly_terms = []
        for i in np.arange(0,len(iso.poly_coeff)):
            term = ff.FunctionalFunction(lambda x: iso.poly_coeff[i]*(x**i))
            poly_terms.append(term)
        exp_term = np.sum(poly_terms)
        sl = ff.FunctionalFunction(lambda x: np.exp(exp_term))
        return sl

    def calcBigLambda(self):
        bl = ff.FunctionalFunction(lambda x: 0)
        scaled_sls = []
        for i,sl in enumerate(self.sl_array):
            scaled_sls.append(lambda x: self.isofracs[i] * sl(x))
        bl = np.sum(scaled_sls)
        print("Big Lambda built. Function is" + str(ins.getsource(bl)))     
        self.Lambda = bl

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

