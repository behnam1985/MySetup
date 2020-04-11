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


class NoneStage(QtCore.QObject):
    """
    Emulates a stage hardware object.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.x = 0.0
        self.y = 0.0

    def getStatus(self):
        return True
    
    def goAbsolute(self, x, y):
        self.x = x
        self.y = y

    def goRelative(self, dx, dy):
        self.goAbsolute(self.x + dx, self.y + dy)

    def jog(self, xs, ys):
        pass
    
    def joystickOnOff(self, flag):
        pass

    def position(self):
        return {"x" : self.x,
                "y" : self.y}

    def setVelocity(self, vx, vy):
        pass

    def shutDown(self):
        pass

    def zero(self):
        self.x = 0.0
        self.y = 0.0
        
        
        

class NoneStageFunctionality(stageModule.StageFunctionality):
    positionUpdate = QtCore.pyqtSignal(dict)
    
    def __init__(self, update_interval = None, **kwds):
        """
        update_interval - How frequently to update in milli-seconds, something 
                          like 500 is usually good.
        """
        super().__init__(**kwds)
        self.am_moving = False
        self.pos_dict = self.stage.position()

        # Pretend it takes 200ms to move, regardless of the actual distance.
        #
        self.move_timer = QtCore.QTimer()
        self.move_timer.setInterval(200)
        self.move_timer.setSingleShot(True)
        self.move_timer.timeout.connect(self.handleMoveTimer)
        
        # Each time this timer fires we'll 'query' the stage for it's
        # current position.
        #
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(update_interval)
        self.update_timer.timeout.connect(self.handleUpdateTimer)
        self.update_timer.start()

        # We use a 'relay' signal as the stage might return
        # stale information when it is moving. However the
        # HardwareWorker that is querying the stage might not
        # know that the stage is moving.
        #
        self.positionUpdate.connect(self.handlePositionUpdate)

    def goAbsolute(self, x, y):
        self.am_moving = True
        self.update_timer.stop()
        
        super().goAbsolute(x, y)
        
        self.pos_dict = {"x" : x, "y" : y}
        
        self.isMoving.emit(True)
        self.move_timer.start()

    def handleMoveTimer(self):
        self.isMoving.emit(False)
        self.am_moving = False
        self.update_timer.start()

    def handlePositionUpdate(self, pos_dict):
        if not self.am_moving:
            self.pos_dict = pos_dict
            self.stagePosition.emit(self.pos_dict)
            
    def handleUpdateTimer(self):
        """
        Query the stage for its current position.
        """
        self.mustRun(task = self.position,
                     ret_signal = self.positionUpdate)

    def position(self):
        return self.stage.position()

    def wait(self):
        self.update_timer.stop()
        super().wait()




class PiStageFunctionality(stageModule.StageFunctionality):
    positionUpdate = QtCore.pyqtSignal(dict)
    
    def __init__(self, update_interval = None, velocity = 10.0, **kwds):
        """
        update_interval - How frequently to update in milli-seconds, something 
                          like 500 is usually good.
        """
        super().__init__(**kwds)
        self.am_moving = False
        self.pos_dict = self.stage.position()
        
        self.max_velocity = velocity # Maximum velocity in um/s (update this, tiger had max 7mm/s but had 1e3 here?)
        self.stage.setVelocity(velocity, velocity)

        # Pretend it takes 200ms to move, regardless of the actual distance.
        #
        self.move_timer = QtCore.QTimer()
        self.move_timer.setInterval(200)
        self.move_timer.setSingleShot(True)
        self.move_timer.timeout.connect(self.handleMoveTimer)
        
        # Each time this timer fires we'll 'query' the stage for it's
        # current position.
        #
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(update_interval)
        self.update_timer.timeout.connect(self.handleUpdateTimer)
        self.update_timer.start()

        # We use a 'relay' signal as the stage might return
        # stale information when it is moving. However the
        # HardwareWorker that is querying the stage might not
        # know that the stage is moving.
        #
        self.positionUpdate.connect(self.handlePositionUpdate)

    def goAbsolute(self, x, y):
        self.am_moving = True
        self.update_timer.stop()
        
        super().goAbsolute(x, y)
        
        self.pos_dict = {"x" : x, "y" : y}
        
        self.isMoving.emit(True)
        self.move_timer.start()

    def handleMoveTimer(self):
        self.isMoving.emit(False)
        self.am_moving = False
        self.update_timer.start()

    def handlePositionUpdate(self, pos_dict):
        if not self.am_moving:
            self.pos_dict = pos_dict
            self.stagePosition.emit(self.pos_dict)
            
    def handleUpdateTimer(self):
        """
        Query the stage for its current position.
        """
        self.mustRun(task = self.position,
                     ret_signal = self.positionUpdate)

    def position(self):
        return self.stage.position()

    def wait(self):
        self.update_timer.stop()
        super().wait()


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

        configuration = module_params.get("configuration")
        self.controller = piC867.piC867(serialnum1 = configuration.get("serialnum1"), serialnum2 = configuration.get("serialnum2")) 
        if self.controller.getStatus():
            devices = configuration.get("devices") 
            for dev_name in devices.getAttrs():
                # XY stage.
                if (dev_name == "xy_stage"):
                    self.vel = devices.get(dev_name).get("velocity")
                    
                    # We do this so that the superclass works correctly."
                    self.stage = self.controller
                    
                    self.stage_functionality = PiStageFunctionality(device_mutex = QtCore.QMutex(),
                                                    stage = self.stage,
                                                    velocity = self.vel,
                                                    update_interval = 500)
        else:
           self.controller = None
        
        #self.stage = NoneStage()
        #self.stage_functionality = NoneStageFunctionality(device_mutex = QtCore.QMutex(),
        #                                                  stage = self.stage,
        #                                                  update_interval = 500)



class PiStageModuleBroken(PiStageModule):
    """
    This is in testing to verify that the watchdog timer
    functionality is working.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.stage_functionality = PiStageFunctionalityBroken(device_mutex = QtCore.QMutex(),
                                                                stage = self.stage,
                                                                update_interval = 500)

        self.watchdog_timeout = 100
