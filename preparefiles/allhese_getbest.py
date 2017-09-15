from icecube import icetray, dataio, dataclasses
from I3Tray import *
import argparse


### Parsing stuff 
usage = "usage: %prog [options] inputfile"
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type=str, default=None, nargs="*",
                  dest="INPUT", help="Input File")

parser.add_argument("--keep", type=str, default="all",
                  dest="KEEP", help="What  you want to keep: cascade, track, all. Default: all")

# parse cmd line args, bail out if anything is not understood
args = parser.parse_args()
if args.INPUT is None:
    error = "you need to specify an input filename!"
    parser.error(error)
else:
	inputfiles = args.INPUT


tray = I3Tray()
tray.AddModule('I3Reader', 'reader',FilenameList=inputfiles)

#nameoforiginalpulses = "OfflinePulsesHLC"
nameoforiginalpulses = "HLCPulses"


hitlist = []
def minhits(frame):
	global hitlist
	header = frame["I3EventHeader"]
	eventID = dataclasses.I3EventHeader.event_id.fget(header)
	runID = dataclasses.I3EventHeader.run_id.fget(header)
	if frame.Has(nameoforiginalpulses ):
		RPSM = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, nameoforiginalpulses )
		listofoms = []
		for omkey,series in RPSM.items():
			listofoms.append([omkey.string, omkey.om])
		numberofhits = len(listofoms)
		hitlist.append(numberofhits)




tray.AddModule(minhits, "Min hits",Streams=[icetray.I3Frame.Physics])
tray.Execute()
tray.Finish()
del tray


def morethan(hitlist):
	hitlist.sort()
	val = hitlist[-6]
	return val

minval = morethan(hitlist)

def Gandalf(frame):
	if frame.Has(nameoforiginalpulses ):
		RPSM = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, nameoforiginalpulses )
		listofoms = []
		for omkey,series in RPSM.items():
			listofoms.append([omkey.string, omkey.om])
		if len(listofoms) >= minval:
			return True
		else:
			return False
	return False


tray = I3Tray()
tray.AddModule('I3Reader', 'reader',FilenameList=inputfiles)
tray.AddModule(Gandalf, "You shall not pass",Streams=[icetray.I3Frame.DAQ, icetray.I3Frame.Physics])
tray.AddModule("I3Writer", "writer",filename="besthese.i3")
tray.Execute()
tray.Finish()
del tray