# src/utils/guide.py
DEADZONE = 0.05


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def encode_axis(normalized_value):
    normalized_value = clamp(normalized_value, -1.0, 1.0)

    if abs(normalized_value) <= DEADZONE:
        return 0x00

    if normalized_value >= 0:
        return int(round(normalized_value * 0x64))

    return int(round(normalized_value * 99)) & 0xFF

def find(tracked, guide_uid):
    for item in tracked:
        if item['id'] == guide_uid:
            return item
    return None


def guide(tracked, guide_uid, img_w, img_h):
    target = find(tracked, guide_uid)

    # Bail out if we don't have a target
    if target is None:
        return None

    center_x = (target['x1'] + target['x2']) / 2
    center_y = (target['y1'] + target['y2']) / 2

    normalized_x = (2.0 * center_x / img_w) - 1.0
    normalized_y = 1.0 - (2.0 * center_y / img_h)

    return encode_axis(normalized_x), encode_axis(normalized_y)
