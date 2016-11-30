#script to pull
from __future__ import print_function
import sys
import urllib2
import json, couchdb
import string, time, re

#---------- UTILITIES FOR USE WITH COUCHDB ---------------#
couch = couchdb.Server()

def connectToDB(dbName):
    status = "ok"
    db = {}
    try:
        db = couch[dbName]
    except:
        print("Failed to connect to " + dbName, file = sys.stderr)
        status = "bad"
    return status, db

def saveToreacdb(newentry):
    """
    Function takes a dictionary and saves it to reacdb.  For pushes containing
    daily reactor operating info, the output format of the getDateReactorStatuses
    function should be pushed to reacdb.
    """
    dbStatus, db = connectToDB('reacdb')
    if dbStatus is 'ok':
        db.save(newentry)
        print("reacdb UPDATE: reactor info. added for date: " + newentry["date"])
#----------- END COUCHDB UTILITIES ----------------#

class NRCDayList(object):
    def __init__(self):
        self.NRCCurrent = self.getNRCCurrentList()
        self.date_info = {}
        self.date_reacs = []

    def show(self):
        """
        Shows the dictionary that has the chosen date's power reactor status info for
        all US reactors from the NRC page.
        """
        print(self.date_info)

    def fillDateNames(self):
        """
        Gets only the reactor names from the oneday_info dictionary and
        returns them as a list.
        """
        reactornames = []
        for reactor in self.date_info["reactor_statuses"]:
            reactornames.append(reactor["reactor_name"])
        self.date_reacs = reactornames

    def getNRCCurrentList(self):
        """
        Gets all of the entries from the current NRC daily textfile and
        Returns them in a list.
        The format for each element of reactor_list is as follows:
        [date,reactor_name,day_power_capacity]
        The webpage with daily power capacities can be found here:
        http://www.nrc.gov/reading-rm/doc-collections/event-status/reactor-status/PowerReactorStatusForLast365Days.txt
        """
        reactor_list = []
        f = urllib2.urlopen('http://www.nrc.gov/reading-rm/doc-collections/event-status/reactor-status/PowerReactorStatusForLast365Days.txt')
        f.next()
        for line in f:
            clean=str.rstrip(line,"\r\n")
            reactor = str.split(clean,"|")
            reactor_list.append(reactor)
        return reactor_list

    def getDateReacStatuses(self,date):
        """
        Takes in a date and returns (from the NRC webpage document)
        a dictionary with all power capacity information 
        available for each reactor on that day.
        Information is pulled from the self.NRCCurrent list.
        """

        if date == 'none':
            print("No date chosen to get info. for.  Set date of interest using " + \
                    "the command className.setReacStatusDate(\'mm\dd\yyyy\')")
            self.date_info = "none"
        else:
            reacdict = {"date": date, "reactor_statuses": [], "type":"daily"}
            for reactor in self.NRCCurrent:
                if reactor[0] == date:
                    this_reactor = {"reactor_name": reactor[1], "power_capacity" : reactor[2]}
                    reacdict["reactor_statuses"].append(this_reactor)
            if not reacdict["reactor_statuses"]:
                print("Given date was not found in the NRC list.  Set another" + \
                        "date using \' className.setReacStatusDate(\'mm\dd\yyyy\')");
                self.date_info = "none"
            else:
                self.date_info = reacdict
    

#Class takes in an NRCDayList class and uses the class to add reactor information to
#the ReacDB couchDB.
class NRCDailyClaws(object):
    def __init__(self,NRCDayList):
        self.NRCDayList = NRCDayList
        self.docsindb, self.datesindb = self.getAllReacDBDaily()

    # ----------- BEGIN METHODS FOR couch/ReacDB INTERFACING ----------#
    def getAllReacDBDaily(self):
        """
        Polls the reactor database and grabs all entries from the "daily" view.
        """
        dbStatus, db = connectToDB("reacdb")
        alldocs = []
        alldates = []
        if dbStatus is "ok":
            try:
                queryresult = db.view("reacdb/daily",descending=False)
                for row in queryresult:
                    doc = db[row.id]
                    alldocs.append(doc)
                    alldates.append(doc["date"])
            except:
                print("Error in query attempt.  Could not get all daily entries.")
        return alldocs, alldates
    	
    def getMostRecentDailyEntry(self):
        """
        Polls the reactor database and grabs the most recent database entry
        from reacdb.
        """
        dbStatus, db = connectToDB("reacdb")
        if dbStatus is "ok":
            try:
                queryresult = db.view("reacdb/daily",descending=False,limit=1)
                for row in queryresult:
                    doc = db[row.id]
            except:
                print("Error in query attempt.  Could not get most recent daily entry.")
                doc = "none"
        return doc
    
    def updateDailyreacdb(self):
        """
        This function grabs the most recent Reactors file from nrc.gov and compares
        to all entries in the reacdb database.  If a date from the nrc text file
        is not in reacdb, the data for that date is added as a document to reacdb.
        """
        for entry in self.NRCDayList.NRCCurrent:
            date = entry[0]
            if date not in self.datesindb:
                newentry = {}
                newentry = self.NRCDayList.getDateReacStatuses(date)
                saveToreacdb(newentry)
                self.datesindb.append(date)
    
    def getReactorsInDateRange(self,reac_name,startdate,enddate):
        """
        Prints the power capacity information for a reactor between
        two specified dates.  The earlier date must be supplied as
        the startdate variable.  Dates must be of format "MM/DD/YYYY".
        """
        dbStatus, db = connectToDB("reacdb")
        if dbStatus is "ok":
            try:
                queryresults = db.view("reacdb/daily",startkey=startdate,endkey=enddate,descending=False,limit=4)
                for row in queryresults:
                    doc = db[row.id]
                    entry = doc["reactor_statuses"]
            except:
                print("Error in query attempt.  Could not get value.")
                entry = "none"
   
if __name__ == "__main__":
    TodaysList = NRCDayList()
    ReacDB_Updater = NRCDailyClaws(TodaysList)
    ReacDB_Updater.updateDailyreacdb()
