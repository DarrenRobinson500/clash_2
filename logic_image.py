from utilities import *
import json
import numpy as np
from pathlib import Path

confidence = 0.8
full_screen_region = (0, 0, pyautogui.size().width, pyautogui.size().height)
auto_images = []
dual_images = []
boats = []

# Persists per-file match counts across separate process runs (main.py is a
# fresh one-shot script each time — see logic_account.py's identical
# reasoning for CURRENT_ACCOUNT_FILE), so counts opted into via Image(count=True)
# build up over the task loop's lifetime instead of resetting every run.
# Only files that have matched at least once ever appear as keys — a file
# missing from this dict (for an Image with count=True) has never matched.
IMAGE_COUNTS_FILE = os.path.join(BASE_DIR, 'image_counts.json')
_image_counts = None


def _load_image_counts():
    global _image_counts
    if _image_counts is None:
        try:
            with open(IMAGE_COUNTS_FILE) as f:
                _image_counts = json.load(f)
        except (FileNotFoundError, ValueError):
            _image_counts = {}
    return _image_counts


def _save_image_counts():
    with open(IMAGE_COUNTS_FILE, 'w') as f:
        json.dump(_image_counts, f, indent=2)

# Last known village-zoom scale, shared across all scalable Images so one
# Image's successful find lets every other one skip straight to a likely
# scale instead of re-sweeping the whole range. In-memory only — zoom can
# change anytime, so a guess persisted across restarts wouldn't be any more
# trustworthy than just sweeping once on first use.
_current_scale = None
_SCALE_SWEEP = [round(s, 2) for s in np.arange(0.5, 1.61, 0.05)]

class Image:
    def __init__(self, file_locations, name=None, confidence=confidence, scalable=False, glide_towards=False, count=False):
        if type(file_locations) != list:
            file_locations = [file_locations]
        if not name: name = file_locations[0]
        self.name = name
        self.confidence = confidence
        self.file_locations = file_locations
        self.loaded_images = {file: self.load_image(file) for file in self.file_locations}
        self.image = self.loaded_images[file_locations[0]]
        # Opt-in per-file match counter, persisted to IMAGE_COUNTS_FILE — lets
        # you tell which of a multi-file Image's templates (e.g. attack_resource)
        # are actually ever matched, and which are dead weight.
        self.count = count
        # Opt-in: most templates are captured from fixed-size UI chrome and
        # never change size on screen. The village/town view can be zoomed
        # by the player though, scaling everything in it uniformly — only
        # Images of things in that view need to search across scales.
        self.scalable = scalable
        # Most clicks can jump straight to the target. Some emulators only
        # register a click if it's preceded by a genuinely gradual mouse
        # movement though — set this True for those specific Images (e.g.
        # builder) rather than gliding everywhere by default.
        self.glide_towards = glide_towards

    def __str__(self):
        return self.name

    def _record_match(self, file):
        # One increment per call in which `file` matched, regardless of how
        # many instances of it were on screen — answers "how many times was
        # this file ever the/a match", not "how many instances were seen".
        if not self.count:
            return
        counts = _load_image_counts()
        counts[file] = counts.get(file, 0) + 1
        _save_image_counts()

    def wait(self, duration=20):
        freq = 4
        count = 0
        while count < duration * freq:
            result = self.find()
            if result: return True
            time.sleep(1 / freq)
            count += 1
        return False

    def load_image(self, file_path):
        full_path = os.path.join(BASE_DIR, file_path)
        if not os.path.exists(full_path):
            # Still treated as "never found" so startup carries on, but loudly —
            # a missing file is almost always a typo'd path or an uncaptured template.
            print(f"ERROR: image file not found: '{file_path}'")
            return None
        try:
            image = cv2.imread(full_path, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"ERROR: could not load image '{file_path}': {e}")
            return None
        if image is None:
            print(f"ERROR: could not read image file (corrupt or not an image): '{file_path}'")
        return image

    def show(self, dur=500, zoom=1):
        for file, image in self.loaded_images.items():
            show(image, file, dur, zoom)

    def find(self, confidence=None, region=full_screen_region, use_implied=True):
        if confidence is None: confidence = self.confidence
        if region != full_screen_region:
            # A caller-supplied region is (dx, dy, w, h) relative to anchor,
            # not an absolute screen box — resolving it here (rather than
            # requiring callers to do it themselves) is what keeps it stable
            # if the emulator window moves.
            region = self._anchor_region((region[0], region[1]), (region[2], region[3]))
            if region is None:
                return None
            # show(screenshot_region((region[0], region[1]), region[2], region[3]), f"{self} region", dur=3000)
        if self.scalable:
            return self._find_scaled(confidence, region)

        for file, image in self.loaded_images.items():
            # print("Find", self, file)
            if image is None:
                continue  # Skip if the image couldn't be loaded

            try:
                # One locate per file, stopping at the first file that matches —
                # every match only reports `confidence` (not the real score), so
                # later files or repeat locates could never beat it, and each
                # locate costs a full screenshot + match (~0.03-0.1s).
                location = pyautogui.locateCenterOnScreen(os.path.join(BASE_DIR, file), confidence=confidence, region=region)
                if location:
                    self._record_match(file)
                    return (int(location.x), int(location.y))
            except: pass
            # except Exception as e:
            #     print(f"Did not find: '{file}'")

        return None

    def _anchor_region(self, offset, size):
        from image import anchor
        anchor_position = anchor.find()
        if not anchor_position:
            return None
        return (round(anchor_position[0] + offset[0]), round(anchor_position[1] + offset[1]), size[0], size[1])

    def find_near_anchor(self, offset, size, confidence=None):
        return self.find(confidence=confidence, region=(offset[0], offset[1], size[0], size[1]))

    def click_near_anchor(self, offset, size, confidence=None, click_offset=(0, 0)):
        pos = self.find_near_anchor(offset, size, confidence=confidence)
        if pos:
            self.click(position=pos, click_offset=click_offset)
        return pos

    def show_near_anchor(self, offset, size, dur=500):
        region = self._anchor_region(offset, size)
        if region is None:
            print(f"{self}: anchor not found, cannot show region")
            return
        image = screenshot_region((region[0], region[1]), region[2], region[3])
        show(image, f"{self} region", dur)

    def _find_scaled(self, confidence, region):
        global _current_scale
        screenshot = pyautogui.screenshot(region=region)
        screen_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        # screenshot() returns physical pixels; region and moveTo use logical pixels.
        # Divide matched positions by this factor to stay in logical space.
        dpi_scale = screenshot.width / (region[2] - region[0])

        if _current_scale is not None:
            match = self._best_match_at_scale(screen_gray, _current_scale, confidence)
            if match:
                file, position, _ = match
                self._record_match(file)
                return (region[0] + round(position[0] / dpi_scale), region[1] + round(position[1] / dpi_scale))

        best = None
        for scale in _SCALE_SWEEP:
            match = self._best_match_at_scale(screen_gray, scale, confidence)
            if match and (best is None or match[2] > best[2]):
                best = match + (scale,)

        if best is None:
            return None
        file, position, _, scale = best
        self._record_match(file)
        _current_scale = scale
        return (region[0] + round(position[0] / dpi_scale), region[1] + round(position[1] / dpi_scale))

    def _best_match_at_scale(self, screen_gray, scale, confidence):
        best_file, best_position, best_confidence = None, None, 0
        for file, image in self.loaded_images.items():
            if image is None:
                continue
            template = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            w = max(1, round(template.shape[1] * scale))
            h = max(1, round(template.shape[0] * scale))
            if h > screen_gray.shape[0] or w > screen_gray.shape[1]:
                continue
            resized = cv2.resize(template, (w, h))
            result = cv2.matchTemplate(screen_gray, resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val > best_confidence:
                best_confidence = max_val
                best_position = (max_loc[0] + w // 2, max_loc[1] + h // 2)
                best_file = file
        if best_position is not None and best_confidence >= confidence:
            return best_file, best_position, best_confidence
        return None

    def _best_match_debug(self, region=full_screen_region):
        """Best match regardless of confidence threshold, for diagnostic output when find() fails."""
        try:
            screenshot = pyautogui.screenshot(region=region)
            screen_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            dpi_scale = screenshot.width / (region[2] - region[0])
        except Exception:
            return None

        if self.scalable:
            scales = [_current_scale] if _current_scale is not None else _SCALE_SWEEP
        else:
            scales = [1.0]

        best_position, best_val = None, -1
        for scale in scales:
            for file, image in self.loaded_images.items():
                if image is None:
                    continue
                template = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                w = max(1, round(template.shape[1] * scale))
                h = max(1, round(template.shape[0] * scale))
                if h > screen_gray.shape[0] or w > screen_gray.shape[1]:
                    continue
                resized = cv2.resize(template, (w, h)) if scale != 1.0 else template
                result = cv2.matchTemplate(screen_gray, resized, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                if max_val > best_val:
                    best_val = max_val
                    best_position = (region[0] + round((max_loc[0] + w // 2) / dpi_scale),
                                      region[1] + round((max_loc[1] + h // 2) / dpi_scale))

        if best_position is None:
            return None
        return best_position, best_val

    def find_all(self, confidence=None, region=full_screen_region):
        # Mirrors find(), but collects every match (top-left corners) across
        # all files instead of stopping at the first one. Scalable Images are
        # searched at the same village-zoom scale find() would use.
        global _current_scale
        if confidence is None: confidence = self.confidence
        if region != full_screen_region:
            region = self._anchor_region((region[0], region[1]), (region[2], region[3]))
            if region is None:
                return []

        screenshot = pyautogui.screenshot(region=region)
        screen_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        # screenshot() returns physical pixels; region and moveTo use logical pixels.
        dpi_scale = screenshot.width / (region[2] - region[0])

        if not self.scalable:
            scale = 1.0
        elif _current_scale is not None and self._best_match_at_scale(screen_gray, _current_scale, confidence):
            scale = _current_scale
        else:
            best = None
            for s in _SCALE_SWEEP:
                match = self._best_match_at_scale(screen_gray, s, confidence)
                if match and (best is None or match[2] > best[2]):
                    best = match + (s,)
            if best is None:
                return []
            scale = _current_scale = best[3]

        all_matches = []
        min_distance = 20
        for file, image in self.loaded_images.items():
            if image is None:
                continue  # Skip if the image couldn't be loaded

            template = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if scale != 1.0:
                template = cv2.resize(template, (max(1, round(template.shape[1] * scale)), max(1, round(template.shape[0] * scale))))
            if template.shape[0] > screen_gray.shape[0] or template.shape[1] > screen_gray.shape[1]:
                continue
            result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= confidence)
            detected_points = [(region[0] + round(x / dpi_scale), region[1] + round(y / dpi_scale)) for y, x in zip(*locations)]
            if detected_points:
                self._record_match(file)

            # Filter out close detections
            for point in detected_points:
                if all(np.linalg.norm(np.array(point) - np.array(existing)) > min_distance for existing in all_matches):
                    all_matches.append(point)

        all_matches.sort()
        return all_matches

    def click(self, confidence=None, click_offset=(0, 0), position=None):
        if confidence is None: confidence = self.confidence
        # Callers that already found a position (e.g. Auto.check()) can pass
        # it straight in — re-running find() here would search again and
        # could miss on a popup that's mid-animation or already gone,
        # silently dropping the click despite the earlier find() succeeding.
        if position is None:
            position = self.find(confidence)
            if position is None:
                time.sleep(0.5)
                position = self.find(confidence)

        if position:
            position_offset = position[0] + click_offset[0], position[1] + click_offset[1]
            # print("Position offset:", position, position_offset)
            if self.glide_towards:
                smooth_move_to(*position_offset)
            else:
                pyautogui.moveTo(*position_offset)
            time.sleep(0.05)
            pyautogui.click()
            # print(f"Clicked on {self} image at {position}")
            return position
        else:
            debug = self._best_match_debug()
            if debug:
                best_position, best_val = debug
                # print(f"Image not found: {self}. No click performed. Best match at {best_position}, similarity {best_val:.2f}.")
            else:
                print(f"Image not found: {self}. No click performed.")
            return False

def auto_click():
    clicked = False
    y_limit = 90
    for image in auto_images:
        for pos in image.find_all():
            if pos[1] > y_limit:
                clicked = True
                image.click(position=pos)
                # print("Auto click:", image.name)
                if image.name == "images/auto/google_back.jpg":
                    time.sleep(0.5)
                    import nav
                    nav.home.click()
    for see_image, click_image in dual_images:
        pos = see_image.find()
        print(see_image, pos)
        if pos:
            click_image.click()
            clicked = True
            print("Dual click: saw", see_image.name, "clicked", click_image.name)
    return clicked

def create_image_group(directory, scalable=False, confidence=0.85):
    group = []
    for f in Path(f'images/{directory}').iterdir():
        if f.is_file():
            name = f.stem
            new_image = Image(str(f), name, scalable=False, confidence=confidence)
            group.append(new_image)
    return group



