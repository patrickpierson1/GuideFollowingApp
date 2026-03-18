import socket
from time import time

try:
    from .can2RNET import cansend, dissect_frame, build_frame
    from . import Shared
except ImportError:
    from can2RNET import cansend, dissect_frame, build_frame
    import Shared

def dec2hex(dec, hexlen):
    h = hex(int(dec))[2:]
    return ('0' * hexlen + h)[-hexlen:]

def inject(can_socket, joystickID):
    raw = build_frame(joystickID + "#0000")

    while not Shared.stop_event.is_set():
        try:
            cf, _ = can_socket.recvfrom(16)
        except socket.timeout:
            continue
        except OSError:
            break

        if cf == raw:
            joystick_x, joystick_y = Shared.get_joystick()
            cansend(
                can_socket,
                joystickID + '#' +
                dec2hex(joystick_x, 2) +
                dec2hex(joystick_y, 2)
            )

def getJoystickID(can_socket, start_time):
    while time() < start_time and not Shared.stop_event.is_set():
        try:
            cf, _ = can_socket.recvfrom(16)
        except socket.timeout:
            continue
        except OSError:
            return "Err!"

        frame = dissect_frame(cf)
        frameid = frame.split('#')[0]

        if frameid.startswith("020"):
            return frameid

    print("JoyFrame wait timed out")
    return "Err!"
