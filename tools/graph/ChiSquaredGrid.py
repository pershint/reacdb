from __future__ import print_function
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import scipy as sp
import sys

def chi2grid(DeltaMSqs,sst12s,chisqs):
    opacity = 0.9
    fig = plt.figure()
    ax = fig.add_subplot(111,projection='3d')
    plt.hexbin(sst12s,DeltaMSqs,chisqs)#,color='b',marker = 'o',alpha=opacity)
    #ax.annotate(r'$\sin^{2}(\theta _{12})$ =' + str(sst12) + '\n' + \
    #        r'$\Delta m^{2}_{21}$ = ' + str(m12), xy=(7,40), fontsize = '16', 
    #        xytext=(6.5,40))
    plt.xlabel('Sine-squared Theta 12')
    plt.ylabel(r'Delta M-Squared')
    plt.title(r'Chi-squared map of experiment')
    plt.show()

if __name__ == '__main__':
    print("No main loop implemented.  It's just a library, get real.")
