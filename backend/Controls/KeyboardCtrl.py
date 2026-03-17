import os
import sys
import termios
import tty
import select
from time import time

ARROW_HOLD_TIME = 0.18

def read_available_stdin():
    """
    Read all currently available bytes from stdin without blocking.
    Returns a decoded string (possibly empty).
    """
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

def update_arrow_state_from_buffer(buf):
    """
    Parse as many terminal escape sequences as possible from buf.
    Supports multiple arrow sequences in a single read, e.g.:
        \\x1b[A\\x1b[C
    Returns any trailing partial sequence to preserve for the next read.
    """
    global last_up, last_down, last_left, last_right, rnet_threads_running

    i = 0

    while i < len(buf):
        ch = buf[i]

        if ch.lower() == 'q':
            rnet_threads_running = False
            i += 1
            continue

        # Arrow keys: ESC [ A/B/C/D
        if ch == '\x1b':
            if i + 2 >= len(buf):
                # partial escape sequence, save for next loop
                return buf[i:]

            if buf[i + 1] == '[':
                code = buf[i + 2]
                now = time()

                if code == 'A':        # Up
                    last_up = now
                    i += 3
                    continue
                elif code == 'B':      # Down
                    last_down = now
                    i += 3
                    continue
                elif code == 'C':      # Right
                    last_right = now
                    i += 3
                    continue
                elif code == 'D':      # Left
                    last_left = now
                    i += 3
                    continue

            # Unknown escape sequence; skip ESC
            i += 1
            continue

        # Ignore any non-arrow input except q
        i += 1

    return ""

# -----------------------------
# KEYBOARD INPUT
# -----------------------------
def keyboard_control():
    """
    Reads arrow keys from terminal and updates joystick_x / joystick_y.

    Left  -> x = 0x9D
    Right -> x = 0x64
    Up    -> y = 0x64
    Down  -> y = 0x9D

    Supports approximate diagonals over SSH by keeping recent arrow
    presses active for a short time window.
    """
    global joystick_x, joystick_y, rnet_threads_running
    global last_up, last_down, last_left, last_right

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    pending = ""

    try:
        tty.setcbreak(fd)

        while rnet_threads_running:
            ready, _, _ = select.select([sys.stdin], [], [], 0.01)

            if ready:
                pending += read_available_stdin()
                pending = update_arrow_state_from_buffer(pending)

            now = time()

            up_active = (now - last_up) < ARROW_HOLD_TIME
            down_active = (now - last_down) < ARROW_HOLD_TIME
            left_active = (now - last_left) < ARROW_HOLD_TIME
            right_active = (now - last_right) < ARROW_HOLD_TIME

            x = 0x00
            y = 0x00

            # X axis
            if left_active and not right_active:
                x = 0x9D
            elif right_active and not left_active:
                x = 0x64

            # Y axis
            if up_active and not down_active:
                y = 0x64
            elif down_active and not up_active:
                y = 0x9D

            joystick_x = x
            joystick_y = y

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

