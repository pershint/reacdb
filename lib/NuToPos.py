#Class takes in an array of neutrino energies and corrects the energy to
#total positron momentum. Can also add on 1.022 MeV for the positron capture.
#NOTE: Our inclusion of the 1.022 MeV due to the positron capture is really
#only good for scintillator, and the detector response for this portion of the
#energy would also need to be treated separately.
import numpy as np
import playDarts as pd

class NuToPosConverter(object):
    def __init__(self):
        self._delta = 1.293 #m_neutron - m_proton in MeV
        self._m_e = 0.511 #m_electron in MeV
        self._m_n = 939.57 #in MeV

    def _convert_0ord(self,nu_E):
        #zeroth order conversion to positron momentum
        p_p0 = np.sqrt((nu_E - self._delta)**2 - (self._m_e)**2)
        return p_p0

    def _convert_1ord(self,p_pos0,nu_E):
        #first order conversion to positron momentum
        #source: Vogel, Beacom, "The angular distribution of the 
        #reaction nu_e + p -> pos + n". arXiv:hep-ph/9903554v1, Apr 1999
        Ee0 = nu_E - self._delta
        ve0 = p_pos0/(nu_E - self._delta)
        exp_cos = -0.034 * ve0 + 2.4 * (nu_E / self._m_n)
        y = (self._delta**2 - self._m_e**2)/2
        Ee1 = Ee0*(1 - (nu_E/self._m_n)*(1 - ve0*exp_cos)) - ((y**2)/self._m_n)
        pe1 = np.sqrt(Ee1**2 - self._m_e**2)
        return pe1

    def getPosMomentums(self,nu_E):
        p_p0 = self._convert_0ord(nu_E)
        p_p1 = self._convert_1ord(p_p0,nu_E)
        return p_p1

    def addAnnihilE(self, pos_KE):
        '''
        Takes an array of positron momentums and adds to each the energy
        released in a positron-electron annihilation.
        '''
        E_ann = self._m_e * 2
        return pos_KE + E_ann

    def ConvertToPositronKE_0ord(self,nu_Es):
        pos_p = self._convert_0ord(nu_Es)
        pos_KE = np.sqrt(pos_p**2 + self._m_e**2) - self._m_e
        E_tot = self.addAnnihilE(pos_KE)
        return E_tot

    def ConvertToPositronP_0ord(self,nu_Es):
        pos_p = self._convert_0ord(nu_Es)
        return pos_p


    def ConvertToPositron(self,nu_Es):
        pos_p = self.getPosMomentums(nu_Es)
        pos_KE = np.sqrt(pos_p**2 + self._m_e**2) - self._m_e
        E_tot = self.addAnnihilE(pos_p)
        return E_tot

    def Smear(self, Energies,resolution):
        '''
        Takes an array of energies deposited into the detector and smears it by the
        defined resolution percentage
        '''
        smeared_Es = pd.RandShoot(Energies, (np.sqrt(Energies) * \
                resolution), len(Energies))
        return smeared_Es
        
