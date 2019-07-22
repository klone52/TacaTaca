from __future__ import print_function

import sys
import time
import threading
import platform
import subprocess
import os
import xlwt
from tempfile import TemporaryFile
from fibre.utils import Event
from odrive.enums import errors

from LibTaca.TacaTools import WriteExcel

try:
    if platform.system() == 'Windows':
        import win32console
        import colorama
        colorama.init()
except ImportError:
    print("Could not init terminal features.")
    print("Refer to install instructions at http://docs.odriverobotics.com/#downloading-and-installing-tools")
    sys.stdout.flush()
    pass

_VT100Colors = {
    'green': '\x1b[92;1m',
    'cyan': '\x1b[96;1m',
    'yellow': '\x1b[93;1m',
    'red': '\x1b[91;1m',
    'default': '\x1b[0m'
}

class OperationAbortedException(Exception):
    pass

def dump_errors(odrv, clear=False):
    axes = [(name, axis) for name, axis in odrv._remote_attributes.items() if 'axis' in name]
    axes.sort()
    for name, axis in axes:
        print(name)

        # Flatten axis and submodules
        # (name, remote_obj, errorcode)
        module_decode_map = [
            ('axis', axis, errors.axis),
            ('motor', axis.motor, errors.motor),
            ('encoder', axis.encoder, errors.encoder),
            ('controller', axis.controller, errors.controller),
        ]

        # Module error decode
        for name, remote_obj, errorcodes in module_decode_map:
            prefix = ' '*2 + name + ": "
            if (remote_obj.error != errorcodes.ERROR_NONE):
                print(prefix + _VT100Colors['red'] + "Error(s):" + _VT100Colors['default'])
                errorcodes_tup = [(name, val) for name, val in errorcodes.__dict__.items() if 'ERROR_' in name]
                for codename, codeval in errorcodes_tup:
                    if remote_obj.error & codeval != 0:
                        print("    " + codename)
                if clear:
                    remote_obj.error = errorcodes.ERROR_NONE
            else:
                print(prefix + _VT100Colors['green'] + "no error" + _VT100Colors['default'])

data_rate = 1000
plot_rate = 100
num_samples = 1000

def start_liveplotter2(get_var_callback, ylabel, LegendsList, Save=False, Titulo='', N=0, Write=False):
    """
    Starts a liveplotter.
    The variable that is plotted is retrieved from get_var_callback.
    This function returns immediately and the liveplotter quits when
    the user closes it.
    """

    import matplotlib.pyplot as plt

    cancellation_token = Event()

    global vals
    global labely
    global legends
    global save
    global titulo
    global iteracion
    global write
    vals = []
    labely = ylabel
    legends = LegendsList
    save = Save
    titulo = Titulo
    iteracion = N
    write = Write
    
    def fetch_data():
        global vals
        global write
        global iteracion
        global titulo
        global legends
        Time = []
        Time.append('Tiempo')
        while not cancellation_token.is_set():
            try:
                data = get_var_callback()
            except Exception as ex:
                print(str(ex))
                time.sleep(1)
                continue
            vals.append(data)
            Time.append(time.monotonic())
            if len(vals) > num_samples:
                vals = vals[-num_samples:]
                Time = Time[-num_samples:]
            time.sleep(1/data_rate)
        if(write == True):
            print('Guardando datos...\n')
            datos = []
            
            #Por cada legenda crea una lista vacia como elemento de la lista datos
            for item in legends:
                datos.append([])
            
            #Agregar Legendas al inicio de las listas en datos
            for e,item in enumerate(legends):
                datos[e].append(item)
            
            #Separa los datos de las variables en vals y las deja en sus propias listas
            #contenidas en lista datos
            for i in range(len(vals)):
                for j in range(len(legends)):
                    datos[j].append(vals[i][j])
            
            #Se crea el elemento book y sheet1 para trabajar el excel (xlsx)
            book = xlwt.Workbook()
            sheet1 = book.add_sheet('sheet1')
            
            #Escribe cada lista de datos en las celdas del excel
            for k in range(len(datos)):
                for i,e in enumerate(datos[k]):
                    #write(fila, columna, dato)
                    sheet1.write(i,k,e)
            
            # Se agrega la columna de los tiempos de cada medicion.
            for i,dato in enumerate(Time):        
                sheet1.write(i, len(datos), dato)
    
            # Se revisa si existe la carpeta con el nombre del experimento, si no existe
            # se crea y se guarda el documento en la carpeta
            if not os.path.exists(titulo):
                os.mkdir(titulo)
                print('Carpeta creada para '+titulo+'.\n')
            else:
               print('Ruta existe para '+titulo+'.\n')

            name = titulo+'/'+titulo +'_'+str(iteracion)+".xls"
            book.save(name)
            book.save(TemporaryFile())
            print('Excel '+ Titulo + ' guardado.\n' )    
                
    # TODO: use animation for better UI performance, see:
    # https://matplotlib.org/examples/animation/simple_anim.html
    def plot_data():
        global vals
        global labely
        global save
        global titulo
        global iteracion
        plt.ion()

        # Make sure the script terminates when the user closes the plotter
        def did_close(evt):
            cancellation_token.set()
        fig = plt.figure()
        fig.canvas.mpl_connect('close_event', did_close)

        while not cancellation_token.is_set():
            plt.clf()
            plt.plot(vals)
            plt.legend(legends)
            plt.ylabel(labely)
            plt.title(titulo)
            plt.grid()
            plt.xlabel('N° muestras cada 1 [ms]')
            fig.canvas.draw()
            fig.canvas.start_event_loop(1/plot_rate)
            
        if(save == True):
           if not os.path.exists(titulo):
               os.mkdir(titulo)
               fig.savefig(titulo+'/'+titulo+'_'+str(N))
               print('Carpeta creada, grafico guardado.\n')
           else:
               fig.savefig(titulo+'/'+titulo+'_'+str(N))
               print('Ruta existe, grafico guardado.\n')

    fetch_t = threading.Thread(target=fetch_data)
    fetch_t.daemon = True
    fetch_t.start()
    
    plot_t = threading.Thread(target=plot_data)
    plot_t.daemon = True
    plot_t.start()
        

    return cancellation_token;
    #plot_data()



def print_drv_regs(name, motor):
    """
    Dumps the current gate driver regisers for the specified motor
    """
    fault = motor.gate_driver.drv_fault
    status_reg_1 = motor.gate_driver.status_reg_1
    status_reg_2 = motor.gate_driver.status_reg_2
    ctrl_reg_1 = motor.gate_driver.ctrl_reg_1
    ctrl_reg_2 = motor.gate_driver.ctrl_reg_2
    print(name + ": " + str(fault))
    print("DRV Fault Code: " + str(fault))
    print("Status Reg 1: " + str(status_reg_1) + " (" + format(status_reg_1, '#010b') + ")")
    print("Status Reg 2: " + str(status_reg_2) + " (" + format(status_reg_2, '#010b') + ")")
    print("Control Reg 1: " + str(ctrl_reg_1) + " (" + format(ctrl_reg_1, '#013b') + ")")
    print("Control Reg 2: " + str(ctrl_reg_2) + " (" + format(ctrl_reg_2, '#09b') + ")")

def show_oscilloscope(odrv):
    size = 18000
    values = []
    for i in range(size):
        values.append(odrv.get_oscilloscope_val(i))

    import matplotlib.pyplot as plt
    plt.plot(values)
    plt.show()

def rate_test(device):
    """
    Tests how many integers per second can be transmitted
    """

    # import matplotlib.pyplot as plt
    # plt.ion()

    print("reading 10000 values...")
    numFrames = 10000
    vals = []
    for _ in range(numFrames):
        vals.append(device.axis0.loop_counter)

    loopsPerFrame = (vals[-1] - vals[0])/numFrames
    loopsPerSec = (168000000/(2*10192))
    FramePerSec = loopsPerSec/loopsPerFrame
    print("Frames per second: " + str(FramePerSec))

    # plt.plot(vals)
    # plt.show(block=True)

def usb_burn_in_test(get_var_callback, cancellation_token):
    """
    Starts background threads that read a values form the USB device in a spin-loop
    """

    def fetch_data():
        global vals
        i = 0
        while not cancellation_token.is_set():
            try:
                get_var_callback()
                i += 1
            except Exception as ex:
                print(str(ex))
                time.sleep(1)
                i = 0
                continue
            if i % 1000 == 0:
                print("read {} values".format(i))
    threading.Thread(target=fetch_data, daemon=True).start()

def yes_no_prompt(question, default=None):
    if default is None:
        question += " [y/n] "
    elif default == True:
        question += " [Y/n] "
    elif default == False:
        question += " [y/N] "

    while True:
        print(question, end='')

        choice = input().lower()
        if choice in {'yes', 'y'}:
            return True
        elif choice in {'no', 'n'}:
            return False
        elif choice == '' and default is not None:
            return default
