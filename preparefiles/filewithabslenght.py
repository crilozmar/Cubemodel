from icecube import icetray, dataio,DomTools, dataclasses
from I3Tray import *
import numpy as np


rootabs = "/data/cristian/MasterThesis/data/EffectiveScatteringCoefficientBe/be_a_400vsDepth.txt"
absdepth, b_inv, a_inv = np.loadtxt(rootabs,usecols=(0,1,2), unpack=True)


depthlist = []

def getdepth(frame):
	global depthlist
	themap = frame["I3ModuleGeoMap"]
	for omkey,series in themap.items():
		if omkey.string == 1 and omkey.om <= 60:
			mymodule = themap[dataclasses.ModuleKey(omkey.string,omkey.om)]
			position = mymodule.pos
			depthlist.append(position[2])

tray = I3Tray()
rooteasygeo = "/data/cristian/WissenschaftenMitarbeiter/IcetrayData/MuonGun/12603/Sunflower_240m/GeoFrame/IceCubeHEX_Sunflower_240m_v3_ExtendedDepthRange_mDOM.GCD.i3"
tray.AddModule('I3Reader', 'reader',FilenameList=[rooteasygeo]) 
tray.Add(getdepth,"build detector", Streams=[icetray.I3Frame.Geometry])
tray.Execute()
tray.Finish()
del tray

def renorm(depthlist):
	middle = (1450.+2450.)/2.
	depthlist = middle - np.array(depthlist)
	return depthlist

depthlist = renorm(depthlist)

tray = I3Tray()
tray.AddModule('I3Reader', 'reader',FilenameList=["BigBird.i3"]) #for example

listtokeep = ["I3Geometry","abs_bright","abs_color","scat_bright","scat_color"]


def nonrealevent(frame,thing):
	RP = dataclasses.I3RecoPulse()
	RP.charge = 0.
	RP.width = 0.1              #this is the uncertanty; somewhere between start time and start time + width the pulse comes
	RP.flags = 7            #bitwise combination of sources: 
	RPSM = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, 'HLCPulses')
	RPSM.clear()
	for string in range (1,86+1):
		RP.time = 100
		for OM in range (1,60 + 1):
			z = depthlist[OM-1]
			if thing ==  "abs":
				chargeval = np.interp(z,absdepth,a_inv)
			elif thing == "scat":
				chargeval = np.interp(z,absdepth,b_inv)
			else:
				print "abs or scat!!"
			RP.charge= chargeval
			RPS = dataclasses.I3RecoPulseSeries()
			RPS.append(RP)
			RPSM[icetray.OMKey(string,OM)] = RPS
	framename = thing+"_bright"
	frame[framename] =  dataclasses.I3RecoPulseSeriesMap(RPSM)
	
	RP.charge = 1.
	RPSM.clear()
	for string in range (1,86+1):
		for OM in range (1,60 + 1):
			z = depthlist[OM-1]
			if thing ==  "abs":
				timeval = np.interp(z,absdepth,a_inv)
			elif thing == "scat":
				timeval = np.interp(z,absdepth,b_inv)
			else: 
				print "abs or scat!!"
			RP.time= np.log10(timeval)
			RPS = dataclasses.I3RecoPulseSeries()
			RPS.append(RP)
			RPSM[icetray.OMKey(string,OM)] = RPS
	framename = thing+"_color"
	frame[framename] =  dataclasses.I3RecoPulseSeriesMap(RPSM)

		
tray.AddModule(nonrealevent, "ee", thing = "abs")
tray.AddModule(nonrealevent, "ee2",thing = "scat")
tray.AddModule('Keep', 'keeper', keys=listtokeep)
tray.AddModule("I3Writer", "writer",filename="iceproperties.i3")
tray.Execute()
tray.Finish()
del tray