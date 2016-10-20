#script to pull
from __future__ import print_function
import sys
import urllib2
import json, couchdb
import string, time, re

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
    daily reactor operating info, the output format of the getDayReactorInfo
    function should be pushed to reacdb.
    """
    dbStatus, db = connectToDB('reacdb')
    if dbStatus is 'ok':
        db.save(newentry)
        print("reacdb UPDATE: reactor info. added for date: " + newentry["date"])

def getNRCDailyList():
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
        if reactor[1] == 'Watts Bar 2':
            return reactor_list
        reactor_list.append(reactor)
    return reactor_list

def getAllReacDBDaily():
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

def getDayReactorInfo(date):
    """
    Takes in a date and returns (from the NRC webpage document)
    a dictionary with all power capacity information 
    available for each reactor on that day.
    Format of reacdict is ready for pushing to reacdb on couchDB.
    The webpage with daily power capacities can be found here:
    http://www.nrc.gov/reading-rm/doc-collections/event-status/reactor-status/PowerReactorStatusForLast365Days.txt
    """
    reacdict = {"date": date, "reactor_statuses": [], "type":"daily"}
    NRCreacs = getNRCDailyList()
    for reactor in NRCreacs:
        if reactor[0] == date:
            this_reactor = {"reactor_name": reactor[1], "power_capacity" : reactor[2]}
            reacdict["reactor_statuses"].append(this_reactor)
    return reacdict

def getMostRecentDailyEntry():
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

def updateDailyreacdb():
    """
    This function grabs the most recent Reactors file from nrc.gov and compares
    to all entries in the reacdb database.  If a date from the nrc text file
    is not in reacdb, the data for that date is added as a document to reacdb.
    """
    NRCcurrent = getNRCDailyList()
    reacdbcurrent, datesinreacdb = getAllReacDBDaily()
    testcount = 0
    for entry in NRCcurrent:
        date = entry[0]
        if date not in datesinreacdb:
            newentry = {}
            newentry = getDayReactorInfo(date)
            saveToreacdb(newentry)
            datesinreacdb.append(date)

def getReactorsInDateRange(reac_name,startdate,enddate):
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
                print(entry)
        except:
            print("Error in query attempt.  Could not get value.")
            entry = "none"
            print(entry)

if __name__ == "__main__":
    updateDailyreacdb()