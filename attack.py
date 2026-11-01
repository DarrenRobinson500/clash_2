from logic_image import *
from nav import *
from logic_building import Building
from troop import *

_building_cache = {}


def find_defence(building_name, image):
    if building_name not in _building_cache:
        _building_cache[building_name] = Building(building_name)
    templates = _building_cache[building_name].images
    if not templates:
        return []

    h_img, w_img = image.shape[:2]
    hits = []
    threshold = 0.65

    for tmpl in templates:
        th, tw = tmpl.shape[:2]
        if th > h_img or tw > w_img:
            continue
        result = cv2.matchTemplate(image, tmpl, cv2.TM_CCOEFF_NORMED)
        locs = np.where(result >= threshold)
        for y, x in zip(*locs):
            hits.append((x + tw // 2, y + th // 2, result[y, x]))

    hits.sort(key=lambda h: -h[2])
    locations = []
    for x, y, _ in hits:
        if all((x - ox) ** 2 + (y - oy) ** 2 > 20 ** 2 for ox, oy in locations):
            locations.append((x, y))
    return locations

# Tuned against images/attack/grass.jpg: uncut grass reads as rougher/more
# mottled than mowed (cut) grass, i.e. higher local edge-density, so a boxed
# Laplacian response distinguishes them better than color alone (rocks/dirt
# are excluded by the green-hue check, but bushes are textured+green too and
# will also count as "uncut" — acceptable since troops can't be placed there
# either way).
_TEXTURE_KERNEL = (9, 9)
_TEXTURE_THRESHOLD = 17
_GREEN_HUE_RANGE = (30, 95)
_GREEN_SAT_MIN = 40


def uncut_grass_mask(image):
    """Boolean mask of uncut grass: the rough-textured border around the
    village edge where troops can be placed during an attack."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    texture = cv2.boxFilter(np.abs(cv2.Laplacian(gray, cv2.CV_64F)), -1, _TEXTURE_KERNEL)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hue, sat = hsv[:, :, 0].astype(int), hsv[:, :, 1].astype(int)
    green = (hue >= _GREEN_HUE_RANGE[0]) & (hue <= _GREEN_HUE_RANGE[1]) & (sat > _GREEN_SAT_MIN)
    return green & (texture >= _TEXTURE_THRESHOLD)


def find_uncut_grass(region):
    x, y, w, h = region
    image = screenshot_region((x, y), w, h)
    return uncut_grass_mask(image)


# Tuned against images/attack/Screenshot *.jpg: the deploy-boundary line
# drawn around a base during an attack is a dark orange — despite looking
# "red" at a glance, it's distinct from both the grass and the saturated
# reds used in UI chrome (e.g. the End Battle button).
_BOUNDARY_HUE_RANGE = (8, 28)
_BOUNDARY_SAT_MIN = 110
_BOUNDARY_VAL_MIN = 90

# How far to step outward from the boundary line when looking for a spot
# (tried in increasing steps until one lands cleanly outside), and how much
# to back off from the image edges — a screenshot's title bar/UI chrome
# isn't grass, so a spot found too close to the edge can land on it instead.
_OUTSIDE_STEP_DISTANCES = (20, 30, 40, 50, 60, 70)
_EDGE_MARGIN = 10
_GREEN_VAL_MIN = 60

# The "Next" button (skip to the next opponent) sits in a fixed spot in the
# bottom-right corner of the game window across screenshots — measured as
# roughly 167px wide, 95-212px tall there, widened a bit for safety margin.
# A deploy tap landing on it would skip the attack instead of placing troops.
_NEXT_BUTTON_EXCLUSION = (225, 275)


def _in_next_button_zone(x, y, w, h):
    return x >= w - _NEXT_BUTTON_EXCLUSION[0] and y >= h - _NEXT_BUTTON_EXCLUSION[1]


# The troop-selection cards (icons + counts, including the empty dashed
# slots for unused army slots) sit in a fixed-width row across the bottom of
# the screen — measured at ~88px tall and roughly x=175 to x=950 across
# several images/attack/Screenshot *.jpg captures, plus a small margin on
# each. Bounded by x as well as height since the row doesn't span the full
# screen width — a height-only band wrongly excludes the (perfectly valid)
# grass to its left and right too, which cost an otherwise-found spot in one
# capture. A deploy tap landing on a card selects/no-ops on it instead of
# placing troops on the battlefield.
_TROOP_BAR_HEIGHT = 100
_TROOP_BAR_X_RANGE = (170, 970)

# End Battle / Boost Army / Boost Heroes buttons sit in the bottom-left strip
# to the left of the troop cards — same height band, x < 170.
_LEFT_BUTTONS_X_MAX = 230
_LEFT_BUTTONS_HEIGHT = 100


def _in_troop_bar_zone(x, y, w, h):
    return y >= h - _TROOP_BAR_HEIGHT and _TROOP_BAR_X_RANGE[0] <= x <= _TROOP_BAR_X_RANGE[1]


def _in_left_buttons_zone(x, y, w, h):
    return y >= h - _LEFT_BUTTONS_HEIGHT and x < _LEFT_BUTTONS_X_MAX


def base_boundary_hull(image):
    """Convex hull of the deploy-boundary line around a base. Interior
    buildings happen to share the line's color too, but since they never
    extend past it, the hull still traces the true outer boundary without
    needing to isolate the line itself from that clutter."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[:, :, 0].astype(int), hsv[:, :, 1].astype(int), hsv[:, :, 2].astype(int)
    boundary_color = (
        (hue >= _BOUNDARY_HUE_RANGE[0]) & (hue <= _BOUNDARY_HUE_RANGE[1])
        & (sat >= _BOUNDARY_SAT_MIN) & (val >= _BOUNDARY_VAL_MIN)
    )
    mask = (boundary_color * 255).astype(np.uint8)
    # Blank out UI zones so their orange pixels don't pollute the hull
    h_img, w_img = image.shape[:2]
    mask[:60, :] = 0         # title bar / battle timer
    mask[h_img - 130:, :] = 0  # troop bar
    mask[:, w_img - 80:] = 0   # Next button
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    cx_img, cy_img = w_img / 2.0, h_img / 2.0
    central = []
    for c in contours:
        if cv2.contourArea(c) < 300:
            continue
        m = cv2.moments(c)
        if m['m00'] == 0:
            continue
        hx, hy = m['m10'] / m['m00'], m['m01'] / m['m00']
        if abs(hx - cx_img) <= w_img * 0.40 and abs(hy - cy_img) <= h_img * 0.40:
            central.append(c)
    if not central:
        return None
    return cv2.convexHull(np.vstack(central))


def _walk_outward_for_spot(image, hull, exclusion_checks):
    """Shared by both village types: given a boundary hull, step outward
    (away from its centroid) from each hull point until one lands cleanly
    outside the hull, on-screen, clear of `exclusion_checks` (UI chrome to
    avoid tapping), and on grass."""
    moments = cv2.moments(hull)
    if moments['m00'] == 0:
        return None
    cx, cy = moments['m10'] / moments['m00'], moments['m01'] / moments['m00']

    h, w = image.shape[:2]
    for distance in _OUTSIDE_STEP_DISTANCES:
        for point in hull[:, 0, :]:
            px, py = float(point[0]), float(point[1])
            dx, dy = px - cx, py - cy
            length = (dx ** 2 + dy ** 2) ** 0.5
            if length < 1:
                continue
            ox = int(px + dx / length * distance)
            oy = int(py + dy / length * distance)
            if not (_EDGE_MARGIN <= ox < w - _EDGE_MARGIN and _EDGE_MARGIN <= oy < h - _EDGE_MARGIN):
                continue
            if any(check(ox, oy, w, h) for check in exclusion_checks):
                continue
            if cv2.pointPolygonTest(hull, (ox, oy), False) >= 0:
                continue
            return ox, oy
    return None


def _hough_deploy_lines(image):
    """Return validated Hough line segments on the outer boundary: diagonal,
    orange-red colour, with green grass on at least one side."""
    h_img, w_img = image.shape[:2]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hue = hsv[:, :, 0].astype(int)
    sat = hsv[:, :, 1].astype(int)
    val = hsv[:, :, 2].astype(int)

    green_mask = (hue >= 30) & (hue <= 90) & (sat >= 35) & (val >= 50)

    red_px = (
        (hue >= 8) & (hue <= 22) & (sat >= 110) & (val >= 90)
    ).astype(np.uint8) * 255
    red_px[:60, :] = 0
    red_px[h_img - 130:, :] = 0
    red_px[h_img - _NEXT_BUTTON_EXCLUSION[1]:, w_img - _NEXT_BUTTON_EXCLUSION[0]:] = 0

    lines = cv2.HoughLinesP(red_px, rho=1, theta=np.pi / 180,
                            threshold=40, minLineLength=50, maxLineGap=25)
    if lines is None:
        return []

    valid = []
    for x1, y1, x2, y2 in lines[:, 0]:
        angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1))) % 180
        if not (30 <= angle <= 60 or 120 <= angle <= 150):
            continue
        dx, dy = x2 - x1, y2 - y1
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length < 1:
            continue
        px, py = -dy / length, dx / length
        steps = max(int(length / 10), 3)
        green_count = total = 0
        for i in range(steps):
            t = i / max(steps - 1, 1)
            cx = int(x1 + t * dx)
            cy = int(y1 + t * dy)
            for d in [8, 12, 16]:
                for sign in (-1, 1):
                    sx = int(cx + px * d * sign)
                    sy = int(cy + py * d * sign)
                    if 0 <= sx < w_img and 0 <= sy < h_img:
                        total += 1
                        if green_mask[sy, sx]:
                            green_count += 1
        if total > 0 and green_count / total >= 0.25:
            valid.append((x1, y1, x2, y2, green_mask, px, py))
    return valid


def find_spots_outside_base(image, count=3):
    """Up to `count` deploy spots just outside the red boundary line,
    spread around the base perimeter."""
    h_img, w_img = image.shape[:2]
    valid_lines = _hough_deploy_lines(image)
    if not valid_lines:
        return []

    # Centroid of all line midpoints → used to determine outward direction
    mids = [((x1 + x2) / 2, (y1 + y2) / 2) for x1, y1, x2, y2, *_ in valid_lines]
    base_cx = sum(m[0] for m in mids) / len(mids)
    base_cy = sum(m[1] for m in mids) / len(mids)

    candidates = []
    for x1, y1, x2, y2, green_mask, px, py in valid_lines:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        # Pick the perpendicular direction that points away from base centre
        if px * (mx - base_cx) + py * (my - base_cy) < 0:
            px, py = -px, -py
        for d in range(12, 45, 4):
            sx = int(mx + px * d)
            sy = int(my + py * d)
            if not (_EDGE_MARGIN <= sx < w_img - _EDGE_MARGIN and
                    _EDGE_MARGIN <= sy < h_img - _EDGE_MARGIN):
                break
            if _in_next_button_zone(sx, sy, w_img, h_img):
                break
            if _in_troop_bar_zone(sx, sy, w_img, h_img):
                break
            if green_mask[sy, sx]:
                candidates.append((sx, sy))
                break

    if not candidates:
        return []

    # Pick `count` spots spread at least 80 px apart from each other
    spots = [candidates[0]]
    for sx, sy in candidates[1:]:
        if len(spots) >= count:
            break
        if all((sx - ox) ** 2 + (sy - oy) ** 2 > 80 ** 2 for ox, oy in spots):
            spots.append((sx, sy))
    return spots


def find_spot_outside_base(image):
    spots = find_spots_outside_base(image, count=1)
    return spots[0] if spots else None


# --- Builder Base ---
# The deploy-boundary line is the same color as the regular village's (the
# hue/sat/val range above), but reads as many more, smaller broken segments
# at this zoom level — decorations occlude more of it, so the single
# largest raw contour is usually a building's rooftop or a troop card, not
# the line. Closing the mask first (dilate then erode) bridges those small
# gaps back into one contour spanning the true perimeter.
#
# This closing is *not* just folded into base_boundary_hull() above: run on
# a regular-village screenshot, the same kernel over-bridges and pulls in
# distant unrelated UI (the loot counter, troop bar, Next button) instead,
# since that boundary line was already close to one contour without it.
# Tuned against the one full example available so far
# (images/attack_builder/2.jpg) — likely needs revisiting once there are
# more real captures to check it against, the same way the regular
# village's detection did.
_BUILDER_BASE_CLOSE_KERNEL = 27


def builder_base_boundary_hull(image):
    """Convex hull of the deploy-boundary line around a Builder Base, after
    closing the color mask to rejoin the segments occlusion breaks it into
    (see module comment above)."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[:, :, 0].astype(int), hsv[:, :, 1].astype(int), hsv[:, :, 2].astype(int)
    boundary_color = (
        (hue >= _BOUNDARY_HUE_RANGE[0]) & (hue <= _BOUNDARY_HUE_RANGE[1])
        & (sat >= _BOUNDARY_SAT_MIN) & (val >= _BOUNDARY_VAL_MIN)
    )
    mask = (boundary_color * 255).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (_BUILDER_BASE_CLOSE_KERNEL, _BUILDER_BASE_CLOSE_KERNEL))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    h_img, w_img = image.shape[:2]
    for c in sorted(contours, key=cv2.contourArea, reverse=True):
        hull = cv2.convexHull(c)
        m = cv2.moments(hull)
        if m['m00'] == 0:
            continue
        hx, hy = m['m10'] / m['m00'], m['m01'] / m['m00']
        if abs(hx - w_img / 2) <= w_img * 0.3 and abs(hy - h_img / 2) <= h_img * 0.3:
            return hull
    return None


# Measured against images/attack_builder/2.jpg only — height and left edge
# are in the same ballpark as the regular village's troop bar, but the
# dashed empty-slot outlines ran all the way to the right edge of the
# screen there rather than stopping around x=970, so there's no right
# bound. No Next-button exclusion: Builder Base has no skip-this-opponent
# button to avoid. Both of those should be re-checked against more captures.
_BUILDER_BASE_TROOP_BAR_HEIGHT = 130
_BUILDER_BASE_TROOP_BAR_X_MIN = 170


def _in_builder_base_troop_bar_zone(x, y, w, h):
    return y >= h - _BUILDER_BASE_TROOP_BAR_HEIGHT and x >= _BUILDER_BASE_TROOP_BAR_X_MIN


def find_spot_outside_builder_base(image):
    """Builder Base equivalent of find_spot_outside_base()."""
    hull = builder_base_boundary_hull(image)
    if hull is None:
        return None
    return _walk_outward_for_spot(image, hull, [_in_builder_base_troop_bar_zone])

def get_attack_time(task):
    if task.account.needs_to_attack():
        return 5
    else:
        return 120

def add_deploy_spot():
    src_dir = os.path.join(BASE_DIR, 'images', 'attack')
    dst_dir = os.path.join(BASE_DIR, 'images', 'attack', 'deploy')
    os.makedirs(dst_dir, exist_ok=True)
    for fname in os.listdir(src_dir):
        if not fname.lower().endswith('.jpg'):
            continue
        image = cv2.imread(os.path.join(src_dir, fname))
        if image is None:
            continue
        for spot in deploy_on_trees(image):
            cv2.circle(image, spot, 8, (0, 255, 255), -1)
        cv2.imwrite(os.path.join(dst_dir, fname), image)


_tree_templates = None


def _load_tree_templates():
    global _tree_templates
    if _tree_templates is not None:
        return _tree_templates
    trees_dir = os.path.join(BASE_DIR, 'images', 'attack', 'trees')
    _tree_templates = []
    for fname in sorted(os.listdir(trees_dir)):
        fpath = os.path.join(trees_dir, fname)
        if not os.path.isfile(fpath) or not fname.lower().endswith('.jpg'):
            continue
        tmpl = cv2.imread(fpath)
        if tmpl is not None:
            _tree_templates.append((fname, tmpl))
    return _tree_templates


def deploy_on_trees(image, count=3):
    """Find up to `count` diverse deploy spots by matching tree templates.
    Returns image-relative (x, y) coordinates."""
    templates = _load_tree_templates()
    if not templates:
        return []

    h_img, w_img = image.shape[:2]
    candidates = []
    threshold = 0.6

    for fname, tmpl in templates:
        th, tw = tmpl.shape[:2]
        if th > h_img or tw > w_img:
            continue
        result = cv2.matchTemplate(image, tmpl, cv2.TM_CCOEFF_NORMED)
        locs = np.where(result >= threshold)
        for y, x in zip(*locs):
            cx = x + tw // 2
            cy = y + th // 2
            if cy < 60:
                continue
            if _in_next_button_zone(cx, cy, w_img, h_img):
                continue
            if _in_troop_bar_zone(cx, cy, w_img, h_img):
                continue
            if _in_left_buttons_zone(cx, cy, w_img, h_img):
                continue
            candidates.append((cx, cy, result[y, x], fname))

    if not candidates:
        return []

    candidates.sort(key=lambda c: -c[2])

    spots = []
    for cx, cy, _, fname in candidates:
        if len(spots) >= count:
            break
        if all((cx - ox) ** 2 + (cy - oy) ** 2 > 80 ** 2 for ox, oy in spots):
            print(f"Tree spot: {fname} at ({cx}, {cy})")
            spots.append((cx, cy))
    return spots


def destroy(building_name, image, origin):
    locations = find_defence(building_name, image)
    anchor_position = anchor.find()
    if anchor_position is None:
        print("destroy: anchor not found, skipping")
        return
    ox, oy = origin
    for ix, iy in locations:
        lightning.click()
        sx, sy = ox + ix - anchor_position[0], oy + iy - anchor_position[1]
        click_at(sx, sy)
        click_at(sx, sy)
        click_at(sx, sy)


def add_building_locations(building_name):
    src_dir = os.path.join(BASE_DIR, 'images', 'attack')
    dst_dir = os.path.join(BASE_DIR, 'images', 'attack', 'building')
    os.makedirs(dst_dir, exist_ok=True)
    for fname in os.listdir(src_dir):
        if not fname.lower().endswith('.jpg'):
            continue
        fpath = os.path.join(src_dir, fname)
        if not os.path.isfile(fpath):
            continue
        image = cv2.imread(fpath)
        if image is None:
            continue
        for x, y in find_defence(building_name, image):
            cv2.circle(image, (x, y), 12, (0, 255, 0), 2)
        cv2.imwrite(os.path.join(dst_dir, fname), image)


def get_attack_screenshots():
    go(attack_selecting_opponent)
    for x in range(5):
        next_button.wait()
        time.sleep(2)
        screenshot_game("images/attack/TH13")
        next_button.click()
    next_button.wait()
    time.sleep(2)
    go(home)

def builder_attack(troop, count, wait):
    go(builder_attack)
    spot_pos = None
    for x in builder_attack_spots:
        pos = x.find()
        if pos: spot_pos = pos
    if not spot_pos:
        print("No spot found")
        go(builder_base)
        return
    anchor_position = anchor.find()
    if anchor_position is None:
        print("builder_attack: anchor not found")
        go(builder_base)
        return
    spot_offset = (spot_pos[0] - anchor_position[0], spot_pos[1] - anchor_position[1])
    chopper_b.click()
    click_at(*spot_offset)
    troop.click()
    for x in range(count):
        click_at(*spot_offset)
        time.sleep(1)
    result = two_stars.wait(duration=wait)
    print("Found two stars:", result)
    go(builder_base)


def attack_builder_5_elixir(task):
    task.account.attack_builder_5(resource='elixir')


# for x in range(3):
#     builder_attack(barb_b, 16, 60)
    # builder_attack(witch_b, 6, 90)
# collect_builder_elixir()

