#Program uses the rdbparse library to push the desired isotope compositions
#and flux parameters to reacdb.
#Code is a one-shot; it currently pushes two documents to reacdb.  The first
#Has published isotope compositions measured/calculated for reactors.
#The second contains several parameters for parametrizing the antineutrino flux from
#a reactor.

import lib.rdbparse as rp
import os.path
import lib.DButils as du
import sys
import couchdb as couch



def BuildCCEntry():
    CCArray = []    
    indices = rp.getCCIndices()
    for index in indices:
        CCEntry = rp.CoreComp(index)
        CCEntry.fill()
        CCEntry.parseMisc()
        CCEntry.buildreacdbEntry()
        CCEntry.showValue()
        print(CCEntry.composition)
        CCArray.append(CCEntry.reacdb_entry)
    reacdbdoc = {"Core_Compositions": CCArray}
    return reacdbdoc

def BuildNcEntry():
    NCArray = []
    indices = rp.getNCIndices()
    for index in indices:
        NCEntry = rp.NuCoeff(index)
        NCEntry.fill()
        NCEntry.parseMisc()
        NCEntry.buildreacdbEntry()
        NCArray.append(NSEntry.reacdb_entry)
    reacdbdoc = {"NuSpectrum_Coefficients": NCArray}
    print(NCArray)
    return reacdbdoc

if __name__ == "__main__":
    CoreCompDoc = BuildCCEntry()
    du.saveToReacdb(CoreCompDoc)
    NuCoeffDoc = BuildNCEntry()
    du.saveToReacdb(NuCoeffDoc)
