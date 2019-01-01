#Author- Machine Koder (Alex Rössler)
#Description- Fusion360 to Machinekit Interface

import adsk.core, adsk.fusion, adsk.cam, traceback
import threading
import json
import socket
import pickle


ui = adsk.core.UserInterface.cast(None)
app = None
handlers = []
stopFlag = None
myCustomEvent = 'MyCustomEventId'
customEvent = None
udp_client = None


def get_joint_positions(app):
    # ui  = app.userInterface
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    joints = root.joints
    positions = {}
    for i in range(9):
        name = 'Joint%i' % i
        joint = joints.itemByName(name)
        if joint:
            jointMotion = adsk.fusion.SliderJointMotion.cast(joint.jointMotion)
            positions[name] = jointMotion.slideValue * 10.0
    return positions
    
    
class UdpClient(object):
    def __init__(self, ip, port):
        self.port = port
        self.ip = ip
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def send_position(self, positions):
        self.socket.sendto(pickle.dumps(positions), (self.ip, self.port))


# The event handler that responds to the custom event being fired.
class ThreadEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            udp_client.send_position(get_joint_positions(app))
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# The class for the new thread.
class MyThread(threading.Thread):
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event

    def run(self):
        # Every five seconds fire a custom event, passing a random number.
        while not self.stopped.wait(0.5):
            args = {}
            app.fireCustomEvent(myCustomEvent, json.dumps(args)) 


def run(context):
    global ui
    global app
    global udp_client

    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        # dostuff(app)
        
        udp_client = UdpClient('127.0.0.1', 5005)
        
        # Register the custom event and connect the handler.
        global customEvent
        customEvent = app.registerCustomEvent(myCustomEvent)
        onThreadEvent = ThreadEventHandler()
        customEvent.add(onThreadEvent)
        handlers.append(onThreadEvent)

        # Create a new thread for the other processing.        
        global stopFlag        
        stopFlag = threading.Event()
        myThread = MyThread(stopFlag)
        myThread.start()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    adsk.autoTerminate(False)
    
def stop(context):
    try:
        if handlers.count:
            customEvent.remove(handlers[0])
        stopFlag.set() 
        app.unregisterCustomEvent(myCustomEvent)
        ui.messageBox('Stop addin')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))