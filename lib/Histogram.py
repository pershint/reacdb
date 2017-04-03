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
    def __init__(self, bin_values, bin_centers, bin_lefts, bin_rights):
        #Initialize arrays that hold bin end locations
        self.bin_lefts = bin_lefts
        self.bin_rights = bin_rights
        #initialize array for each bin's center value
        self.bin_centers = bin_centers
        #initialize array to hold the bin's value
        self.bin_values = bin_values
        #initialize value that tells you the bin width in x-axis units
        self.bin_width = self.bin_rights[0] - self.bin_lefts[0]

class dNdE_Hist(Histogram):
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
        self.bin_values = np.array(self.bin_values)

        super(dNdE_Hist, self).__init__(self.bin_values, self.bin_centers, \
                self.bin_lefts, self.bin_rights)

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
            #First, average over spectrum values in the cbin region
            binavg = np.mean(self.spectrum[(self.specvals_perbin * \
                    cbin):((self.specvals_perbin * (cbin+1)) - 1)])
            #Now, calculate the number of values in the bin
            binvalue = binavg * self.binwidth
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
                    cbin):((self.specvals_perbin * (cbin+1))-1)])
            self.bin_centers.append(axisvalue)
            cbin += 1
        self.binwidth = self.x_axis[self.specvals_perbin] - self.x_axis[0]
    

