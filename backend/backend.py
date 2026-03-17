import logging
import threading
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
    
    if following and guide_uid is not None:
        print(f"Attempting to guide to ID {guide_uid}...")
        res = guide(tracked, guide_uid, w, h)
        if res is not None:
            print(f"Guide found: X={res[0]}, Y={res[1]}")
            Shared.joystick_x, Shared.joystick_y = res
        else:
            Shared.joystick_x = 0x00
            Shared.joystick_y = 0x00
    else:
        Shared.joystick_x = 0x00
        Shared.joystick_y = 0x00
    
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
    return {"status": "reset"}
