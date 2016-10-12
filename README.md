REACTOR ANTINEUTRINO DATABASE/ANALYSIS SOFTWARE

The following repository contains various python scripts to construct databases
with daily reactor operational information (publicly available from NRC.gov) and
static details regarding reactors (licensed thermal power output, location, etc.)

Dependencies:
Python 2.7
couchdb
numpy
matplotlib

Some details on important scripts:

daily/pollReacDB.py:
Pulls daily posted reactor status information from NRC.gov and pushes the data to
a local couchDB named 'reacdb'.

static/NRCgrabber.py:
Contains the 'claws' class for grabbing/calculating static reactor details, packaging them toa couchDB format, and pushing the details as a document to a local couchDB named
'reacdb'.  The 'RDBclaws' subclass adds an additional function that parses the
REACTORS.ratdb file found in the SNO+ RAT distribution for reactor information.  The
'NRCclaws' subclass can pull a reactor's type and thermal power from NRC.gov.  'NRCclaws'
also grabs reactor location details from db/ReacPos_corr.txt, which contains position
information for US reactors found using Google Earth.

graph/
Home for various graphing scripts.  The scripts query the 'reacdb' couchDB for reactor
information for data needed to complete the plots.

graph/SigPlots.py
Outputs matplotlib plots graphing all US/CA reactors significance factors relative to
SNO+.  A reactor's significance factor is defined as it's licensed thermal output,
given in MW, divided by the squared distance from SNO+ in kilometers.
