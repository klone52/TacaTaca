#!/usr/bin/env python3

from __future__ import print_function

import odrive
from odrive.enums import *
from odrive.utils import start_liveplotter
from odrive.utils import start_liveplotter2
from odrive.utils import dump_errors
import time
import math
import pandas as pd
import usb.core
import usb.util
import serial


ser = serial.Serial('COM4', 115200, timeout = 1)
ser.is_open
ser.write(b'r axis0.encoder.pos_estimate\n')
s = ser.read(64)
print(s)
ser.write(b'w axi0.encoder.set_linear_count(0)\n')
s = ser.read(64)
print(s)
ser.close()


# Find a connected ODrive (this will block until you connect one)
print("finding an odrive...")
my_drive = odrive.find_any()
A0 = my_drive.axis0
print("Odrive found.")
# Find an ODrive that is connected on the serial port /dev/ttyUSB0
#my_drive = odrive.find_any("serial:/dev/ttyUSB0")


#Protocolo USB
#
#idVendor 0x1209
#idProduct 0x0d32
#
#EndPoint 0x3 (Bulk Out)
#EndPoint 0x83 (Bulk In)

device = usb.core.find(idVendor=0x1209, idProduct=0x0d32)
print(device)
device.set_configuration()
cfg = device.get_active_configuration()
#interface_number = cfg[(0,0)].bInterfaceNumber 
#device.write(0x83,'q 0 1000 10000 10' )
#
#if((A0.motor.is_calibrated)==False):
#    # Calibrate motor and wait for it to finish
#    print("starting calibration...")
#    my_drive.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
#
#    
#while my_drive.axis0.current_state != AXIS_STATE_IDLE:
#    time.sleep(0.1)
#
#my_drive.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
#
#my_drive.axis0.motor.config.current_lim = 25 # Amperes de corriente limite


#################### EN CASO DE ERROR  ##################################
#dump_errors(my_drive,True) #Lista de errores (textual) y limpia errores
#my_drive.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL

#########################################################################


