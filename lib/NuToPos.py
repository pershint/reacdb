#Class takes in an array of neutrino energies and corrects the energy to
#total positron momentum. Can also add on 1.022 MeV for the positron capture.
#NOTE: Our inclusion of the 1.022 MeV due to the positron capture is really
#only good for scintillator, and the detector response for this portion of the
#energy would also need to be treated separately.
import numpy as np


class NuToPosConverter(object):
    def __init__(self, E_nus):
        self.E_nus = np.array(E_nus)
        self._delta = 1.293 #m_neutron - m_proton in MeV
        self._m_e = 0.511 #m_electron in MeV
        self._m_n = 939.57 #in MeV

    def convert0(self):
        #zeroth order conversion to positron momentum
        p_p0 = np.sqrt((self.E_nus - self._delta)**2 - (self._m_e)**2)
        return p_p0

    def convert1(self,p_pos0):
        #first order conversion to positron momentum
        #source: Vogel, Beacom, "The angular distribution of the 
        #reaction nu_e + p -> pos + n". arXiv:hep-ph/9903554v1, Apr 1999
        Ee0 = self.E_nus - self._delta
        ve0 = p_pos0/(self.E_nus - self._delta)
        exp_cos = -0.034 * ve0 + 2.4 * (self.E_nus / self.m_n)
        y = (self._delta**2 - self._m_e**2)/2
        Ee1 = Ee0(1 - (self.E_nus/self._m_n)*(1 - ve0*exp_cos)) - ((y**2)/self._m_n)
        pe1 = np.sqrt(Ee1**2 - self._m_e**2)
        return pe1

    def addAnnihilE(self, pe1):
        E_ann = self._m_e * 2
        return pe1 + E_ann


