import argparse
import sys
#Oscillation variables that will be measured by SNO+/vary
#between SuperK and KamLAND; fixed parameters are found hard-coded in
#./lib/NuSPectrum.py

def setOscParams(parameter_choice):
    oscParams = []
    if parameter_choice == "SK":
        print("USING SUPERKAMIOKANDE OSCILLATION PARAMETERS")
        sst12 = 0.308
        dmsq = 4.85E-05
        oscParams = [dmsq, sst12]

    elif parameter_choice == "KAMLAND":
        print("USING KAMLAND OSCILLATION PARAMETERS")
        sst12 = 0.316
        dmsq = 7.54E-05
        oscParams = [dmsq, sst12]

    elif parameter_choice == "PDG":
        print("USING PDG 2016 OSCILLATION PARAMETERS")
        sst12 = 0.297
#        dmsq = 7.37E-05
        dmsq = 1.75E-04
        oscParams = [dmsq, sst12]

    elif parameter_choice == "none":
        print("NO OSCILLATION PARAMETERS SET.  NOOOO")
        sys.exit(0)
    else:
        print("CHOOSE A VALID OSCILLATION PARAMETER SET (SK or KAMLAND).")
        sys.exit(0)
    return oscParams

parser = argparse.ArgumentParser(description='Program for calculating the reactor'+\
        ' antineutrino spectra at any location on Earth')
parser.add_argument("--debug",action="store_true")
parser.add_argument("-p", "--parameters",action="store",dest="parameters",
                  type=str,
                  help="Specify which experiment's oscillation parameters to use")
parser.add_argument("-r", "--reactors",action="store",dest="reactors",
                  type=str,
                  help="Specify what set of reactors to use (US, WORLD, CA, or USCA)")
parser.add_argument("-j", "--jobnum",action="store",dest="jobnum",
                  type=str,
                  help="Specify a jobnumber to save onto the end of the generated data")
parser.add_argument("-s", "--seed", action="store_true", dest="seed",
                  help="Runs feeds in a DMS value to minuit" + \
                  "found by doing a rough global minimization across DMS at fixed SST")

parser.set_defaults(parameters="KAMLAND",reactors="WORLD",jobnum="0",debug="False",
        seed="False")
args = parser.parse_args()
oscParams = setOscParams(args.parameters)
debug = args.debug
reactors = args.reactors
parameters = args.parameters
jobnum = args.jobnum
seed = args.seed

#Uses whatever type is set in the arguments for -r to pick a reactor name list
def setListType(List_Dictionary):
    if args.reactors == ("USCA"):
        USCAList = List_Dictionary['US'] + List_Dictionary['CA']
        return USCAList
    else:
        try:
            return List_Dictionary[args.reactors]
        except KeyError:
            print("Choose a valid reactor list option.  see python main.py --help" + \
                    "for choices")
            raise


def showReactors():
    if args.reactors == "CA":
        print("GRAPHING THE SUM OF CANADIAN REACTORS")
    if args.reactors == "US":
        print("GRAPHING THE SUM OF US REACTORS")
    if args.reactors == "USCA":
        print("GRAPHING THE SUM OF US AND CA REACTORS")
    if args.reactors == "WORLD":
        print("GRAPHING SUM OF WORLD'S REACTORS AT SNO+")


