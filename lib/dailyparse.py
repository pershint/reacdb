#Library provides classes for loading JSON files from the db/daily/daily_updates
#directory.  These JSON files contain power information from NRC.gov webpage for
#each core

import calendar, time
import numpy as np
import json
import os.path
import sys
import glob

basepath = os.path.dirname(__file__)
dbpath = os.path.abspath(os.path.join(basepath, "..", "db"))
dailypath = os.path.abspath(os.path.join(dbpath,"daily","daily_updates"))

def getAllEntriesInDailyUpdates(ReacName):
    '''
    Returns all entries available for a reactor in the daily_updates database.
    '''

    filenames = glob.glob(dailypath + '/*.json')
    numdays = int(len(filenames))
    onereac_alldailyentries = []
    for name in filenames:
        with open(name,'r') as f:
            entry = json.load(f)
            try:
                reacentry = entry[ReacName]
                onereac_alldailyentries.append(reacentry)
            except KeyError:
                print("No data for {0} plant in filename ".format(ReacName) + \
                        "{0}. Continuing to other days".format(name))
                continue
    return numdays, onereac_alldailyentries

def load_day(timestamp):
    try:
        infile = open("{0}/USDAILYPOWERS_{1}.json".format(dailypath,timestamp, 'r'))
    except IOError:
        print("No daily information available for timestamp {}".format(timestamp))
        return None
    day_data = json.load(infile)
    return day_data

def power_onday(timestamp,reacname):
    day_data = load_day(timestamp)
    return day_data[reacname]

if __name__ == '__main__':
    ANO_entry = power_onday(1473120000,"ANO")
    print(ANO_entry)

