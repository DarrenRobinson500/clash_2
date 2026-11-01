import hashlib
import math
import time
from collections import deque
from logic_image import *
from image import *

_all_locs = []
_locs_by_name = {}
_current_loc = None

AUTO_DIR = os.path.join(BASE_DIR, 'images', 'nav_old', 'auto')
Locs = []

# Escalating waits (seconds) used when an action runs but the screen doesn't
# change at all. A same-loc result usually means the game itself isn't
# responding (emulator/server hiccup), so it's worth riding out with
# increasing delays instead of burning through max_steps instantly.
_STALL_BACKOFF = (10, 30, 60, 120, 300, 600, 3600, 3600, 3600, 3600, 3600, 3600, 3600, 3600, 3600, 3600, 3600, 3600)  # 10s, 30s, 1m, 2m, 5m, 10m

def _action_name(fn):
    # Bound methods like image.click all share __name__ == 'click';
    # qualify with the bound instance (e.g. the Image) to keep names unique.
    if hasattr(fn, '__self__'):
        return f'{fn.__self__}.{fn.__name__}'
    return fn.__name__


class Action:
    def __init__(self, fn, dest, name=None, waypoint=True):
        self.fn = fn
        # dest is the Loc this action is expected to land on. A list means it
        # can land on any of them (e.g. closing settings returns to whichever
        # base it was opened from). None means the destination is unknown —
        # go() only falls back to such an action when no declared route exists.
        if dest is None:
            self.dests = []
        else:
            self.dests = dest if isinstance(dest, list) else [dest]
        for d in self.dests:
            if not isinstance(d, Loc):
                raise TypeError(f"Action dest must be a Loc, got {type(d).__name__}: {d!r}")
        self.name = name or _action_name(fn)
        # waypoint=False marks an action with side effects you don't want as a
        # mere step on the way somewhere else (e.g. one that starts an attack):
        # go() only takes it when go()'s target is this action's destination.
        self.waypoint = waypoint

    def usable_for(self, target):
        return self.waypoint or target in self.dests

    def __call__(self):
        return self.fn()

    def __repr__(self):
        dests = ', '.join(d.name for d in self.dests) or '?'
        return f'{self.name} -> {dests}'


NAV_DIR = os.path.join('images', 'nav')


def _resolve_image(image, loc_name):
    # Lets a Loc be declared with a string instead of an Image:
    #  - a bare name ("buildings and heroes") is the Loc's own template file,
    #    images/nav/<loc name>/<string>.jpg — or, if the Loc has no name, the
    #    one file of that name anywhere under images/nav;
    #  - anything with a folder or extension ("images/nav/home/battle.jpg")
    #    is a path, same as Image() takes.
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


class Loc:
    def __init__(self, image, name=None, order=None):
        images = image if isinstance(image, list) else [image]
        self.images = [_resolve_image(img, name) for img in images]
        self.image = self.images[0]
        self.name = name or str(self.image)
        self.actions = []
        self.checks = []
        # Lower order is checked first by _scan(), so when two Locs' identifying
        # images are visible at once, the one with the lower order wins. Defaults
        # to definition order, so the first Loc defined takes priority.
        self.order = order if order is not None else len(_all_locs)
        _all_locs.append(self)
        _locs_by_name[self.name] = self
        Locs.append(self)

    def add_action(self, fn, dest, name=None, waypoint=True):
        action = Action(fn, dest, name=name, waypoint=waypoint)
        self.actions.append(action)
        return action

    def add_check(self, loc):
        if isinstance(loc, list):
            for l in loc:
                self.add_check(l)
            return loc
        if loc is not self:
            # A Loc checking itself would make find() recurse into itself
            # forever (each frame re-running the same expensive image match).
            self.checks.append(loc)
        return loc

    def looks_like(self, other):
        # True when two Locs are identified by pixel-identical templates (even
        # under different filenames, e.g. each base's build panel header) —
        # the screen alone can't tell them apart, so _scan() resolves a match
        # to whichever one navigation expects.
        if other is self:
            return True
        return self._signature() == other._signature()

    def _signature(self):
        if not hasattr(self, '_sig'):
            self._sig = frozenset(
                hashlib.md5(img.tobytes()).hexdigest()
                for image in self.images
                for img in getattr(image, 'loaded_images', {}).values()
                if img is not None
            ) or frozenset([id(self)])
        return self._sig

    def find(self):
        # Some Locs share a visible identifying image with an overlay state
        # (e.g. a "Are you still there?" popup on top of the home screen still
        # shows the home background). A checked Loc takes priority: if it's
        # also currently visible, this Loc isn't considered a match, in both
        # go()'s cached-location check and the full ordered _scan().
        if not all(img.find() for img in self.images):
            return False
        return not any(check.find() for check in self.checks)

    def __repr__(self):
        return f'Loc({self.name})'


def path(current, destination, action, back=None, name=None, waypoint=True):
    forward = current.add_action(action, destination, name=name, waypoint=waypoint)
    if back is not None:
        if not isinstance(destination, Loc):
            raise TypeError(f"path(): back needs a single Loc destination, got {destination!r}")
        destination.add_action(back, current)
    return forward


class Auto:
    """A button that should just be clicked whenever it's seen, with no
    notion of location — e.g. a "Reload"/"Try again" popup that can appear
    on top of almost any screen."""
    def __init__(self, image, delay=0):
        self.image = image
        # Some popups (e.g. "reload") shouldn't be clicked the instant they
        # appear — waiting lets whatever caused them (connection drop, server
        # hiccup) resolve on its own instead of just re-triggering the same
        # popup in a fast click loop. delay is seconds to actually block and
        # wait, once seen, before clicking.
        self.delay = delay

    def check(self):
        position = self.image.find()
        if not position:
            return False

        if self.delay:
            print(f"{self.image.name} seen — waiting {self.delay / 60:.0f} minutes before clicking")
            time.sleep(self.delay)
            position = self.image.find()
            if not position:
                return False

        # Logged on every click, whoever triggered the check — an auto that
        # matches something it shouldn't (e.g. a panel's own close button)
        # silently undoes navigation otherwise.
        # print(f"Auto clicked: {self.image.name} at {position}")
        self.image.click(position=position)
        return True


# Filenames (within AUTO_DIR) that should be held for a while before being
# clicked, rather than clicked the instant they're seen — see Auto.delay.
_AUTO_DELAYS = {
    'reload.jpg': 15 * 60,
}


def _load_autos():
    autos = []
    for fname in sorted(os.listdir(AUTO_DIR)):
        path = os.path.join('images', 'nav_old', 'auto', fname)
        autos.append(Auto(Image(path, glide_towards=True), delay=_AUTO_DELAYS.get(fname, 0)))
    return autos

_autos = _load_autos()



def check_autos():
    return [auto.image.name for auto in _autos if auto.check()]


def _print_near_misses(top=3):
    scores = []
    for loc in _all_locs:
        for img in loc.images:
            debug = img._best_match_debug()
            if debug:
                scores.append((debug[1], loc.name, img.name, img.confidence))
    for score, loc_name, img_name, needed in sorted(scores, reverse=True)[:top]:
        print(f"  closest: {loc_name} ({img_name}) {score:.2f} / {needed}")

def _recover_lost():
    print("Lost — cannot determine current location, waiting...")
    _print_near_misses()
    check_autos()
    time.sleep(5)
    _scan()
    clash_icon.click()
    return _scan()

def _outranked_by(loc, known_absent=()):
    # A visible Loc with a lower order than `loc` (other than a look-alike of
    # it), or None. Lets a quick "is `loc` visible?" check still honour order
    # — e.g. builder base's icon also shows behind the builder attack screen,
    # which has the lower order and so is where we really are.
    for other in sorted(_all_locs, key=lambda l: l.order):
        if other.order >= loc.order:
            return None
        if other in known_absent or other.looks_like(loc):
            continue
        if other.find():
            return other
    return None


def _scan(prefer=()):
    def resolve(loc):
        for preferred in prefer:
            if preferred.looks_like(loc):
                return preferred
        return loc

    known_absent = set()
    for loc in prefer:
        if loc in known_absent:
            continue
        if loc.find():
            outranking = _outranked_by(loc, known_absent)
            return resolve(outranking) if outranking else loc
        known_absent.add(loc)
    for loc in sorted(_all_locs, key=lambda loc: loc.order):
        if loc not in known_absent and loc.find():
            return resolve(loc)
    return None


# check_autos() costs ~2s (every auto image is a full-screen locate), so the
# post-action wait loop only runs it this often rather than on every poll —
# otherwise it, not the poll interval, sets how quickly arrival is noticed.
# go()'s no-progress branch still clears autos straight away on a stall.
_AUTO_CHECK_INTERVAL = 3


def _scan_after_action(from_loc, action=None, target=None, timeout=20, interval=0.5):
    # Give the screen time to transition — scanning immediately after an
    # action can still see from_loc mid-transition (which would otherwise get
    # learned as a bogus self-loop), or land on an unrecognized loading screen
    # (no Loc matches at all) before settling on the real destination.
    prefer = ([target] if target else []) + (list(action.dests) if action else []) + [from_loc]
    start = time.monotonic()
    deadline = start + timeout
    last_autos = start
    # Seeing from_loc — or a look-alike of it, such as the target when both
    # share a template — means the screen hasn't changed yet (e.g. a panel
    # still animating closed), not that we've arrived somewhere.
    still_here = lambda loc: loc is None or loc.looks_like(from_loc)
    result = _scan(prefer)
    while still_here(result) and time.monotonic() < deadline:
        if time.monotonic() - last_autos >= _AUTO_CHECK_INTERVAL:
            check_autos()
            last_autos = time.monotonic()
        time.sleep(interval)
        result = _scan(prefer)
    if result is not None and result.looks_like(from_loc):
        result = from_loc
    return result


def _find_path(start, target):
    """Fewest-hop list of Actions from `start` to `target`, using declared destinations."""
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


def _next_action(start, target):
    path = _find_path(start, target)
    if path:
        return path[0]
    # No declared route — try an action whose destination is unknown (e.g.
    # refocusing the game from pycharm) and replan from wherever it lands.
    for action in start.actions:
        if not action.dests and action.usable_for(target):
            return action
    return None


# Print every step go() takes (not just unexpected ones), so a run's output
# shows exactly which clicks navigation made and where each one landed.
NAV_LOG = False


def _perform_action(from_loc, action, target=None):
    if NAV_LOG:
        print(f"nav: at {from_loc.name}, doing {action.name}")
    action()
    new_loc = _scan_after_action(from_loc, action, target)
    if NAV_LOG:
        print(f"nav:   -> now at {new_loc.name if new_loc else '?'}")
    while new_loc is None:
        new_loc = _recover_lost()
    if action.dests and new_loc is not from_loc and new_loc not in action.dests:
        # Not fatal — go() just replans from wherever we actually are — but
        # worth seeing, since a repeat offender means a wrong dest in nav.py.
        # The expected Locs' best scores show whether they were nearly
        # matched (threshold/template issue) or genuinely not on screen.
        expected = []
        for d in action.dests:
            debug = d.image._best_match_debug()
            expected.append(f"{d.name} {debug[1]:.2f}/{d.image.confidence}" if debug else d.name)
        # print(f"Unexpected: {from_loc.name} --{action.name}--> {new_loc.name} "
        #       f"(expected {', '.join(expected)})")
    return new_loc


def current_loc():
    """The Loc currently on screen, or None if none is recognized.

    Checks the screen rather than trusting go()'s cached answer, since the
    game can change underneath it (popups, a panel closing). The cached Loc
    is checked first, so it's one image match when nothing has changed.
    """
    global _current_loc
    loc = _scan([_current_loc] if _current_loc else [])
    if loc is not None:
        _current_loc = loc
    return loc


def go(dest, max_steps=80):
    global _current_loc

    if not isinstance(dest, Loc):
        raise TypeError(f"go() expected a Loc, got {type(dest).__name__}: {dest!r}")

    # Check the target first: if it's already visible (and no lower-order Loc
    # is visible on top of it), assume we're there.
    if dest.find() and not _outranked_by(dest):
        if NAV_LOG:
            print(f"nav: go({dest.name}) — already there")
        _current_loc = dest
        return

    if _current_loc is None or not _current_loc.find() or _outranked_by(_current_loc):
        _current_loc = _scan()
        while _current_loc is None:
            _current_loc = _recover_lost()

    stall_count = 0

    for _ in range(max_steps):
        if _current_loc is dest:
            return

        action = _next_action(_current_loc, dest)
        if action is None:
            raise RuntimeError(f"No route from {_current_loc.name} to {dest.name}")

        from_loc = _current_loc
        _current_loc = _perform_action(from_loc, action, dest)

        if _current_loc is from_loc:
            # No progress is often a popup (ad, "reload", etc.) sitting on top
            # of the action's real target and absorbing the click — clear any
            # visible auto button and retry immediately before backing off,
            # since that's a much faster recovery than just waiting it out.
            cleared = check_autos()
            if cleared:
                print(f"No progress from {from_loc.name} — cleared auto popup(s) {', '.join(cleared)}, retrying")
                continue

            # A glide_towards image's click can fail to register if the
            # mouse is already sitting at the target from a previous click —
            # nudging it away and back forces real movement before clicking
            # again, which some emulators need to recognize the click at all.
            bound_image = getattr(action.fn, '__self__', None)
            if isinstance(bound_image, Image) and bound_image.glide_towards:
                print(f"No progress from {from_loc.name} — nudging mouse and retrying {action.name}")
                x, y = pyautogui.position()
                pyautogui.moveTo(x + 20, y)
                pyautogui.moveTo(x + 10, y)
                _current_loc = _perform_action(from_loc, action, dest)
                if _current_loc is not from_loc:
                    stall_count = 0
                continue

            if stall_count >= len(_STALL_BACKOFF):
                raise RuntimeError(f"Navigation stalled: no progress from {from_loc.name} after repeated retries")
            wait = _STALL_BACKOFF[stall_count]
            stall_count += 1
            print(f"No progress from {from_loc.name} — waiting {wait}s before retrying")
            time.sleep(wait)
        else:
            stall_count = 0

    raise RuntimeError("Navigation failed: max steps exceeded")


def open_clash():
    icon_toolbar.click()


# Offset from anchor's center to the center of the game screen, measured
# from images/main screen.jpg (a reference capture of the emulator window,
# which doesn't fill the whole physical screen). Lets _game_center() find
# the game's center at runtime from wherever anchor actually is, rather than
# assuming the game fills pyautogui.size().
_GAME_CENTER_OFFSET = (538, 338)


def _game_center():
    position = anchor.find()
    if not position:
        return None
    return position[0] + _GAME_CENTER_OFFSET[0], position[1] + _GAME_CENTER_OFFSET[1]


# Top-left of images/main screen.jpg (a reference capture of the emulator
# window) relative to anchor's center, plus that reference capture's size.
# Lets screenshot_game() capture the same window region at runtime from
# wherever anchor actually is, rather than assuming the game fills
# pyautogui.size() or sits at a fixed screen position.
_GAME_SCREENSHOT_OFFSET = (-65.5, 20)
_GAME_SCREENSHOT_SIZE = (1207, 717)


def game_screenshot_origin():
    # Top-left corner screenshot_game() captures from — exposed separately
    # so a caller can convert a point found in that screenshot (e.g. a
    # deploy spot) back into an absolute screen coordinate to click.
    position = anchor.find()
    if not position:
        return None
    return round(position[0] + _GAME_SCREENSHOT_OFFSET[0]), round(position[1] + _GAME_SCREENSHOT_OFFSET[1])


def screenshot_game(directory):
    origin = game_screenshot_origin()
    if origin is None:
        return None
    w, h = _GAME_SCREENSHOT_SIZE
    image = screenshot_region(origin, w, h)
    filename = time.strftime('Screenshot %Y-%m-%d %H%M%S.jpg')
    path = os.path.join(BASE_DIR, directory, filename)
    cv2.imwrite(path, image)
    return cv2.imread(path)


def screenshot_loop(directory='images/screenshots', interval=3, duration=120):
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        screenshot_game(directory)
        time.sleep(interval)


def press_esc():
    # Keyboard input goes wherever the OS currently has focus, not
    # necessarily the emulator — if focus has drifted elsewhere (e.g. the
    # IDE/terminal this is running in), esc gets sent nowhere useful and
    # nothing happens. Clicking anchor first (pure window chrome, doesn't
    # affect game state) guarantees the right window is focused before esc
    # fires.
    anchor.click()
    pyautogui.press('esc')


def click_at(x, y):
    # Deploy taps jump straight to the spot rather than tweening like
    # smooth_move_to — unlike nav clicks, these land on freshly-placed
    # troops/empty grass each time, so there's no risk of landing mid-tween
    # on the wrong thing, and skipping the tween matters for deploy speed.
    # x, y are an offset from the anchor position, not absolute screen coords.
    anchor_position = anchor.find()
    if anchor_position is None:
        print("click_at: anchor not found, skipping click")
        return
    if x is None or y is None: return
    pyautogui.moveTo(anchor_position[0] + x, anchor_position[1] + y)
    time.sleep(0.05)
    pyautogui.click()


def click_again():
    # Re-tap wherever the cursor already is, e.g. to place several troops at
    # the same deploy spot — skips smooth_move_to's tween, since that's only
    # needed to get the cursor there the first time, not to tap it again.
    time.sleep(0.05)
    pyautogui.click()

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


# def line_click_old(a, b, gap, max_distance=200, click_anyway=False):
#     anchor_position = anchor.find()
#     if anchor_position is None:
#         print("line_click: anchor not found, skipping")
#         return
#     resource_spots = attack_resource.find_all()
#     if not resource_spots and not click_anyway:
#         print("line_click: no resources found, skipping")
#         return
#
#     def near_resource(x, y):
#         if click_anyway:
#             return True
#         return any(math.hypot(x - rx, y - ry) <= max_distance for rx, ry in resource_spots)
#
#     ax, ay = anchor_position
#     x0, y0 = a
#     x1, y1 = b
#     dx, dy = x1 - x0, y1 - y0
#     dist = math.hypot(dx, dy)
#     steps = int(dist // gap)
#     for i in range(steps + 1):
#         t = (i * gap) / dist if dist else 0
#         rel_y = y0 + dy * t
#         if not 30 < rel_y < 590:
#             continue
#         x, y = ax + x0 + dx * t, ay + rel_y
#         if not near_resource(x, y):
#             continue
#         pyautogui.moveTo(x, y)
#         time.sleep(0.05)
#         pyautogui.click()
#         pyautogui.click()
#     if steps * gap < dist and 30 < y1 < 590:
#         # Last step short of gap didn't land exactly on b — click it too so
#         # the line's endpoint always gets covered.
#         x, y = ax + x1, ay + y1
#         if near_resource(x, y):
#             pyautogui.moveTo(x, y)
#             time.sleep(0.05)
#             pyautogui.click()


def move(x, y):
    # Pan the camera: drag from the game screen's center by (-x, -y).
    # drag() resolves _GAME_CENTER_OFFSET against anchor itself.
    ox, oy = _GAME_CENTER_OFFSET
    drag((ox, oy), (ox - x, oy - y))


_WHEEL_NOTCH = 120
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
            pyautogui.scroll(direction * _WHEEL_NOTCH)
            time.sleep(delay)
    finally:
        pyautogui.keyUp('ctrl')

