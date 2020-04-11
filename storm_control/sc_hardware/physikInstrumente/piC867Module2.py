#!/usr/bin/env python
"""
HAL module for emulating a stage.

Hazen 04/17
"""
import math
from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.stageModule as stageModule

import storm_control.sc_hardware.physikInstrumente.piC867 as piC867


class PiStageFunctionality(stageModule.StageFunctionalityNF):
    """
    According to the documentation, 
    https://www.pi-usa.us/fileadmin/user_upload/pi_us/files/product_datasheets/Q-545_Mini_Positioning_Stage_201520192.pdf
    this stage has a maximum velocity of 10mm / second.
    """
    def __init__(self, velocity = None, **kwds):
        super().__init__(**kwds)
        self.max_velocity = 1.0e+3 * velocity # Maximum velocity in um/s (update this, tiger had max 7mm/s but had 1e3 here?)
        
        self.stage.setVelocity(velocity, velocity)

    def calculateMoveTime(self, dx, dy):
        time_estimate = math.sqrt(dx*dx + dy*dy)/self.max_velocity + 1.0
        #print("> stage move time estimate is {0:.3f} seconds".format(time_estimate))
        return time_estimate



class PiStageFunctionalityBroken(PiStageFunctionality):
    """
    This is used in testing to verify that the watchdog timer
    functionality is working.
    """
    def handleMoveTimer(self):
        pass


class PiStageModule(stageModule.StageModule):
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.controller_mutex = QtCore.QMutex() # a shared Mutex for both stages
        self.functionalities = {} # a list of the functionalities 
        configuration = module_params.get("configuration") # get the config parameters from the xml file under <PiController>
        self.controller = piC867.piC867(serialnum1 = configuration.get("serialnum1"), serialnum2 = configuration.get("serialnum2")) 
        if self.controller.getStatus():
            devices = configuration.get("devices") 
            for dev_name in devices.getAttrs():
                # XY stage.
                if (dev_name == "xy_stage"):
                    settings = devices.get(dev_name)
                    
                    # We do this so that the superclass works correctly."
                    self.stage = self.controller
                    
                    self.stage_functionality = PiStageFunctionality(device_mutex = self.controller_mutex,
                                                                    stage = self.stage,
                                                                    update_interval = 500,
                                                                    velocity = settings.get("velocity", 10))
        else:
           self.controller = None
        
