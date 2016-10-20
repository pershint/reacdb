#Various functions for parsing any ratdb file for reactor information.
#TO ADD YOUR OWN CLASS PARSER:
# 1. Create a new class that inherits from class ratdbEntry
# 2. Write a parseMisc() function that parses out your
#    RATDB entry's information specific to the RATDB type
# 3. Write a buildreacdbEntry() function that adds the values
#    Specific to your RATDB type to the reacdb_entry dictionary
#*** See the CoreComp subclass for an example of how this is done.

import numpy as np
import os.path
import sys

basepath = os.path.dirname(__file__)
dbpath = os.path.abspath(os.path.join(basepath, "..", "db"))

REACTOR_RATDB = 'REACTORS_corr.ratdb'
CORECOMP_RATDB = 'CoreComps.ratdb'
NUSPEC_RATDB = 'NuSpectraConsts.ratdb'

def getCCIndices():
    """
    Opens CoreComp.ratdb and grabs all the index values present.
    """
    CCindices = []
    ccpath = os.path.abspath(os.path.join(dbpath, CORECOMP_RATDB))
    f = open(ccpath, 'r')
    for line in f:
        if line.find('index') != -1:
            indexline = line.split(":")
            index = indexline[1].lstrip(" \"").rstrip("\",\n")
            CCindices.append(index)
    return CCindices


def getNSIndices():
    """
    Opens NuSpectraConst.ratdb and grabs all the index values present.
    """
    NSindices = []
    nspath = os.path.abspath(os.path.join(dbpath, NUSPEC_RATDB))
    f = open(nspath, 'r')
    for line in f:
        if line.find('index') != -1:
            indexline = line.split(":")
            index = indexline[1].lstrip(" \"").rstrip("\",\n")
            NSindices.append(index)
    return NSindices

#Class is defined with a RATDB database file, RDB type, and RDB index. grabs the basic
#information for that entry in the database.
class ratdbEntry(object):
    def __init__(self,filename,rdbtype,index):
        self.rdb_type = rdbtype
        self.ver = 'unknown'
        self.index = index
        self.run_range = []
        self.passing = 'unknown'
        self.comment = 'unknown'
        self.timestamp = 'unknown'
        self.misc = {}
        self.reacdb_entry = {}
        self.ratdbpath = os.path.abspath(os.path.join(dbpath, filename))

    def showValue(self):
        print("RATDB type: " + self.rdb_type)
        print("Version: " + self.ver)
        print("Entry index: " + self.index)
        print("Run range: " + str(self.run_range))
        print("Pass?: " + str(self.passing))
        print("Comments: " + self.comment)
        print("timestamp: " + self.timestamp)
        print("Miscillaneous values: " + str(self.misc))
        print("Current reacdb_entry: " + str(self.reacdb_entry))

    def fill(self):
        '''
        Fills the defined class variables with the general information 
        universal to all RATDB files. The misc dictionary is filled with
        information specific to a RATDB entry type.
        '''
        f=open(self.ratdbpath, 'r')
        doneparse = False
        startparse = False
        while True:
            stuff = str(f.readline())
            if stuff.find('{') != -1:
                nextline = str(f.readline())
                nxlinepieces = nextline.split(":")
                if nxlinepieces[0] == "type" and \
                nxlinepieces[1].rstrip("\",\n").lstrip(" \"") == self.rdb_type:
                    verline = f.readline()
                    indexline = f.readline()
                    inlinepieces = indexline.split(":")
                    if inlinepieces[0] == "index" and \
                    inlinepieces[1].rstrip("\",\n").lstrip(" \"") == self.index:
                        break
                else:
                    print("type was not the first entry in a DB, check your DB entries" + \
                    "for proper formatting!!!!!")
        verlinepieces = verline.split(":")
        self.ver = verlinepieces[1].rstrip(",\n")
        while True:
            line = str(f.readline())
            if line.find('}') == -1:
                linepieces = line.split(":")
                if linepieces[0] == 'version':
                    self.ver = int(linepieces[1].rstrip(",\n"))
                elif linepieces[0] == 'run_range':
                    rr = linepieces[1].split(",")
                    for i,entry in enumerate(rr):
                        if i == 0:
                            runstart = int(entry.lstrip(" ["))
                            self.run_range.append(runstart)
                        if i == (len(rr) - 2): #There's a blank entry after last comma
                            runend = int(entry.rstrip("],\n"))
                            self.run_range.append(runend)
                elif linepieces[0] == "pass":
                    self.passing = int(linepieces[1].rstrip(",\n"))
                elif linepieces[0] == "comment":
                    self.comment = linepieces[1].rstrip(",\n")
                elif linepieces[0] == "timestamp":
                    self.timestamp = linepieces[1].rstrip(",\n")
                else:
                    self.misc[linepieces[0]] = linepieces[1]
            else:
                break

    def buildReacdbEntry(self):
        """
        Fills in self.reacdb_entry with the standard RATDB entry values."
        """
        stdratdict = {"RATDB_type": self.rdb_type, "version": self.ver, "index": self.index,
        "run_range": self.run_range, "pass": self.passing, "comment": self.comment,
        "timestamp": self.timestamp}
        readytobuild = True
        for key in stdratdict:
            if stdratdict[key] == 'none':
                print("One or more entries were not filled in for the ratdb entry." + \
                "reacdb_entry not built.")
                readytobuild = False
        if readytobuild:
            self.reacdb_entry = stdratdict
            print("Standard RATDB entry values filled in.  Please add miscillaneous " + \
            "information before pushing to ReacDB.")
    def pushToDB(self):
        dbStatus, db = connectToDB('reacdb')
        if dbStatus is "ok":
            db.save(self.reacdb_entry)

#Subclass of ratdbEntry that also parses isotope compositions
#Super call inherits the parent's (class ratdbEntry's) init parameters
#Have to do this; just starting a new init would overwrite the parent init
class CoreComp(ratdbEntry):
    def __init__(self,index):
        self.rdb_type = "REACTORCOMPS"
        self.filename = CORECOMP_RATDB
        self.composition = []
        super(CoreComp, self).__init__(self.filename, self.rdb_type, index)
        self.stuff = "things"

    def showValue(self):
        super(CoreComp,self).showValue() #performs the parent method showValue()
        print("Isotope composition: " + str(self.composition))

    def parseMisc(self):
        composition = self.misc['iso_comp']
        composition = composition.lstrip("\' [").rstrip("],\n\'")
        print(composition)
        composition = composition.split(",")
        comp_array = []
        for entry in composition:
            entry = float(entry)
            comp_array.append(entry)
        self.composition = comp_array

    def buildreacdbEntry(self):
        super(CoreComp, self).buildReacdbEntry()
        self.reacdb_entry["Core Composition (U238, U235, Pu239, Pu241)"] = self.composition

class NuCoeff(ratdbEntry):
    def __init__(self,index):
        self.rdb_type = "SPECTRACOEFF"
        self.filename = NUSPEC_RATDB
        self.U235 = []
        self.U238 = []
        self.Pu239 = []
        self.Pu241 = []
        super(NuCoeff, self).__init__(self.filename, self.rdb_type, index)

    def showValue(self):
        super(NuCoeff,self).showValue() #performs the parent method showValue()
        print("U235 parameters: " + str(self.U235))
        print("U238 parameters: " + str(self.U238))
        print("Pu239 parameters: " + str(self.Pu239))
        print("Pu241 parameters: " + str(self.Pu241))


    def parseMisc(self):
        U235_str = self.misc['U235']
        U235_str = U235_str.lstrip("\' [").rstrip("],\n\'")
        U235_str = U235_str.split(",")
        U235_arr = []
        for entry in U235_str:
            entry = float(entry)
            U235_arr.append(entry)
        self.U235 = U235_arr
        U238_str = self.misc['U238']
        U238_str = U238_str.lstrip("\' [").rstrip("],\n\'")
        U238_str = U238_str.split(",")
        U238_arr = []
        for entry in U238_str:
            entry = float(entry)
            U238_arr.append(entry)
        self.U238 = U238_arr
        Pu239_str = self.misc['Pu239']
        Pu239_str = Pu239_str.lstrip("\' [").rstrip("],\n\'")
        Pu239_str = Pu239_str.split(",")
        Pu239_arr = []
        for entry in Pu239_str:
            entry = float(entry)
            Pu239_arr.append(entry)
        self.Pu239 = Pu239_arr
        Pu241_str = self.misc['Pu241']
        Pu241_str = Pu241_str.lstrip("\' [").rstrip("],\n\'")
        Pu241_str = Pu241_str.split(",")
        Pu241_arr = []
        for entry in Pu241_str:
            entry = float(entry)
            Pu241_arr.append(entry)
        self.Pu241 = Pu241_arr
      
    def buildreacdbEntry(self):
        super(NuCoeff, self).buildReacdbEntry()
        self.reacdb_entry["U235 parameter values [a1,a2,a3,a4,a5,a6]"] = self.U235
        self.reacdb_entry["U238 parameter values [a1,a2,a3,a4,a5,a6]"] = self.U238
        self.reacdb_entry["Pu239 parameter values [a1,a2,a3,a4,a5,a6]"] = self.Pu239
        self.reacdb_entry["Pu241 parameter values [a1,a2,a3,a4,a5,a6]"] = self.Pu241
 
class ReactorSpecs(ratdbEntry):
    def __init__(self,index):
        self.rdb_type = "REACTORS"
        self.filename = REACTOR_RATDB
        self.power_therm = 'unknown'
        self.longlat = ['unknown', 'unknown']
        super(ReactorSpecs, self).__init__(self.filename, self.rdb_type, index)

    def showValue(self):
        super(ReactorSpecs,self).showValue() #performs the parent method showValue()
        print("Reactor Thermal Output (MW): " + str(self.power_therm))
        print("Reactor position [long, lat] (degrees): " + str(self.longlat))

    def parseMisc(self):
        power = self.misc['power_therm']
        power = float(power.lstrip().rstrip(",\n"))
        self.power_therm = power
        longitude = self.misc['longitude']
        longitude = round(float(longitude.lstrip().rstrip(",\n")),2)
        self.longlat[0]=longitude
        latitude = self.misc['latitude']
        latitude = round(float(latitude.lstrip().rstrip(",\n")),2)
        self.longlat[1]=latitude
        
    def buildreacdbEntry(self):
        self.reacdb_entry["thermal_output (MW)"] = self.composition
        self.reacdb_entry["location (long,lat)"] = self.longlat
        super(CoreComp, self).buildReacdbEntry()

              

        
if __name__ == '__main__':
    print('Still nothing in main loop yet')
