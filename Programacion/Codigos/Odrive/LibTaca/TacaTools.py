#!/usr/bin/env python3
"""
Config python script of startup calibration and configuration's defaults
"""

from __future__ import print_function

import odrive
from odrive.enums import *
from odrive.utils import start_liveplotter
from odrive.utils import start_liveplotter2
from odrive.utils import dump_errors
import time
import xlwt
import xlrd
from xlrd import open_workbook
from tempfile import TemporaryFile

def CalibSystem(my_drive):
# Calibrate motor and wait for it to finish
    A0 = my_drive.axis0

    print("starting calibration...\n")
    A0.encoder.config.use_index = True
    print("Searching for index.\n")
    A0.requested_state = AXIS_STATE_ENCODER_INDEX_SEARCH
    print("Index found.\n")
    
    my_drive.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
       
    while my_drive.axis0.current_state != AXIS_STATE_IDLE:
        time.sleep(0.1)
    
    if(A0.error==0):
        print("Encoder offset calibration: OK\n")
        A0.encoder.config.pre_calibrated = True
        
    A0.config.startup_encoder_index_search = True
    A0.encoder.config.pre_calibrated = True
    A0.motor.config.pre_calibrated = True
    
    A0.motor.config.current_lim = 25 # Amperes de corriente limite
    A0.controller.config.pos_gain = 100
    A0.controller.config.vel_gain = 3/10000
    A0.controller.config.vel_integrator_gain = 0
    
    my_drive.save_configuration()
    print("Config. Saved\n")
    my_drive.reboot()



def Homing(my_drive):
# Lista de posiciones Pos_Setpoint(SP) y Pos_estimate(EP). No son necesarios
# para el funcionamiento del homing pero para revisar su correcto funcionamiento
# se dejan en el codigo.
    A0 = my_drive.axis0
    
    A0.controller.config.vel_limit = 30000
    
    SP = [] 
    EP = []
    
    Rango = 0
    Centro = 0
    
    print('Buscando rango mecanico...\n')
    timeout = 5
    t0 = time.monotonic()
    t1 = time.monotonic()
    while((A0.encoder.pos_estimate - A0.controller.pos_setpoint <25000) 
        and (t1-t0 < timeout)):
        A0.controller.pos_setpoint = A0.controller.pos_setpoint - 100
        SP.append(A0.controller.pos_setpoint)
        EP.append(A0.encoder.pos_estimate)  
        t1 = time.monotonic()
        
    if(t1-t0 < timeout):
        MinPos = A0.encoder.pos_estimate
        A0.controller.pos_setpoint = 0
        print('Extremo 1 encontrado.\n')
        time.sleep(0.75)
    else:
        print('Error en proceso. Timeout excedido.\n')
    
    SP2 = [] 
    EP2 = []
    t0 = time.monotonic()
    t1 = time.monotonic()
    while((A0.controller.pos_setpoint - A0.encoder.pos_estimate < 25000) 
        and (t1-t0 < timeout)):
        A0.controller.pos_setpoint = A0.controller.pos_setpoint + 100
        SP2.append(A0.controller.pos_setpoint)
        EP2.append(A0.encoder.pos_estimate)  
        t1 = time.monotonic()
    
    if(t1-t0 < timeout):
        MaxPos = A0.encoder.pos_estimate
        A0.controller.pos_setpoint = 0
        print('Extremo 2 encontrado.\n')
        time.sleep(0.75)
    else:
        print('Error en proceso. Timeout excedido.\n')
    
    #print('Rango de movimiento:' + str(MaxPos- MinPos)+ ' [counts]')
    
    # Calculo de centro del recorrido
    Rango = MaxPos + abs(MinPos)
    Centro = (MaxPos + MinPos)/2
    
    #Envio carro al centro mecanico
    A0.controller.pos_setpoint = Centro

    return Rango, Centro, MaxPos, MinPos


def WriteExcel(Titulo, Lista, columna):
    
    book = xlwt.Workbook()
    sheet1 = book.add_sheet('sheet1')
    
    for i,e in enumerate(Lista):
        sheet1.write(i,columna,e)
    
    name = Titulo+".xls"
    book.save(name)
    book.save(TemporaryFile())
    print('Excel '+ Titulo + ' guardado.\n' )
  
    
