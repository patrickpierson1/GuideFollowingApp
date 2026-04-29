# /backend/Controls/Shared.py
import json
import threading
from time import time
from pathlib import Path

# Shared state and utilities for joystick control across different modules.
# This module uses a JSON file for joystick state so both the FastAPI process
# and the Connect subprocess can share state. It also uses a JSON file for
# max-speed so the backend can set it and the Connect process can read it.

JOYSTICK_STATE_PATH = Path("/tmp/guidefollowing_joystick_state.json")
MAX_SPEED_STATE_PATH = Path("/tmp/guidefollowing_maxspeed.json")

last_up = 0.0
last_down = 0.0
last_left = 0.0
last_right = 0.0

stop_event = threading.Event()
_state_lock = threading.Lock()
_file_lock = threading.Lock()

# default state for the joystick, with X and Y centered and no expiration
def _default_state():
    return {"joystick_x": 0x00, "joystick_y": 0x00, "expires_at": 0.0}

# reads joystick state from JSON file
def _read_state():
    try:
        text = JOYSTICK_STATE_PATH.read_text()
        return json.loads(text)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return _default_state()

# writes joystick state to JSON file
def _write_state(state):
    try:
        JOYSTICK_STATE_PATH.write_text(json.dumps(state))
    except OSError:
        # best-effort; ignore write errors
        pass

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

# -------------------------
# Max speed file-backed state
# -------------------------
# The backend writes the desired max speed (percent 0.0..100.0) to a JSON file.
# The Connect subprocess reads this file periodically and applies the new value.
# This avoids cross-process memory sharing issues.

def _default_max_speed_state():
    return {"percent": None, "ts": 0.0}

def _read_max_speed_state():
    try:
        text = MAX_SPEED_STATE_PATH.read_text()
        return json.loads(text)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return _default_max_speed_state()

def _write_max_speed_state(state):
    try:
        MAX_SPEED_STATE_PATH.write_text(json.dumps(state))
    except OSError:
        # ignore write errors (best-effort)
        pass

def set_max_speed_percent(percent: float | None):
    """
    Set desired max speed percent (0..100) or None to clear.
    This writes the value to /tmp/guidefollowing_maxspeed.json with a timestamp.
    """
    with _file_lock:
        if percent is None:
            state = {"percent": None, "ts": time()}
        else:
            p = float(percent)
            if p < 0.0:
                p = 0.0
            elif p > 100.0:
                p = 100.0
            state = {"percent": p, "ts": time()}
        _write_max_speed_state(state)

def get_max_speed_percent():
    """
    Read the current max speed percent from the file.
    Returns float 0..100 or None if not set.
    """
    with _file_lock:
        state = _read_max_speed_state()
    return state.get("percent", None)

def get_max_speed_state_timestamp():
    """
    Return the timestamp of the last write to the max speed file (or 0.0).
    """
    with _file_lock:
        state = _read_max_speed_state()
    return float(state.get("ts", 0.0))
