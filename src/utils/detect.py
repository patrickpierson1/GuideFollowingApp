import io
from typing import Dict, List
from fastapi import UploadFile, File, Form
from fastapi.responses import JSONResponse
from PIL import Image, ImageOps
from ultralytics import YOLO

# define the API endpoint for person detection
async def detectPerson(
    image,
    model,
    MODELS,
    PERSON_CLASS_ID,
    MIN_CONFIDENCE,
    MIN_REL_AREA):

    # Load YOLO model
    model_key = model or "n"
    yolo = MODELS.get(model_key, MODELS["n"])

    # Read uploaded file bytes
    try:
        data = await image.read()
        if not data:
            return JSONResponse({"error": "empty image"}, status_code=400)
    except Exception:
        return JSONResponse({"error": "invalid upload"}, status_code=400)

    # Open + normalize EXIF orientation so portrait/landscape pixels are consistent
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Exception:
        return JSONResponse({"error": "invalid image"}, status_code=400)

    # Get image dimensions
    w, h = img.size
    img_area = float(w * h)

    # Run YOLO detection
    results = yolo(
        img,
        classes=[PERSON_CLASS_ID],
        conf=MIN_CONFIDENCE,
        verbose=False,
    )

    # Parse YOLO results
    detections: List[Dict] = []
    for r in results:

        # Skip if no boxes
        if not hasattr(r, "boxes") or r.boxes is None:
            continue

        for box_xyxy, box_conf in zip(r.boxes.xyxy, r.boxes.conf):
            x1, y1, x2, y2 = box_xyxy.tolist()
            conf = float(box_conf.item())
            area = (x2 - x1) * (y2 - y1)

            # Skip if below confidence threshold or relative area threshold
            if conf < MIN_CONFIDENCE:
                continue
            if MIN_REL_AREA > 0.0 and (area / img_area) < MIN_REL_AREA:
                continue

            # Append detection
            detections.append(
                {
                    "x1": x1 / w,
                    "y1": y1 / h,
                    "x2": x2 / w,
                    "y2": y2 / h,
                    "conf": conf,
                }
            )
    return detections, w, h