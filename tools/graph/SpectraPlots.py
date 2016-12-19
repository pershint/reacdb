from __future__ import print_function
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import sys


def cumulSum(array):
    """
    Takes in an array of numbers and returns an array with the cumulative
    sum values.  Example: cumulSum([2,4,5,7])
    will return [7, 12, 16, 18].
    """
    array = np.sort(array)[::-1] #Sorts any array from low to high
    csarray = np.zeros(array.size)
    for i, val in enumerate(array):
        if i == 0:
            csarray[i] = val
        else:
           csarray[i] = csarray[i-1] + val
    print(csarray)
    return csarray

def normalizeArrMax(array):
    """
    Takes in any numpyarray and normalizes it's elements by the largest value.
    """
    largest = np.amax(array)
    for i,entry in enumerate(array):
        array[i] = entry/largest
    print(array)
    return array
        
def normalizeArrSum(array):
    """
    Takes in any numpy array and normalizes all elements by the sum of all values.
    """
    largest = np.sum(array)
    for i,entry in enumerate(array):
        array[i] = entry/largest
    print(array)
    return array

def dNdEPlot_pts(energies,numSpec,bin_left,bin_right,sst12,m12):
    num_points = len(energies)
    opacity = 0.9
    fix, ax = plt.subplots()
    plt.plot(energies,numSpec,'ro', alpha=opacity, color='b')
    plt.hlines(numSpec,bin_left,bin_right, color = 'b')
    ax.annotate(r'$\sin^{2}(\theta _{12})$ =' + str(sst12) + '\n' + \
            r'$\Delta m^{2}_{21}$ = ' + str(m12), xy=(7,40), fontsize = '16', 
            xytext=(6.5,40))
    plt.xlabel('Energy (MeV)')
    plt.ylabel(r'events/$10^{32}proton-years/MeV$')
    plt.title(r'SNO+ Neutrino Spectrum for all US and Canadian Reactors')
    plt.show()

def dNdEPlot_line(energies,numSpec,sst12,m12):
    num_points = len(energies)
    opacity = 0.9
    fix, ax = plt.subplots()
    plt.plot(energies,numSpec, alpha=opacity, color='m')
    plt.fill_between(energies, 1e-10, numSpec, facecolor ='magenta',alpha = 0.4)
    ax.annotate(r'$\sin^{2}(\theta _{12})$ =' + str(sst12) + '\n' + \
            r'$\Delta m^{2}_{21}$ = ' + str(m12), xy=(7,40), fontsize = '16', 
            xytext=(6.5,40))
    plt.xlabel('Energy (MeV)')
    plt.ylabel(r'events/$10^{32}proton-years/MeV$')
    plt.title(r'SNO+ Neutrino Spectrum for all US and Canadian Reactors')
    plt.show()

def CAspectrumPlot(energies,spectrum):
    '''
    Takes an array evaluated at energy points and plots them vs. energy.
    Specific to Canadian spectrum to have labels ready.
    '''
    num_points = len(energies)
    opacity = 0.9
    fig, ax = plt.subplots()
    #plt.gcf().subplots_adjust(bottom=0.2)
    plt.plot(energies, spectrum, alpha=opacity, color='b')
    plt.xlabel('Energy (MeV)')
    plt.ylabel(r'(Sum of Oscillated Spectra$m^{-2}$)')
    plt.title(r'Plot of oscillated neutrino spectrum at SNO+ for all' + \
            'Canadian plants')
    #plt.xticks(index + bar_width, x, y=0.001)
    #plt.legend()
    #plt.tight_layout()  #could use instead of the subplots_adjust line
    plt.show()


def plotSumOscSpectrum(OscSpectra):
    """
    Plots the "core_number"s spectrum in the passed in UnoscSpectra class using
    Matplotlib.pyplot.
    """
    num_points = len(OscSpectra.Summed_Spectra)
    spectrum = OscSpectra.Summed_Spectra
    energies = OscSpectra.E_arr
    opacity = 0.9
    fig, ax = plt.subplots()
    #plt.gcf().subplots_adjust(bottom=0.2)
    plt.plot(energies, spectrum, alpha=opacity, color='g')
    plt.xlabel('Energy (MeV)')
    plt.ylabel(r'(Sum of Oscillated Spectra$m^{-2}$)')
    plt.title(r'Plot of oscillated Core Spectrums for Plant ' +  \
            str(OscSpectra.ReacDetails.index) + ' at SNO+')
    #plt.xticks(index + bar_width, x, y=0.001)
    #plt.legend()
    #plt.tight_layout()  #could use instead of the subplots_adjust line
    plt.show()

def plotCoreOscSpectrum(core_number,OscSpectra):
    """
    Plots the "core_number"s spectrum in the passed in UnoscSpectra class using
    Matplotlib.pyplot.
    """
    num_points = len(OscSpectra.Osc_Spectra[core_number])
    spectrum = OscSpectra.Osc_Spectra[core_number]
    energies = OscSpectra.E_arr
    opacity = 0.9
    fig, ax = plt.subplots()
    #plt.gcf().subplots_adjust(bottom=0.2)
    plt.plot(energies, spectrum, alpha=opacity, color='g')
    plt.xlabel('Energy (MeV)')
    plt.ylabel(r'Unoscillated spectra ($m^{-2}$)')
    plt.title(r'Plot of oscillated Core Spectrum for the ' + str(core_number) + \
    r'th core of Plant ' + str(OscSpectra.ReacDetails.index) + ' at SNO+')
    #plt.xticks(index + bar_width, x, y=0.001)
    #plt.legend()
    #plt.tight_layout()  #could use instead of the subplots_adjust line
    plt.show()

def plotCoreUnoscSpectrum(core_number,UnoscSpectra):
    """
    Plots the "core_number"s spectrum in the passed in UnoscSpectra class using
    Matplotlib.pyplot.
    """
    num_points = len(UnoscSpectra.Unosc_Spectra[core_number])
    spectrum = UnoscSpectra.Unosc_Spectra[core_number]
    energies = UnoscSpectra.E_arr
    opacity = 0.9
    fig, ax = plt.subplots()
    #plt.gcf().subplots_adjust(bottom=0.2)
    plt.plot(energies, spectrum, alpha=opacity, color='g')
    plt.xlabel('Energy (MeV)')
    plt.ylabel(r'Unoscillated spectra ($m^{-2}$)')
    plt.title(r'Plot of Unoscillated Core Spectrum for the ' + str(core_number) + \
    r'th core of Plant ' + str(UnoscSpectra.ReacDetails.index) + ' at SNO+')
    #plt.xticks(index + bar_width, x, y=0.001)
    #plt.legend()
    #plt.tight_layout()  #could use instead of the subplots_adjust line
    plt.show()

if __name__ == '__main__':
    print("No main loop implemented.  It's just a library, get real.")
