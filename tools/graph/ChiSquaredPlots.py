from __future__ import print_function
import matplotlib.pyplot as plt
#from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import scipy as sp
import sys
import scipy.ndimage as ndimage

#Takes in an array of chi-squared test results and plots them as a function of the
#sine squared theta values used to get the results.  dms is fixed.
def chi2vssst(chi2_array,sst_array,oscParams):
    opacity = 0.9
    fig, ax = plt.subplots()
    #plt.gcf().subplots_adjust(bottom=0.2)
    plt.plot(sst_array, chi2_array, alpha=opacity, color='r')
    plt.xlabel('Sine-squared theta 12')
    plt.ylabel(r'chi-squared')
    plt.title(r'Chi-squared value between a statistically fluctuated SNO+' + \
            'spectrum (dms = {0}, sst={1}, and a non-fluctuated spectrum with' + \
            'dms={0} and the y-axis sst value.'.format(oscParams[0],oscParams[1]))
    #plt.xticks(index + bar_width, x, y=0.001)
    #plt.legend()
    #plt.tight_layout()  #could use instead of the subplots_adjust line
    plt.show()

def chi2contour(DeltaMSqs,sst12s,chisqs):
    opacity = 0.9
    fig = plt.figure()
    ax = fig.add_subplot(1,2,1)#,projection='2d')#3d')
    #ax.hexbin(sst12s,DeltaMSqs,chisqs)#,color='b',marker = 'o',alpha=opacity)
    #ax.plot_surface(sst12s, DeltaMSqs, chisqs)
    cont = ax.contourf(sst12s, DeltaMSqs, chisqs)
    #ax.annotate(r'$\sin^{2}(\theta _{12})$ =' + str(sst12) + '\n' + \
    #        r'$\Delta m^{2}_{21}$ = ' + str(m12), xy=(7,40), fontsize = '16', 
    #        xytext=(6.5,40))
    ax.set_xlabel('Sine-squared Theta 12')
    ax.set_ylabel(r'Delta M-Squared')
    ax.set_title(r'Chi-squared map of experiment')

    ax2= fig.add_subplot(1,2,2)
    Z2 = ndimage.gaussian_filter(chisqs, sigma=1.0, order=0)
    ax2.imshow(Z2)
    ax2.set_xlabel('Sine-squared Theta 12')
    ax2.set_ylabel(r'Delta M-Squared')
    ax2.set_title(r'Chi-squared map of experiment')
    fig.colorbar(cont,shrink=0.5, aspect=5)
    plt.show()

def chi2scatter(dms_arr, sst_arr,oscParamsSeed):
    '''
    Takes in an array of sine-squared theta values and delta-m squared values
    from performing a chi-squared minimization between the SNO+ event spectrum
    with oscillation parameters oscParamsSeed = [dms, sst] and the same spectrum
    with poisson fluctuations.
    '''
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot(sst_arr, dms_arr, 'ro', alpha=0.7, color='m', label='Best fits')
    ax.plot(oscParamsSeed[1], oscParamsSeed[0], '*', markersize=20, alpha=0.7, color='b', label = 'Seed values')
    ax.plot(np.average(sst_arr), np.average(dms_arr), '*', markersize=20, alpha=0.7, color='r', label = 'Fit average')
    ax.set_xlabel(r'$\sin^{2}(\theta_{12})$')
    ax.set_ylabel(r'$\Delta m^{2}_{12} (ev^{2})$')
    ax.set_title('Scatter plot of best-fit oscillation parameters')
    ax.grid(True)
    plt.show()

if __name__ == '__main__':
    print("SOME TESTS OF CHISQ GRAPH FUNCTIONS")
    x = np.arange(1,5,1)
    y = np.arange(1,5,1)
    chi2scatter(x,y)
    X,Y = np.meshgrid(x, y, sparse=False)
    z = np.sin(X**2 + Y**2) / (X**2 + Y**2)
    chi2contour(X,Y,z)

