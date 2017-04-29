#Functions here for fusing data together that's stored in the output directory.

import os.path
import numpy as np
import glob
import json

basepath=os.path.dirname(__file__)
datapath=os.path.abspath(os.path.join(basepath, "..","output"))

def getcontourlines(CL,numslices,data,origin):
    '''
    For a chosen origin, return an array which, when drawn in sequence, will
    give a contour containing CL% of the points in the data fed in.
    '''
    datx =  (np.array(data["sst"]) - origin[0])
    daty =  (np.array(data["dms"]) - origin[1])

    slicenum = 0
    theta = 0
    theta_last = 0
    #Find each point's angle relative to the +1 x-axis.
    xaxis = np.array([1,0])
    datapts = np.column_stack((datx,daty))

    #TRY SCALING BY THE MAGNITUDES TO BRING NUMBERS NEAR COS/SIN VALUES
    Acost = np.dot(xaxis,[datx,daty])   #Magnitude of data point times costheta
    print(Acost)
    Asint = np.cross(xaxis,datapts) * 10000#Magnitude of data point times sintheta
    print(Asint)
#    Angle = np.arctan2(Asint,Acost) #Angle of point from x-axis
    Angle = np.arctan2(daty, datx)
    CLLine_points = []
    points_in_slice = []  #Indices of points within datx,daty which lie within each slice
    while slicenum < numslices:
        theta += (np.pi * 2.) / float(numslices)
        print(theta)
        print(theta_last)
        #See if the theta of each point is between the current theta and last theta
        this_slices_xpts = datx[np.where((theta_last<Angle) & (Angle<=theta))[0]]
        this_slices_ypts = daty[np.where((theta_last<Angle) & (Angle<=theta))[0]]
        print(this_slices_xpts)
        print(len(this_slices_xpts))
        CLindex = int(float(len(this_slices_xpts)) * CL)
        print(CLindex)
        #CLLine_points.append([this_slices_xpts[CLindex],this_slices_ypts[CLindex]])
        slicenum+=1
        theta_last = theta
    return Angle#return CLLine_points


   
