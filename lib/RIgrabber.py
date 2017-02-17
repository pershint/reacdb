#Functions for grabbing US reactor information from the NRC webpage and CA
#reactor information from /db/REACTORS_corr.ratdb. The class
#NRCClaws scrapes the NRC webpage for reactor information, bundles the data into
#dictionary format for pushing to couchDB, and pushes the information to the
#reacdb database.
#Class can be used to grab and enter individual reactors.  This must be done for
#the canadian reactor information found in db/REACTORS.ratdb. Running the script
#as main is a one-shot program that fills reacdb with all US reactors.

from __future__ import print_function
import sys
import urllib2
import SNOdist as sd
import getCAreacs as gca
import couch_utils.DButils as dbu
import rdbparse as rp
import json
import string, time, re
from bs4 import BeautifulSoup as bs

def getReacNames():
    """
    Connects to reacdb and gets the names of all reactors posted in the
    most recent database entry.  Returns the names in a list.
    """
    AllReactors = []
    dbStatus, db = dbu.connectToDB('reacdb')
    if dbStatus is "ok":
        queryresult = db.view("reacdb/daily",descending=True,limit=1)
        status_list = queryresult.rows[0].value["reactor_statuses"]
        for entries in status_list:
            #Entry in daily text file inconsistent with name on list page
            #treat specifically
            if entries['reactor_name'] == 'Harris 1':
                AllReactors.append('Shearon Harris 1')
            else:
                AllReactors.append(entries['reactor_name'])
    return AllReactors
        #for row in queryresult:
        #    print(row.value["reactor_statuses"][0]["reactor_name"])
        #Gives reactor nameat index 0... must be a cleaner way though

def saveToreacdb(newentry):
    """
    Function takes a dictionary and saves it to reacdb.  For pushes containing
    daily reactor operating info, the output format of the getDayReactorInfo
    function should be pushed to reacdb.
    """
    dbStatus, db = dbu.connectToDB('reacdb')
    if dbStatus is 'ok':
        db.save(newentry)


class claws:
    _dbtype = 'static'

    def __init__(self, reac_name):
        self.reac_name = reac_name
        self._match_dailytolist()
        self.MWt = 'unknown'
        self.reac_type = 'unknown'
        self.position = ['unknown','unknown']
        self.dist_from_SNOplus = 'unknown'
        self.significance = 'unknown'
        self.readytopush = False
        self.reacdb_entry = {}

    def _cutNameInteger(self):
        """
        Returns the reactor's name without the reactor # at the end.
        """
        shortname = "".join([i for i in self.reac_name if not i.isdigit()])
        shortname = shortname.rstrip()
        return shortname
    def _match_dailytolist(self):
        '''
        Some extra conditionals are put here.  Shearon Harris 1, La Salle 1
        and La Salle 2 are listed different on the daily page.  We change
        inputs from the daily page to look like the ones found on the list.
        '''
        if self.reac_name == 'LaSalle 1':
            self.reac_name = 'La Salle 1'
        elif self.reac_name == 'LaSalle 2':
            self.reac_name = 'La Salle 2'
        elif self.reac_name == 'Harris 1':
            self.reac_name = 'Shearon Harris 1'


    def showSpecs(self):
        """
        Prints each of the relevant reactor details needed for the
        reacdb.  
        """
        print("Reactor Name: " + self.reac_name)
        print("Reactor MWt: " + str(self.MWt))
        print("Reactor Type: " + self.reac_type)
        print("Reactor Position in degrees (longitude, latitude): " + str(self.position))
        print("Distance from SNO+ (km): " + str(self.dist_from_SNOplus))

    def getDist(self):
        """
        Uses the latlongparse library to calculate a reactor's distance
        from SNOLAB.
        """
        self.dist_from_SNOplus = sd.getDistFromSNOLAB(self.position)
 
    def calculateSignificance(self):
        """
        Takes the reactor's MWt and divides by the distance from SNO+ squared.
        Eventually, this can be normalized to the largest significance value
        (which should be one of the four main Canadian reactors).
        """
        try:
            self.significance = (self.MWt)/((self.dist_from_SNOplus)**2)
        except:
            print('Error calculating significance factor. check your' + \
            'distance and MWt factors are filled in properly.')


    def buildReacdbDoc(self):
        """
        Takes the values in your current claws and pushes them to reacdb.
        """
        staticdict = {"reactor_name": self.reac_name, "reactor_type": self.reac_type,
        "thermal_output (MWt)": self.MWt, "location (long,lat)": self.position,
        "distance_from_snoplus (km)": self.dist_from_SNOplus, "isotope_composition": [],
        "significance_factor": self.significance, "type": self._dbtype}
        #Some checks that you're not just pushing empty values to reacdb
        self.reacdb_entry = staticdict
        if (self.reac_type == 'unknown') or (self.MWt == 'unknown'):
            print("WARNING: Reactor Type and/or MWt could not be collected.  Document \
            is not ready to push to couchDB.")
        elif (self.position == ['unknown', 'unknown']) or (self.dist_from_SNOplus == 'unknown'):
            print("WARNING: Reactor position and distance from" + \
            'SNO+ Not filled in. Document is not ready to push to couchDB.')
        else:
            self.readytopush = True
            print("reacdb format dictionary built.  Call pushToDB to push document.")

    def pushToDB(self):
        dbu.saveToReacdb(self.reacdb_entry)

class RDBclaws(claws):
    def getRATDBReacInfo(self):
        """
        Grabs a reactor's MWt and [longitude,latitude] from the
        REACTORS.ratdb file in /ReacDB/db.
        We import from the rdbparse library to help get canadian
        Reactor information.
        """
        RATDBEntry = rp.ReactorSpecs(self.reac_name)
        RATDBEntry.fill()
        RATDBEntry.parseMisc()
        self.MWt, self.position = RATDBEntry.power_therm, RATDBEntry.longlat



class NRCclaws(claws):
    _homepage = 'http://www.nrc.gov'
    _listpgext = '/reactors/operating/list-power-reactor-units.html'

    def scrapeTypeAndMWt(self):
        """
        Grabs the desired data from NRC.gov given the provided reactor name.
        """
        listpage = urllib2.urlopen(self._homepage + self._listpgext)
        soup = bs(listpage, 'html.parser') #represents the listpage html
        reacloc = "none"
        for link in soup.find_all('a'):
            if (link.string == self.reac_name) or \
            (link.string == self.reac_name + " "):
                reacloc = link.get('href')
                break
        if reacloc is "none":
            print("Reactor name not found in list on NRC.GOV webpage." + \
            "Missing reactor: " + self.reac_name)
            reacloc = "none"
            self.reac_type = "none"
            self.MWt = "none"
        else:
            reacpage = urllib2.urlopen(self._homepage + reacloc)
            mainsoup = bs(reacpage, 'html.parser')
            #All information for the reactor is in a table object. grab them.
            gotmwt = False
            gottype = False
            for table in mainsoup.find_all('table'):
                if table.get('summary'):
                    for index, string in enumerate(table.strings):
                        if string == 'Reactor Type:' or string == 'Reactor Type: ':
                            self.reac_type = list(table.strings)[index+1]
                            gottype = True
                        if string == 'Licensed MWt:' or string == 'Licensed MWt: ':
                            self.MWt = list(table.strings)[index+1]
                            self.MWt = float(self.MWt.replace(",",""))
                            gotmwt = True
            if (gotmwt is False) or (gottype is False):
                print('Thermal power output or reactor type could not be' + \
                'scraped from nrc.gov.  Contact Teal for help with' + \
                'troubleshooting.')

    def getPos(self):
        """
        Uses the latlongparse library to update the reactor's latitude and
        longitude.  A particular core (Wolf Creek 1 == first core at wolf
        creek) is defined as being at the plant's location (AKA Wolf Creek,
        which is the shortname). parsecoord() gets position data from
        Vincent's DB file only.
        """
        reactor_posns = ll.parsecoord()
        shortname = self._cutNameInteger()
        self.position = reactor_posns[shortname]

if __name__ == '__main__':
    #Adds all static CA reactor info. to the static database
    CA_reacs = gca.getCAreacs()
    for reactorname in CA_reacs:
        caclaws = RDBclaws(reactorname)
        caclaws.getRATDBReacInfo()
        caclaws.reac_type = "CANDU"
        caclaws.getDist()
        caclaws.calculateSignificance()
        caclaws.buildReacdbDoc()
        if caclaws.readytopush:
            caclaws.pushToDB()

    #Adds all static US reactor info. to the static database
    USReactors = getReacNames()
    for reactorname in USReactors:
        usclaws = NRCclaws(reactorname)
        usclaws.scrapeTypeAndMWt()
        usclaws.getPos()
        usclaws.getDist()
        usclaws.calculateSignificance()
        usclaws.buildReacdbDoc()
        if usclaws.readytopush:
            usclaws.pushToDB()
