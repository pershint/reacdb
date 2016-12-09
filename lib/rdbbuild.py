#Various classes for building RATDB entries and saving the entry
#into a text file.

import pytz, datetime
import RIgrabber as rig
import GetNRCDailyInfo as gus
import numpy as np
import os.path
import sys

basepath = os.path.dirname(__file__)
dbpath = os.path.abspath(os.path.join(basepath, "..", "db"))

REACTORC_RATDB = 'static/REACTORS_corr.ratdb'
REACTOR_RATDB = 'static/REACTORS.ratdb'
CORECOMP_RATDB = 'static/CoreComps.ratdb'
NUSPEC_RATDB = 'static/NuSpectraConsts.ratdb'

REACTOR_STATUS_VERSION = 1
MAX_CORES_IN_US_REACTORS = 4

#-----------UTILITY FUNCTIONS FOR BUILDING A RATDB CLASS------------------#
def USListToRATDBFormat(AllReactors):
    """
    Takes in a list of reactor names (as formatted on NRC.gov) and
    converts the names to name format found in REACTORS.ratdb in db/static.
    """
    AllReacRATDBFormat = []
    for ReacName in AllReactors:
        ReacName = ReacName.rstrip('1234567890 ')
        if ReacName == 'D.C. Cook':
            ReacName = ReacName.replace('D.C. ','')
        if ReacName == 'Davis-Besse':
            ReacName = ReacName.replace('-',' ')
        if ReacName == 'La Salle':
            ReacName = ReacName.replace(" ","")
        if ReacName == 'Columbia Generating Station':
            ReacName = ReacName.replace(" Generating Station","")
        if ReacName == 'Arkansas Nuclear':
            ReacName = 'ANO'
        if ReacName == 'Saint Lucie':
            ReacName = ReacName.replace("Saint","st.")
        AllReacRATDBFormat.append(ReacName.upper())
    AllReacRATDBFormat=list(set(AllReacRATDBFormat)) #Removes duplicate entries
    return AllReacRATDBFormat
#-----------END UTILITY FUNCTIONS----------------#



#Class is defined with a RATDB database file, RDB type, and RDB index. grabs the basic
#filename input is where a completed RATDB dictionary will be saved.
#rdbtype is the "type" entryin the RATDB dictionary
#index is the "index" entry in the RATDB dictionary
class ratdbBuilder(object):
    def __init__(self,filename,rdbtype,index):
        self.rdb_type = rdbtype
        self.version = ''
        self.index = index
        self.run_range = []
        self.passing = ''
        self.comment = ''
        self.timestamp = ''
        self.ratdb_dict = {}
        self.ratdbpath = os.path.abspath(os.path.join(dbpath, filename))

    def show(self):
        print("type: " + self.rdb_type)
        print("version: " + str(self.version))
        print("index: " + self.index)
        print("run range: " + str(self.run_range))
        print("pass: " + str(self.passing))
        print("comments: " + self.comment)
        print("timestamp: " + self.timestamp)



    def buildratdbEntry(self):
        """
        Fills in self.reacdb_entry with the standard RATDB entry values."
        """
        stdratdict = {"type": self.rdb_type, "version": self.version, "index": self.index,
        "run_range": self.run_range, "pass": self.passing, "comment": self.comment,
        "timestamp": self.timestamp}
        readytobuild = True
        for key in stdratdict:
            if stdratdict[key] == '':
                print("One or more entries were not filled in for the ratdb entry." + \
                "reacdb_entry not built.")
                readytobuild = False
        if readytobuild:
            self.reacdb_entry = stdratdict
            print("Standard RATDB entry values filled in.  Please add miscillaneous " + \
            "information before pushing to ReacDB.")
    def pushToFile(self):
        print("This is where we will add all entries to the file")


#Subclass uses RIgrabber to get a day's power output from the NRC webpage and
#build a ratdb entry with similar structure to the REACTOR_STATUS entry by nuno.
#NRC_Name should be input as a reactor's name as seen on the NRC Power Reactors List.
#FIXME: Need to convert date to timestamp and run range still.  Still need to
#Address if I should have the core_comp or spectrum for the day in here.
class StatusBuilder(ratdbBuilder):
    def __init__(self,NRC_Format_ReacName,date):
        self.rdb_type = "REACTOR_STATUS"
        self.filename = "TESTING.ratdb"
        self.NRC_Name = NRC_Format_ReacName
        super(StatusBuilder, self).__init__(self.filename, self.rdb_type, self.RATDBIndex())
        self.version = REACTOR_STATUS_VERSION
        self.date = date
        self.day_poweroutput = []
        self.no_cores = "unknown"
        self.licensed_core_powers = []
        self.eff_core_powers = []
        self.core_spectrums = []
        #Methods run at init to fill in ratdb entries
        self.getLicensedMWts()
        self.getPowerCapacities()

    def show(self):
        print("{")
        super(StatusBuilder,self).show() #performs the parent method show()
        print("no_cores: " + str(self.no_cores))
        print("licensed_core_powers: " + str(self.licensed_core_powers))
        print("day_poweroutput:" + str(self.day_poweroutput))
        print("}")
        print("Date relevant to staus entry: " + str(self.date))

    def setTimestamp(self):
        """
        converts the date given to a timestamp associated with that date's
        time at midnight EST.  Need to get the right timestamp libraries.
        """
        #eastern_tz = pytz.timezone("America/Toronto")
        #snotime = datetime.datetime.strptime(self.date, "%m/%d/%Y")
        #sno_dt = eastern_tz.localize(
        
    def setRunRange(self):
        """
        Takes the entry's timestamp and finds all SNO+ runs that fit into the
        time between the entered timestamp and the timestamp + 1 day.
        going to want to get runs from snopl.us/runs/ or the database the
        webpage is filled from
        """

    def getLicensedMWts(self):
        """
        Get the licensed thermal core outputs from the NRC webpage.
        Uses the NRCClaws sublass in RIgrabber.py to get the Core Powers
        """
        Core_names_withnums = []
        #single core reactors have no number on NRC webpage
        Core_names_withnums.append(self.NRC_Name)
        #Multiple cores listed on NRC webpage as Reactor's name + core numbmer
        i = 0
        while i < MAX_CORES_IN_US_REACTORS:
            Core_names_withnums.append(self.NRC_Name + " " + str(i))
            i+=1
        for corename in Core_names_withnums:
            Static_Info = rig.NRCclaws(corename)
            Static_Info.scrapeTypeAndMWt()
            if Static_Info.MWt != 'none':
                self.licensed_core_powers.append(Static_Info.MWt)

    def calculateEffMwts(self):
        """
        Scale the licensed MWts by the day's reported power output
        """

        StaticInfo = ReactorSpecs(self.RATDBIndex())

        for i,entry in enumerate(day_poweroutput):
            print(" ")

    def RATDBIndex(self):
        index = self.NRC_Name
        if index == 'D.C. Cook':
            index = index.lstrip('D.C. ')
        if index == 'Davis-Besse':
            index = index.replace('-',' ')
        if index == 'La Salle':
            index = index.replace(" ","")
        index = index.upper()
        return index

    def getPowerCapacities(self):
        """
        Takes the date the subclass is initialized with and grabs the daily
        operating capacity from NRC.gov.
        """
        NRCDailyFile = gus.NRCDayList()
        NRCDailyFile.setDayReacStatuses(self.date)
        if NRCDailyFile.oneday_info == "none":
            return
        Reacs_onDate = NRCDailyFile.oneday_info['reactor_statuses']
        #Reacs_onDate is a list of dictionarys, each with the operational 
        #capacity for a US reactor on the date given
        numCores = 0
        for entry in Reacs_onDate:
            name = entry['reactor_name']
            if self.NRC_Name == name.rstrip('1234567890 '):
                numCores +=1 
                self.day_poweroutput.append(entry['power_capacity'])
        self.no_cores = numCores        

    def buildreacdbEntry(self):
        self.reacdb_entry["thermal_output (MW)"] = self.composition
        super(CoreComp, self).buildReacdbEntry()

if __name__ == '__main__':
    print('Still nothing in main loop yet')
