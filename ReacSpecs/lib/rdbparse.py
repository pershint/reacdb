#Various functions for parsing the CoreComps.ratdb file for reactor information.

import numpy as np
import os.path
import sys

basepath = os.path.dirname(__file__)
dbpath = os.path.abspath(os.path.join(basepath, "..", "db"))

REACTOR_RATDB = 'REACTORS_corr.ratdb'
CORECOMP_RATDB = 'CoreComps.ratdb'

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

    def getEntryInfo(self):
        '''
        Grabs the general information universal to all RATDB files and fills
        the defined class variables.
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
                print(linepieces)
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
        stdratdict = {"type": self.rdb_type, "version": self.ver, "index": self.index,
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

    def parseComps(self):
        composition = self.misc['iso_comp']
        composition = composition.lstrip("\' ").rstrip(",\n\'")
        comp_array = composition.split(",")
        self.composition = comp_array
        
    def buildreacdbEntry(self):
       self.reacdb_entry["Core Composition (U238, U235, Pu239, Pu241)"] = self.composition
       super(CoreComp, self).buildReacdbEntry()

    def printTheReal(self):
        print("Gettingreal")

#STILL NEEDS THE buildreacdbEntry FUNCTION
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

    def parsePowLoc(self):
        power = self.misc['power_therm']
        power = float(power.lstrip().rstrip(",\n"))
        self.power_therm = power
        longitude = self.misc['longitude']
        longitude = round(float(longitude.lstrip().rstrip(",\n")),2)
        self.longlat[0]=longitude
        latitude = self.misc['latitude']
        latitude = round(float(latitude.lstrip().rstrip(",\n")),2)
        self.longlat[1]=latitude
        
               

        
if __name__ == '__main__':
    print('Still nothing in main loop yet')
