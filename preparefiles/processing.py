#!/usr/bin/env python
from os import listdir, system
from os.path import isfile, join
from icecube import icetray, dataio,DomTools, dataclasses
from I3Tray import *

#path_input = "/data/cristian/WissenschaftenMitarbeiter/Icetray_work/ckopper/self_veto_years5and6/fullsample_charge/data/"
#inputfiles_list = [path_input+f for f in listdir(path_input) if isfile(join(path_input, f))]
inputfiles_list = ["SomeCascadeEvents.i3"]
outputname = "SomeCascadeEvents2"
HLC = True


#create a file with only the geometry
tray = I3Tray()
tray.AddModule('I3Reader', 'reader',FilenameList=[inputfiles_list[0]])
keep_keys = ['I3Geometry']
tray.AddModule('Keep', 'keeper', keys=keep_keys)
tray.AddModule("I3Writer", "writer", Streams=[icetray.I3Frame.Geometry],filename="Geometry_only.i3")
tray.AddModule("TrashCan", "YesWeCan")
tray.Execute()
tray.Finish()
del tray

#create a file with the configured keys only woth all events
tray = I3Tray()
tray.AddModule('I3Reader', 'reader',FilenameList=inputfiles_list)

if not HLC:
	tray.AddModule('I3LCPulseCleaning', 'cleaning',
		OutputHLC='HLCPulses',
		OutputSLC='',
		Input="SplitInIcePulses")

keep_keys = ['SplitInIcePulses','SplitInIcePulsesTimeRange','ReextractedInIcePulses','InIcePulses','HLCPulses']
tray.AddModule('Keep', 'keeper', keys=keep_keys)
tray.AddModule("I3Writer", "writer", Streams=[icetray.I3Frame.DAQ,icetray.I3Frame.Physics],filename="AllPhysics.i3")
tray.AddModule("TrashCan", "YesWeCan")
tray.Execute()
tray.Finish()
del tray

#merge the geometry to the physics 
infilenames = ["Geometry_only.i3","AllPhysics.i3"]
tray = I3Tray()
tray.AddModule('I3Reader', 'reader',FilenameList=infilenames)
tray.AddModule("I3Writer", "writer",filename=outputname+".i3")
tray.AddModule("TrashCan", "YesWeCan")
tray.Execute()
tray.Finish()
del tray
print "Ok, I put now",len(inputfiles_list),"events and one fitting geometry into one file called "+str(outputname)+"i3. Is that what you wanted?"


#Truncate time for a nice visualization:
def checktime(timelist,time):
	firstcut = 0. # %
	lastcut = 0.3 # %
	
	last = max(timelist)
	first = min(timelist)
	
	
	lentime = last-first
	lowestval = first+lentime*firstcut
	biggestval = first+lentime*lastcut
	
	if (time >= lowestval) and (time <= biggestval):
		return True
	else:
		return False

def truncatetime(frame):
	timelist = []
	RPSM = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, 'HLCPulses')
	for omkey,series in RPSM.items():
		RPS = RPSM[icetray.OMKey(omkey.string,omkey.om,omkey.pmt)]
		for pulse in RPS:
			timelist.append(pulse.time)

	frame['TruncatedTime'] = dataclasses.I3RecoPulseSeriesMapMask(frame, 'ReextractedInIcePulses', lambda omkey, index, pulse: checktime(timelist,pulse.time) == True)
	
	"""
	newRPSM = dataclasses.I3RecoPulseSeriesMap.copy(frame["HLCPulses"])
	for omkey,series in newRPSM.items():
		RPS = RPSM[icetray.OMKey(omkey.string,omkey.om,omkey.pmt)]
		for pulse in RPS:
			if checktime(pulse.time):
				newRPSM.
	"""

tray = I3Tray()
tray.AddModule('I3Reader', 'reader',FilenameList=[outputname+".i3"])
tray.AddModule(truncatetime,"truncatetime", Streams=[icetray.I3Frame.Physics])
tray.AddModule("I3Writer", "writer",filename=outputname+"3.i3")
tray.Execute()
tray.Finish()
del tray

