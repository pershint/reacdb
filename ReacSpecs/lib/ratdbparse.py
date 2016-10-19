import numpy as np
import os.path
import sys

basepath = os.path.dirname(__file__)
ratdbpath = os.path.abspath(os.path.join(basepath, "..", "db", "REACTORS_corr.ratdb"))

Rearth = 6371000 #Radius of earth at sea level, In meters
DSNOLAB = 2070   #Distance of SNOLAB underground, In meters
SNOLAB_latlong = [-81.1868, 46.4719]  #[longitude, latitude] according to Google Earth
SNOLAB_XYZ = [672000,-4335000,4618000] #Calculated with the X,Y,Z calculator below

def getCAreacs():
    """
    Returns a list of the canadian reactor names in REACTORS.ratdb
    """
    CA_reacs = []
    f=open(ratdbpath, 'r')
    beginparse = False
    parsing = False
    while beginparse == False:
        stuff = str(f.readline())
        if stuff.find('C A N A D A') != -1:
            beginparse = True
            parsing = True
    while parsing == True:
        parseline = f.readline()
        if parseline.find('U S A') != -1:
            parsing = False
        line_pieces = parseline.split(":")
        if line_pieces[0] == 'index':
            CA_reacs.append(line_pieces[1].rstrip("\",\n").lstrip(" \""))
    return CA_reacs


def parseRATDB(reacname):
    """
    Opens the REACTORS.ratdb in the /ReacDB/db directory and grabs the
    relevant reactor information from the ratdb file. Information includes
    the reactor's licensed MWt, latitude and longitude, and reactor type
    (if available). Longitude and latitude are rounded to two decimal
    places for more conservative distance accuracy.
    """
    MWt = 'none'
    longlat = ['none', 'none']
    f=open(ratdbpath, 'r')
    beginparse = False
    parsing = False
    while beginparse == False:
        stuff = str(f.readline())
        if stuff.find(reacname) != -1:
            beginparse = True
            parsing = True
    while parsing == True:
        parseline = f.readline()
        if parseline == '':
            print("Reached the end of the data block or file. stopping")
            break
        line_pieces = parseline.split(":")
        if line_pieces[0] == 'power_therm':
            MWt = round(float(line_pieces[1].rstrip(",\n").lstrip()),1)
        elif line_pieces[0] == 'longitude':
            longlat[0] = round(float(line_pieces[1].rstrip(",\n").lstrip()),2)
        elif line_pieces[0] == 'latitude':
            longlat[1] = round(float(line_pieces[1].rstrip(",\n").lstrip()),2)
        if (MWt != 'none') and ('none' not in longlat):
            parsing = False
    print(MWt, longlat)
    return MWt, longlat

if __name__ == '__main__':
    names = getCAreacs()
