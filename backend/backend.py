# /backend/backend.py
import logging
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form
from ultralytics import YOLO
from ImageProcessing.detect import Detect
from ImageProcessing.track import SimpleTracker
from ImageProcessing.guide import guide
from Controls import Shared

# Run with: uvicorn backend:app --reload --host 0.0.0.0 --port 8000 --no-access-log

# Suppress ultralytics logging and start FastAPI server
logging.getLogger("ultralytics").setLevel(logging.ERROR)
app = FastAPI()
app.state.connect_process = None

# --- Detection config you can tweak ---
PERSON_CLASS_ID = 0      # 0 = "person" in COCO
MIN_CONFIDENCE = 0.7     # raise to reduce false positives (e.g. 0.7+ recommended to reduce ID swaps)
MIN_REL_AREA = 0.01      # e.g. 0.01 to drop tiny boxes (<1% of image)
# --------------------------------------

# Preload available models so swapping is cheap.
MODEL_FILES = {
    "n": "models/yolov8n.pt",
    "m": "models/yolov8m.pt",
    "x": "models/yolov8x.pt",
}
MODELS = {k: YOLO(path) for k, path in MODEL_FILES.items()}

# Initialize tracker and lock for thread safety
tracker = SimpleTracker(
    track_high_thresh=0.45,
    track_low_thresh=0.2,
    new_track_thresh=0.45,
    match_thresh=0.85,
    track_buffer=20,
    fps=30.0,
)
tracker_lock = threading.Lock()

# Constants for joystick encoding and guiding behavior
CONNECT_SCRIPT = Path(__file__).resolve().parent / "Controls" / "Connect.py"
GUIDE_COMMAND_HOLD_SECONDS = 0.75
GUIDE_DEADZONE = 0.05
GUIDE_APPROACH_AREA_THRESHOLD = 0.8
JOYSTICK_POSITIVE_MAX = 0x64
JOYSTICK_NEGATIVE_MAX = 0x9D
JOYSTICK_NEGATIVE_MAGNITUDE = 0x100 - JOYSTICK_NEGATIVE_MAX

# clamp a value to a specified range
def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))

# encode a normalized axis value (-1.0 to 1.0) into a joystick byte (0x00 to 0xFF)
def encode_axis(normalized_value: float) -> int:
    normalized_value = clamp(normalized_value, -1.0, 1.0)

    if abs(normalized_value) <= GUIDE_DEADZONE:
        return 0x00

    if normalized_value >= 0:
        return int(round(normalized_value * JOYSTICK_POSITIVE_MAX))

    signed_value = -int(round(abs(normalized_value) * JOYSTICK_NEGATIVE_MAGNITUDE))
    return signed_value & 0xFF

# convert target center coordinates to joystick commands
def center_to_joystick(center_x: float, center_y: float) -> tuple[int, int]:
    normalized_x = (2.0 * center_x) - 1.0
    normalized_y = 1.0 - (2.0 * center_y)
    return encode_axis(normalized_x), encode_axis(normalized_y)

# on startup, launch the Connect.py script as a subprocess to handle CAN communication and joystick control
@app.on_event("startup")
async def startup_event():
    if app.state.connect_process is None or app.state.connect_process.poll() is not None:
        app.state.connect_process = subprocess.Popen(
            [sys.executable, str(CONNECT_SCRIPT), "--no-keyboard"],
            cwd=str(CONNECT_SCRIPT.parent),
        )

# on shutdown, terminate the Connect.py subprocess gracefully
@app.on_event("shutdown")
async def shutdown_event():
    process = app.state.connect_process
    if process is None or process.poll() is not None:
        app.state.connect_process = None
        return

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    finally:
        app.state.connect_process = None

# Define the route for the detection endpoint
@app.post("/detect")
async def detect(
    image: UploadFile = File(...),
    model: str = Form("n"),
    following: bool = Form(False),
    guide_uid: Optional[int] = Form(None),
):
    # Run detection using YOLO model
    detections, w, h = await Detect(image, model, MODELS, PERSON_CLASS_ID, MIN_CONFIDENCE, MIN_REL_AREA)
    
    # Track detected persons using the SimpleTracker
    with tracker_lock:
        tracked = tracker.update(detections, (w, h))
    
    # If following mode is enabled and a guide_uid is provided
    if following and guide_uid is not None:
        
        # print(f"Attempting to guide to ID {guide_uid}...")
        target = guide(tracked, guide_uid, w, h)
        if target is not None:
            # send joystick commands to guide towards the target center
            center_x, center_y, area = target
            joystick_x, joystick_y = center_to_joystick(center_x, center_y)
            if area < GUIDE_APPROACH_AREA_THRESHOLD:
                joystick_y = JOYSTICK_POSITIVE_MAX
            print(
                f"Guide center: X={center_x:.3f}, Y={center_y:.3f}, area={area:.3f} -> "
                f"joystick X={joystick_x}, Y={joystick_y}"
            )
            Shared.set_joystick(joystick_x, joystick_y, hold_seconds=GUIDE_COMMAND_HOLD_SECONDS)
        else:
            Shared.reset_joystick()
    else:
        Shared.reset_joystick()
    
    # Return the count of tracked persons, their bounding boxes, and image dimensions
    if len(tracked) > 15:
        await reset_tracker()
        
    return {
        "count": len(tracked),
        "boxes": [
            {
                "id": int(p["id"]),
                "x1": float(p["x1"]),
                "y1": float(p["y1"]),
                "x2": float(p["x2"]),
                "y2": float(p["y2"]),
                "conf": float(p["conf"]),
                "cls": float(p["cls"]),
            }
            for p in tracked
        ],
        "img_w": int(w),
        "img_h": int(h),
    }

# Define the route for resetting the tracker
@app.post("/reset-tracker")
async def reset_tracker():
    # Reset the tracker to clear all tracks and reset the next ID
    with tracker_lock:
        tracker.reset()
    Shared.reset_joystick()
    return {"status": "reset"}
