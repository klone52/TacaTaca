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

#device = usb.core.find(idVendor=0x1209, idProduct=0x0d32)
#print(device)
#device.set_configuration()
#cfg = device.get_active_configuration()
#interface_number = cfg[(0,0)].bInterfaceNumber 
#device.write(0x82,'q 0 1000 10000 10' )

if((A0.motor.is_calibrated)==False):
    # Calibrate motor and wait for it to finish
    print("starting calibration...")
    my_drive.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE

    
while my_drive.axis0.current_state != AXIS_STATE_IDLE:
    time.sleep(0.1)

my_drive.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL

my_drive.axis0.motor.config.current_lim = 25 # Amperes de corriente limite


# To read a value, simply read the property
print("Bus voltage is " + str(my_drive.vbus_voltage) + " [V]")
print("Corriente limite: " + str(my_drive.axis0.motor.config.current_lim) + " [A]")    
print("Velocidad limite: " + str(my_drive.axis0.controller.config.vel_limit) + " [counts/s]")
print("Posicion: " + str(my_drive.axis0.controller.pos_setpoint))
print("Encoder 0 Pos.: " + str(my_drive.axis0.encoder.pos_estimate) + " [counts]")
print("Encoder 1 Pos.: " + str(my_drive.axis1.encoder.pos_estimate) + " [counts]")

#################### EN CASO DE ERROR  ##################################
#dump_errors(my_drive,True) #Lista de errores (textual) y limpia errores
#my_drive.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL

#########################################################################

# Lista de posiciones Pos_Setpoint(SP) y Pos_estimate(EP). No son necesarios
# para el funcionamiento del homing pero para revisar su correcto funcionamiento
# se dejan en el codigo.
SP = [] 
EP = []

print('Buscando rango mecanico...')
timeout = 5
t0 = time.monotonic()
t1 = time.monotonic()
while((A0.encoder.pos_estimate - A0.controller.pos_setpoint < 15000) 
    and (t1-t0 < timeout)):
    A0.controller.pos_setpoint = A0.controller.pos_setpoint - 100
    SP.append(A0.controller.pos_setpoint)
    EP.append(A0.encoder.pos_estimate)  
    t1 = time.monotonic()
    
if(t1-t0 < timeout):
    Pos0 = A0.encoder.pos_estimate
    A0.controller.pos_setpoint = 0
    print('Extremo 1 encontrado.')
    time.sleep(1)
else:
    print('Error en proceso. Timeout excedido')

SP2 = [] 
EP2 = []
t0 = time.monotonic()
t1 = time.monotonic()
while((A0.controller.pos_setpoint - A0.encoder.pos_estimate < 15000) 
    and (t1-t0 < timeout)):
    A0.controller.pos_setpoint = A0.controller.pos_setpoint + 100
    SP2.append(A0.controller.pos_setpoint)
    EP2.append(A0.encoder.pos_estimate)  
    t1 = time.monotonic()

if(t1-t0 < timeout):
    Pos1 = A0.encoder.pos_estimate
    A0.controller.pos_setpoint = 0
    print('Extremo 2 encontrado.')
    time.sleep(1)
else:
    print('Error en proceso. Timeout excedido')

print('Rango de movimiento:' + str(Pos1-Pos0)+ ' [counts]')
    

