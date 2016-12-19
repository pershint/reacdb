#!/usr/bin/python
import numpy as np
def reBin_EW(spectrum,x_axis,num_combine):
    """
    X_AXIS MUST HAVE EQUAL DISTANCE VALUES FOR THIS TO WORK
    Takes in a spectrum and corresponding x-axis array, rebins by averaging
    over each range according to the number given.  So, if the spectrum
    has 100 bins, and num_combine == 10, the final number of bins will be
    10 with the average of 10 bins in each.
    """
    bin_values = []
    bin_left = []
    bin_right = []
    bin_center = []
    no_total_bins = len(spectrum)
    #Putting in integers will round down so the last bin is always full
    #of the num_combine points.
    num_collapsed_bins = no_total_bins/num_combine
    cbin = 0
    while cbin < num_collapsed_bins:
        binvalue = np.mean(spectrum[(num_combine * cbin):(num_combine * (cbin+1))])
        print(num_combine *(cbin+1))
        bin_left.append(x_axis[num_combine * cbin])
        bin_right.append(x_axis[(num_combine * (cbin+1)) - 1])
        bin_values.append(binvalue)
        axisvalue = np.mean(x_axis[(num_combine * cbin):(num_combine * (cbin+1))])
        print(axisvalue)
        bin_center.append(axisvalue)
        cbin += 1
    binwidth = x_axis[0] - x_axis[num_combine]
    return bin_values, bin_center, bin_left, bin_right
