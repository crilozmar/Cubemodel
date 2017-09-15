from icecube import icetray, dataio, dataclasses
from I3Tray import *
import argparse


### Parsing stuff 
usage = "usage: %prog [options] inputfile"
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type=str, default=None, nargs="*",
                  dest="INPUT", help="Input File")

parser.add_argument("--minE", type=float, default=1e4,
                  dest="MIN_E", help="Min E of the events (GeV)")

parser.add_argument("--minHits", type=float, default=45,
                  dest="MIN_HITS", help="Min modules hit")

parser.add_argument("--keep", type=str, default="all",
                  dest="KEEP", help="What  you want to keep: cascade, track, all. Default: all")

# parse cmd line args, bail out if anything is not understood
args = parser.parse_args()
if args.INPUT is None:
    error = "you need to specify an input filename!"
    parser.error(error)
else:
	inputfiles = args.INPUT
	

print "#######################"
print "You will keep "+args.KEEP+" events with more than "+str(args.MIN_HITS)+" modules hit and with E > "+str(args.MIN_E)+" GeV"
print "#######################"

tray = I3Tray()
tray.AddModule('I3Reader', 'reader',FilenameList=inputfiles)

DAQdict = {}
Pdict = {}

#nameoforiginalpulses = "OfflinePulsesHLC"
nameoforiginalpulses = "HLCPulses"

def minhits(frame):
	header = frame["I3EventHeader"]
	eventID = dataclasses.I3EventHeader.event_id.fget(header)
	runID = dataclasses.I3EventHeader.run_id.fget(header)
	if frame.Has(nameoforiginalpulses ):
		RPSM = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, nameoforiginalpulses )
		listofoms = []
		for omkey,series in RPSM.items():
			listofoms.append([omkey.string, omkey.om])
		if len(listofoms) >= args.MIN_HITS:
			if frame.Has('OnlineL2_BestFit_TruncatedEnergy_ORIG_Neutrino'):
				recopart = frame["OnlineL2_BestFit_TruncatedEnergy_ORIG_Neutrino"]
				frame["RecoParticle"] = dataclasses.I3Particle(recopart)
			DAQdict[""+str(+runID)+"-"+str(eventID)+""] = True
		else:
			DAQdict[""+str(+runID)+"-"+str(eventID)+""] = False
	else:
		DAQdict[""+str(+runID)+"-"+str(eventID)+""] = False

def keeponly(frame):
	header = frame["I3EventHeader"]
	eventID = dataclasses.I3EventHeader.event_id.fget(header)
	runID = dataclasses.I3EventHeader.run_id.fget(header)
	if frame.Has('I3MCTree'):
		myI3MCTree = frame["I3MCTree"]
		EE = dataclasses.get_most_energetic_primary(myI3MCTree)
		iscascade = dataclasses.I3Particle.is_cascade.fget(EE)
		istrack = dataclasses.I3Particle.is_track.fget(EE)
		try:
			mostcascade = dataclasses.get_most_energetic_cascade(myI3MCTree)
			energy_cascade = dataclasses.I3Particle.energy.fget(mostcascade)/I3Units.GeV
			loc_cascade = dataclasses.I3Particle.location_type_string.fget(mostcascade)
		except:
			energy_cascade = 0.
		try:
			mosttrack = dataclasses.get_most_energetic_track(myI3MCTree)
			energy_track = dataclasses.I3Particle.energy.fget(mosttrack)/I3Units.GeV
			loc_track = dataclasses.I3Particle.location_type.fget(mosttrack)
		except:
			energy_track = 0.
		if energy_track >= args.MIN_E:
			result = "track"
		elif energy_track <= energy_cascade  and energy_cascade > args.MIN_E:
			result = "cascade"
		else:
			result = "empty heart"
		if (result == args.KEEP) or args.KEEP == "all":
			Pdict[""+str(+runID)+"-"+str(eventID)+""] = True
		else:
			Pdict[""+str(+runID)+"-"+str(eventID)+""] = False
	else:
		Pdict[""+str(+runID)+"-"+str(eventID)+""] = False
		

def keeponly_byenergy(frame):
	header = frame["I3EventHeader"]
	eventID = dataclasses.I3EventHeader.event_id.fget(header)
	runID = dataclasses.I3EventHeader.run_id.fget(header)
	if frame.Has('I3MCTree'):
		myI3MCTree = frame["I3MCTree"]
		EE = dataclasses.get_most_energetic_primary(myI3MCTree)
		energy = dataclasses.I3Particle.energy.fget(EE)/I3Units.GeV
		print "eeeooo"
		if energy >= args.MIN_E:
			Pdict[""+str(+runID)+"-"+str(eventID)+""] = True
			print "eeeooo"
		else:
			Pdict[""+str(+runID)+"-"+str(eventID)+""] = False
	else:
		Pdict[""+str(+runID)+"-"+str(eventID)+""] = False


tray.AddModule(minhits, "Min hits",Streams=[icetray.I3Frame.Physics])
#tray.AddModule(keeponly, "keeping just one type of event",Streams=[icetray.I3Frame.DAQ])
tray.AddModule(keeponly_byenergy, "keeping high energy events",Streams=[icetray.I3Frame.DAQ])
tray.Execute()
tray.Finish()
del tray



def Gandalf(frame):
	header = frame["I3EventHeader"]
	eventID = dataclasses.I3EventHeader.event_id.fget(header)
	runID = dataclasses.I3EventHeader.run_id.fget(header)
	if DAQdict[""+str(+runID)+"-"+str(eventID)+""] and Pdict[""+str(+runID)+"-"+str(eventID)+""]:
		if frame.Has(nameoforiginalpulses ):
			RPSM = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, nameoforiginalpulses )
			frame["HLCPulses"] =  dataclasses.I3RecoPulseSeriesMap(RPSM)
		return True
	else:
		return False

tray = I3Tray()
tray.AddModule('I3Reader', 'reader',FilenameList=inputfiles)
tray.AddModule(Gandalf, "You shall not pass",Streams=[icetray.I3Frame.DAQ, icetray.I3Frame.Physics])
listtokeep = ["I3EventHeader","InIcePulses","InIceDSTPulses","I3SuperDST","I3MCTree","HLCPulses","RecoParticle"]
tray.AddModule('Keep', 'keeper2', keys=listtokeep)
tray.AddModule("I3Writer", "writer",filename="superevents_"+args.KEEP+"s.i3")
tray.Execute()
tray.Finish()
del tray

