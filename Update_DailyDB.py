#File uses the rdbbuild library to construct and save JSON files that contain
#The dictionaries used to eventually construct RATDB format files.

import lib.rdbbuild as rb
import lib.GetNRCDailyInfo as gc
import os

basepath = os.path.dirname(__file__)
dailypath = os.path.abspath(os.path.join(basepath,'db','daily','daily_updates')
        
def IsDuplicate(self,timestamp):
    '''
    Checks the daily_updates directory in DB/daily to see if any json files
    have the same timestamp as is input
    '''
    datafiles = [f for f in os.listdir(dailypath) if isfile(join(dailypath, f))]
    for f in datafiles:
        if timestamp in f:
            print("Date at timestamp {} has already ".format(timestamp) + \
                    "been constructed previously.  Continuing to next date.")
            return True
    return False

if __name__ == '__main__':
    
