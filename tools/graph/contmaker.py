#Functions here for fusing data together that's stored in the output directory.

import os.path
import numpy as np
import glob
import json

basepath=os.path.dirname(__file__)
datapath=os.path.abspath(os.path.join(basepath, "..","output"))

def poltocart(r,phi):
    x = r * np.cos(phi)
    y = r * np.sin(phi)
    return x,y

def getcontourlines(CL,numslices,data,origin):
    '''
    For a chosen origin, return an array which, when drawn in sequence, will
    give a contour containing CL% of the points in the data fed in.
    '''
    origx = np.array(data["sst"])
    origy = np.array(data["dms"])
    #You need the relative scales to be the same to make your regions
    scale = float(origin[0]/origin[1])*10
    circx =  np.array(origx - origin[0])
    circy =  np.array((origy - origin[1])*scale)
    slicenum = 0
    Angle = np.arctan2(circy, circx) #angle given in range[ -pi,pi]

    #Now, split the data into slices based on angle
    CLLine_sst = []
    CLLine_dms = []
    points_in_slice = []  #Indices of points within datx,daty which lie within each slice
    theta = -np.pi
    theta_last = -np.pi
    slice_angle = (np.pi * 2) / float(numslices)
    while slicenum < numslices:
        theta += slice_angle
        #See if the theta of each point is between the current theta and last theta
        this_slices_xpts = (circx[np.where((theta_last<Angle) & (Angle<=theta))[0]])
        this_slices_ypts = (circy[np.where((theta_last<Angle) & (Angle<=theta))[0]])
        #Now, find the distance from the origin for each point in the slice
        this_slices_mags = np.sqrt((this_slices_xpts)**2 + \
                (this_slices_ypts)**2)
        CLindex = int(float(len(this_slices_mags)) * CL)
        mags_mintomax = np.sort(this_slices_mags)
        #Take this magnitude and the current angle, go to cartesian, and
        #Add on the origin again
        sst, dms = poltocart(mags_mintomax[CLindex],(theta - \
                (slice_angle/2)))

        #now scale back...
        dms = dms/scale
        CLLine_sst.append(sst + origin[0])
        CLLine_dms.append(dms + origin[1])
        slicenum+=1
        theta_last = theta
    #Finally, add the first point to the end to make a closed loop
    CLLine_sst.append(CLLine_sst[0])
    CLLine_dms.append(CLLine_dms[0])
    return CLLine_sst,CLLine_dms


   
