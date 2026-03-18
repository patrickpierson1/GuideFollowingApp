# /backend/Controls/KeyboardCtrl.py
import os
import sys
import termios
import tty
import select
from time import time
try:
    from . import Shared
except ImportError:
    import Shared

ARROW_HOLD_TIME = 0.18
KEYBOARD_COMMAND_HOLD_SECONDS = 0.25

# reads all available data from stdin without blocking
def read_available_stdin():
    data = ""
    fd = sys.stdin.fileno()

    while True:
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if not ready:
            break
        chunk = os.read(fd, 64)
        if not chunk:
            break
        data += chunk.decode(errors="ignore")
        if len(chunk) < 64:
            break
    return data

# parses the input buffer for arrow key sequences and updates the joystick state accordingly
def update_arrow_state_from_buffer(buf):
    i = 0

    # Arrow keys send escape sequences like '\x1b[A' for up, '\x1b[B' for down, etc.
    while i < len(buf):
        ch = buf[i]
        if ch.lower() == 'q':
            Shared.stop_event.set()
            i += 1
            continue
        if ch == '\x1b':
            if i + 2 >= len(buf):
                return buf[i:]
            if buf[i + 1] == '[':
                code = buf[i + 2]
                now = time()

                # Update the last press time for the corresponding arrow key
                if code == 'A':
                    Shared.last_up = now
                    i += 3
                    continue
                elif code == 'B':
                    Shared.last_down = now
                    i += 3
                    continue
                elif code == 'C':
                    Shared.last_right = now
                    i += 3
                    continue
                elif code == 'D':
                    Shared.last_left = now
                    i += 3
                    continue
            i += 1
            continue
        i += 1
    return ""

# main function to handle keyboard input and update joystick state based on arrow key presses
def keyboard_control():

    # Save original terminal settings and set to cbreak mode for non-blocking input
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    pending = ""
    try:
        tty.setcbreak(fd)

        # Main loop to read keyboard input and update joystick state based on arrow key presses
        while not Shared.stop_event.is_set():
            ready, _, _ = select.select([sys.stdin], [], [], 0.01)

            # If there's input ready, read it and update the arrow key states
            if ready:
                pending += read_available_stdin()
                pending = update_arrow_state_from_buffer(pending)

            now = time()

            # Determine if each arrow key is currently active based on the last press time and the defined hold time
            up_active = (now - Shared.last_up) < ARROW_HOLD_TIME
            down_active = (now - Shared.last_down) < ARROW_HOLD_TIME
            left_active = (now - Shared.last_left) < ARROW_HOLD_TIME
            right_active = (now - Shared.last_right) < ARROW_HOLD_TIME

            x = 0x00
            y = 0x00

            # Set joystick X and Y values based on which arrow keys are active
            if left_active and not right_active:
                x = 0x9D
                y = 0x64
            elif right_active and not left_active:
                x = 0x64
                y = 0x64
            if up_active and not down_active:
                y = 0x64
            elif down_active and not up_active:
                y = 0x9D

            # Update the shared joystick state with the new X and Y values
            Shared.set_joystick(x, y, hold_seconds=KEYBOARD_COMMAND_HOLD_SECONDS)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
