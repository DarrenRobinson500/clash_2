import pyautogui
import cv2
import os
import re
import time
import sys
from datetime import datetime, timedelta


# pyautogui sleeps PAUSE seconds after every moveTo/click/mouseDown/mouseUp.
# The 0.1s default dominated goblin_run (~33s across its drags and
# line_clicks); 0.02 keeps a small gap so the emulator still registers
# back-to-back taps. Raise it again if clicks start getting dropped.
pyautogui.PAUSE = 0.02

# ImageGrab raises "OSError: screen grab failed" while the desktop is
# unavailable (screen locked, RDP minimised/disconnected, UAC prompt). Every
# caller does `import pyautogui` and shares this module object, so patching
# it here makes all screenshots wait for the desktop to come back instead of
# crashing the main loop.
_raw_screenshot = pyautogui.screenshot

def _retrying_screenshot(*args, **kwargs):
    delay = 5
    while True:
        try:
            return _raw_screenshot(*args, **kwargs)
        except OSError as e:
            print(f"screenshot failed ({e}); desktop unavailable? retrying in {delay}s")
            time.sleep(delay)
            delay = min(delay * 2, 300)

pyautogui.screenshot = _retrying_screenshot

_TIME_UNITS = {'h': 3600, 'm': 60, 's': 1}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def parse_time(s):
    if not s:
        return None
    matches = re.findall(r'(\d+)([hms])', s)
    if not matches:
        return None
    return sum(int(n) * _TIME_UNITS[u] for n, u in matches)

def show(image, file="Image", dur=500, zoom=1):
    cv2.imshow(file, cv2.resize(image, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_NEAREST))
    cv2.waitKey(dur)  # Waits until a key is pressed
    cv2.destroyAllWindows()  # Closes the window

def offset(position, x, y):
    return position[0] + x, position[1] + y

def smooth_move_to(x, y, steps=20, delay=0.01):
    # pyautogui's own `duration` tweening still resolves to a handful of
    # SetCursorPos jumps — some emulators only react to genuinely gradual
    # movement, so step there in small increments with a real sleep between
    # each one instead.
    start_x, start_y = pyautogui.position()
    for i in range(1, steps + 1):
        pyautogui.moveTo(start_x + (x - start_x) * i / steps, start_y + (y - start_y) * i / steps)
        time.sleep(delay)

def drag(start, end, dur=0.3):
    from image import anchor
    position = anchor.find()
    if position is None:
        print("drag: anchor not found, cannot determine offset")
        return
    ax, ay = position
    start = (ax + start[0], ay + start[1])
    end = (ax + end[0], ay + end[1])
    pyautogui.moveTo(*start)
    pyautogui.dragTo(*end, duration=dur, button='left')


def screenshot_region(position, width, height):
    import numpy as np
    x, y = position
    img = pyautogui.screenshot(region=(x, y, width, height))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def wait(minutes, show_dur=True):
    start = datetime.now()
    end = start + timedelta(minutes=minutes)
    while datetime.now() < end:
        m = (datetime.now() - start).seconds
        if show_dur:
            sys.stdout.write(f"\rWaiting {m/60:.1f} / {minutes} minutes ({m/60/minutes:.0%})")
            sys.stdout.flush()
        time.sleep(10)

    print()  # move to next line after finishing

def mouse_tracker():
    # Imported lazily to avoid a circular import (image.py -> logic_image.py -> utilities.py).
    from image import anchor
    while True:
        position = anchor.find()
        if position is None:
            print("mouse_tracker: anchor not found")
        else:
            ax, ay = position
            mx, my = pyautogui.position()
            print(f"Mouse: ({mx - ax}, {my - ay})")
        time.sleep(1)

def files_in_directory(directory_path):
    try:
        return [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    except:
        print(f"Directory not found: {directory_path}")
        return []
def get_image(top_left, bottom_right, filename=None, directory='images/screenshots'):
    # top_left/bottom_right are offsets from anchor's position, same as
    # drag() — keeps captured regions stable wherever the emulator window sits.
    # Imported lazily to avoid a circular import (image.py -> logic_image.py -> utilities.py).
    from image import anchor, clash_icon
    position = anchor.find()
    if position is None:
        # Anchor is emulator window chrome — not seeing it usually means the
        # emulator isn't in front, so bring it up and give it time to appear.
        clash_icon.click()
        if not anchor.wait(duration=10):
            print("get_image: anchor not found, even after clicking clash_icon")
            return None
        position = anchor.find()
        if position is None:
            print("get_image: anchor not found, even after clicking clash_icon")
            return None
    ax, ay = position
    x0, y0 = ax + top_left[0], ay + top_left[1]
    width, height = bottom_right[0] - top_left[0], bottom_right[1] - top_left[1]
    image = screenshot_region((x0, y0), width, height)
    os.makedirs(os.path.join(BASE_DIR, directory), exist_ok=True)
    if filename is None:
        filename = time.strftime('Screenshot %Y-%m-%d %H%M%S.jpg')
    elif not os.path.splitext(filename)[1]:
        # cv2.imwrite picks the format from the extension and fails without one.
        filename += '.jpg'
    cv2.imwrite(os.path.join(BASE_DIR, directory, filename), image)
    show(image, filename, dur=2000)
    return image

def extract_image(source_file, top_left, bottom_right, filename):
    # Crops a saved screenshot rather than the live screen — top_left and
    # bottom_right are pixel coordinates within source_file itself (not
    # anchor-relative), since the anchor's position at capture time isn't known.
    screenshots_dir = os.path.join(BASE_DIR, 'images', 'screenshots')
    extracts_dir = os.path.join(screenshots_dir, 'extracts')
    if not os.path.splitext(source_file)[1]:
        source_file += '.jpg'
    # cv2.imwrite picks the format from the extension and fails without one.
    if not os.path.splitext(filename)[1]:
        filename += '.jpg'
    source = cv2.imread(os.path.join(screenshots_dir, source_file))
    if source is None:
        print(f"extract_image: could not read '{source_file}' in images/screenshots")
        return None
    (x0, y0), (x1, y1) = top_left, bottom_right
    image = source[y0:y1, x0:x1]
    if image.size == 0:
        print(f"extract_image: region {top_left}-{bottom_right} is outside '{source_file}' ({source.shape[1]}x{source.shape[0]})")
        return None
    os.makedirs(extracts_dir, exist_ok=True)
    cv2.imwrite(os.path.join(extracts_dir, filename), image)
    return image


def white_mask(image, threshold=170):
    # Near-white pixels -> 255, everything else -> 0, as a single-channel
    # image. A pixel counts as white when every channel is >= threshold, so
    # this is the same for BGR (cv2.imread) and RGB (pyautogui.screenshot).
    import numpy as np
    return np.where((image >= threshold).all(axis=2), 255, 0).astype(np.uint8)

def extract_time(filename, threshold=170):
    # Text (timers, counts) is drawn bright white over varied backgrounds —
    # keeping only near-white pixels strips the background so the digits
    # are the same shape whatever is behind them. A pixel counts as white
    # when every channel is >= threshold, which also excludes bright but
    # coloured pixels (yellow grass, gold bars).
    screenshots_dir = os.path.join(BASE_DIR, 'images', 'screenshots')
    extracts_dir = screenshots_dir
    if not os.path.splitext(filename)[1]:
        filename += '.jpg'
    source = cv2.imread(os.path.join(screenshots_dir, filename))
    if source is None:
        print(f"extract_time: could not read '{filename}' in images/screenshots")
        return None
    image = white_mask(source, threshold)
    os.makedirs(extracts_dir, exist_ok=True)
    # Saved as png under its own suffix: jpg compression would blur the pure
    # black/white back into greys, and a plain '<name>.jpg' could overwrite a
    # same-named digit crop from extract_image (e.g. extracts/1.jpg).
    out_name = os.path.splitext(filename)[0] + '_white.png'
    cv2.imwrite(os.path.join(extracts_dir, out_name), image)
    return image

def to_int(text, default=0):
    try:
      return int(text)
    except (TypeError, ValueError):
      return default

STATUS_FILE = r'C:\Users\darre\OneDrive\Game\Clash\status.txt'

def write_to_file(text):
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        f.write(text)
