#Various functions for parsing any ratdb file for reactor information.
#TO ADD YOUR OWN CLASS PARSER:
# 1. Create a new class that inherits from class ratdbEntry
# 2. Write a parseMisc() function that parses out your
#    RATDB entry's information specific to the RATDB type
# 3. Write a buildreacdbEntry() function that adds the values
#    Specific to your RATDB type to the reacdb_entry dictionary
#*** See the CoreComp subclass for an example of how this is done.

import numpy as np
import os.path
import sys

basepath = os.path.dirname(__file__)
dbpath = os.path.abspath(os.path.join(basepath, "..", "db"))

REACTORC_RATDB = 'static/REACTORS_corr.ratdb'
REACTOR_RATDB = 'static/REACTORS.ratdb'
REACTORSTAT_RATDB = 'daily/REACTORS_STATUS.ratdb'
CORECOMP_RATDB = 'static/CoreComps.ratdb'
NUSPEC_RATDB = 'static/NuSpectraConsts.ratdb'

def getCCIndices():
    """
    Opens CoreComp.ratdb and grabs all the index values present.
    """
    CCindices = []
    ccpath = os.path.abspath(os.path.join(dbpath, CORECOMP_RATDB))
    f = open(ccpath, 'r')
    for line in f:
        if line.find('index') != -1:
            indexline = line.split(":")
            index = indexline[1].lstrip(" \"").rstrip("\",\n")
            CCindices.append(index)
    return CCindices


def getNSIndices():
    """
    Opens NuSpectraConst.ratdb and grabs all the index values present.
    """
    NSindices = []
    nspath = os.path.abspath(os.path.join(dbpath, NUSPEC_RATDB))
    f = open(nspath, 'r')
    for line in f:
        if line.find('index') != -1:
            indexline = line.split(":")
            index = indexline[1].lstrip(" \"").rstrip("\",\n")
            NSindices.append(index)
    return NSindices

def getRLIndices():
    """
    Opens REACTORS.ratdb and grabs all the Reactor index values present.
    """
    RLindices = []
    nspath = os.path.abspath(os.path.join(dbpath, REACTOR_RATDB))
    f = open(nspath, 'r')
    content = f.readlines()
    for i,line in enumerate(content):
        if content[i].find('\"REACTOR\"') != -1:
            indexline = content[i+2].split(":")
            RLindex = indexline[1]
            RLindex = RLindex.lstrip(" \"").rstrip("\",\n")
            RLindices.append(RLindex)
    return RLindices

#Class is defined with a RATDB database file, RDB type, and RDB index. grabs the basic
#information for that entry in the database.
class ratdbEntry(object):
    def __init__(self,filename,rdbtype,index):
        self.rdb_type = rdbtype
        self.ver = 'unknown'
        self.index = index
        self.run_range = []
        self.passing = 'unknown'
        self.comment = 'unknown'
        self.timestamp = 'unknown'

        self.misc = {}
        self.reacdb_entry = {}
        self.ratdbpath = os.path.abspath(os.path.join(dbpath, filename))
        self.fill()

    def show(self):
        print("RATDB type: " + self.rdb_type)
        print("Version: " + self.ver)
        print("Entry index: " + self.index)
        print("Run range: " + str(self.run_range))
        print("Pass?: " + str(self.passing))
        print("Comments: " + self.comment)
        print("timestamp: " + self.timestamp)
        print("Miscillaneous values: " + str(self.misc))
        print("Current reacdb_entry: " + str(self.reacdb_entry))

    def fill(self):
        '''
        Fills the defined class variables with the general information 
        universal to all RATDB files. The misc dictionary is filled with
        information specific to a RATDB entry type.
        '''
        try:
            f=open(self.ratdbpath, 'r')
        except(IOError):
            print("Issue opening RATDB file to read entries from.  Check" + \
                    "your subclass has a specified filename.")
            return

        startparse = False
        filelines = f.readlines()
        entryfinished = False
        for i,stuff in enumerate(filelines):
            if not entryfinished:
                if i == len(filelines)-1:
                    raise ValueError('Index not found in RATDB file')
                #found an entry; check if it's the one we want in the class
                if stuff.find('{') != -1:
                    nextline = filelines[i+1]
                    #split line into key and value
                    nxlinepieces = nextline.split(":")
                    key = nxlinepieces[0]
                    value = ""
                    #re-fuses entries split within the value 
                    for j,entry in enumerate(nxlinepieces):
                        if j > 0:
                            value = value + entry
                    if key == "type" and \
                    value.rstrip("\",\n").lstrip(" \"") == self.rdb_type:
                        verline = filelines[i+2]
                        indexline = filelines[i+3]
                        inlinepieces = indexline.split(":")
                        if inlinepieces[0] == "index" and \
                        inlinepieces[1].rstrip("\",\n").lstrip(" \"") == self.index:
                            startparse = True                            
                if startparse:
                    verlinepieces = verline.split(":")
                    self.ver = verlinepieces[1].rstrip(",\n")
                    entryline = 4
                    while not entryfinished:
                        line = filelines[i+entryline]
                        if line.find('//') != -1:
                            line = line.split('//',1)[0].rstrip(' ')
                        if line in ['\n', '\r\n']:
                            entryline+=1
                            continue
                        if line.find('}') == -1:
                            entryline+=1
                            linepieces = line.split(":")
                            key = linepieces[0]
                            value = ""
                            for k,entry in enumerate(linepieces):
                                if k > 0:
                                    value = value + entry
                            if key  == 'version':
                                self.ver = int(value.rstrip(",\n"))
                            elif key == 'run_range':
                                rr = value.split(",")
                                for l,entry in enumerate(rr):
                                    if l == 0:
                                        runstart = int(entry.lstrip(" ["))
                                        self.run_range.append(runstart)
                                    if l == (len(rr) - 2): #There's a blank entry after last comma
                                        runend = int(entry.rstrip("],\n"))
                                        self.run_range.append(runend)
                            elif key == "pass":
                                self.passing = int(value.rstrip(",\n"))
                            elif key == "comment":
                                self.comment = value.rstrip(",\n")
                            elif key == "timestamp":
                                self.timestamp = value.rstrip(",\n")
                            else:
                                self.misc[key] = value
                        else:
                            entryfinished = True

    def buildReacdbEntry(self):
        """
        Fills in self.reacdb_entry with the standard RATDB entry values."
        """
        stdratdict = {"RATDB_type": self.rdb_type, "version": self.ver, "index": self.index,
        "run_range": self.run_range, "pass": self.passing, "comment": self.comment,
        "timestamp": self.timestamp}
        readytobuild = True
        for key in stdratdict:
            if stdratdict[key] == 'none':
                print("One or more entries were not filled in for the ratdb entry." + \
                "reacdb_entry not built.")
                readytobuild = False
        if readytobuild:
            self.reacdb_entry = stdratdict
            print("Standard RATDB entry values filled in.  Please add miscillaneous " + \
            "information before pushing to ReacDB.")
    def pushToDB(self):
        dbStatus, db = connectToDB('reacdb')
        if dbStatus is "ok":
            db.save(self.reacdb_entry)

#Subclass of ratdbEntry that also parses isotope compositions
#Super call inherits the parent's (class ratdbEntry's) init parameters
#Have to do this; just starting a new init would overwrite the parent init
class CoreComp(ratdbEntry):
    def __init__(self,index):
        self.rdb_type = "REACTORCOMPS"
        self.filename = CORECOMP_RATDB

        self.composition = []

        super(CoreComp, self).__init__(self.filename, self.rdb_type, index)
        self.stuff = "things"

    def show(self):
        super(CoreComp,self).show() #performs the parent method show()
        print("Isotope composition: " + str(self.composition))

    def parseMisc(self):
        composition = self.misc['iso_comp']
        composition = composition.lstrip("\' [").rstrip("],\n\'")
        print(composition)
        composition = composition.split(",")
        comp_array = []
        for entry in composition:
            entry = float(entry)
            comp_array.append(entry)
        self.composition = comp_array

    def buildreacdbEntry(self):
        super(CoreComp, self).buildReacdbEntry()
        self.reacdb_entry["Core Composition (U238, U235, Pu239, Pu241)"] = self.composition

class Reactor_Spectrum(ratdbEntry):
    def __init__(self,index):
        self.rdb_type = "REACTOR_SPECTRUM"
        self.filename = REACTOR_RATDB

        self.emin = 'none'
        self.emax = 'none'
        self.spectrum_type = 'none'
        self.spec_e = []
        self.spec_flux = []
        self.flux_norm = 'none'
        self.param_isotope = []
        self.param_composition = []

        super(Reactor_Spectrum, self).__init__(self.filename, self.rdb_type, index)
        self.parseMisc()

    def show(self):
        super(Reactor_Spectrum, self).show()
        print("Minimum valid energy for spectrum: " + str(self.emin))
        print("Maximum valid energy for spectrum: " + str(self.emax))
        print("Spectrum type: " + str(self.spectrum_type))
        print("Energy values (x-axis for spectrum): " + str(self.spec_e))
        print("Flux values (y-axis for spectrum): " + str(self.spec_flux))
        print("Flux normalization factor: " + str(self.flux_norm))
        print("Isotopes used to build spectrum: " + str(self.param_isotope))
        print("% of each isotope (235U, 238U, 239Pu, 241Pu): " + str(self.param_composition))

    def parseMisc(self):
        spece_vals = self.misc['spec_e']
        spece_vals = spece_vals.lstrip("\' [").rstrip("],\n\'")
        spece_vals = spece_vals.split(",")
        spece_vals_arr = []
        for entry in spece_vals:
            if entry != '':
                value = float(entry)
                spece_vals_arr.append(value)
        self.spec_e = spece_vals_arr

        specf_vals = self.misc['spec_flux']
        specf_vals = specf_vals.lstrip("\' [").rstrip("],\n\'")
        specf_vals = specf_vals.split(",")
        specf_vals_arr = []
        for entry in specf_vals:
            if entry != '':
                value = float(entry)
                specf_vals_arr.append(value)
        self.spec_flux = specf_vals_arr

        emin = self.misc['emin']
        emin = emin.lstrip("\' ").rstrip(",\n\'")
        self.emin = float(emin)

        emax = self.misc['emax']
        emax = emax.lstrip("\' ").rstrip(",\n\'")
        self.emax = float(emax)
       
        fnorm = self.misc['flux_norm']
        fnorm = fnorm.lstrip("\' ").rstrip(",\n\'")
        self.flux_norm = float(fnorm)
        
        spectype = self.misc['spectrum_type']
        spectype = spectype.lstrip("\' \"").rstrip("\",\n\'")
        self.spectrum_type = spectype
        
        paramiso_vals = self.misc['param_isotope']
        paramiso_vals = paramiso_vals.lstrip("\' [").rstrip("],\n\'")
        paramiso_vals = paramiso_vals.split(",")
        paramiso_vals_arr = []
        for entry in paramiso_vals:
            entry = entry.lstrip(" \"").rstrip("\"")
            paramiso_vals_arr.append(entry)
        self.param_isotope = paramiso_vals_arr
        
        paramcomp_vals = self.misc['param_composition']
        paramcomp_vals = paramcomp_vals.lstrip("\' [").rstrip("],\n\'")
        paramcomp_vals = paramcomp_vals.split(",")
        paramcomp_vals_arr = []
        for entry in paramcomp_vals:
            value = float(entry)
            paramcomp_vals_arr.append(value)
        self.param_composition = paramcomp_vals_arr

    def buildreacdbEntry(self):
        super(Reactor_Spectrum, self).buildReacdbEntry()
        self.reacdb_entry["Spectrum energy (x-axis)"] = self.spec_e
        self.reacdb_entry["Spectrum flux (y-axis)"] = self.spec_flux
        self.reacdb_entry["Minimum valid energy for spectrum"] = self.emin
        self.reacdb_entry["Maximum valid energy for spectrum"] = self.emax
        self.reacdb_entry["Normalization factor for spectrum"] = self.flux_norm
        self.reacdb_entry["Spectrum type"] = self.spectrum_type
        self.reacdb_entry["Isotopes used to generate spectrum"] = self.param_isotope
        self.reacdb_entry["% of each isotope composing reactor [235U, 238U, 239Pu, 241Pu]"] = self.param_composition

#Subclass reads RATDB entries from REACTORS.ratdb
class Reactor_Isotope_Info(ratdbEntry):
    def __init__(self,index):
        self.rdb_type = "REACTOR_ISOTOPE_INFO"
        self.filename = REACTOR_RATDB
        self.index = index

        self.nuperfission = 'none'
        self.nuperfission_err = 'none'
        self.Eperfission = 'none'
        self.Eperfission_err = 'none'
        self.spec_type = 'none'
        self.poly_coeff = []

        super(Reactor_Isotope_Info, self).__init__(self.filename, self.rdb_type, index)
        self.parseMisc()

    def show(self):
        super(Reactor_Isotope_Info,self).show() #performs the parent method show()
        print("neutrinos per fission: " + str(self.nuperfission))
        print("error on neutrinos per fission: " + str(self.nuperfission_err))
        print("Energy released per fission: " + str(self.Eperfission))
        print("error on energy released per fission: " + str(self.Eperfission_err))
        print("Type used to characterize spectrum: " + str(self.spec_type))
        print("Polynomial coefficients: " + str(self.poly_coeff))

    def parseMisc(self):
        PolyCoeffs = self.misc['poly_coeff']
        PolyCoeffs = PolyCoeffs.lstrip("\' [").rstrip("],\n\'")
        PolyCoeffs = PolyCoeffs.split(",")
        PolyCoeffs_arr = []
        for entry in PolyCoeffs:
            value = float(entry)
            PolyCoeffs_arr.append(value)
        self.poly_coeff = PolyCoeffs_arr
        nnuf = self.misc['n_nu_fission']
        nnuf = nnuf.lstrip("\' ").rstrip(",\n\'")
        self.nuperfission = float(nnuf)
        nnuf_err = self.misc['n_nu_fission_err']
        nnuf_err = nnuf_err.lstrip("\' ").rstrip(",\n\'")
        self.nuperfission_err = float(nnuf_err)
        epf = self.misc['e_per_fission']
        epf = epf.lstrip("\' ").rstrip(",\n\'")
        self.Eperfission = float(epf)
        epf_err = self.misc['e_per_fission_err']
        epf_err = epf_err.lstrip("\' ").rstrip(",\n\'")
        self.Eperfission_err = float(epf_err)
        spectype = self.misc['spec_type']
        spectype = spectype.lstrip("\' \"").rstrip("\",\n\'")
        self.spec_type = spectype

    def buildreacdbEntry(self):
        super(Reactor_Isotope_Info, self).buildReacdbEntry()
        self.reacdb_entry["Parameter values [a1,a2,a3,a4,a5,a6]"] = self.poly_coeff
        self.reacdb_entry["Number of neutrinos per fission"] = self.nuperfission
        self.reacdb_entry["Error on # neutrinos per fission"] = self.nuperfission_err
        self.reacdb_entry["Energy released per fission (MeV)"] = self.Eperfission
        self.reacdb_entry["Error on E released per fission (MeV)"] = self.Eperfission_err
        self.reacdb_entry["Type used to characterize spectrum"] = self.spec_type

#Subclass reads from REACTORS.RATDB to get the position information
#(longitude,latitude,altitude)for each core for input reactor name (index input)
class ReactorDetails(ratdbEntry):
    def __init__(self,index):
        self.rdb_type = "REACTOR"
        self.filename = REACTOR_RATDB

        self.no_cores = 'unknown'
        self.core_longitudes = []
        self.core_latitudes = []
        self.core_altitudes = []

        super(ReactorDetails, self).__init__(self.filename, self.rdb_type, index)
        self.parseMisc()

    def show(self):
        super(ReactorDetails,self).show() #performs the parent method show()
        print("Number of cores: " + str(self.no_cores))
        print("Reactor core longitudes (degrees): " + str(self.core_longitudes))
        print("Reactor core latitudes (degrees): " + str(self.core_latitudes))
        print("Reactor core altitudes (meters): " + str(self.core_altitudes))

    def parseMisc(self):
        numcores = self.misc['no_cores']
        numcores = numcores.lstrip("\' ").rstrip(",\n\'")
        self.no_cores = int(numcores)

        lat_vals = self.misc['latitude']
        lat_vals = lat_vals.lstrip("\' [").rstrip("],\n\'")
        lat_vals = lat_vals.split(",")
        lat_arr = []
        for entry in lat_vals:
            if entry != '':
                value = float(entry)
                lat_arr.append(value)
        self.core_latitudes = lat_arr

        long_vals = self.misc['longitude']
        long_vals = long_vals.lstrip("\' [").rstrip("],\n\'")
        long_vals = long_vals.split(",")
        long_arr = []
        for entry in long_vals:
            if entry != '':
                value = float(entry)
                long_arr.append(value)
        self.core_longitudes = long_arr

        alt_vals = self.misc['altitude']
        alt_vals = alt_vals.lstrip("\' [").rstrip("],\n\'")
        alt_vals = alt_vals.split(",")
        alt_arr = []
        for entry in alt_vals:
            if entry != '':
                value = float(entry)
                alt_arr.append(value)
        self.core_altitudes = alt_arr

    def buildreacdbEntry(self):
        self.reacdb_entry["Number of cores"] = self.no_cores
        self.reacdb_entry["Reactor core longitudes (deg.)"] = self.core_longitudes
        self.reacdb_entry["Reactor core latitudes (deg.)"] = self.core_latitudes
        self.reacdb_entry["Reactor core altitudes (m)"] = self.core_altitudes
        super(ReactorDetails, self).buildReacdbEntry()

class ReactorStatus(ratdbEntry):
    def __init__(self,index):
        self.rdb_type = "REACTOR_STATUS"
        self.filename = REACTORSTAT_RATDB
        self.no_cores = 'unknown'
        self.core_powers = []
        self.core_types = []
        super(ReactorStatus, self).__init__(self.filename, self.rdb_type, index)
        self.parseMisc()

    def show(self):
        super(ReactorStatus,self).show() #performs the parent method show()
        print("Number of cores: " + str(self.no_cores))
        print("Thermal output of each core (MW):  " + str(self.core_powers))
        print("Reactor core type (PWR,BWR,PHWR,etc.): " + str(self.core_types))


    def parseMisc(self):
        numcores = self.misc['no_cores']
        numcores = numcores.lstrip("\' ").rstrip(",\n\'")
        self.no_cores = int(numcores)
        
        type_vals = self.misc['core_spectrum']
        type_vals = type_vals.lstrip("\' [").rstrip("],\n\'")
        type_vals = type_vals.split(",")
        type_vals_arr = []
        for entry in type_vals:
            if entry != '':
                entry = entry.lstrip(" \"").rstrip("\"")
                type_vals_arr.append(entry)
        self.core_types = type_vals_arr

        power_vals = self.misc['core_power']
        power_vals = power_vals.lstrip("\' [").rstrip("],\n\'")
        power_vals = power_vals.split(",")
        power_arr = []
        for entry in power_vals:
            if entry != '':
                value = float(entry)
                power_arr.append(value)
        self.core_powers = power_arr

def buildreacdbEntry(self):
        self.reacdb_entry["Number of cores"] = self.no_cores
        self.reacdb_entry["Thermal output of each core (MW)"] = self.core_longitudes
        self.reacdb_entry["Reactor core type (PWR,BWR,PHWR, etc.)"] = self.core_latitudes
        super(ReactorStatus, self).buildReacdbEntry()
             

        
if __name__ == '__main__':
    print('Still nothing in main loop yet')
