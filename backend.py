from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image, UnidentifiedImageError
import base64
import io

app = FastAPI()

# --- Detection config you can tweak ---
PERSON_CLASS_ID = 0      # 0 = "person" in COCO
MIN_CONFIDENCE = 0.6     # raise to reduce false positives (e.g. 0.7)
MIN_REL_AREA = 0.0       # e.g. 0.01 to drop tiny boxes (<1% of image)
# ---------------------------------------

model = YOLO("yolov8x.pt")

@app.post("/detect")
async def detect(payload: dict = Body(...)):
    image_b64 = payload.get("image")
    if not image_b64:
        return JSONResponse({"error": "no image"}, status_code=400)

    # Decode base64 image
    try:
        data = base64.b64decode(image_b64)
    except Exception:
        return JSONResponse({"error": "invalid image"}, status_code=400)

    # Open as PIL image
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        return JSONResponse({"error": "invalid image"}, status_code=400)

    w, h = img.size
    img_area = float(w * h)

    # Run YOLO on the image (person class only)
    results = model(
        img,
        classes=[PERSON_CLASS_ID],
        conf=MIN_CONFIDENCE,
    )

    boxes = []

    for r in results:
        if not hasattr(r, "boxes") or r.boxes is None:
            continue

        # r.boxes.xyxy: Nx4, r.boxes.conf: N
        for box_xyxy, box_conf in zip(r.boxes.xyxy, r.boxes.conf):
            x1, y1, x2, y2 = box_xyxy.tolist()
            conf = float(box_conf.item())

            # Optional: filter by minimum relative area
            area = (x2 - x1) * (y2 - y1)
            if MIN_REL_AREA > 0.0 and (area / img_area) < MIN_REL_AREA:
                continue

            # x and y inverted to match camera coords
            boxes.append(
                {
                    "y1": x1 / w,
                    "x1": y1 / h,
                    "y2": x2 / w,
                    "x2": y2 / h,
                    "conf": conf,
                }
            )

    return {"count": len(boxes), "boxes": boxes}
