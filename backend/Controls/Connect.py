import sys
import threading
from time import sleep, time
from can2RNET.can2RNET import cansend, opencansocket
from Inject import inject, getJoystickID
from KeyboardCtrl import keyboard_control

joystick_x = 0x00
joystick_y = 0x00
rnet_threads_running = True

def dec2hex(dec, hexlen):
    h = hex(int(dec))[2:]
    return ('0' * hexlen + h)[-hexlen:]

def RNETsetSpeedRange(speed_range):
    cansend(can_socket, '0A040100#' + dec2hex(speed_range, 2))

def connect():
    global can_socket
    can_socket = opencansocket(0)
    if (can_socket == ''):
        print ('Cannot open CAN interface, exiting.')
        sys.exit()
    print("CAN socket opened successfully.")

    print("Waiting for RNET-Joystick frame")
    joy_id = getJoystickID(time() + 0.20)
    if joy_id == "Err!":
        sys.exit()

    print("Found:", joy_id)
    RNETsetSpeedRange(0)

    threading.Thread(target=keyboard_control, daemon=True).start()
    threading.Thread(target=inject, args=(joy_id,), daemon=True).start()

    start = time()
    while rnet_threads_running:
        sleep(0.5)
        print(f"{round(time()-start, 2)}s  X:{dec2hex(joystick_x,2)}  Y:{dec2hex(joystick_y,2)}")

    print("Exiting")

connect()



