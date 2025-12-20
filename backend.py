import base64
import io
import logging
import threading
from typing import Dict, List

from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from PIL import Image, ImageOps
from ultralytics import YOLO

# Run with:
# uvicorn backend:app --reload --host 0.0.0.0 --port 8000 --no-access-log

logging.getLogger("ultralytics").setLevel(logging.ERROR)

app = FastAPI()

# --- Detection config you can tweak ---
PERSON_CLASS_ID = 0      # 0 = "person" in COCO
MIN_CONFIDENCE = 0.6     # raise to reduce false positives (e.g. 0.7)
MIN_REL_AREA = 0.0       # e.g. 0.01 to drop tiny boxes (<1% of image)
# --------------------------------------

model = YOLO("models/yolov8m.pt")


def _iou(a: Dict, b: Dict) -> float:
    ax1, ay1, ax2, ay2 = a["x1"], a["y1"], a["x2"], a["y2"]
    bx1, by1, bx2, by2 = b["x1"], b["y1"], b["x2"], b["y2"]

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    iw = max(0.0, inter_x2 - inter_x1)
    ih = max(0.0, inter_y2 - inter_y1)
    inter = iw * ih

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    if union <= 0.0:
        return 0.0
    return inter / union


class SimpleTracker:
    """
    Lightweight IoU tracker to assign stable IDs across frames.
    Good enough for a few people at decent FPS.
    """
    def __init__(self, iou_thresh: float = 0.3, max_missed: int = 10):
        self.iou_thresh = iou_thresh
        self.max_missed = max_missed
        self.next_id = 1
        self.tracks: Dict[int, Dict] = {}  # id -> {"bbox": box, "missed": int}

    def update(self, detections: List[Dict]) -> List[Dict]:
        # mark all as missed
        for tid in list(self.tracks.keys()):
            self.tracks[tid]["missed"] += 1

        # compute IoU pairs
        pairs = []
        for tid, t in self.tracks.items():
            for di, det in enumerate(detections):
                pairs.append((_iou(t["bbox"], det), tid, di))
        pairs.sort(reverse=True, key=lambda x: x[0])

        matched_tracks = set()
        matched_dets = set()

        # greedy assignment by highest IoU
        for score, tid, di in pairs:
            if score < self.iou_thresh:
                break
            if tid in matched_tracks or di in matched_dets:
                continue
            self.tracks[tid]["bbox"] = detections[di]
            self.tracks[tid]["missed"] = 0
            matched_tracks.add(tid)
            matched_dets.add(di)

        # create new tracks for unmatched detections
        for di, det in enumerate(detections):
            if di in matched_dets:
                continue
            tid = self.next_id
            self.next_id += 1
            self.tracks[tid] = {"bbox": det, "missed": 0}

        # drop stale tracks
        for tid in list(self.tracks.keys()):
            if self.tracks[tid]["missed"] > self.max_missed:
                del self.tracks[tid]

        # return tracks seen THIS frame only
        out = []
        for tid, t in self.tracks.items():
            if t["missed"] == 0:
                box = dict(t["bbox"])
                box["id"] = tid
                out.append(box)
        return out


tracker = SimpleTracker(iou_thresh=0.3, max_missed=10)
tracker_lock = threading.Lock()


@app.post("/detect")
async def detect(payload: dict = Body(...)):
    image_b64 = payload.get("image")
    if not image_b64:
        return JSONResponse({"error": "no image"}, status_code=400)

    # Decode base64
    try:
        data = base64.b64decode(image_b64)
    except Exception:
        return JSONResponse({"error": "invalid image"}, status_code=400)

    # Open + normalize EXIF orientation so portrait/landscape pixels are consistent
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Exception:
        return JSONResponse({"error": "invalid image"}, status_code=400)

    w, h = img.size
    img_area = float(w * h)

    results = model(
        img,
        classes=[PERSON_CLASS_ID],
        conf=MIN_CONFIDENCE,
        verbose=False,
    )

    detections: List[Dict] = []

    for r in results:
        if not hasattr(r, "boxes") or r.boxes is None:
            continue

        for box_xyxy, box_conf in zip(r.boxes.xyxy, r.boxes.conf):
            x1, y1, x2, y2 = box_xyxy.tolist()
            conf = float(box_conf.item())

            area = (x2 - x1) * (y2 - y1)
            if MIN_REL_AREA > 0.0 and (area / img_area) < MIN_REL_AREA:
                continue

            # Standard normalized coords (no swapping)
            detections.append(
                {
                    "x1": x1 / w,
                    "y1": y1 / h,
                    "x2": x2 / w,
                    "y2": y2 / h,
                    "conf": conf,
                }
            )

    with tracker_lock:
        tracked = tracker.update(detections)

    # CRITICAL: return the exact processed image dimensions used for normalization
    return {"count": len(tracked), "boxes": tracked, "img_w": w, "img_h": h}
