#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Connect to a PI stage using two C-867 PI controllers and a M-686.D64 translation stage

Behnam Abaie, April, 2020

Notes: 
This module requires the PIPython library that ships with the PI controllers and is 
accessible online by User Name and Password.
The path to the library can be added to the python path using setup.py in the library;
for more information read readme.txt file in the package.
"""


from __future__ import print_function

# Update the path to the PIPython Library: 
#
# Note: This might be better done by creating a xyz.pth module in the Python
#       library folder?
# 
import sys
sys.path.append(r'C:\Users\behna\Documents\GitHub\PI\PIPython-1.5.0.10')

from copy import deepcopy

import storm_control.sc_library.parameters as params

from pipython import GCSDevice, pitools

#CONTROLLERNAME = 'E-873.3QTU'  # 'C-884' will also work
#STAGES = ['Q-545.140', 'Q-545.140', 'Q-545.140']  #, 'Q-545.140',
CONTROLLERNAME = 'C-867'
STAGES = ['M-686.D64']
REFMODES = 'FRF' # ['FNL', 'FRF']



class piC867(object):

    ## __init__
    #
    # Connect to the piC-867 controllers.
    #
    #
    def __init__(self, serialnum1 = '0109029920',serialnum2 = '0109029922'):   # should become a parameter, see other stages
        print(serialnum1, serialnum2, sep = '\n')
        
        pidevice1 = GCSDevice(CONTROLLERNAME) 
        pidevice1.ConnectUSB(serialnum1) 
        pidevice2 = GCSDevice(CONTROLLERNAME) 
        pidevice2.ConnectUSB(serialnum2)
        print('connected: {}'.format(pidevice1.qIDN().strip()),'connected: {}'.format(pidevice2.qIDN().strip()), sep = '\n')

        # Show the version info which is helpful for PI support when there
        # are any issues.

        if pidevice1.HasqVER():
            print('version info:\n{}'.format(pidevice1.qVER().strip()))
        #if pidevice2.HasqVEL():
        #    print('version info:\n{}'.format(pidevice2.qVER().strip()))
        
        # In the module pipython.pitools there are some helper
        # functions to make using a PI device more convenient. The "startup"
        # function will initialize your system. There are controllers that
        # cannot discover the connected stages hence we set them with the
        # "stages" argument. The desired referencing method (see controller
        # user manual) is passed as "refmode" argument. All connected axes
        # will be stopped if they are moving and their servo will be enabled.

        print('initialize connected stages...')
        pitools.startup(pidevice1, stages=STAGES, refmodes=REFMODES)
        pitools.startup(pidevice2, stages=STAGES, refmodes=REFMODES)
        
        # Now we query the allowed motion range and current position of all
        # connected stages. GCS commands often return an (ordered) dictionary
        # with axes/channels as "keys" and the according values as "values".

        self.pidevice1 = pidevice1
        self.pidevice2 = pidevice2
        self.pidevice = pidevice2
        
        self.wait = 1 # move commands wait for motion to stop
        self.unit_to_um = 1000.0 # PI stage's unit is in millimeters
        self.um_to_unit = 1.0/self.unit_to_um


        # Connect to the stage.
        self.good = 1

        # get min and max range for X controller
        self.rangemin_x = pidevice1.qTMN()
        self.rangemax_x = pidevice1.qTMX()
        self.curpos_x = pidevice1.qPOS()

        # get min and max range for Y controller        
        self.rangemin_y = pidevice2.qTMN()
        self.rangemax_y = pidevice2.qTMX()
        self.curpos_y = pidevice2.qPOS()
        

    ## getStatus
    #
    # @return True/False if we are actually connected to the stage.
    #
    def getStatus(self):
        return self.good

    ## goAbsolute
    #
    # @param x Stage x position in um.
    # @param y Stage y position in um.
    #
    def goAbsolute(self, x, y):
        if self.good:
            print(x,y)
            # If the stage is currently moving due to a jog command
            # and then you try to do a positional move everything
            # will freeze, so we stop the stage first.
            # self.jog(0.0,0.0)

            X = x * self.um_to_unit
            Y = y * self.um_to_unit
            if X >= self.rangemin_x['1'] and X <= self.rangemax_x['1'] and Y >= self.rangemin_y['1'] and Y <= self.rangemax_y['1']:
                self.pidevice1.MOV(1, X)
                self.pidevice2.MOV(1, Y)
            else:
                print('requested move is outside stage range!')

    ## goRelative
    #
    # @param dx Amount to displace the stage in x in um.
    # @param dy Amount to displace the stage in y in um.
    #
    def goRelative(self, dx, dy):
        if self.good:
            # self.jog(0.0,0.0)
            x0 = self.pidevice1.qPOS(1)[1]  # query single axis [need to check units. Also, shouldn't this be zero indexed?]
            y0 = self.pidevice2.qPOS(1)[1]  # query single axis
                # position = pidevice.qPOS()[str(axis)] # query all axes
            X = x0 + dx * self.um_to_unit
            Y = y0 + dy * self.um_to_unit
            if X >= self.rangemin_x['1'] and X <= self.rangemax_x['1'] and Y >= self.rangemin_y['1'] and Y <= self.rangemax_y['1']:
                self.pidevice1.MOV(1, X)
                self.pidevice2.MOV(1, Y)
            else:
                print('requested move is outside stage range')
            # pitools.waitontarget(self.pidevice, axes=1) # actively hold on target
            # pitools.waitontarget(self.pidevice, axes=2) # actively hold on target
            
            
    ## position
    #
    # @return [stage x (um), stage y (um), stage z (um)]
    #
    def position(self):
        if self.good:
            x0 = self.pidevice1.qPOS(1)[1] * self.unit_to_um  # query single axis and convert to um
            y0 = self.pidevice2.qPOS(1)[1] * self.unit_to_um  # query single axis and convert to um
            return {"x" : x0,
                "y" : y0}
    ## jog
    #
    # @param x_speed Speed to jog the stage in x in um/s.
    # @param y_speed Speed to jog the stage in y in um/s.
    #
    def jog(self, x_speed, y_speed):
        pass
        # figure out how to do something here
        # if self.good:
        #     c_xs = c_double(x_speed * self.um_to_unit)
        #     c_ys = c_double(y_speed * self.um_to_unit)
        #     c_zr = c_double(0.0)
        #     tango.LSX_SetDigJoySpeed(self.LSID, c_xs, c_ys, c_zr, c_zr)

    ## joystickOnOff
    #
    # @param on True/False enable/disable the joystick.
    #
    def joystickOnOff(self, on):
        pass
        # No joystick used

    ## lockout
    #
    # Calls joystickOnOff.
    #
    # @param flag True/False.
    #
    def lockout(self, flag):
        self.joystickOnOff(not flag)

            

    ## setVelocity
    #
    # FIXME: figure out how to set velocity..
    #
    def setVelocity(self, vx, vy):
        self.pidevice1.VEL(1, vx)
        self.pidevice2.VEL(1, vy)

    ## shutDown
    #
    # Disconnect from the stage.
    #
    def shutDown(self):
        # Disconnect from the stage
        if self.good:
            self.pidevice1.StopAll(noraise=True)
            pitools.waitonready(self.pidevice1)  # there are controllers that need some time to halt all axes
            self.pidevice2.StopAll(noraise=True)
            pitools.waitonready(self.pidevice2)  # there are controllers that need some time to halt all axes

    ## zero
    #
    # Set the current position as the new zero position.
    #
    #def zero(self):
    #    if self.good:
    #        pitools.startup(self.pidevice1, stages=STAGES, refmodes='POS')
    #        pitools.startup(self.pidevice2, stages=STAGES, refmodes='POS')
    
    