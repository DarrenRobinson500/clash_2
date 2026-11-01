import hashlib
import math
from collections import deque
from image import *

Locs = []
_current_loc = None
autos = []
NAV_DIR = os.path.join('images', 'nav')

def get_image(image, loc_name):
    if not isinstance(image, str):
        return image
    if os.path.dirname(image) or os.path.splitext(image)[1]:
        return Image(image if os.path.splitext(image)[1] else image + '.jpg')
    filename = image + '.jpg'
    if loc_name:
        return Image(os.path.join(NAV_DIR, loc_name, filename).replace('\\', '/'))
    matches = [os.path.relpath(os.path.join(root, filename), BASE_DIR).replace('\\', '/')
               for root, _, files in os.walk(os.path.join(BASE_DIR, NAV_DIR)) if filename in files]
    if len(matches) != 1:
        raise ValueError(f"Loc('{image}'): expected one '{filename}' under {NAV_DIR}, found {matches or 'none'} "
                         f"— give the Loc a name or the full path")
    return Image(matches[0])

def action_name(fn):
    # Bound Image method (e.g. clash_icon.click) -> 'clash_icon.click', using the
    # first template's file stem since Images don't know their variable name
    owner = getattr(fn, '__self__', None)
    if isinstance(owner, Image):
        stem = os.path.splitext(os.path.basename(owner.file_locations[0]))[0]
        return f'{stem}.{fn.__name__}'
    return getattr(fn, '__name__', repr(fn))

class Action:
    def __init__(self, fn, dest, name=None, waypoint=True):
        self.fn = fn
        if dest is None:
            self.dests = []
        else:
            self.dests = dest if isinstance(dest, list) else [dest]
        for d in self.dests:
            if not isinstance(d, Loc):
                raise TypeError(f"Action dest must be a Loc, got {type(d).__name__}: {d!r}")
        self.name = name or action_name(fn)
        self.waypoint = waypoint

    def usable_for(self, target):
        return self.waypoint or target in self.dests

    def __call__(self):
        return self.fn()

    def __repr__(self):
        return self.name

class Loc:
    def __init__(self, image, name=None, order=None):
        images = image if isinstance(image, list) else [image]
        self.images = [get_image(img, name) for img in images]
        self.image = self.images[0]
        self.name = name or str(self.image)
        self.order = order
        self.actions = []
        self.checks = []
        Locs.append(self)

    def find(self):
        for image in self.images:
            if image.find(): return True

    def add_action(self, fn, dest, name=None, waypoint=True):
        action = Action(fn, dest, name=name, waypoint=waypoint)
        self.actions.append(action)
        return action

    def __repr__(self):
        return f'{self.name}'

def path(current, destination, action, back=None, name=None, waypoint=True):
    forward = current.add_action(action, destination, name=name, waypoint=waypoint)
    if back is not None:
        if not isinstance(destination, Loc):
            raise TypeError(f"path(): back needs a single Loc destination, got {destination!r}")
        destination.add_action(back, current)
    return forward

class Auto:
    def __init__(self, image, delay=0):
        self.image = image
        self.delay = delay
        autos.append(self)

    def check(self):
        if not self.image.find(): return

        if self.delay:
            print(f"{self.image.name} seen — waiting {self.delay / 60:.0f} minutes before clicking")
            time.sleep(self.delay)

        self.image.click()
        return True

def load_autos():
    dir = 'images/nav/autos/'
    for fname in sorted(os.listdir(dir)):
        delay = 0
        if fname == 'reload.jpg': delay = 10.1 * 60
        Auto(Image(dir + fname), delay=delay)

load_autos()

def check_autos():
    # print("Checking autos")
    for auto in autos:
        if auto.check(): return True

def find_path(start, target):
    if start is target:
        return []
    visited = {start}
    queue = deque([(start, [])])
    while queue:
        loc, path = queue.popleft()
        for action in loc.actions:
            if not action.usable_for(target):
                continue
            for next_loc in action.dests:
                if next_loc in visited:
                    continue
                new_path = path + [action]
                if next_loc is target:
                    return new_path
                visited.add(next_loc)
                queue.append((next_loc, new_path))
    return None

def click_at(x, y):
    anchor_position = anchor.find()
    if anchor_position is None or x is None or y is None: return
    pyautogui.click(anchor_position[0] + x, anchor_position[1] + y)

def move(x, y):
    ox, oy = (538, 338)
    drag((ox, oy), (ox - x, oy - y))

def line_click(a, b, gap, max_distance=200):
    anchor_position = anchor.find()
    if anchor_position is None:
        print("line_click: anchor not found, skipping")
        return

    ax, ay = anchor_position
    x0, y0 = a
    x1, y1 = b
    dx, dy = x1 - x0, y1 - y0
    dist = math.hypot(dx, dy)
    steps = int(dist // gap)
    for i in range(steps + 1):
        t = (i * gap) / dist if dist else 0
        rel_y = y0 + dy * t
        if not 30 < rel_y < 590:
            continue
        x, y = ax + x0 + dx * t, ay + rel_y
        pyautogui.moveTo(x, y)
        time.sleep(0.05)
        pyautogui.click()
        pyautogui.click()
        pyautogui.click()
    if steps * gap < dist and 30 < y1 < 590:
        x, y = ax + x1, ay + y1
        pyautogui.moveTo(x, y)
        time.sleep(0.05)
        pyautogui.click()

def _game_center():
    position = anchor.find()
    if not position:
        return None
    return position[0] + 550 , position[1] + 330

def zoom(notches, delay=0.05):
    center = _game_center()
    if center is None:
        print("zoom: anchor not found, cannot determine game screen center")
        return
    pyautogui.moveTo(*center)
    direction = 1 if notches > 0 else -1
    pyautogui.keyDown('ctrl')
    try:
        for _ in range(abs(notches)):
            pyautogui.scroll(direction * 120)
            time.sleep(delay)
    finally:
        pyautogui.keyUp('ctrl')

def sort_locs():
    Locs.sort(key=lambda loc: (loc.order is None, loc.order or 0))
    return Locs

def current_loc():
    global _current_loc
    if _current_loc and _current_loc.find():
        return _current_loc
    check_autos()
    if _current_loc and _current_loc.find():
        # print(f"Current loc (success post autos): {_current_loc}")
        return _current_loc
    pauses = [0.1, 0.1, 1, 1, 10, 11, 11, 30, 30, 60]
    count = 0
    while True:
        for loc in Locs:
            if loc.find():
                # print(f"Current loc (expected {_current_loc} got {loc})")
                _current_loc = loc
                return loc
        pause = pauses[count]
        if pause > 1:
            print("Lost. Sleeping: ", pause)
            clash_icon.click()
        wait(pause, show_dur=pause>1)
        count += 1

def go(dest):
    global _current_loc
    if not isinstance(dest, Loc):
        raise TypeError(f"go() expected a Loc, got {type(dest).__name__}: {dest!r}")

    current = current_loc()
    prev_action = None
    while current != dest:
        action = find_path(current, dest)
        # print(f"Go: {str(current):<15} -> {str(dest):<15} path: {action[0]}")
        if prev_action == action:
            check_autos()
        prev_action = action
        action[0]()
        _current_loc = action[0].dests[0]
        time.sleep(0.3)
        current = current_loc()

