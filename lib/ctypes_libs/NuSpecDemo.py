#!/usr/bin/env python2
import sys
import numpy as np
import ctypes as ct
import matplotlib.pyplot as plt

#AN EXAMPLE OF HOW TO CALL/USE A FUNCTION WITH CTYPES
#Based on Morgan's muonhandfitter class methods
def dNdESmearer(spectrum, energy_array, resolution, binwidth):
    numpoints = len(spectrum)
    #call library you're going to use, and get the function from it
    libns = ct.CDLL('./libNuSpectrum.so')
    specsmearer= libns.convolveWER

    #Define the ctypes you will be feeding into the function
    pdub = ct.POINTER(ct.c_double)
    cint = ct.c_int
    cdub = ct.c_double
    specsmearer.argtypes = [pdub, pdub, cint, cdub]
    specsmearer.restype = pdub

    #cast inputs as numpy arrays (just in case they were a list)
    spec = np.array(spectrum)
    e_arr = np.array(energy_array)

    #use the np.array.ctypes function call to cast data as needed for ctypes
    spec_in = spec.ctypes.data_as(pdub)
    e_arr_in = e_arr.ctypes.data_as(pdub)

    #Allocate space for the function's output to be stored in
    indata = (ct.c_double * numpoints)()

    #actually run the function
    indata = specsmearer(spec_in,e_arr_in,numpoints,resolution)

    #go back to a python-usable numpy array
    smearedspec = np.array(np.fromiter(indata, dtype=np.float64, count=numpoints))
    return smearedspec

if __name__ == "__main__":
    binwidth= 0.01
    earr = np.arange(1.0,11.0,binwidth)
    spec = np.zeros(len(earr))
    spec[len(spec)/2] = 1.0
    res = 0.31
    outsmear = dNdESmearer(spec, earr, res, binwidth)
    outsmear = outsmear * binwidth
    print("SUM OF SMEAR: " + str( np.sum(outsmear)))
    plt.plot(outsmear)
    plt.show()
