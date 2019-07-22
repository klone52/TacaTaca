#!/usr/bin/env python3

from __future__ import print_function

import odrive
from odrive.enums import *
from odrive.utils import start_liveplotter
from odrive.utils import dump_errors
import time
import math
import usb.core
import usb.util

# IMPORTANTE: si se trabaja en Anaconda elegir el directroio de trabajo como la 
# la carpeta root donde se tienen los script .py y la carpeta LibTaca
# o en su defecto agregar la ruta a sys.path
from LibTaca.TacaTools import Homing
from LibTaca.TacaTools import WriteExcel
from LibTaca.utilsmod import start_liveplotter2 as lp2

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


## To read a value, simply read the property
#print("Bus voltage is " + str(my_drive.vbus_voltage) + " [V]")
#print("Corriente limite: " + str(my_drive.axis0.motor.config.current_lim) + " [A]")    
#print("Velocidad limite: " + str(my_drive.axis0.controller.config.vel_limit) + " [counts/s]")
#print("Posicion: " + str(my_drive.axis0.controller.pos_setpoint))
#print("Encoder 0 Pos.: " + str(my_drive.axis0.encoder.pos_estimate) + " [counts]")
#print("Encoder 1 Pos.: " + str(my_drive.axis1.encoder.pos_estimate) + " [counts]")
#

#################### EN CASO DE ERROR  ##################################
#dump_errors(my_drive,True) #Lista de errores (textual) y limpia errores
#my_drive.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL

#########################################################################

Rango, Centro, MaxPos, MinPos = Homing(my_drive)


def mov_seguimiento(vel = 30000):
    my_drive.axis0.controller.config.vel_limit = vel    
    
    
    #time.sleep(0.002)
    my_drive.axis0.controller.pos_setpoint = Centro
    time.sleep(0.5)
    my_drive.axis0.controller.pos_setpoint = MaxPos * 0.4
    time.sleep(0.5)
    my_drive.axis0.controller.pos_setpoint = MaxPos* 0.85
    time.sleep(0.5)
    my_drive.axis0.controller.pos_setpoint = Centro
    #for i in range(10):
    #    my_drive.axis0.controller.pos_setpoint = 16000
    #    time.sleep(0.1)
    #    my_drive.axis0.controller.pos_setpoint = -16000
    time.sleep(0.5)
    
    my_drive.axis0.controller.config.vel_limit = 30000    
    my_drive.axis0.controller.pos_setpoint = Centro
    time.sleep(1)
    my_drive.axis0.controller.config.vel_limit = 30000
    
    
def mov_sinusoidal(vel = 30000):
    my_drive.axis0.controller.config.vel_limit = vel 
  
    # A sine wave to test
    t0 = time.monotonic()
    for i in range(600):
        setpoint = ((Rango/2)*0.8)  * math.sin((time.monotonic() - t0)*1) + Centro
        #print("goto " + str(int(setpoint)))
        my_drive.axis0.controller.pos_setpoint = setpoint
        time.sleep(0.001)
   
    my_drive.axis0.controller.pos_setpoint = Centro
    time.sleep(1)
    my_drive.axis0.controller.config.vel_limit = 30000
    
def mov_rampa(vel = 30000):
    my_drive.axis0.controller.config.vel_limit = vel 
    offset = 1000
    my_drive.axis0.controller.pos_setpoint = int(MinPos) + offset
    
    for i in range(90):        
        setpoint = int(MinPos) + Rango*i/100 + offset
        my_drive.axis0.controller.pos_setpoint = setpoint
        time.sleep(0.001)
#    my_drive.axis0.controller.pos_setpoint = Centro
    time.sleep(1)
    my_drive.axis0.controller.config.vel_limit = 30000
    
    

####################      Test de Homing       #######################

#Se prueba la capacidad de repetir el homing correctamente y cual es el error 
#del rango encontrado.
def Test_Homing(k=10):
    RangoExp = []
    MaxRange = 0 
    MinRange = 1000000000
    suma = 0
    for i in range(k):
        Rango, Centro, MaxPos, MinPos = Homing(my_drive)
        RangoExp.append(Rango)
        time.sleep(0.5)
        print('Iteración: '+ str(i))
        
    for item in RangoExp:
        MaxRange = max(MaxRange, item)
        MinRange = min(MinRange, item )
        suma += item
     # Calculo de variables estadisticas para el Homing, no son necesarias.   
#    RangeError = MaxRange - MinRange
#    RangoProm = suma/len(RangoExp)
    
    WriteExcel('Homing_Test', RangoExp, 0)


##############################################################################
    
####################  Test de seguimiento de referencia  #####################
 
def Test_SeguimientoRef(i, img = True, excel = True, name='SeguimientoRef'): 
   
    my_drive.axis0.controller.config.vel_limit = 150000
    
    Legends = ['Encoder_Motor', 'Referencia']
    cancelation_token = lp2(lambda: [
                my_drive.axis0.encoder.pos_estimate,
                my_drive.axis0.controller.pos_setpoint,],'Posición Encoder',Legends, Save=img,
                Titulo = name,N = i, Write = excel)
    
    t0 = time.monotonic() # Tiempo inicial

    my_drive.axis0.controller.pos_setpoint = Centro
    time.sleep(0.5)
    my_drive.axis0.controller.pos_setpoint = MaxPos * 0.4
    time.sleep(0.5)
    my_drive.axis0.controller.pos_setpoint = MaxPos * 0.6
    time.sleep(0.5)
    my_drive.axis0.controller.pos_setpoint = Centro
   
    time.sleep(0.5)
    t1 = time.monotonic() # Tiempo de final
    cancelation_token.set()
    print('Timepo de ejecucion: '+ str(t1-t0) + ' [s]\n')
    my_drive.axis0.controller.config.vel_limit = 30000    
    my_drive.axis0.controller.pos_setpoint = Centro
    time.sleep(2)
    my_drive.axis0.controller.config.vel_limit = 30000
    
############################################################################
    
#################### Test Plataforma #######################
 
# Funcion dieñada para probar la plataforma de pruebas del taca, sin embargo deberia
# funcionar sin platforma.
    
def Test_Plataforma(i, img = True, excel = True, name='SeguimientoRef'): 
   
    my_drive.axis0.controller.config.vel_limit = 100000
    
    Legends = ['Encoder_Motor', 'Referencia']
    cancelation_token = lp2(lambda: [
                my_drive.axis0.encoder.pos_estimate,
                my_drive.axis0.controller.pos_setpoint,],'Posición Encoder',Legends, Save=img,
                Titulo = name,N = i, Write = excel)
    
    t0 = time.monotonic()
    #time.sleep(0.002)
    my_drive.axis0.controller.pos_setpoint = Centro
    time.sleep(0.5)
    my_drive.axis0.controller.pos_setpoint = MaxPos * 0.4
    time.sleep(0.5)
    my_drive.axis0.controller.pos_setpoint = MaxPos* 0.85
    time.sleep(0.5)
    my_drive.axis0.controller.pos_setpoint = Centro
    #for i in range(10):
    #    my_drive.axis0.controller.pos_setpoint = 16000
    #    time.sleep(0.1)
    #    my_drive.axis0.controller.pos_setpoint = -16000
    time.sleep(0.5)
    t1 = time.monotonic()
    cancelation_token.set()
    print('Timepo de ejecucion: '+ str(t1-t0) + ' [s]\n')
    my_drive.axis0.controller.config.vel_limit = 30000    
    my_drive.axis0.controller.pos_setpoint = Centro
    time.sleep(2)
    my_drive.axis0.controller.config.vel_limit = 30000
    
############################################################################    
    

def Test_Plataforma2(i, img = True, excel = True, name='SeguimientoRef'): 
   
    my_drive.axis0.controller.config.vel_limit = 200000
    
    Legends = ['Encoder_Motor', 'Referencia','Encoder_Carro']
    cancelation_token = lp2(lambda: [
                my_drive.axis0.encoder.pos_estimate,
                my_drive.axis0.controller.pos_setpoint,
                my_drive.axis1.encoder.pos_estimate,],'Posición Encoder',Legends, Save=img,
                Titulo = name,N = i, Write = excel)
    
    t0 = time.monotonic()
    #time.sleep(0.002)
    for i in range(5):
        my_drive.axis0.controller.pos_setpoint = Centro
        time.sleep(0.5)
        my_drive.axis0.controller.pos_setpoint = MaxPos* 0.6
        time.sleep(0.5)
   
    #for i in range(10):
    #    my_drive.axis0.controller.pos_setpoint = 16000
    #    time.sleep(0.1)
    #    my_drive.axis0.controller.pos_setpoint = -16000
    time.sleep(0.5)
    t1 = time.monotonic()
    cancelation_token.set()
    print('Timepo de ejecucion: '+ str(t1-t0) + ' [s]\n')
    my_drive.axis0.controller.config.vel_limit = 30000    
    my_drive.axis0.controller.pos_setpoint = Centro
    time.sleep(2)
    my_drive.axis0.controller.config.vel_limit = 30000
    
############################################################################     

####################### Referencia Sinusoidal  #############################
def Test_RefSinusoidal(i, img = True, excel = True, name='RefSinusoidal'):
    Legends = ['Encoder_Motor', 'Referencia']
    cancelation_token = lp2(lambda: [
                my_drive.axis0.encoder.pos_estimate,
                my_drive.axis0.controller.pos_setpoint,
            ],'Posición Encoder',Legends, Save = img, Titulo = name, 
            N = i, Write = excel)
        
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
def Test_ObtencionDatos(i, img = True, excel = True, name='ObtencionDatos'):
    Legends = ["EncoderMotor", "EncoderCarro"]
    cancelation_token = lp2(lambda: [
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
def Test_CorrienteVoltaje(i, img=True, excel=True, name='MedCorrienteVoltaje', mov=0):
    Legends  = ['Corriente Motor','Referencia','EncoderMotor']
    cancelation_token = lp2(lambda: [
                my_drive.axis0.motor.current_control.Iq_measured,
#                my_drive.axis0.motor.current_control.v_current_control_integral_q,
                my_drive.axis0.controller.pos_setpoint,
                my_drive.axis0.encoder.pos_estimate,
            ],'Corriente [A]',Legends, Save=img, Titulo=name, Write=excel,
            N=i)
    time.sleep(0.5)
    veloc = 100000
    if(mov == 0):
        mov_seguimiento(veloc)        
    elif(mov == 1):
        mov_sinusoidal(veloc)
    elif(mov == 2):
        mov_rampa(veloc)
    else:
        mov_seguimiento(veloc)
    
    cancelation_token.set()
    

    
#########################################################################

#for i in range(5):
#    Test_SeguimientoRef(0, name='PIDCalib')
#    time.sleep(0.5)
        
#for i in range(5):
#    Test_RefSinusoidal(i, name='RefSinusoidalSinCarga')
#    time.sleep(1)
for i in range(5):    
    Test_CorrienteVoltaje(i, name='MedCorrienteSinCargaVel100000Rampa',mov=2)
    time.sleep(1)

