# src/util/tracking.py
from typing import Dict, List

# compute intersection over union of two bounding boxes
def iou(a: Dict, b: Dict) -> float:

    # extract coordinates
    ax1, ay1, ax2, ay2 = a["x1"], a["y1"], a["x2"], a["y2"]
    bx1, by1, bx2, by2 = b["x1"], b["y1"], b["x2"], b["y2"]

    # compute intersection
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    iw = max(0.0, inter_x2 - inter_x1)
    ih = max(0.0, inter_y2 - inter_y1)
    inter = iw * ih

    # compute union
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter

    # avoid division by zero
    if union <= 0.0:
        return 0.0
    
    # return IoU
    return inter / union

# simple tracker class
class SimpleTracker:

    # initialize tracker
    def __init__(self, iou_thresh: float = 0.3, max_missed: int = 10):
        self.iou_thresh = iou_thresh
        self.max_missed = max_missed
        self.next_id = 1
        self.tracks: Dict[int, Dict] = {}  # id -> {"bbox": box, "missed": int}

    # update tracker with new detections
    def update(self, detections: List[Dict]) -> List[Dict]:

        # mark all as missed
        for tid in list(self.tracks.keys()):
            self.tracks[tid]["missed"] += 1

        # compute IoU pairs
        pairs = []
        for tid, t in self.tracks.items():

            # compute IoU against all detections
            for di, det in enumerate(detections):
                pairs.append((iou(t["bbox"], det), tid, di))
        
        # sort pairs by IoU
        pairs.sort(reverse=True, key=lambda x: x[0])

        # greedy assignment by highest IoU
        matched_tracks = set()
        matched_dets = set()
        for score, tid, di in pairs:

            # skip if below threshold or already matched
            if score < self.iou_thresh:
                break

            # continue if already matched
            if tid in matched_tracks or di in matched_dets:
                continue

            # update track
            self.tracks[tid]["bbox"] = detections[di]
            self.tracks[tid]["missed"] = 0

            # mark as matched
            matched_tracks.add(tid)
            matched_dets.add(di)

        # create new tracks for unmatched detections
        for di, det in enumerate(detections):

            # skip if already matched
            if di in matched_dets:
                continue

            # create new track
            tid = self.next_id
            self.next_id += 1
            self.tracks[tid] = {"bbox": det, "missed": 0}

        # drop stale tracks
        for tid in list(self.tracks.keys()):

            # drop if missed too many times
            if self.tracks[tid]["missed"] > self.max_missed:
                del self.tracks[tid]

        # return tracks seen THIS frame only
        out = []
        for tid, t in self.tracks.items():

            # only return if seen this frame
            if t["missed"] == 0:
                box = dict(t["bbox"])
                box["id"] = tid
                out.append(box)
        return out
