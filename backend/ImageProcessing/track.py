# ByteTrack-backed tracker that keeps the same public API/outputs as the old IoU tracker.
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple

import numpy as np

# Try both known Ultralytics import paths so we work across versions.
BYTE_IMPORT_ERROR = (
    "ByteTrack is not available. Install ultralytics with tracker extras "
    "(pip install ultralytics) to enable tracking."
)
ByteTrackBase = None
try:
    from ultralytics.trackers.byte_tracker import BYTETracker, STrack  # type: ignore
    from ultralytics.trackers.basetrack import BaseTrack as ByteTrackBase  # type: ignore
    from ultralytics.engine.results import Boxes  # type: ignore
except Exception:
    try:
        from ultralytics.utils.trackers.byte_tracker import BYTETracker, STrack  # type: ignore
        from ultralytics.utils.trackers.basetrack import BaseTrack as ByteTrackBase  # type: ignore
        from ultralytics.engine.results import Boxes  # type: ignore
    except Exception as exc:  # pragma: no cover - handled at runtime
        raise ImportError(BYTE_IMPORT_ERROR) from exc


def _is_normalized(detections: List[Dict], img_w: float, img_h: float) -> bool:
    """Check if all detection coordinates look normalized (<=1)."""
    if img_w <= 0.0 or img_h <= 0.0:
        return True
    for det in detections:
        if max(det.get("x1", 0.0), det.get("y1", 0.0), det.get("x2", 0.0), det.get("y2", 0.0)) > 1.0:
            return False
    return True


def _prepare_detections(
    detections: List[Dict], img_w: float, img_h: float
) -> Tuple[np.ndarray, bool]:
    """
    Convert detection dicts to ByteTrack's expected ndarray and report if they were normalized.
    ByteTrack expects [x1, y1, x2, y2, score, class] in absolute coordinates.
    """
    if not detections:
        return np.empty((0, 6), dtype=np.float32), True

    normalized = _is_normalized(detections, img_w, img_h)
    rows = []
    for det in detections:
        x1, y1, x2, y2 = (
            float(det["x1"]),
            float(det["y1"]),
            float(det["x2"]),
            float(det["y2"]),
        )
        score = float(det.get("conf", 1.0))
        cls = float(det.get("cls", det.get("class", 0.0)))

        if normalized and img_w > 0.0 and img_h > 0.0:
            x1 *= img_w
            x2 *= img_w
            y1 *= img_h
            y2 *= img_h

        rows.append([x1, y1, x2, y2, score, cls])

    return np.asarray(rows, dtype=np.float32), normalized


class SimpleTracker:
    """
    Wrapper around ByteTrack that keeps the same update signature and output schema as the
    previous IoU tracker. Call update(detections, (img_w, img_h)) to track across frames.
    """

    def __init__(
        self,
        track_thresh: float = 0.25,
        track_high_thresh: Optional[float] = None,
        track_low_thresh: float = 0.1,
        new_track_thresh: Optional[float] = None,
        track_buffer: int = 10,
        match_thresh: float = 0.85,
        min_box_area: float = 0.0,
        fuse_score: bool = True,
        mot20: bool = False,
        fps: float = 30.0,
        **_: Dict,
    ):
        # Fall back to Ultralytics defaults if overrides are not provided
        high = track_high_thresh if track_high_thresh is not None else track_thresh
        new_track = new_track_thresh if new_track_thresh is not None else high
        self.args = SimpleNamespace(
            track_high_thresh=high,
            track_low_thresh=track_low_thresh,
            new_track_thresh=new_track,
            track_thresh=track_thresh,
            track_buffer=track_buffer,
            match_thresh=match_thresh,
            min_box_area=min_box_area,
            mot20=mot20,
            fuse_score=fuse_score,
        )
        self.fps = fps
        self.next_id = 1  # legacy compatibility
        self.tracks: List[Dict] = []  # last returned tracks for compatibility
        self._init_tracker()

    def _init_tracker(self) -> None:
        if ByteTrackBase is not None:
            ByteTrackBase._count = 0  # reset global ID counter
        self._tracker = BYTETracker(self.args, frame_rate=self.fps)

    def reset(self) -> None:
        """Clear internal state and reset IDs."""
        self._init_tracker()
        self.tracks.clear()
        self.next_id = 1

    def update(
        self, detections: List[Dict], img_size: Optional[Tuple[float, float]] = None
    ) -> List[Dict]:
        """
        Update tracker with detections for the current frame.
        detections: list of {"x1","y1","x2","y2","conf"} in normalized or absolute coords.
        img_size: optional (width, height) tuple for scaling normalized boxes to pixels.
        """
        img_w, img_h = (float(img_size[0]), float(img_size[1])) if img_size else (1.0, 1.0)
        det_array, normalized = _prepare_detections(detections, img_w, img_h)

        # Wrap into Ultralytics Boxes so ByteTrack receives the full structure it expects
        boxes = Boxes(det_array, (int(img_h), int(img_w)))
        online_targets = self._tracker.update(boxes)

        tracked: List[Dict] = []
        for target in online_targets:
            if hasattr(target, "tlbr"):
                # STrack object path
                x1, y1, x2, y2 = target.tlbr
                score = float(getattr(target, "score", 1.0))
                tid = int(target.track_id)
                cls = float(getattr(target, "cls", 0.0))
            else:
                # Numpy row path returned by ByteTrack (xyxy, track_id, score, cls, idx)
                arr = np.asarray(target).flatten()
                x1, y1, x2, y2 = arr[:4]
                tid = int(arr[4]) if len(arr) > 4 else -1
                score = float(arr[5]) if len(arr) > 5 else 1.0
                cls = float(arr[6]) if len(arr) > 6 else 0.0

            if normalized and img_w > 0.0 and img_h > 0.0:
                x1 /= img_w
                x2 /= img_w
                y1 /= img_h
                y2 /= img_h

            tracked.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "conf": score, "id": tid, "cls": cls})

        self.tracks = tracked
        if ByteTrackBase is not None:
            self.next_id = getattr(ByteTrackBase, "_count", self.next_id)
        return tracked
