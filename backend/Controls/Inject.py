from time import time
from can2RNET.can2RNET import cansend, dissect_frame, build_frame

def dec2hex(dec, hexlen):
    h = hex(int(dec))[2:]
    return ('0' * hexlen + h)[-hexlen:]

def inject(joystickID):
    global joystick_x, joystick_y
    global rnet_threads_running
    global can_socket
    raw = build_frame(joystickID + "#0000")
    while rnet_threads_running:
        cf, _ = can_socket.recvfrom(16)
        if cf == raw:
            cansend(
                can_socket,
                joystickID + '#' + dec2hex(joystick_x, 2) + dec2hex(joystick_y, 2)
            )

def getJoystickID(start_time):
    global can_socket
    while True:
        cf, _ = can_socket.recvfrom(16)
        frame = dissect_frame(cf)
        frameid = frame.split('#')[0]
        if frameid.startswith("020"):
            return frameid
        if time() > start_time:
            print("JoyFrame wait timed out")
            return "Err!"
