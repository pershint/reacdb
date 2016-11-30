import numpy as np
import os.path
import sys

basepath = os.path.dirname(__file__)
posdbpath = os.path.abspath(os.path.join(basepath, "..", "db", "static", "ReacPos_corr.txt"))

Rearth = 6371000 #Radius of earth at sea level, In meters
DSNOLAB = 2070   #Distance of SNOLAB underground, In meters
SNOLAB_latlong = [-81.1868, 46.4719]  #[longitude, latitude] according to Google Earth
SNOLAB_XYZ = [672000,-4335000,4618000] #Calculated with the X,Y,Z calculator below


def parsecoord():
    """
    function for parsing out longitude and latitude values from Vincent's file.
    Returns a dictionary with the key as the place, and the value as [long, lat].
    """
    locationdict = {}
    f = open(posdbpath, 'r')
    beginparse = False
    while beginparse == False:
        stuff = str(f.readline())
        if stuff.find("United States") != -1:
            beginparse = True
    while True:
        parseline = f.readline()
        if parseline.find('END') != -1:
            break
        sline = parseline.split(",")
        try:
            sline[3] = sline[3].rstrip("\'")
            sline[3] = sline[3].lstrip("\'")
            locn = sline[1].split(" ")
            locn[0] = float(locn[0].lstrip('\'['))
            locn[1] = float(locn[1].rstrip(']\''))
            locationdict[sline[3]] = locn
        except:
            print("No data in line.  Continue.")
            continue
    return locationdict

def getDistFromSNOLAB(longlat):
    """
    Function takes in a longitude and latitude, and  list formatted
    as [longitude(deg),latitude(deg)], and returns the reactor name anddistance
    from SNO+ in kilometers.
    The function first takes the location's longitude and latitude and
    converts to cartesian coordinates.  The distance between SNOLAB (which is
    ~2070 meters underground!) and the calculation result is returned.
    The X-axis is aligned with the Greenwich meridian and equator.
    The Y-axis is normal to the X-axis and in the equator plane.
    Tye Z-axis is aligned with the North and South Pole.
    """

    X=(6371000-2070)*np.cos(((np.pi)*longlat[1])/180)*np.cos(((np.pi)*longlat[0])/180)
    Y=(6371000-2070)*np.cos(((np.pi)*longlat[1])/180)*np.sin(((np.pi)*longlat[0])/180)
    Z=(6371000-2070)*np.sin(((np.pi)*longlat[1])/180)
    print('Calculated cartesian coordinates: ' + str(X) + ',' + str(Y) + ',' + str(Z))
    dist = np.sqrt(((X-SNOLAB_XYZ[0])**2) + ((Y-SNOLAB_XYZ[1])**2) + ((Z-SNOLAB_XYZ[2])**2))
    #give the distance in kilometers; cut off decimals, as uncertainties definitely
    #are too large for meter resolution
    dist = int(dist/1000)
    #dist = round(dist, -1)  USE IN FUTURE TO ROUND TO THE TENS IN KM
    print('Calculated distance from SNOLAB: ' + str(dist) + 'km')
    return dist

if __name__ == '__main__':
    locationdict = parsecoord()
