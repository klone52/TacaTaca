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
while((A0.encoder.pos_estimate - A0.controller.pos_setpoint <20000) 
    and (t1-t0 < timeout)):
    A0.controller.pos_setpoint = A0.controller.pos_setpoint - 100
    SP.append(A0.controller.pos_setpoint)
    EP.append(A0.encoder.pos_estimate)  
    t1 = time.monotonic()
    
if(t1-t0 < timeout):
    MinPos = A0.encoder.pos_estimate
    A0.controller.pos_setpoint = 0
    print('Extremo 1 encontrado.')
    time.sleep(1)
else:
    print('Error en proceso. Timeout excedido')

SP2 = [] 
EP2 = []
t0 = time.monotonic()
t1 = time.monotonic()
while((A0.controller.pos_setpoint - A0.encoder.pos_estimate < 20000) 
    and (t1-t0 < timeout)):
    A0.controller.pos_setpoint = A0.controller.pos_setpoint + 100
    SP2.append(A0.controller.pos_setpoint)
    EP2.append(A0.encoder.pos_estimate)  
    t1 = time.monotonic()

if(t1-t0 < timeout):
    MaxPos = A0.encoder.pos_estimate
    A0.controller.pos_setpoint = 0
    print('Extremo 2 encontrado.')
    time.sleep(1)
else:
    print('Error en proceso. Timeout excedido')

print('Rango de movimiento:' + str(MaxPos- MinPos)+ ' [counts]')

# Calculo de centro del recorrido
Rango = MaxPos + abs(MinPos)
Centro = (MaxPos + MinPos)/2

#Envio carro al centro mecanico
A0.controller.pos_setpoint = Centro



####################Test de seguimiento de referencia  #######################

my_drive.axis0.controller.config.vel_limit = 100000

Legends = ['Encoder_Motor', 'Referencia']
cancelation_token = start_liveplotter2(lambda: [
            my_drive.axis0.encoder.pos_estimate,
            my_drive.axis0.controller.pos_setpoint,
        ],'Posición Encoder',Legends)
t0 = time.monotonic()
#time.sleep(0.002)
my_drive.axis0.controller.pos_setpoint = Centro
time.sleep(0.5)
my_drive.axis0.controller.pos_setpoint = MaxPos * 0.5
time.sleep(0.5)
my_drive.axis0.controller.pos_setpoint = MaxPos * 0.8
time.sleep(0.5)
my_drive.axis0.controller.pos_setpoint = Centro
#for i in range(10):
#    my_drive.axis0.controller.pos_setpoint = 16000
#    time.sleep(0.1)
#    my_drive.axis0.controller.pos_setpoint = -16000
time.sleep(0.5)
t1 = time.monotonic()
cancelation_token.set()
print('Timepo de ejecucion: '+ str(t1-t0) + ' [s]')
my_drive.axis0.controller.config.vel_limit = 30000    
my_drive.axis0.controller.pos_setpoint = Centro
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
    setpoint = ((Rango/2)*0.8 + Centro)* math.sin((time.monotonic() - t0)*1)
    #print("goto " + str(int(setpoint)))
    my_drive.axis0.controller.pos_setpoint = setpoint
    time.sleep(0.001)
t1 = time.monotonic()
cancelation_token.set()
print('Timepo de ejecucion: '+ str(t1-t0) + ' [s]')

my_drive.axis0.controller.pos_setpoint = Centro
time.sleep(2)
my_drive.axis0.controller.config.vel_limit = 20000
############################################################################    


####################### Obtención de Datos  #############################
Legends = ["EncoderMotor", "EncoderCarro"]
cancelation_token = start_liveplotter2(lambda: [
            my_drive.axis0.encoder.pos_estimate,
            my_drive.axis1.encoder.pos_estimate,
        ],'Posición Encoder',Legends)
    
my_drive.axis0.controller.config.vel_limit = 30000    

encoder0_sample = []
encoder1_sample = []
current0_sample = []

# A sine wave to test
t0 = time.monotonic()
for i in range(600):
    setpoint = ((Rango/2)*0.8 + Centro)  * math.sin((time.monotonic() - t0)*1)
    #print("goto " + str(int(setpoint)))
    my_drive.axis0.controller.pos_setpoint = setpoint
    time.sleep(0.001)
    encoder0_sample.append(my_drive.axis0.encoder.pos_estimate)
    encoder1_sample.append(my_drive.axis1.encoder.pos_estimate)
    current0_sample.append(my_drive.axis0.motor.current_control.Iq_measured)
t1 = time.monotonic()
cancelation_token.set()
print('Timepo de ejecucion: '+ str(t1-t0) + ' [s]')
my_drive.axis0.controller.pos_setpoint = Centro
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
    setpoint = MaxPos* 0.8 * math.sin((time.monotonic() - t0)*10)
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
my_drive.axis0.controller.pos_setpoint = Centro
time.sleep(2)
my_drive.axis0.controller.config.vel_limit = 50000
#########################################################################




    #print("Encoder 0 Pos.: " + str(my_drive.axis0.encoder.pos_estimate) + "\t\t[counts]")
    #print("Encoder 1 Pos.: " + str(my_drive.axis1.encoder.pos_estimate) + "\t\t[counts]")