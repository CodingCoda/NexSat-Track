# NexSat Track

NexSat Track is a python script to auto-align all Nexstar SE telescope series to a chosen satelite.  

## Dependencies

NexSat Track will need the following python libraries:

colorama, atexit, ephem, serial, and keyboard.

## Usage

First, align the telescope and attach handcontrol to pc with usb cable and note the com port,
then inside the script add the tle data of the satelite you want to track (default is ISS).
Finally with python 3.7.* ->, just use:
```
python SatTrack.py
```
in a terminal.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.