#Various functions for parsing the REACTORS.ratdb file for reactor information.

import numpy as np
import os.path
import sys

basepath = os.path.dirname(__file__)
ratdbpath = os.path.abspath(os.path.join(basepath, "..", "db", "REACTORS_corr.ratdb"))

def getCAreacs():
    """
    Returns a list of the canadian reactor names in REACTORS.ratdb
    """
    CA_reacs = []
    f=open(ratdbpath, 'r')
    beginparse = False
    parsing = False
    while beginparse == False:
        stuff = str(f.readline())
        if stuff.find('C A N A D A') != -1:
            beginparse = True
            parsing = True
    while parsing == True:
        parseline = f.readline()
        if parseline.find('U S A') != -1:
            parsing = False
        line_pieces = parseline.split(":")
        if line_pieces[0] == 'index':
            CA_reacs.append(line_pieces[1].rstrip("\",\n").lstrip(" \""))
    return CA_reacs

if __name__ == '__main__':
    names = getCAreacs()
