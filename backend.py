import logging
import threading
from fastapi import FastAPI, UploadFile, File, Form
from ultralytics import YOLO
from src.utils.detect import detectPerson
from src.utils.track import SimpleTracker

# Run with: uvicorn backend:app --reload --host 0.0.0.0 --port 8000 --no-access-log

# Suppress ultralytics logging and start FastAPI server
logging.getLogger("ultralytics").setLevel(logging.ERROR)
app = FastAPI()

# --- Detection config you can tweak ---
PERSON_CLASS_ID = 0      # 0 = "person" in COCO
MIN_CONFIDENCE = 0.6     # raise to reduce false positives (e.g. 0.7)
MIN_REL_AREA = 0.01       # e.g. 0.01 to drop tiny boxes (<1% of image)
# --------------------------------------

# Preload available models so swapping is cheap.
MODEL_FILES = {
    "n": "models/yolov8n.pt",
    "m": "models/yolov8m.pt",
    "x": "models/yolov8x.pt",
}
MODELS = {k: YOLO(path) for k, path in MODEL_FILES.items()}

# Initialize tracker and lock for thread safety
tracker = SimpleTracker(iou_thresh=0.3, max_missed=10)
tracker_lock = threading.Lock()

# Define the route for the detection endpoint
@app.post("/detect")
async def detect(
    image: UploadFile = File(...),
    model: str = Form("n"),
):
    # Run detection using YOLO model
    detections, w, h = await detectPerson(image, model, MODELS, PERSON_CLASS_ID, MIN_CONFIDENCE, MIN_REL_AREA)
    
    # Track detected persons using the SimpleTracker
    with tracker_lock:
        tracked = tracker.update(detections)

    # Return the count of tracked persons, their bounding boxes, and image dimensions
    return {"count": len(tracked), "boxes": tracked, "img_w": w, "img_h": h}
    
# Define the route for resetting the tracker
@app.post("/reset-tracker")
async def reset_tracker():

    # Reset the tracker to clear all tracks and reset the next ID
    with tracker_lock:
        tracker.tracks.clear()
        tracker.next_id = 1
    return {"status": "reset"}