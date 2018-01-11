import numpy as np
import os.path
import sys

basepath = os.path.dirname(__file__)
posdbpath = os.path.abspath(os.path.join(basepath, "..", "db", "static", "ReacPos_corr.txt"))

REARTH = 6378137. #Radius of earth at sea level, In meters (Matching RAT)
F = 1./298.257223   #Flattening factor for WGS84 model

######## SNOLAB specific depth and position parameters ########
#SNOLAB_LONGLAT = [-81.1868, 46.4719]  #[longitude, latitude] according to Google Earth
SNODEPTH = (2070.-307.)/1000.   #Distance of SNOLAB underground, In km
SNOLAB_LONGLATALT = [-81.2014,46.4753,SNODEPTH]  #[longitude, latitude] according to RAT
##############################################################

def longlat2xyz_ECEF(longlatalt):
    #Function converts a [longitude,latitude,depth(km)] array to an X,Y,
    #and Z position on earth in meters. Default assumes position of SNOLAB.
    LS = (180./np.pi)*np.arctan(((1-F)**2)*np.tan((np.pi/180.)*longlatalt[1]))
    RS = np.sqrt((REARTH**2)/(1+(((1/((1-F)**2))-1)*(np.sin((np.pi/180.)*LS)**2))))
    X=((RS * np.cos((np.pi/180.)*LS)*np.cos((np.pi/180.)*longlatalt[0])) + \
            (longlatalt[2]*1000*np.cos((np.pi/180.)*longlatalt[1])* \
            np.cos((np.pi/180.)*longlatalt[0])))
    Y=((RS * np.cos((np.pi/180.)*LS)*np.sin((np.pi/180.)*longlatalt[0])) + \
            (longlatalt[2]*1000*np.cos((np.pi/180.)*longlatalt[1])* \
            np.sin((np.pi/180.)*longlatalt[0])))
    Z=((RS * np.sin((np.pi/180.)*LS)) + longlatalt[2]*1000*np.sin((np.pi/180.)*longlatalt[1]))
    return [X,Y,Z]

print("SNOLAB XYZ: " + str(longlat2xyz_ECEF(SNOLAB_LONGLATALT)))

def distance(longlatalt1,longlatalt2):
    """
    Function takes in a longitude, latitude, and altitude (formatted as
    as [longitude(deg),latitude(deg),altitude(km)]). returns distance
    from SNO+ in kilometers.
    The function first takes the location's longitude and latitude and
    converts to cartesian coordinates.  The distance between SNOLAB (which is
    ~2070 meters underground!) and the calculation result is returned.
    The X-axis is aligned with the Greenwich meridian and equator.
    The Y-axis is normal to the X-axis and in the equator plane.
    Tye Z-axis is aligned with the North and South Pole.
    """
    XYZ1 = longlat2xyz_ECEF(longlatalt1)
    XYZ2 = longlat2xyz_ECEF(longlatalt2)

    dist = np.sqrt(((XYZ1[0]-XYZ2[0])**2) + ((XYZ1[1]-XYZ2[1])**2) + ((XYZ1[2] - XYZ2[2])**2))
    #give the distance in kilometers; cut off decimals, as uncertainties definitely
    #are too large for meter resolution
    dist = (dist/1000.)
    #dist = round(dist, -1)  USE IN FUTURE TO ROUND TO THE TENS IN KM
    return dist

def distancefromSNOLAB(longlatalt):
    """
    Function takes in a longitude, latitude, and altitude (formatted as
    as [longitude(deg),latitude(deg),altitude(km)]). returns distance
    from SNO+ in kilometers.
    The function first takes the location's longitude and latitude and
    converts to cartesian coordinates.  The distance between SNOLAB (which is
    ~2070 meters underground!) and the calculation result is returned.
    The X-axis is aligned with the Greenwich meridian and equator.
    The Y-axis is normal to the X-axis and in the equator plane.
    Tye Z-axis is aligned with the North and South Pole.
    """
    XYZ1 = longlat2xyz_ECEF(SNOLAB_LONGLATALT)
    XYZ2 = longlat2xyz_ECEF(longlatalt2)

    dist = np.sqrt(((XYZ1[0]-XYZ2[0])**2) + ((XYZ1[1]-XYZ2[1])**2) + ((XYZ1[2] - XYZ2[2])**2))
    #give the distance in kilometers; cut off decimals, as uncertainties definitely
    #are too large for meter resolution
    dist = (dist/1000.)
    #dist = round(dist, -1)  USE IN FUTURE TO ROUND TO THE TENS IN KM
    return dist

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

if __name__ == '__main__':
    locationdict = parsecoord()
