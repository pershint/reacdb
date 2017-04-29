#Functions here for fusing data together that's stored in the output directory.

import os.path
import glob
import json

basepath=os.path.dirname(__file__)
datapath=os.path.abspath(os.path.join(basepath, "..","output"))

def datatypecheck(filenames):
    '''
    checks all infed files to see that parameters are the same (OscParameters, 
    Reactor spectrums, etc.).  If not, returns false.
    '''
    issame = True
    params = []
    #Grab the first file's parameters
    ignorekeys = ["sst","dms","negML"]
    for f in filenames:
        with open(f,"r") as data:
            dat = json.load(data)
	    if f == filenames[0]:
	        for key in dat:
	            if key not in ignorekeys:
	                params.append(dat[key])
	    else:
	        for key in dat:
	            if key not in ignorekeys:
	                if dat[key] not in params:
	                    issame = False
	                    print("File has a different parameter from first file.")



def fuseallinout():
    filelocs = glob.glob(datapath+"/*.json")
    identical_params = datatypecheck
    dat_keys = ["dms","sst","negML"]
    if identical_params:

        fused_dat = {}
        for key in dat_keys:
            fused_dat[key] = []
        for f in filelocs:
            with open(f,"r") as data:
                dat = json.load(data)
                for key in dat:
                    print(key)
                    #extend data arrays with data in file
                    if key in dat_keys:
                        fused_dat[key].extend(dat[key])
                    else:
                    #if not data, add parameters to the fused_dat dict    
                        if key not in fused_dat:
                            fused_dat[key] = dat[key]
    return fused_dat

