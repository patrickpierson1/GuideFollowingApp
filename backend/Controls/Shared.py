# /backend/Controls/Shared.py
import json
import threading
from time import time
from pathlib import Path

# Shared state and utilities for joystick control across different modules
JOYSTICK_STATE_PATH = Path("/tmp/guidefollowing_joystick_state.json")

last_up = 0.0
last_down = 0.0
last_left = 0.0
last_right = 0.0
stop_event = threading.Event()
_state_lock = threading.Lock()

# default state for the joystick, with X and Y centered and no expiration
def _default_state():
    return {"joystick_x": 0x00, "joystick_y": 0x00, "expires_at": 0.0}

# reads joystick state from JSON file
def _read_state():
    try:
        return json.loads(JOYSTICK_STATE_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return _default_state()

# writes joystick state to JSON file
def _write_state(state):
    JOYSTICK_STATE_PATH.write_text(json.dumps(state))

# sets the joystick state with given X and Y values
def set_joystick(x, y, hold_seconds=0.0):
    state = {
        "joystick_x": int(x) & 0xFF,
        "joystick_y": int(y) & 0xFF,
        "expires_at": time() + max(0.0, float(hold_seconds)),
    }
    with _state_lock:
        _write_state(state)

# returns the current joystick state, or (0, 0) if the state has expired
def get_joystick():
    with _state_lock:
        state = _read_state()
    if float(state.get("expires_at", 0.0)) < time():
        return 0x00, 0x00
    return int(state.get("joystick_x", 0x00)), int(state.get("joystick_y", 0x00))

# resets the joystick state to centered (0, 0) with no expiration
def reset_joystick():
    set_joystick(0x00, 0x00, hold_seconds=0.0)
