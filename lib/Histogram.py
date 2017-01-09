import rdbparse as rp
import SNOdist as sd
import NuSpectrum as ns
import numpy as np


#FIXME: So, I need a base histogram class that would take in bin values,
#bin_centers, bin_lefts, and bin_rights and just group them as a Histogram
#object.  Could then make a Histogram subclass for the dNdE Histogram?

#Class takes in a dNdE function (as defined in /lib/NuSpectrum.py in the
#dNdE class) and produces a histogram that gives the number of events per
#bin with a total number of numbins
class Histogram(object):
    def __init__(self, dNdE, numbins):
        self.spectrum = dNdE.dNdE
        self.x_axis = dNdE.Energy_Array
        self.numbins = numbins
        self.specvals_perbin = len(self.spectrum) / self.numbins
        self.bincheck()

        #Initialize arrays that hold bin end locations
        self.bin_lefts = []
        self.bin_rights = []
        #initialize array for each bin's center value
        self.bin_centers = []
        #initialize array to hold the bin's value
        self.bin_values = []
        #initialize value that tells you the bin width in x-axis units
        self.binwidth = 'none'

        self.reBin_spectrum()
        self.fill_binvalues()
        

    def bincheck(self):
        '''
        Function that checks the number of bins is not greater than the
        number of spectrum entries.
        '''
        if self.numbins > len(self.spectrum):
            print("ERROR: CANNOT USE MORE BINS THAN SPECTRUM ARRAY ENTRIES." +\
                    "SETTING NUMBER OF BINS TO NUMBER OF SPECTRUM VALUES.")
            self.numbins = self.spectrum

    def fill_binvalues(self):
        cbin = 0
        while cbin < self.numbins:
            dNdE_binavg = np.mean(self.spectrum[(self.specvals_perbin * \
                    cbin):(self.specvals_perbin * (cbin+1))])
            binvalue = dNdE_binavg * self.binwidth
            self.bin_values.append(binvalue)
            cbin+=1

    def reBin_spectrum(self):
        """
        X_AXIS MUST HAVE EQUAL DISTANCE VALUES FOR THIS TO WORK
        Takes in a spectrum and corresponding x-axis array, rebins by averaging
        over each range according to the number given.  So, if the spectrum
        has 100 bins, and num_combine == 10, the final number of bins will be
        10 with the average of 10 bins in each.
        """
        cbin = 0
        while cbin < self.numbins:
            self.bin_lefts.append(self.x_axis[self.specvals_perbin * cbin])
            self.bin_rights.append(self.x_axis[(self.specvals_perbin * (cbin+1)) - 1])
            axisvalue = np.mean(self.x_axis[(self.specvals_perbin * \
                    cbin):(self.specvals_perbin * (cbin+1))])
            print(axisvalue)
            self.bin_centers.append(axisvalue)
            cbin += 1
        self.binwidth = self.x_axis[self.specvals_perbin] - self.x_axis[0]
        print("THE WIDTH OF A BIN IS" + str(self.binwidth))
    
#FIXME: Need to make a class that can take in the unoscilated spectrum info.
#for a reactor, and uses scipy to integrate over that function times
#The survival probability function times the cross-section.  Right now, how
#The classes are written, you can't use the individual pieces cleanly, so we
#May have to restructure a bit.


