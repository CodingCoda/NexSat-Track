#

import math, time, ephem, serial, keyboard, datetime
from serial import Serial
from datetime import datetime
import atexit, os
from colorama import Fore, Back, Style

pi=3.141952
speedcap = 7
runoffset = 8 * 36000#18000

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

TLE1 = 'COSMOS 1626'
TLE2 = "1 15494U 85009A   19281.68062771 +.00000615 +00000-0 +24157-4 0  9998"
TLE3 = "2 15494 082.4770 124.8092 0002321 018.7503 341.3818 15.23809320896881"


iss = ephem.readtle(str(TLE1), str(TLE2), str(TLE3))

def AltAzi(y, m, d, h, mi, s): #x=0-360 y=-90-90
	home.date = int(y), int(m), int(d), int(h), int(mi), int(s)
	iss.compute(home)
	alt = iss.alt * degrees_per_radian
	azi = iss.az * degrees_per_radian
	return alt, azi

def AltAziNow(): #Get te cuurent alt azi of the ISS at current time
	home.date = datetime.utcnow()
	iss.compute(home)
	alt = iss.alt * degrees_per_radian
	azi = iss.az * degrees_per_radian
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

def slewspeed(var):
	var = abs(var)
	if var <= .005: 	
		return 1
	elif var <= 0.01:	
		return 2
	elif var <= 0.04:
		return 3
	elif var <= 0.08:
		return 4
	elif var <= 0.16:
		return 5
	elif var <= 0.64:
		return 6
	elif var <= 1:
		return 7
	elif var <= 3:
		return 8
	elif var <= 5:
		return 9
	else:
		return 10

	return "ERROR"

os.system("cls")

#if not testTLEAge(TLE2):
#	print("TLE data is more than a week old and may not be accurate!!") 

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
	timelag = b-a-1
	a = time.time()
	os.system("cls")
	
	y, x = getAltAziTelescope()
		
	#y += riseoffset
	#x += runoffset
	
	y1, x1 = AltAzi(datetime.utcnow().year, datetime.utcnow().month, datetime.utcnow().day, datetime.utcnow().hour, datetime.utcnow().minute, datetime.utcnow().second+1+timelag)
	
	#fixing telescope map to match iss map
	if y > 90 and y < 180:
		y = 90-(y-90)
	if y > 270:
		y = y -360
	if y > 180 and y < 270:
		y = (y-180)*-1

	rise = y - y1
	run = x - x1

	speedrise = abs(round(rise,2))#slewspeed(rise)		#abs(round(rise * 2 * riseoffset))
	speedrun = abs(round(run,2))#slewspeed(run)		#abs(round(run * 2 * runoffset))
	
	#speed limit
	if speedrise >= speedcap:
		speedrise = speedcap
	if speedrun >= speedcap:
		speedrun = speedcap
	
	deviation = ((abs(run) + abs(rise)) / 2)
	
	if deviation < 0.1:
		deviationMark = "low"
	if deviation < .5:
		deviationMark = "moderate"
	elif deviation < .8:
		deviationMark = "fairly high"
	elif deviation < 1:
		deviationMark = "high"
	elif deviation < 1.5:
		deviationMark = "very high"
	else:
		deviationMark = "too much"
	
	
	print(Fore.WHITE, " ")
	print("Tracking satelite with " + deviationMark + " (" + str(round(deviation,2)) + ") " + "deviation...")
	print(" ")
	print("TARGET: \t " + str(TLE1))
	print(" ")
	print("Current: \t " + str(round(x,2)) + " \t " + str(round(y,2)))
	print("Target: \t " + str(round(x1,2)) + " \t " + str(round(y1,2)))
	print("Deviation: \t " + str(round(x - x1,2)) + " \t\t " + str(round(y-y1,2)))
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
			
	'''
	if keyboard.is_pressed('w'):
		riseoffset += offsetsize
	elif keyboard.is_pressed('s'):
		riseoffset -= offsetsize
		
	if keyboard.is_pressed('d'):
		runoffset += offsetsize
	elif keyboard.is_pressed('a'):
		runoffset -= offsetsize
	
	if keyboard.is_pressed('q'):
		break
	
	print(" ")
	print("Run off-set: \t" + str(runoffset))
	print("Rise off-set: \t" + str(riseoffset))
	'''
	
	time.sleep(1)
	b = time.time()

'''
azmNeg(0)
azmPos(0)
altNeg(0)
altPos(0)

north = input("Point North? (y/n): ")

if north == "y" or north == "yes" or north == "Y" or north == "YES" or north == "true" or north == "1":
	north = True
	gotoAltAzi(0,0)
	ser.close()
else:
	north = False
	ser.close()
	
os.system("cls")
print("Bye!")
'''




