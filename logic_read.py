from datetime import datetime, timedelta
import re
import json
import numpy as np
from logic_image import *

READ_DIR = os.path.join(BASE_DIR, 'images', 'read')
FAILS_DIR = os.path.join(READ_DIR, 'fails')
REGIONS_FILE = os.path.join(BASE_DIR, 'read_regions.json')


def _load_regions():
    if not os.path.exists(REGIONS_FILE):
        return {}
    with open(REGIONS_FILE) as f:
        return json.load(f)


def _save_regions(regions):
    with open(REGIONS_FILE, 'w') as f:
        json.dump(regions, f, indent=2)


class Read:
    def __init__(self, name, region, anchor=None, confidence=0.75, char_confidence=None, mask=False, template_dir=None, low_priority_chars=(), fixed_region=False, image_path=None, black_and_white=False, white_threshold=170):
        self.name = name
        # When set, reads always come from this jpg (cropped to `region`,
        # treated as an absolute box) instead of a live screenshot — there's
        # no screen to find `anchor` on, and no live region to remember, so
        # image_path reads never touch the anchor lookup or the persisted
        # regions file.
        self.image_path = image_path
        self.fixed_region = fixed_region
        self.confidence = confidence
        # Per-character overrides of `confidence` (e.g. {'1': 0.9}) — a narrow
        # glyph like '1' can clear the default threshold as a false positive
        # inside a wider digit's stroke, so raising just its own threshold
        # keeps it from matching at all there instead of only losing the
        # overlap tie-break (see low_priority_chars below).
        self.char_confidence = char_confidence or {}
        # A narrow glyph like '1' can score a higher raw match confidence as
        # a false positive inside a wider digit's stroke (e.g. part of a '4'
        # or '7') than that digit's own template does at its true position.
        # Listing such chars here makes them lose every overlap tie-break
        # regardless of raw score, so a real wider-digit match always wins
        # where the two compete for the same pixels. Default empty so every
        # existing Read keeps today's pure-confidence ordering unchanged.
        self.low_priority_chars = set(low_priority_chars)
        # Resource counters sit on a gold/purple/green background depending on
        # type and stock level, which shifts raw grayscale pixel values too
        # much for one template per digit to match reliably. The digit text
        # itself is always bright and low-saturation though, so masking down
        # to just that (via HSV saturation/value thresholds) before matching
        # makes the background irrelevant instead of needing a template per
        # background color.
        self.use_mask = mask
        # Like mask, but keeps only near-white pixels (see utilities.white_mask,
        # the same filter extract_time saves) — templates and captures alike, so
        # matching only ever compares the white text, never the background.
        # Takes precedence over mask if both are set.
        self.black_and_white = black_and_white
        # Per-read cut-off for black_and_white. Some counters are drawn in
        # grey rather than white (dark elixir reads ~130-150), which the
        # default 170 strips out entirely — lower it for those reads.
        self.white_threshold = white_threshold
        # Defaults to `name`, but several Reads can share one template set
        # (e.g. gold/elixir use the same digit font, just a different on-screen
        # row and background color) without duplicating the template files.
        self.template_dir = template_dir or name
        self.templates = self._load_templates()
        # Characters are rarely unique in shape (the same digit font is reused
        # all over the screen for resource counts, troop levels, other timers,
        # etc.), so a search box must always be given rather than guessed —
        # `region` is that starting search box. If `anchor` (an Image) is
        # given, `region` is a (dx, dy, w, h) offset from wherever anchor is
        # found on screen, rather than an absolute box — so it keeps working
        # if the window/UI moves. Once a read succeeds, the remembered/
        # persisted region below takes over and narrows further (always
        # absolute, since it's from a real capture).
        self.anchor = anchor
        self.initial_region = region
        saved_region = _load_regions().get(self.name)
        self.region = tuple(saved_region) if saved_region else None

    def _load_templates(self):
        folder = os.path.join(READ_DIR, self.template_dir)
        # Keyed by file stem: '3' is the character itself, and '3b', '3c'...
        # are extra variants of the same character (key[0]) — e.g. the
        # resource digits render slightly differently on the gold/elixir
        # counters than on dark elixir, and no single template matches both.
        # Whichever variant scores best at a position wins.
        templates = {}
        for fname in sorted(os.listdir(folder)):
            stem, ext = os.path.splitext(fname)
            if not re.fullmatch(r'.[a-z]?', stem):
                continue  # skip reference screenshots etc.
            image = cv2.imread(os.path.join(folder, fname))
            if image is not None:
                templates[stem] = self._prepare(image, cv2.COLOR_BGR2GRAY)
        return templates

    def _char_size(self, char):
        # (h, w) of the largest variant of char, for sizing a remembered region.
        shapes = [t.shape for key, t in self.templates.items() if key[0] == char]
        return max(h for h, _ in shapes), max(w for _, w in shapes)

    def _prepare(self, image, gray_code):
        # gray_code: cv2.COLOR_BGR2GRAY for cv2.imread images, COLOR_RGB2GRAY
        # for pyautogui screenshots. Both masks are channel-order independent.
        if self.black_and_white:
            return white_mask(image, self.white_threshold)
        if self.use_mask:
            return self._to_mask(image)
        return cv2.cvtColor(image, gray_code)

    _ERODE_KERNEL = np.ones((2, 2), np.uint8)

    @classmethod
    def _to_mask(cls, image):
        # Saturation/value are computed from just max/min across channels, so
        # this gives identical results whether `image` is BGR (cv2.imread) or
        # RGB (pyautogui.screenshot) — only hue would differ, which is unused.
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        s, v = hsv[:, :, 1], hsv[:, :, 2]
        mask = ((s < 90) & (v > 140)).astype(np.uint8) * 255
        # Tightly-kerned digits can render with touching strokes (no gap
        # pixel between them), which contaminates each character's template
        # match with its neighbor's strokes. A 1px erosion thins every glyph
        # just enough to break that bridge without losing its own shape.
        return cv2.erode(mask, cls._ERODE_KERNEL)

    def _initial_box(self):
        if self.anchor is None:
            return self.initial_region
        position = self.anchor.find()
        if not position:
            # Anchor isn't on screen right now — don't fall back to a blind
            # full-screen search, since that's exactly the garbage-match
            # problem anchor-relative regions exist to avoid. Skip this read
            # instead of guessing.
            return None
        dx, dy, w, h = self.initial_region
        return (position[0] + dx, position[1] + dy, w, h)

    def _box(self):
        return self.region or self._initial_box()

    def _capture(self):
        if self.image_path:
            return self._capture_from_file()
        box = self._box()
        if box is None:
            return None, None, None
        x, y, w, h = box
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        array = np.array(screenshot)
        # Raw colour capture (BGR, like cv2.imread) kept for _save_failure.
        self._last_raw = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
        image = self._prepare(array, cv2.COLOR_RGB2GRAY)
        return image, x, y

    def _capture_from_file(self):
        array = cv2.imread(self.image_path)
        if array is None:
            print(f"{self.name}: couldn't read image file '{self.image_path}'")
            return None, None, None
        x, y = 0, 0
        if self.initial_region:
            x, y, w, h = self.initial_region
            array = array[y:y + h, x:x + w]
        self._last_raw = array
        image = self._prepare(array, cv2.COLOR_BGR2GRAY)
        return image, x, y

    def show_region(self):
        box = self._box()
        if box is None:
            print(f"{self.name}: anchor not found, nothing to show")
            return
        x, y, w, h = box
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        show(image, self.name, dur=2000)

    def _find_chars(self, gray):
        # A fixed grid (cell = x // max_w) misaligns with real character
        # spacing: two distinct, tightly-kerned characters can land in the
        # same cell (silently dropping one), while sub-pixel echoes of a
        # single character's peak can split across a cell boundary (creating
        # a phantom duplicate). Greedy non-max suppression by proximity to
        # the best-scoring match avoids both, regardless of absolute position.
        candidates = []
        for key, template in self.templates.items():
            char = key[0]
            h, w = template.shape
            result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            threshold = self.char_confidence.get(char, self.confidence)
            ys, xs = np.where(result >= threshold)
            for y, x in zip(ys.tolist(), xs.tolist()):
                conf = float(result[y, x])
                candidates.append((conf, x, y, char, w, h))

        candidates.sort(key=lambda c: (c[3] not in self.low_priority_chars, c[0]), reverse=True)
        accepted = []
        for conf, x, y, char, w, h in candidates:
            # Proximity alone (distance < one template width) wrongly treats
            # tightly-kerned distinct characters as duplicates of each other
            # when their spacing approaches their own width (e.g. "65" in a
            # narrow font). Real duplicates — the same glyph's peak detected
            # at a 1-2px sub-pixel offset — overlap heavily; distinct
            # neighbors barely overlap even touching edge-to-edge. Overlap
            # fraction tells them apart where raw distance can't.
            if any(self._overlap_fraction(x, y, w, h, ax, ay, aw, ah) > 0.5
                   for _, ax, ay, _, aw, ah in accepted):
                continue
            accepted.append((conf, x, y, char, w, h))
        return [(conf, x, y, char) for conf, x, y, char, _, _ in accepted]

    @staticmethod
    def _overlap_fraction(x, y, w, h, ax, ay, aw, ah):
        overlap_w = max(0, min(x + w, ax + aw) - max(x, ax))
        overlap_h = max(0, min(y + h, ay + ah) - max(y, ay))
        return (overlap_w * overlap_h) / min(w * h, aw * ah)

    def _remember_region(self, matches, ox, oy):
        pad = 10
        left = min(x for _, x, _, _ in matches)
        top = min(y for _, _, y, _ in matches)
        right = max(x + self._char_size(char)[1] for _, x, _, char in matches)
        bottom = max(y + self._char_size(char)[0] for _, _, y, char in matches)
        x = max(ox + left - pad, 0)
        y = max(oy + top - pad, 0)
        self.region = (x, y, right - left + pad * 2, bottom - top + pad * 2)

        regions = _load_regions()
        regions[self.name] = list(self.region)
        _save_regions(regions)

    def _forget_region(self):
        self.region = None
        regions = _load_regions()
        if regions.pop(self.name, None) is not None:
            _save_regions(regions)

    def _save_failure(self):
        # The raw colour capture rather than the masked one, so it can be fed
        # straight back in later (Read(..., image_path=...)) or cropped into a
        # new template with extract_image.
        os.makedirs(FAILS_DIR, exist_ok=True)
        filename = time.strftime(f'{self.name} %Y-%m-%d %H%M%S.jpg')
        cv2.imwrite(os.path.join(FAILS_DIR, filename), self._last_raw)

    def _show_failure(self, gray):
        # Shows what the matcher actually saw (after mask/black_and_white),
        # enlarged since read regions are only a few dozen pixels, plus each
        # character's best score — usually tells you straight away whether the
        # region is off or a template's threshold is just too high.
        best = {}
        for char, template in self.templates.items():
            if template.shape[0] <= gray.shape[0] and template.shape[1] <= gray.shape[1]:
                best[char] = cv2.minMaxLoc(cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED))[1]
        scores = ', '.join(f"{c}={v:.2f}" for c, v in sorted(best.items(), key=lambda kv: -kv[1])[:5])
        # print(f"{self.name}: no characters read (confidence {self.confidence}); best: {scores or 'none'}")
        self._show_capture(gray, f"{self.name}: nothing read", dur=4000)

    def _show_capture(self, gray, title, dur):
        # Raw colour capture on top, filtered version below — shows whether the
        # filter itself is what's losing the characters.
        filtered = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        combined = np.vstack([self._last_raw, filtered]) if self._last_raw.shape == filtered.shape else filtered
        show(cv2.resize(combined, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST), title, dur=dur)

    def __call__(self, save=False, return_details=False, show_on_fail=True, wait=0, as_int=False, show_capture=False):
        # wait: seconds to keep retrying a live read that finds nothing — for
        # text on a panel that's still animating in, where the first capture
        # can see whatever is behind it. Only the final attempt's failure is
        # saved/shown.
        # as_int: return the result as an int, or None if it isn't all digits.
        # Ignored when return_details is set.
        # show_capture: display the capture that was read (raw on top,
        # filtered below) with the result in the title, even on success.
        gray, ox, oy = self._capture()
        if gray is None:
            if show_on_fail:
                print(f"{self.name}: nothing to read (anchor not found or image missing)")
            return [] if return_details else None

        matches = self._find_chars(gray)

        if not matches and self.region:
            # remembered region may be stale (UI moved/changed) — fall back to
            # initial_region once
            self._forget_region()
            gray, ox, oy = self._capture()
            if gray is None:
                if show_on_fail:
                    print(f"{self.name}: nothing to read (anchor not found or image missing)")
                return [] if return_details else None
            matches = self._find_chars(gray)

        deadline = time.monotonic() + wait
        while not matches and not self.image_path and time.monotonic() < deadline:
            time.sleep(0.25)
            retry, rx, ry = self._capture()
            if retry is not None:
                gray, ox, oy = retry, rx, ry
                matches = self._find_chars(gray)

        result = None
        details = []
        if matches:
            matches.sort(key=lambda m: m[1])  # left to right by x
            if not self.fixed_region and not self.image_path:
                self._remember_region(matches, ox, oy)
            result = ''.join(char for _, _, _, char in matches)
            details = [{'position': (ox + x, oy + y), 'value': char} for _, x, y, char in matches]
        else:
            self._save_failure()
            if show_on_fail:
                self._show_failure(gray)

        if show_capture and (matches or not show_on_fail):
            self._show_capture(gray, f"{self.name}: {result}", dur=2000)

        if save:
            path = os.path.join(READ_DIR, 'testing', f'{self.name}_{result}.jpg')
            cv2.imwrite(path, gray)

        if return_details:
            return details
        if as_int:
            return int(result) if result and result.isdigit() else None
        return result


_TIME_UNITS = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
_NEXT_UNIT = {'d': 'h', 'h': 'm', 'm': 's'}


def time_to_seconds(text):
    """Seconds in a builder-time reading like '4H2M', '1d16H' or '23M23'.

    The game drops the last unit's letter when it's the one below the
    previous unit, so a bare trailing number ('23M23') is read as that next
    unit down (23m 23s). Returns None if the text can't be parsed.
    """
    if not text:
        return None
    parts = re.findall(r'(\d+)([dhms]?)', text.strip().lower())
    if not parts or ''.join(n + u for n, u in parts) != re.sub(r'\s', '', text.lower()):
        return None
    seconds, prev_unit = 0, None
    for number, unit in parts:
        if not unit:
            unit = _NEXT_UNIT.get(prev_unit, 's')
        seconds += int(number) * _TIME_UNITS[unit]
        prev_unit = unit
    return seconds


def time_from_now(text):
    """The datetime a builder-time reading like '4H2M' finishes, or None."""
    seconds = time_to_seconds(text)
    if seconds is None:
        return None
    return datetime.now() + timedelta(seconds=seconds)


def friendly_time_from_now(text):
    """When a builder-time reading finishes, e.g. '19:44', '00:51 tomorrow'
    or '07:42 on Oct 18'. Accepts the reading ('4H2M') or a datetime.
    Returns None if the reading can't be parsed."""
    when = text if isinstance(text, datetime) else time_from_now(text)
    if when is None:
        return None
    days = (when.date() - datetime.now().date()).days
    clock = when.strftime('%H:%M')
    if days == 0:
        return clock
    if days == 1:
        return f"{clock} tomorrow"
    return f"{clock} on {when.strftime('%b')} {when.day}"
