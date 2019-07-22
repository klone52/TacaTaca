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


####################Test de seguimiento de referencia  #######################

my_drive.axis0.controller.config.vel_limit = 100000

Legends = ['Encoder_Motor', 'Referencia']
cancelation_token = start_liveplotter2(lambda: [
            my_drive.axis0.encoder.pos_estimate,
            my_drive.axis0.controller.pos_setpoint,
        ],'Posición Encoder',Legends)
t0 = time.monotonic()
#time.sleep(0.002)
my_drive.axis0.controller.pos_setpoint = 0
time.sleep(0.5)
my_drive.axis0.controller.pos_setpoint = 5000
time.sleep(0.5)
my_drive.axis0.controller.pos_setpoint = 10000
time.sleep(0.5)
my_drive.axis0.controller.pos_setpoint = 0
#for i in range(10):
#    my_drive.axis0.controller.pos_setpoint = 16000
#    time.sleep(0.1)
#    my_drive.axis0.controller.pos_setpoint = -16000
time.sleep(0.5)
t1 = time.monotonic()
cancelation_token.set()
print('Timepo de ejecucion: '+ str(t1-t0) + ' [s]')
my_drive.axis0.controller.config.vel_limit = 30000    
my_drive.axis0.controller.pos_setpoint = 0
time.sleep(2)
my_drive.axis0.controller.config.vel_limit = 30000
############################################################################

####################### Referencia Sinusoidal  #############################
Legends = ['Encoder_Motor', 'Referencia']
cancelation_token = start_liveplotter2(lambda: [
            my_drive.axis0.encoder.pos_estimate,
            my_drive.axis0.controller.pos_setpoint,
        ],'Posición Encoder',Legends)
    
my_drive.axis0.controller.config.vel_limit = 80000    

# A sine wave to test
t0 = time.monotonic()
for i in range(600):
    setpoint = 14000.0 * math.sin((time.monotonic() - t0)*1)
    #print("goto " + str(int(setpoint)))
    my_drive.axis0.controller.pos_setpoint = setpoint
    time.sleep(0.001)
t1 = time.monotonic()
cancelation_token.set()
print('Timepo de ejecucion: '+ str(t1-t0) + ' [s]')

my_drive.axis0.controller.pos_setpoint = 0
time.sleep(2)
my_drive.axis0.controller.config.vel_limit = 20000
############################################################################    


####################### Obtención de Datos  #############################
Legends = ["EncoderMotor", "EncoderCarro"]
cancelation_token = start_liveplotter2(lambda: [
            my_drive.axis0.encoder.pos_estimate,
            my_drive.axis1.encoder.pos_estimate,
        ],'Posición Encoder',Legendes)
    
my_drive.axis0.controller.config.vel_limit = 30000    

encoder0_sample = []
encoder1_sample = []
current0_sample = []

# A sine wave to test
t0 = time.monotonic()
for i in range(600):
    setpoint = 14000.0 * math.sin((time.monotonic() - t0)*1)
    #print("goto " + str(int(setpoint)))
    my_drive.axis0.controller.pos_setpoint = setpoint
    time.sleep(0.001)
    encoder0_sample.append(my_drive.axis0.encoder.pos_estimate)
    encoder1_sample.append(my_drive.axis1.encoder.pos_estimate)
    current0_sample.append(my_drive.axis0.motor.current_control.Iq_measured)
t1 = time.monotonic()
cancelation_token.set()
print('Timepo de ejecucion: '+ str(t1-t0) + ' [s]')
my_drive.axis0.controller.pos_setpoint = 0
time.sleep(2)
my_drive.axis0.controller.config.vel_limit = 20000
##############################################################################  




################## Obtención de Corriente y Voltaje en Motor##################
Legends  = ['Corriente Motor']
cancelation_token = start_liveplotter2(lambda: [
            #my_drive.axis0.motor.current_control.Iq_measured,
            my_drive.axis0.motor.current_control.v_current_control_integral_q,
        ],'Corriente [A]',Legends)
    
my_drive.axis0.controller.config.vel_limit = 50000    

encoder0_sample = []
encoder1_sample = []
current0_sample = []
tension0_sample = []

# A sine wave to test
t0 = time.monotonic()
for i in range(600):
    setpoint = 14000.0 * math.sin((time.monotonic() - t0)*10)
    #print("goto " + str(int(setpoint)))
    my_drive.axis0.controller.pos_setpoint = setpoint
    time.sleep(0.001)
    #Mediciones Motor 0
    encoder0_sample.append(my_drive.axis0.encoder.pos_estimate)
    current0_sample.append(my_drive.axis0.motor.current_control.Iq_measured)
    tension0_sample.append(my_drive.axis0.motor.current_control.v_current_control_integral_q)
    
    #Mediciones Motor 1
    encoder1_sample.append(my_drive.axis1.encoder.pos_estimate)
    
t1 = time.monotonic()    
cancelation_token.set()
print('Timepo de ejecucion: '+ str(t1-t0) + ' [s]')

my_drive.axis0.controller.config.vel_limit = 50000    
my_drive.axis0.controller.pos_setpoint = 0
time.sleep(2)
my_drive.axis0.controller.config.vel_limit = 50000
#########################################################################




    #print("Encoder 0 Pos.: " + str(my_drive.axis0.encoder.pos_estimate) + "\t\t[counts]")
    #print("Encoder 1 Pos.: " + str(my_drive.axis1.encoder.pos_estimate) + "\t\t[counts]")