# /backend/ImageProcessing/guide.py

# find target id
def find(tracked, guide_uid):
    for item in tracked:
        if item['id'] == guide_uid:
            return item
    return None

# calculate joystick commands to guide towards the center of the target, with a simple proportional controller
def guide(tracked, guide_uid, img_w, img_h):
    target = find(tracked, guide_uid)

    # Bail out if we don't have a target
    if target is None:
        return None

    center_x = (target['x1'] + target['x2']) / 2
    center_y = (target['y1'] + target['y2']) / 2
    area = (target['x2'] - target['x1']) * (target['y2'] - target['y1'])
    return center_x, center_y, area
