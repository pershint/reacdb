#Program takes in a spectrum and information on the binning.  The code
#Then plays darts, picking random numbers on the spectrum's defined
#region.  If the number shot is below the spectrum, Store it in an array as
#an event.  When the number of events requested is collected, build the
#Experiment's histogram.

import numpy as np

def RandShoot(mu, sigma,n):
    '''
    Returns an array of n numbers from a gaussian distribution of
    average mu and variance sigma.
    '''
    return mu + sigma * np.random.randn(n)

def playDarts(n,spectrum,bin_left,bin_right,bin_center):
    '''
    Takes in a spectrum and the dimensions of the bins for each
    spectrum entry.  Returns a new spectrum with n entries as
    picked with random x and y value shots; if y>spectrum for the
    considered bin, the event is added to the new spectrum.
    '''
    events = 0
    exp_spectrum = np.zeros(len(spectrum))
    while events < n:
        x = bin_left[0] + np.random.random(1)*(bin_right[len(bin_right)-1] - \
                bin_left[0])
        y = np.random.random(1)*(np.max(spectrum))
        for i,thebin in enumerate(bin_left):
            if x > bin_left[i] and x < bin_right[i]:
                if y < spectrum[i]:
                    exp_spectrum[i] += 1
                    events +=1
                    break
                else:
                    break
    return exp_spectrum

def arr_average(arrays):
    '''
    Takes in an array of arrays.  Calculates the average and standard deviation
    for each index.  Returns them as arrays.
    '''
    average = np.sum(arrays,axis=0)
    stdevs = np.std(arrays,axis=0)
    return average, stdevs
