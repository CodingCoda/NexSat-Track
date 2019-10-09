#

import math, time, ephem, serial, keyboard, datetime
from serial import Serial
from datetime import datetime
import atexit, os
from colorama import Fore, Back, Style

pi=3.141952
speedcap = 30 #35 is recommended max speed for 6SE 6th gen mount.
refreshrate = .5

comport = "COM4" #TODO Auto-detect port
ser = serial.Serial(comport)

try:
	ser.open()
except:
	try:
		ser.close()
		ser.open()
	except:
		print("Cannot open port!")
		quit()


degrees_per_radian = 180.0 / math.pi
home = ephem.Observer()

home.lon = '151.2218624'
home.lat = '-33.7805312'
home.elevation = 40

TLE1 = 'COSMOS 2058'
TLE2 = "1 20465U 90010A   19282.14924744  .00000184  00000-0  13301-4 0  9999"
TLE3 = "2 20465  82.4897 156.1243 0014919 336.9664  23.0887 14.97914373611666"

sat = ephem.readtle(str(TLE1), str(TLE2), str(TLE3))

def AltAzi(y, m, d, h, mi, s): #x=0-360 y=-90-90
	home.date = int(y), int(m), int(d), int(h), int(mi), int(s)
	sat.compute(home)
	alt = sat.alt * degrees_per_radian
	azi = sat.az * degrees_per_radian
	return alt, azi

def AltAziNow(): #Get te cuurent alt azi of the sat at current time
	home.date = datetime.utcnow()
	sat.compute(home)
	alt = sat.alt * degrees_per_radian
	azi = sat.az * degrees_per_radian
	return alt, azi

def setTimeNow(): #QRSTUVWX
	V = datetime.now().year
	T = datetime.now().month
	U = datetime.now().day
	Q = datetime.now().hour
	R = datetime.now().minute
	S = datetime.now().second
	W = 256 - 10
	X = 0	   #0 standard, 1 daylight savings
	command = ('H' + chr(Q) + chr(R) + chr(S) + chr(T) + chr(U) + chr(V) + chr(W) + chr(X))
	ser.write(command.encode())
	response = ser.read()

def setLocationHere(): #151.13.19 S , -33.46.50 E
	A = 33
	B = 46
	C = 50
	D = 1
	E = 151
	F = 13
	G = 19
	H = 0
	command = ('W' + chr(A) + chr(B) + chr(C) + chr(D) + chr(E) + chr(F) + chr(G) + chr(H))
	ser.write(command.encode())
	response = ser.read()

def azmPos(rate): # In the 0.0.1 update, Needs to convert degrees to arc seconds
	rate = rate * 3600
	rateHigh = int((rate/4) / 256)
	rateLow = int((rate/4) % 256)
	command = ('P' + chr(3) + chr(16) + chr(6) + chr(rateHigh) + chr(rateLow) + chr(0) + chr(0))
	#command = ('P' + chr(2) + chr(16) + chr(36) + chr(rate) + chr(0) + chr(0) + chr(0))
	
	ser.write(command.encode())
	response = ser.read()

def azmNeg(rate):
	rate = rate * 3600
	rateHigh = int((rate/4) / 256)
	rateLow = int((rate/4) % 256)
	command = ('P' + chr(3) + chr(16) + chr(7) + chr(rateHigh) + chr(rateLow) + chr(0) + chr(0))
	#command = ('P' + chr(2) + chr(16) + chr(37) + chr(rate) + chr(0) + chr(0) + chr(0))
	ser.write(command.encode())
	response = ser.read()

def altPos(rate):
	rate = rate * 3600
	rateHigh = int((rate/4) / 256)
	rateLow = int((rate/4) % 256)
	command = ('P' + chr(3) + chr(17) + chr(6) + chr(rateHigh) + chr(rateLow) + chr(0) + chr(0))
	#command = ('P' + chr(2) + chr(17) + chr(36) + chr(rate) + chr(0) + chr(0) + chr(0))
	ser.write(command.encode())
	response = ser.read()

def altNeg(rate):
	rate = rate * 3600
	rateHigh = int((rate/4) / 256)
	rateLow = int((rate/4) % 256)
	command = ('P' + chr(3) + chr(17) + chr(7) + chr(rateHigh) + chr(rateLow) + chr(0) + chr(0))
	#command = ('P' + chr(2) + chr(17) + chr(37) + chr(rate) + chr(0) + chr(0) + chr(0))
	ser.write(command.encode())
	response = ser.read()

def gotoAltAzi(Alt, Azi):
	Alt = format(int(Alt/360*65536), '04X')
	Azi = format(int(Azi/360*65536), '04X')
	command = ("B" + str(Azi) + "," + str(Alt))
	ser.write(command.encode())
	response = ser.read(1)

def getAltAziTelescope(): # x=0-360 and y=0-360
	command = ("Z\r")
	ser.write(command.encode())
	response = ser.read(10).decode("utf-8")
	data = response.split(",")
	azi = data[0]
	alt = data[1]
	alt = alt[:4]
	azi = int(azi, 16)/65536*360
	alt = int(alt, 16)/65536*360
	try:
		return alt, azi
	except:
		print("Telescope doesn't want to speak?")
		quit()

def testTLEAge(TLE2):
	day_of_year = datetime.now().timetuple().tm_yday
	ISSTLEAge = str(TLE2.split(" ")[5])
	ISSTLEAge = ISSTLEAge[2:5]
	if day_of_year - float(ISSTLEAge) > 7:
		return False
	return True

def findPass(): #Find next pass (within the day)
	year = int(datetime.utcnow().year)
	month = int(datetime.utcnow().month)
	day = int(datetime.utcnow().day)
	hour = int(datetime.utcnow().hour)

	#Next pass on same day
	for h in range(hour, 24):
		for mi in range(0, 60):
			for s in range(0, 60):
				x, y = AltAzi(year, month, day, h, mi, s)
				if x > 0 and h > hour:
					return False, day, h, mi, s, y

	#Next pass for next day  (will crash if on next month; time is hard)
	day += 1
	for h in range(0, 24):
		for mi in range(0, 60):
			for s in range(0, 60):
				x, y = AltAzi(year, month, day, h, mi, s)
				if x > 0:
					return True, day, h, mi, s, y
	return False


def debugFlag(state, msg):
	if state:
		print(str(msg))
	else:
		print("ERROR! \t" + str(msg))

os.system("cls")

#if not testTLEAge(TLE2):
#	print("TLE data is more than a week old and may not be accurate!!") TODO Fix this

print(" ")
print("Location: \t " + str(home.lon) + " " + str(home.lat))
print("Satelite: \t " + TLE1)
print("COM Port: \t " + comport)
print(" ")
print("The telescope must be aligned to track the satelite accuratly!")
print(" ")
print("Finding next pass for " + str(TLE1))

if findPass() == False:
	print("Pass not found!")
	print("The satelite will not pass over your location within the next two days.")
	print("You may try changing location, time, or TLE data to fix this issue...")
	quit()
else:
	cort, day, h, mi, s, y = findPass()
	if cort == False:
		print("Next pass found at UTC " + str(h) + ":" + str(mi) + ":" + str(s) + " @ " + str(round(y)))
	else:
		print("Next pass found at UTC " + str(h) + ":" + str(mi) + ":" + str(s) + " @ " + str(round(y)) + " tomorrow")

print(" ")
print("Connecting to telescope...")
try:
	setTimeNow()
	setLocationHere()
	print("Connection made!")
except:
	print("Connection failed...")
	
#time.sleep(5)
print(" ")
print(Fore.GREEN + "Please keep an eye on your telescope at all times!")
#time.sleep(5)

riseoffset = 1
runoffset = 1
offsetsize = 1
b = time.time()
a = time.time()

while 1:
	timelag = abs(b-a-1)
	a = time.time()
	os.system("cls")
	
	y, x = getAltAziTelescope()
	
	y1, x1 = AltAzi(datetime.utcnow().year, datetime.utcnow().month, datetime.utcnow().day, datetime.utcnow().hour, datetime.utcnow().minute, datetime.utcnow().second+refreshrate+timelag)
	
	#fixing telescope map to match telescope map
	if y > 90 and y < 180:
		y = 90-(y-90)
	if y > 270:
		y = y -360
	if y > 180 and y < 270:
		y = (y-180)*-1

	rise = y - y1
	run = x - x1

	speedrise = abs(round(rise,2))
	speedrun = abs(round(run,2))
	
	#speed limit
	if speedrise >= speedcap:
		speedrise = speedcap
	if speedrun >= speedcap:
		speedrun = speedcap
	
	print(Fore.WHITE, " ")
	print("TARGET: \t " + str(TLE1))
	print(" ")
	print("Current: \t " + str(round(x,2)) + " \t " + str(round(y,2)))
	print("Target: \t " + str(round(x1,2)) + " \t " + str(round(y1,2)))
	print(" ")
	print("X Axis Speed: \t " + str(speedrun))
	print("Y Axis Speed: \t " + str(speedrise))
	print("Time Delay: \t " + str(round(timelag,2)))
	
	#Track ISS
	if rise>0:	#Down
		altPos(0)
		altNeg(speedrise)
	else:		#Up
		altNeg(0)
		altPos(speedrise)		

	if abs(run) > 180:
		if run>0:	#Right
			azmNeg(0)
			azmPos(speedrun)
		else:		#Left
			azmPos(0)
			azmNeg(speedrun)
	else:
		if run<0:	#Right
			azmNeg(0)
			azmPos(speedrun)
		else:		#Left
			azmPos(0)
			azmNeg(speedrun)

	time.sleep(refreshrate)
	b = time.time()