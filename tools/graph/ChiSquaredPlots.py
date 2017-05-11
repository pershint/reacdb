from __future__ import print_function
import matplotlib.pyplot as plt
#from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import scipy as sp
import sys
import scipy.ndimage as ndimage
import scipy.interpolate as si
import contmaker as cm

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

def chi2CLs(data1):
    '''
    Takes in a data set, plots the delta m-squared and sine-squared
    theta values, and plots their 68.3% and 90% CLs on the same plot.
    The CLs are calculated in slices and the region between each point is
    interpolated.
    '''
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
#    ax.plot(data1['sst'], data1['dms'], 'ro', alpha=0.7, color='b', \
#            label='Best fits, universe is' + data1['Params'],zorder=1)
    if data1['Params'] == 'KAMLAND':
        ax.plot(0.316,7.54E-05, '*', markersize=20, alpha=0.7, color='w', markeredgecolor='b', label = 'KL Values')
    avgsst = np.average(data1['sst'])
    avgdms = np.average(data1['dms'])
    ax.plot(avgsst, avgdms, '*', markersize=20, alpha=0.7, color='r', label = 'Mean of fits',zorder=2)
    CL68_sst,CL68_dms = cm.getcontourlines(0.683,120,data1,[avgsst,avgdms])
    CL90_sst,CL90_dms = cm.getcontourlines(0.90,120,data1,[avgsst,avgdms])
    #tsk = si.splprep(68CL_sst,68CL_dms,s=0)
    ax.plot(CL68_sst, CL68_dms, color='blue', label = '68.3% CL')
    ax.plot(CL90_sst, CL90_dms, color='purple', label = '90% CL')
    ax.set_xlim(0.20,0.55)
    ax.set_ylim(0.000055,0.000090)
    ax.set_xlabel(r'$\sin^{2}(\theta_{12})$')
    ax.set_ylabel(r'$\Delta m^{2}_{12} (ev^{2})$')
    ax.set_title('Scatter plot of best-fit oscillation parameters')
    ax.grid(True)
    box = ax.get_position()
    #shrink the graph a bit so the legend fits
    ax.set_position([box.x0,box.y0,box.width*0.75, box.height])
    plt.legend(loc = 'center left', bbox_to_anchor=(1,0.5))
    plt.show()

def chi2scatter(data1):
    '''
    Takes in a data set, plots the delta m-squared and sine-squared
    theta values, and plots them along with their density contours.
    '''
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot(data1['sst'], data1['dms'], 'ro', alpha=0.7, color='b', \
            label='Best fits, universe is' + data1['Params'],zorder=1)
    if data1['Params'] == 'KAMLAND':
        ax.plot(0.316,7.54E-05, '*', markersize=20, alpha=0.7, color='w', markeredgecolor='b', label = '(1): KL parameters')
    #Now, plot a density contour on top
    hrange = [[0.20,0.50],[0.00002,0.0003]]
    H, xedges, yedges = np.histogram2d(data1['sst'],data1['dms'],range=hrange,bins=30)
    H=np.transpose(H)   #Zero point is at top right
    #xedges, yedges = np.meshgrid(xedges[:-1],yedges[:-1])
    extent = [0.20, 0.50, 0.00002, 0.0003] #xedges[0],xedges[-1],yedges[0],yedges[-1]]
    CT = ax.contour(H, extent=extent, origin="lower",linewidths=4,zorder=4)
    ax.plot(np.average(data1['sst']), np.average(data1['dms']), '*', markersize=20, alpha=0.7, color='r', label = 'Fit avg.',zorder=2)
    ax.plot(np.median(data1['sst']), np.median(data1['dms']), '*', markersize=20, alpha=0.7, color='k', label = 'median avg.',zorder=3)
    ax.set_xlim(0.20,0.50)
    ax.set_ylim(0.00002,0.00030)
    ax.set_xlabel(r'$\sin^{2}(\theta_{12})$')
    ax.set_ylabel(r'$\Delta m^{2}_{12} (ev^{2})$')
    ax.set_title('Scatter plot of best-fit oscillation parameters')
    ax.grid(True)
    box = ax.get_position()
    #shrink the graph a bit so the legend fits
    ax.set_position([box.x0,box.y0,box.width*0.75, box.height])
    plt.legend(loc = 'center left', bbox_to_anchor=(1,0.5))
    plt.colorbar(CT,shrink=0.8, extend='both')
    plt.show()

def chi2scatter_2sets(data1, data2,oscParamsSeed1,oscParamsSeed2):
    '''
    Takes in an array of sine-squared theta values and delta-m squared values
    from performing a chi-squared minimization between the SNO+ event spectrum
    with oscillation parameters oscParamsSeed = [dms, sst] and the same spectrum
    with poisson fluctuations.
    '''
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot(data1['sst_fits'], data1['dms_fits'], 'ro', alpha=0.7, color='b', label='Best fits to seed (1)')
    ax.plot(data2['sst_fits'], data2['dms_fits'], 'ro', alpha=0.7, color='g', label='Best fits to seed (2)')
    ax.plot(oscParamsSeed1[1], oscParamsSeed1[0], '*', markersize=20, alpha=0.7, color='w', markeredgecolor='b', label = '(1): KL parameters')
    ax.plot(oscParamsSeed2[1], oscParamsSeed2[0], '*', markersize=20, alpha=0.7, color='w', markeredgecolor='g', label = '(2): SK parameters')
    ax.plot(np.average(data1['sst_fits']), np.average(data1['dms_fits']), '*', markersize=20, alpha=0.7, color='r', label = 'Fit avg. seed (1)')
    ax.plot(np.average(data2['sst_fits']), np.average(data2['dms_fits']), '*', markersize=20, alpha=0.7, color='m', label = 'Fit avg. seed (2)')
    ax.set_xlim(0.20,0.50)
    ax.set_ylim(0.000045,0.000080)
    ax.set_xlabel(r'$\sin^{2}(\theta_{12})$')
    ax.set_ylabel(r'$\Delta m^{2}_{12} (ev^{2})$')
    ax.set_title('Scatter plot of best-fit oscillation parameters')
    ax.grid(True)
    box = ax.get_position()
    #shrink the graph a bit so the legend fits
    ax.set_position([box.x0,box.y0,box.width*0.75, box.height])
    plt.legend(loc = 'center left', bbox_to_anchor=(1,0.5))
    plt.show()

if __name__ == '__main__':
    print("SOME TESTS OF CHISQ GRAPH FUNCTIONS")
    x = np.arange(1,5,1)
    y = np.arange(1,5,1)
    chi2scatter(x,y)
    X,Y = np.meshgrid(x, y, sparse=False)
    z = np.sin(X**2 + Y**2) / (X**2 + Y**2)
    chi2contour(X,Y,z)

