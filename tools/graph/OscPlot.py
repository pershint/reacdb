from __future__ import print_function
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import sys


#Takes in an oscillated spectra class and uses the Pee method to plot the
#electron antineutrino survival probablilty as a functon of energy at the
#Distance for the "core_number"th core.
def plotCoreSurvivalProb(core_number,OscSpectra):
    num_points = len(OscSpectra.E_arr)
    L = OscSpectra.Core_Distances[core_number]
    energies = OscSpectra.E_arr
    Pee_arr = []
    for E in energies:
        Pee_arr.append(OscSpectra.Pee(E,L))
    opacity = 0.9
    fig, ax = plt.subplots()
    #plt.gcf().subplots_adjust(bottom=0.2)
    plt.plot(energies, Pee_arr, alpha=opacity, color='r')
    plt.xlabel('Energy (MeV)')
    plt.ylabel(r'Survival Probability')
    plt.title(r'Survival probability of \nu_{e} from ' + str(core_number) + \
    r'th core of Plant ' + str(OscSpectra.ReacDetails.index) + ' at SNO+')
    #plt.xticks(index + bar_width, x, y=0.001)
    #plt.legend()
    #plt.tight_layout()  #could use instead of the subplots_adjust line
    plt.show()

if __name__ == '__main__':
    print("No main loop implemented.  It's just a library, get real.")
