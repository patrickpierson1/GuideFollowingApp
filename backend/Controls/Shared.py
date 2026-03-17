import threading

joystick_x = 0x00
joystick_y = 0x00

last_up = 0.0
last_down = 0.0
last_left = 0.0
last_right = 0.0

stop_event = threading.Event()