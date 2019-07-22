#!/usr/bin/env python3
"""
Config python script of startup calibration and configuration's defaults
"""

from __future__ import print_function

import odrive
from odrive.enums import *
from odrive.utils import start_liveplotter
from odrive.utils import dump_errors
import time
import math
import usb.core
import usb.util

# Find a connected ODrive (this will block until you connect one)
print("finding an odrive...")
my_drive = odrive.find_any()
A0 = my_drive.axis0
print("Odrive encontrado.")

# Calibrate motor and wait for it to finish


print("starting calibration...")
A0.encoder.config.use_index = True
print("Searching for index.")
A0.requested_state = AXIS_STATE_ENCODER_INDEX_SEARCH
print("Index found.")

my_drive.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
   
while my_drive.axis0.current_state != AXIS_STATE_IDLE:
    time.sleep(0.1)

if(A0.error==0):
    print("Encoder offset calibration: OK")
    A0.encoder.config.pre_calibrated = True
    
A0.config.startup_encoder_index_search = True
A0.encoder.config.pre_calibrated = True
A0.motor.config.pre_calibrated = True
#
#A0.motor.config.current_lim = 25 # Amperes de corriente limite
#A0.controller.config.pos_gain = 100
#A0.controller.config.vel_gain = 3/10000
#A0.controller.config.vel_integrator_gain = 0
#

A0.motor.config.current_lim = 25 # Amperes de corriente limite
A0.controller.config.pos_gain = 20 * 0.90
A0.controller.config.vel_gain = (5.0/10000) * 0.90
A0.controller.config.vel_integrator_gain = 0.5 * 10 * (5.0/10000) * 0.90

my_drive.save_configuration()
print("Config. Saved")
my_drive.reboot()

