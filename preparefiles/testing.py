from icecube import icetray, dataio,DomTools, dataclasses
from I3Tray import *
from os import listdir, system
import numpy as np



tray = I3Tray()
tray.AddModule('I3Reader', 'reader',FilenameList=["BigBird.i3"])


def is_deepcore(string):
	if string in (26,27,35,36,37,45,46):
		return True
	else:
		return False

listtokeep = []
listtokeep = ["I3Geometry"]
for string in range (1,86+1):
	framename = "string_"+str(string)+""
	listtokeep.append(framename)


def nonrealevent(frame):
	RP = dataclasses.I3RecoPulse()
	RP.charge = 1
	RP.width = 0.1              #this is the uncertanty; somewhere between start time and start time + width the pulse comes
	RP.flags = 7            #bitwise combination of sources: 
	for string in range (1,86+1):
		RPSM = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, 'HLCPulses')
		RPSM.clear()
		RP.time = 100
		for OM in range (1,60 + 1):
			RPS = dataclasses.I3RecoPulseSeries()
			RP.time += np.log(OM*100)
			RPS.append(RP)
			RPSM[icetray.OMKey(string,OM)] = RPS
		framename = "string_"+str(string)+""
		frame[framename] =  dataclasses.I3RecoPulseSeriesMap(RPSM)

class nonreal_class(icetray.I3ConditionalModule):
	def __init__(self, context):
		super(nonreal_class, self).__init__(context)
		
	def Configure(self):
		pass
	
	def DAQ(self, frame):
		pass
	
	def Physics(self, frame):
		nonrealevent(frame)
		self.PushFrame(frame)
		
	def Geometry(self, frame):
		self.PushFrame(frame)


tray.AddModule(nonreal_class,"non real events")
print listtokeep
tray.AddModule('Keep', 'keeper', keys=listtokeep)
tray.AddModule("I3Writer", "writer",filename="testing.i3")
tray.Execute()
tray.Finish()
del tray