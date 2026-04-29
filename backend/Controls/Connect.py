# /backend/Controls/Connect.py
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

# converts dec to hex (zero-padded)
def dec2hex(dec, hexlen):
    h = hex(int(dec))[2:]
    return ('0' * hexlen + h)[-hexlen:]

# injects the speed range into the RNET system, 0-255
def RNETsetSpeedRange(can_socket, speed_range):
    # speed_range expected 0..255
    frame = '0A040100#' + dec2hex(speed_range, 2) + '00'
    print("RNETsetSpeedRange sending:", frame)
    cansend(can_socket, '0A040100#' + dec2hex(speed_range, 2))

# connects to RNET bus
def connect(use_keyboard=False):

    # Open CAN socket
    can_socket = opencansocket(0)
    if can_socket == '':
        print('Cannot open CAN interface, exiting.')
        sys.exit()
    can_socket.settimeout(0.1)
    print("CAN socket opened successfully.")

    # Wait for joystick frame to identify the correct ID
    print("Waiting for RNET-Joystick frame")
    joy_id = getJoystickID(can_socket, time() + 0.20)
    if joy_id == "Err!":
        can_socket.close()
        sys.exit()
    print("Found:", joy_id)

    # On startup, set speed to 0 (minimum) to ensure a known state
    RNETsetSpeedRange(can_socket, 0)

    # Start threads for keyboard control and CAN injection
    print(f"Keyboard control {'enabled' if use_keyboard else 'disabled'}")
    kb_thread = None
    inj_thread = threading.Thread(target=inject, args=(can_socket, joy_id))
    if use_keyboard:
        kb_thread = threading.Thread(target=keyboard_control)
        kb_thread.start()
    inj_thread.start()
    start = time()

    # Keep track of last applied speed byte to avoid redundant frames
    last_applied_speed_byte = None
    # Keep track of last seen timestamp of the max-speed file so we can detect changes
    last_maxspeed_ts = 0.0

    # Main loop to print joystick state every 0.5 seconds, and handle graceful shutdown on Ctrl+C
    try:
        while not Shared.stop_event.is_set():
            sleep(0.5)

            # Read file-backed max speed state and apply if changed (always apply first time)
            try:
                current_ts = Shared.get_max_speed_state_timestamp()
                if current_ts and current_ts != last_maxspeed_ts:
                    last_maxspeed_ts = current_ts
                    new_percent = Shared.get_max_speed_percent()
                    if new_percent is None:
                        speed_byte = 0
                    else:
                        speed_byte = int(new_percent)
                    if speed_byte != last_applied_speed_byte:
                        frame = '0A040100#' + dec2hex(speed_byte, 2) + '00'
                        print(f"Applying max speed -> {new_percent} % -> frame: {frame}")
                        RNETsetSpeedRange(can_socket, speed_byte)
                        last_applied_speed_byte = speed_byte
            except Exception as e:
                print("Error applying max speed:", e)

            joystick_x, joystick_y = Shared.get_joystick()
            print(
                f"{round(time()-start, 2)}s  "
                f"X:{dec2hex(joystick_x,2)}  "
                f"Y:{dec2hex(joystick_y,2)}"
            )

    # Handle Ctrl+C for graceful shutdown
    except KeyboardInterrupt:
        print("\nStopping...")
        Shared.stop_event.set()

    # Ensure all threads are stopped and resources are cleaned up
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
