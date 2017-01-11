#Program takes in a spectrum and information on the binning.  The code
#Then plays darts, picking random numbers on the spectrum's defined
#region.  If the number shot is below the spectrum, Store it in an array as
#an event.  When the number of events requested is collected, build the
#Experiment's histogram.

import numpy as np
import Histogram as h

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
    return np.array(exp_spectrum)

def playDarts_h(n,EventHist):
    '''
    Takes in an event histogram. Returns a new histogram with n events as
    picked with random x and y value shots; if y<EventHist.bin_value for the
    considered bin, the event is added to the new spectrum.
    '''
    events = 0
    exp_spectrum = np.zeros(len(EventHist.bin_values))
    while events < n:
        x = EventHist.bin_lefts[0] + np.random.random(1) * \
                (EventHist.bin_rights[len(EventHist.bin_rights)-1] - \
                EventHist.bin_lefts[0])
        y = np.random.random(1)*(np.max(EventHist.bin_values))
        for i,thebin in enumerate(EventHist.bin_lefts):
            if x > EventHist.bin_lefts[i] and x < EventHist.bin_rights[i]:
                if y < EventHist.bin_values[i]:
                    exp_spectrum[i] += 1
                    events +=1
                    break
                else:
                    break
    return h.Histogram(np.array(exp_spectrum),EventHist.bin_centers, \
            EventHist.bin_lefts, EventHist.bin_rights)

def arr_average(arrays):
    '''
    Takes in an array of arrays.  Calculates the average and standard deviation
    for each index.  Returns them as arrays.
    '''
    average = np.average(arrays,axis=0)
    stdevs = np.std(arrays,axis=0)
    return average, stdevs

def hist_average(histograms):
    """
    Takes in an array of histograms. Calculates the average and standard
    deviation for each bin.  Returns them each as a histogram.
    ALL HISTOGRAMS MUST HAVE SAME BIN WIDTHS.
    """
    #Use first histogram to define bin regions
    bc, bl, br = histograms[0].bin_centers, histograms[0].bin_lefts, \
            histograms[0].bin_rights
    allhist_binvalues = []
    for hist in histograms:
        allhist_binvalues.append(hist.bin_values)
    average = np.average(allhist_binvalues, axis=0)
    stdevs = np.std(allhist_binvalues, axis=0)
    avg_hist = h.Histogram(average, bc, bl, br)
    stddev_hist = h.Histogram(stdevs, bc, bl, br)
    return avg_hist, stddev_hist
