# src/utils/guide.py
delta = 0.05

def find(tracked, guide_uid):
    for item in tracked:
        if item['id'] == guide_uid:
            return item
    return None


def guide(tracked, guide_uid):
    target = find(tracked, guide_uid)

    # Bail out if we don't have a target
    if target is None:
        return None

    # Use the horizontal center of the bounding box to decide direction
    center_x = (target['x1'] + target['x2']) / 2

    if center_x > 0.5 + delta:
        return "right"
    if center_x < 0.5 - delta:
        return "left"
    return "middle"
