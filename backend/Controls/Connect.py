import sys
import socket
import threading
from time import sleep, time
try:
    from .can2RNET import cansend, opencansocket
    from .Inject import inject, getJoystickID
    from .KeyboardCtrl import keyboard_control
    from . import Shared
except ImportError:
    from can2RNET import cansend, opencansocket
    from Inject import inject, getJoystickID
    from KeyboardCtrl import keyboard_control
    import Shared

def dec2hex(dec, hexlen):
    h = hex(int(dec))[2:]
    return ('0' * hexlen + h)[-hexlen:]

def RNETsetSpeedRange(can_socket, speed_range):
    cansend(can_socket, '0A040100#' + dec2hex(speed_range, 2))

def connect(use_keyboard=False):
    can_socket = opencansocket(0)
    if can_socket == '':
        print('Cannot open CAN interface, exiting.')
        sys.exit()

    can_socket.settimeout(0.1)

    print("CAN socket opened successfully.")
    print("Waiting for RNET-Joystick frame")

    joy_id = getJoystickID(can_socket, time() + 0.20)
    if joy_id == "Err!":
        can_socket.close()
        sys.exit()

    print("Found:", joy_id)
    RNETsetSpeedRange(can_socket, 0)
    print(f"Keyboard control {'enabled' if use_keyboard else 'disabled'}")

    kb_thread = None
    inj_thread = threading.Thread(target=inject, args=(can_socket, joy_id))

    if use_keyboard:
        kb_thread = threading.Thread(target=keyboard_control)
        kb_thread.start()
    inj_thread.start()

    start = time()

    try:
        while not Shared.stop_event.is_set():
            sleep(0.5)
            joystick_x, joystick_y = Shared.get_joystick()
            print(
                f"{round(time()-start, 2)}s  "
                f"X:{dec2hex(joystick_x,2)}  "
                f"Y:{dec2hex(joystick_y,2)}"
            )
    except KeyboardInterrupt:
        print("\nStopping...")
        Shared.stop_event.set()
    finally:
        Shared.stop_event.set()
        Shared.reset_joystick()

        try:
            can_socket.close()
        except Exception:
            pass

        if kb_thread is not None:
            kb_thread.join(timeout=1.0)
        inj_thread.join(timeout=1.0)

        print("Exiting cleanly")

if __name__ == "__main__":
    use_keyboard = "--no-keyboard" not in sys.argv
    connect(use_keyboard=use_keyboard)
