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
        #pidevice2 = GCSDevice(CONTROLLERNAME) 
        #pidevice2.ConnectUSB(serialnum2)
