from __future__ import print_function
import sys
import urllib2
import string
import json, couchdb

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

def saveToReacdb(doc):
    dbStatus, db = connectToDB('reacdb')
    if dbStatus is "ok":
        try:
            db.save(doc)
        except:
            print("Error saving document to reacdb. Check your document's format.")

def delViewFromDB(dbname, viewname):
    dbStatus, db = connectToDB(dbname)
    if dbStatus is "ok":
        try:
            queryresult = db.view(dbname + '/' + viewname, descending=False)
            for row in queryresult:
                doc = db[row.id]
                db.delete(doc)
        except:
            print("Error deleting a document.  Check the given DB and View")
            print("names.")

def normalizeReacSig(reacname):
    """
    Normalizes all reactor significance values to that of the reactor name
    given.  The reactor name given is set to one.
    """
    normalizer = 'none'
    dbStatus, db = connectToDB('reacdb')
    if dbStatus is "ok":
        try:
            queryresult = db.view('reacdb/static', key=reacname, descending=False)
            for row in queryresult:
                doc = db[row.id]
                print("got here")
                print(doc["reactor_name"])
                normalizer = doc["significance_factor"]
        except:
            print("Error getting normalizing significance.  Check DB and view status")
        try:
            queryresult = db.view('reacdb/static', descending=False)
            for row in queryresult:
                doc = db[row.id]
                doc["significance_factor"] = (doc["significance_factor"]/normalizer)
                print(doc["significance_factor"])
                db.save(doc)
        except:
            print("Error re-normalizing significance factors.  Check DB/view status")


