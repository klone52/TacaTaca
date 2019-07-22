#!/usr/bin/env python3
"""
Example usage of the ODrive python library to monitor and control ODrive devices
"""

from __future__ import print_function

import odrive
from odrive.enums import *
import time
import math

# Find a connected ODrive (this will block until you connect one)
print("finding an odrive...")
my_drive = odrive.find_any()

# Find an ODrive that is connected on the serial port /dev/ttyUSB0
#my_drive = odrive.find_any("serial:/dev/ttyUSB0")

# Calibrate motor and wait for it to finish
print("starting calibration...")
my_drive.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
while my_drive.axis0.current_state != AXIS_STATE_IDLE:
    time.sleep(0.1)

my_drive.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL

# To read a value, simply read the property
print("Bus voltage is " + str(my_drive.vbus_voltage) + " [V]")
print("Corriente limite: " + str(my_drive.axis0.motor.config.current_lim) + " [A]")    
print("Velocidad limite: " + str(my_drive.axis0.controller.config.vel_limit) + " [counts/s]")

# Or to change a value, just assign to the property
#my_drive.axis0.controller.pos_setpoint = 3.14
#print("Position setpoint is " + str(my_drive.axis0.controller.pos_setpoint))

# And this is how function calls are done:
#for i in [1,2,3,4]:
#    print('voltage on GPIO{} is {} Volt'.format(i, my_drive.get_adc_voltage(i)))



# Assign an incompatible value:
#my_drive.motor0.pos_setpoint = "I like trains" # fails with `ValueError: could not convert string to float`
print("Posicion: " + str(my_drive.axis0.controller.pos_setpoint))
print("Encoder 0 Pos.: " + str(my_drive.axis0.encoder.pos_estimate) + " [counts]")
print("Encoder 1 Pos.: " + str(my_drive.axis1.encoder.pos_estimate) + " [counts]")


    