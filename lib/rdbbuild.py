#Various classes for building RATDB entries and saving the entry
#into a text file.

import calendar, time
import RIgrabber as rig
import GetNRCDailyInfo as gus
import numpy as np
import json
import os.path
import sys

basepath = os.path.dirname(__file__)
dbpath = os.path.abspath(os.path.join(basepath, "..", "db"))

DAILYSTATUS_LOC = 'daily/daily_updates'

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

def USToRATDBFormat(ReacName):
    """
    Takes in a reactor name (as formatted on NRC.gov) and
    converts the name to the format found in REACTORS.ratdb in db/static.
    """
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
    return ReacName
#-----------END UTILITY FUNCTIONS----------------#



#Class is defined with a RATDB database file, RDB type, and RDB index. grabs the basic
#filename input is where a completed RATDB dictionary will be saved.
#rdbtype is the "type" entryin the RATDB dictionary
#index is the "index" entry in the RATDB dictionary
class ratdbBuilder(object):
    def __init__(self,rdbtype,index):
        self.rdb_type = rdbtype
        self.version = ''
        self.index = index
        self.run_range = []
        self.passing = 0
        self.comment = ''
        self.timestamp = ''
        self.ratdb_dict = {}

    def show(self):
        print("type: " + self.rdb_type)
        print("version: " + str(self.version))
        print("index: " + self.index)
        print("run range: " + str(self.run_range))
        print("pass: " + str(self.passing))
        print("comments: " + self.comment)
        print("timestamp: " + str(self.timestamp))



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
                print("WARNING: Entry {0} is not filled in ".format(key) + \
                "for this RATDB entry.")
        self.reacdb_entry = stdratdict


#Class is one REACTOR_STATUS entry that will compose a full StatusFileBuilder
#result.
#FIXME: Need the NRC format core name to get the licensed_core_powers from the
#NRC webpage
class reactorStatus(ratdbBuilder):
    def __init__(self,core_name_RDB,date):
        self.RATDBIndex = core_name_RDB
        self.rdb_type = "REACTOR_STATUS"
        self.date = date
        super(reactorStatus, self).__init__(self.rdb_type, self.RATDBIndex)
        self.version = REACTOR_STATUS_VERSION
        self.licensed_core_powers = []
        self.core_powercaps = []   #Capacity cores were running at for the day
        self.num_cores = 0
        self.setTimestamp()


    def setTimestamp(self):
        """
        converts the date given to a timestamp associated with that date's
        time at midnight, UTC..  Need to get the right timestamp libraries.
        """
        self.date += str(" 00:00:00 UTC")
        pattern = str("%m/%d/%Y %H:%M:%S %Z")
        timestamp = int(calendar.timegm(time.strptime(self.date, pattern)))
        self.timestamp = timestamp

    def setRunRange(self):
        """
        Takes the entry's timestamp and finds all SNO+ runs that fit into the
        time between the entered timestamp and the timestamp + 1 day.
        going to want to get runs from snopl.us/runs/ or the database the
        webpage is filled from
        """
        print("CURRENTLY NOT IMPLEMENTED.")
   
    def show(self):
        print("{")
        super(reactorStatus,self).show() #performs the parent method show()
        print("no_cores: " + str(self.num_cores))
        print("licensed_core_powers: " + str(self.licensed_core_powers))
        print("day_poweroutput:" + str(self.core_powercaps))
        print("}")
        print("Date relevant to status entry: " + str(self.date))


#Subclass takes in an NRCDayList and creates a .ratdb file that has each
#Reactor's day information in it.  For each date, a different .ratdb file will
#be written.
class StatusFileBuilder(object):
    def __init__(self,NRCDayList,date):
        self.filename = "TESTING" #needs timestamp and .ratdb appended
        self.NRCDayList= NRCDayList
        self.date = date
        self.timestamp = 'none'
        self.setTimestamp()
        self.filename += str("_{}.ratdb".format(self.timestamp))
        self.savepath = os.path.abspath(os.path.join(dbpath, \
                DAILYSTATUS_LOC,self.filename))

        self.entries = {}
        #Methods run at init to fill in ratdb entries

    def setTimestamp(self):
        """
        converts the date given to a timestamp associated with that date's
        time at midnight, UTC..  Need to get the right timestamp libraries.
        """
        fulldate = self.date + str(" 00:00:00 UTC")
        pattern = str("%m/%d/%Y %H:%M:%S %Z")
        timestamp = int(calendar.timegm(time.strptime(fulldate, pattern)))
        self.timestamp = timestamp

    def buildStatusFileEntries(self):
        """
        Takes the date the subclass is initialized with and grabs the daily
        operating capacity from NRC.gov.
        """
        self.NRCDayList.setDateReacStatuses(self.date)
        if self.NRCDayList.date_info == "none":
            return
        Reacs_onDate = self.NRCDayList.date_info['reactor_statuses']
        #Reacs_onDate is a list of dictionarys, each with the operational 
        #capacity for a US reactor on the date given

        #Now, build each reactor plant's REACTOR_STATUS entry
        for entry in Reacs_onDate:
            #Get the name of the plant this core is associated with
            core_name = entry['reactor_name']
            core_MWt = self.getLicensedMWt(core_name)
            core_powercap = entry['power_capacity']
            core_name_RDB=USToRATDBFormat(core_name)
            if core_name_RDB not in self.entries:
                #Make a new addition to our array of RATDB entries
                PlantStatus = reactorStatus(core_name_RDB,self.date)
                PlantStatus.core_powercaps.append(core_powercap)
                PlantStatus.licensed_core_powers.append(core_MWt)
                PlantStatus.num_cores += 1
                self.entries[PlantStatus.index] = PlantStatus
            else:
                #Add information on this core to it's present plant
                self.entries[core_name_RDB].num_cores += 1
                self.entries[core_name_RDB].core_powercaps.append(core_powercap)
                self.entries[core_name_RDB].licensed_core_powers.append(core_MWt)
        
        #Use filled entries to make the dictionary of each PlantStatus entry
        for reactor in self.entries:
            self.entries[reactor].buildratdbEntry()

    #FIXME: This is a biiiig bottleneck on time.  Have to connect to get every
    #Licensed MWt.  Could have this be a yearly get?
    def getLicensedMWt(self,core_name):
        """
        Get the licensed thermal core outputs from the NRC webpage.
        Uses the NRCClaws sublass in RIgrabber.py to get the Core Powers
        """
        Static_Info = rig.NRCclaws(core_name)
        Static_Info.scrapeTypeAndMWt()
        if Static_Info.MWt != 'none':
            return Static_Info.MWt

    #FIXME: The data here is a dictionary with the PlantStatus classes.  We really
    #want this as a dictionary where the key is the reactor index and the value is
    #the ratdb entry dictionary.
    def save(self):
        '''
        dumps all RATDB entries stored in reactor_status_entries to a .ratdb
        file at the specified save location.
        '''
        data = self.entries
        with open(self.savepath,'w') as outfile:
            json.dump(data,outfile, sort_keys = True, indent = 0)

if __name__ == '__main__':
    print('Still nothing in main loop yet')
