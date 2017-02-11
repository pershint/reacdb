#File uses the rdbbuild library to construct and save JSON files that contain
#The dictionaries used to eventually construct RATDB format files.

import lib.rdbbuild as rb
import lib.GetNRCDailyInfo as gc
import os
import calendar, time
import logging, traceback
import sys

basepath = os.path.dirname(__file__)
dailypath = os.path.abspath(os.path.join(basepath,'db','daily','daily_updates'))
logpath = os.path.abspath(os.path.join(basepath,'log'))
LOGFILE = logpath + '/dailydb_update.log'

# ----- some basic logging to keep track of if database updates fail ------ #
logging.basicConfig(filename=LOGFILE, level=logging.INFO, \
        format='%(asctime)s %(message)s')
logging.info("INITIALIZING DAILY UPDATE FOR TODAY'S DATE")

def DayUpdateFail_handler(date,exec_info):
    logging.exception("For {} update in dailydb, update failed.".format(date))
    logging.exception("Uncaught exception: {0}".format(str(exec_info[1])))
    logging.exception("Error type: " + str(exec_info[0]))
    logging.exception("Traceback: " + str(traceback.format_tb(exec_info[2])))

def DateToUTC(date):
    """
    converts the date given to a timestamp associated with that date's
    time at midnight, UTC..  Date must be format 'mm/dd/yyyy'.
    """
    date += str(" 00:00:00 UTC")
    pattern = str("%m/%d/%Y %H:%M:%S %Z")
    timestamp = int(calendar.timegm(time.strptime(date, pattern)))
    return timestamp

       
def IsDuplicate(timestamp,datafiles):
    '''
    Checks the daily_updates directory in DB/daily to see if any json files
    have the same timestamp as is input
    '''
    print(datafiles)
    for f in datafiles:
        if str(timestamp) in f:
            print("Date at timestamp {} has already ".format(timestamp) + \
                    "been constructed previously.  Continuing to next date.")
            return True
    return False

if __name__ == '__main__':
    #get all files currently in the daily DB
    datafiles_inDB = [f for f in os.listdir(dailypath) if \
            os.path.isfile(os.path.join(dailypath, f))]

    #Get dates of all data currently available on NRC webpage
    current_NRCinfo = gc.NRCDayList()
    #Entry format for current_NRCAsList: [[date, core_name, day_powercap],...]
    current_NRCAsList = current_NRCinfo.getNRCCurrentList()
    current_NRCDates = []
    for entry in current_NRCAsList:
        current_NRCDates.append(entry[0])
    #get rid of duplicate dates to check for
    current_NRCDates = list(set(current_NRCDates))

    #
    for date in current_NRCDates:
        timestamp = DateToUTC(date)
        if not IsDuplicate(timestamp,datafiles_inDB):
            print("No power data for date {}. Saving to DB".format(date))
            try:
                NewPowerData = rb.StatusFileBuilder(current_NRCinfo,date)
                NewPowerData.buildPowerFileEntries()
                NewPowerData.save()
            except StandardError:
                #Something failed with with getting info for this date.
                #Log the error, but continue with other dates
                DayUpdateFail_handler(date,sys.exc_info())
                continue

