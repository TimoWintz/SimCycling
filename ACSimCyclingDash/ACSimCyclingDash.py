import ac   
import json
import mmap
import subprocess
import sys
import acsys
import signal
import os

antManagerExecutable = None
antManagerState      = None
uiElements           = None



    

class RaceState:

    def _getMemoryMap(self):
        return mmap.mmap(0, 1024, "SimCyclingRaceState")

    def updateToMemory(self, stop=True):
        
        car_positions = []
        car_velocities = []

        for i in range(ac.getCarsCount()):
            x,y,z = ac.getCarState(i, acsys.CS.WorldPosition)
            pos = {
                "_x" : x,
                "_y" : y,
                "_z" : z
            }
            car_positions.append(pos)
            x,y,z = ac.getCarState(i, acsys.CS.Velocity)
            vel = {
                "_x" : x,
                "_y" : y,
                "_z" : z
            }
            car_velocities.append(vel)


        #heading = info.physics.heading
        #pitch = info.physics.pitch
        #roll = info.physics.roll
       
        dict = {
            "car_positions" : car_positions,
            "car_velocities" : car_velocities,
            "stop" : stop
            #"heading" : heading,
            #"pitch" : pitch,
            #"roll" : roll
        }
        memoryMap = self._getMemoryMap()
        memoryMap.seek(0)
        memoryMap.write(1024 * b"\0")
        memoryMap.seek(0)
        memoryMap.write(json.dumps(dict).encode())
        memoryMap.close()

class AntManagerState:
    def __init__(self):
        self.BikeCadence = 0
        self.BikeSpeedKmh = 0.0
        self.BikeIncline = 0.0
        self.CyclistHeartRate = 0
        self.CyclistPower = 0.0
        self.TripTotalKm = 0.0
        self.TargetPower = 0.0
        self.TrackLength = 0.0

    def _instanciateFromDict(self, dictionary):
        for k, v in dictionary.items():
            setattr(self, k, v)

    def _getMemoryMap(self):
        return mmap.mmap(0, 256, "SimCycling")

    def updateFromMemory(self):
        memoryMap = self._getMemoryMap()
        memoryMap.seek(0)
        readBytes  = memoryMap.read()
        memoryMap.close()
        readString = readBytes.decode("utf-8").rstrip("\0")
        #ac.console(readString)
        dictData   = json.loads(readString)
        self._instanciateFromDict(dictData)

    def eraseMemory(self):
        memoryMap = self._getMemoryMap()
        memoryMap.seek(0)
        memoryMap.write(bytes(256))
        memoryMap.close()

def start(*args):
    global antManagerExecutable
    ac.console("Hello start")
    if antManagerExecutable is None:
        ac.console("Starting exeinstance")
        try:
            antManagerExecutable = subprocess.Popen(r".\apps\python\ACSimCyclingDash\bin\SimCycling.exe", cwd=os.path.join(os.path.dirname(os.path.realpath(__file__)), "bin"))
            ac.console("Executable launched : " + str(antManagerExecutable))
        except Exception as e:
            ac.log(repr(e))
            ac.console(str(antManagerExecutable))

def stop(*args):
    global antManagerExecutable
    ac.console("Hello stop")
    if antManagerExecutable is not None:
        antManagerExecutable.stdin.write("X")
    antManagerExecutable = None



class UIElement():
    def __init__(self, valueName, appWindow, x, y, fontSize=48, unit="", format=None):
        self.valueName = valueName
        self.unit = unit
        self.label = ac.addLabel(appWindow, "0")
        self.unitLabel = ac.addLabel(appWindow, self.unit)
        self.format = format
        self.x = x
        self.y = y
        self.fontSize = fontSize


    def setup(self):
        ac.setFontSize(self.label, self.fontSize)
        ac.setFontAlignment(self.label, "right")
        ac.setFontSize(self.unitLabel, self.fontSize//2)
        ac.setPosition(self.label, self.x, self.y)  
        ac.setPosition(self.unitLabel, self.x+self.fontSize//10, self.y+self.fontSize//2)

    def update(self, state):
        value = getattr(state, self.valueName)
        if self.format is not None:
            ac.setText(self.label, ("{0:" + self.format + "}").format(value))
        else:
            ac.setText(self.label, "{0}".format(getattr(state, self.valueName)))
        
class UIElements:
    def __init__(self, appWindow):
        self.appWindow = appWindow
        self.uiElements = []
        self.uiElements.append(UIElement("CyclistPower", appWindow, 225, 10, 96, 'W'))
        self.uiElements.append(UIElement("BikeSpeedKmh", appWindow, 115, 130, 48, 'km/h', ".1f"))
        self.uiElements.append(UIElement("BikeCadence", appWindow, 265, 130, 48, 'rpm', ".1f"))
        self.uiElements.append(UIElement("BikeIncline", appWindow, 115, 200, 48, '%', ".1f"))
        self.uiElements.append(UIElement("CyclistHeartRate", appWindow, 265, 200, 48, 'bpm', ".1f"))
        self.uiElements.append(UIElement("TripTotalKm", appWindow, 115, 270, 32, 'km', ".1f"))
        self.uiElements.append(UIElement("TrackLength", appWindow, 265, 270, 32, 'km', ".1f"))

        self.startButton   = ac.addButton(self.appWindow, "start")
        self.stopButton    = ac.addButton(self.appWindow, "stop")

    def setup(self):
        ac.addRenderCallback(self.appWindow, onRender)
        ac.setSize(self.appWindow,333,343)
        ac.drawBorder(self.appWindow,0)
        ac.drawBackground(self.appWindow, 0)
        for el in self.uiElements:
            el.setup()
        self.setupButtons()

    
    def setupButtons(self):
        ac.setSize(self.startButton, 165, 26)
        ac.setSize(self.stopButton , 165, 26)
        ac.setFontSize(self.startButton, 18)
        ac.setFontSize(self.stopButton , 18)
        ac.setFontAlignment(self.startButton, "center")
        ac.setFontAlignment(self.stopButton, "center")
        ac.setPosition(self.startButton, 1  , 318)
        ac.setPosition(self.stopButton , 168, 318)
        ac.addOnClickedListener(self.startButton, start)
        ac.addOnClickedListener(self.stopButton , stop)

    def update(self, antManagerState: AntManagerState):
        for el in self.uiElements:
            el.update(antManagerState)


def acMain(ac_version):
    global uiElements, antManagerState
    appWindow=ac.newApp("ACSimCyclingDash")

    antManagerState = AntManagerState()
    antManagerState.eraseMemory()

    uiElements = UIElements(appWindow)
    uiElements.setup()

    return "ACSimCyclingDash"

def onRender(*args):
    global antManagerExecutable, antManagerState
    try:
        antManagerState.updateFromMemory()
    except Exception as e:
        ac.console(repr(e))
    antManagerState.TrackLength = ac.getTrackLength(0) / 1000
    uiElements.update(antManagerState)
    RaceState().updateToMemory()
    if antManagerExecutable is not None and antManagerExecutable.poll() is not None:
         antManagerExecutable = None

def acShutdown():
    ac.log("BIKEDASH acShutdown")
    #antManagerExecutable.kill()
