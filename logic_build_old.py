

DIGIT_DIR = os.path.join(BASE_DIR, 'images', 'read', 'builder_time')
BUILDER_COUNT_DIR = os.path.join(BASE_DIR, 'images', 'read', 'builder_count')
_digit_templates = None
_letter_templates = None
_builder_count_templates = None

def _load_templates():
    global _digit_templates
    if _digit_templates is None:
        _digit_templates = {}
        for d in range(10):
            t = cv2.imread(os.path.join(DIGIT_DIR, f'{d}.jpg'))
            if t is not None:
                _digit_templates[d] = t
    return _digit_templates

def _load_letter_templates():
    global _letter_templates
    if _letter_templates is None:
        _letter_templates = {}
        for c in ['h', 'm', 's']:
            t = cv2.imread(os.path.join(DIGIT_DIR, f'{c}.jpg'))
            if t is not None:
                _letter_templates[c] = t
    return _letter_templates

def _to_seconds(numbers, groups):
    if len(numbers) == 3:
        return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]
    if len(numbers) == 2:
        if len(groups[0]) == 1 and numbers[0] <= 23:
            return numbers[0] * 3600 + numbers[1] * 60
        return numbers[0] * 60 + numbers[1]
    if len(numbers) == 1:
        return numbers[0] * 60
    return None


def _bright_segments(mask, min_gap=3):
    segs, start, gap = [], None, 0
    for i, v in enumerate(mask):
        if v:
            if start is None:
                start = i
            gap = 0
        elif start is not None:
            gap += 1
            if gap >= min_gap:
                segs.append((start, i - gap + 1))
                start, gap = None, 0
    if start is not None:
        segs.append((start, len(mask)))
    return segs


def next_completion_time(image):
    templates = _load_templates()
    letter_templates = _load_letter_templates()
    if not templates:
        return None

    max_h = max(t.shape[0] for t in templates.values())
    max_w = max(t.shape[1] for t in templates.values())

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    timer_regions = []
    for r0, r1 in _bright_segments(gray.max(axis=1) > 150):
        col_blocks = _bright_segments(gray[r0:r1, :].max(axis=0) > 150)
        for c0, c1 in col_blocks:
            timer_regions.append((r0, r1, c0, c1))

    if not timer_regions:
        return None

    def in_timer(y, x):
        return any(r0 - max_h <= y <= r1 and c0 <= x <= c1 for r0, r1, c0, c1 in timer_regions)

    cell_w = max_w
    digit_cells = {}
    for digit, tmpl in templates.items():
        result = cv2.matchTemplate(image, tmpl, cv2.TM_CCOEFF_NORMED)
        ys, xs = np.where(result >= 0.78)
        for y, x in zip(ys.tolist(), xs.tolist()):
            if not in_timer(y, x):
                continue
            conf = float(result[y, x])
            cell = (x // cell_w, y // max_h)
            if cell not in digit_cells or conf > digit_cells[cell][3]:
                digit_cells[cell] = (int(y), int(x), digit, conf)

    if not digit_cells:
        return None

    letter_cells = {}
    for letter, tmpl in letter_templates.items():
        lw = tmpl.shape[1]
        lcell_w = lw + 2
        result = cv2.matchTemplate(image, tmpl, cv2.TM_CCOEFF_NORMED)
        ys, xs = np.where(result >= 0.75)
        for y, x in zip(ys.tolist(), xs.tolist()):
            if not in_timer(y, x):
                continue
            conf = float(result[y, x])
            cell = (x // lcell_w, y // max_h)
            if cell not in letter_cells or conf > letter_cells[cell][3]:
                letter_cells[cell] = (int(y), int(x), letter, conf)

    cv2.imwrite(os.path.join(BASE_DIR, f'images/numbers/testing/{int(monotonic()*1000)}.jpg'), image)

    def region_for(y, x):
        for r0, r1, c0, c1 in timer_regions:
            if r0 - max_h <= y <= r1 and c0 <= x <= c1:
                return (r0, r1)
        return None

    rows = {}
    for y, x, digit, _ in digit_cells.values():
        key = region_for(y, x)
        if key:
            rows.setdefault(key, {'digits': [], 'letters': []})['digits'].append((x, digit))
    for y, x, letter, _ in letter_cells.values():
        key = region_for(y, x)
        if key:
            rows.setdefault(key, {'digits': [], 'letters': []})['letters'].append((x, letter))

    unit = {'h': 3600, 'm': 60, 's': 1}
    times = []

    for key in sorted(rows):
        row = rows[key]
        digits = sorted(row['digits'])
        letters = sorted(row['letters'])

        if not digits:
            continue

        groups = [[digits[0]]]
        for i in range(1, len(digits)):
            if digits[i][0] - digits[i - 1][0] <= max_w + 4:
                groups[-1].append(digits[i])
            else:
                groups.append([digits[i]])

        unit_max = {'h': 99, 'm': 59, 's': 59}
        if letters:
            total = 0
            for g in groups:
                group_end_x = g[-1][0] + max_w
                rights = [(x, l) for x, l in letters if x >= group_end_x - 2]
                if not rights:
                    continue
                _, letter = min(rights, key=lambda p: p[0])
                digits_str = ''.join(str(d) for _, d in g)
                while len(digits_str) > 1 and int(digits_str) > unit_max.get(letter, 999):
                    digits_str = digits_str[1:]
                number = int(digits_str)
                total += number * unit[letter]
            if total > 0:
                times.append(total)
        else:
            numbers = [int(''.join(str(d) for _, d in g)) for g in groups]
            total = _to_seconds(numbers, groups)
            if total:
                times.append(total)

    return min(times) if times else None

def _load_builder_count_templates():
    global _builder_count_templates
    if _builder_count_templates is None:
        _builder_count_templates = {}
        for d in [0, 1, 2]:
            t = cv2.imread(os.path.join(BUILDER_COUNT_DIR, f'{d}.jpg'))
            if t is not None:
                _builder_count_templates[d] = t
    return _builder_count_templates

def free_builders(image):
    templates = _load_builder_count_templates()
    if not templates:
        return None

    max_h = max(t.shape[0] for t in templates.values())
    max_w = max(t.shape[1] for t in templates.values())
    cell_w = max_w + 2

    cells = {}
    for digit, tmpl in templates.items():
        result = cv2.matchTemplate(image, tmpl, cv2.TM_CCOEFF_NORMED)
        ys, xs = np.where(result >= 0.78)
        for y, x in zip(ys.tolist(), xs.tolist()):
            conf = float(result[y, x])
            cell = (x // cell_w, y // max_h)
            if cell not in cells or conf > cells[cell][3]:
                cells[cell] = (int(y), int(x), digit, conf)

    if not cells:
        return None

    leftmost = min(cells.values(), key=lambda v: v[1])
    return leftmost[2]

def get_builder_count():
    position = builder.find()
    if not position:
        print("Position not found")
        return None
    position = offset(position,0, -15)
    image = screenshot_region(position, 80, 40)
    # show(image, dur=2000)
    return free_builders(image)

def get_time_image():
    if not suggested_upgrades.find():
        builder.click()
        sleep(0.5)
    if not suggested_upgrades.find():
        return
    sleep(0.5)
    position = upgrades_in_progress.find()
    if not position:
        return None
    position = offset(position, 70, 15)
    image = screenshot_region(position, 90, 30)
    show(image, dur=2000)
    time = next_completion_time(image)
    cv2.imwrite(f'images/times/{ time }.jpg', image)
    return time

def build_panel_move(direction="up"):
    if direction == "up":
        a = (670, 425)
        b = (670, 145)
    else:
        b = (670, 425)
        a = (670, 145)
    drag(a, b)

def build(task):
    # Goblin builder face means the game has swapped builders out for an
    # event — don't build while it's showing, just check back later.
    if builder_goblin.find():
        print(f"{task.account.name}: goblin builder showing - skipping build for 1 hour")
        task.pause(60)
        return

    if get_builder_count() == 0:
        print("No builders")
        return

    go(builder_panel)
    region = (400, 100, 340, 370)
    print("Finding suggested upgrades")
    anchor_x, anchor_y = anchor.find()
    a_raw = suggested_upgrades.find(region=region, confidence=0.75)
    a = a_raw[0] - anchor_x, a_raw[1] - anchor_y
    b = (489, 87)
    print("Suggested upgrades:", a)
    if not a:
        print("Couldn't find suggested upgrades")
        return
    drag(a, b)
    sleep(0.5)
    result, count = None, 0
    while not result and count < 3:
        result = find_item_on_build_panel(build_list)
        print("Result:", result)
        if not result and count < 2:
            build_panel_move()
        elif result:
            position, item = result
            pyautogui.click(position)
            sleep(0.1)
            upgrade.click()
            sleep(0.1)
            confirm.click()
            sleep(0.3)
            if you_need_more.find():
                you_need_more_cross_1.click()
                sleep(0.1)
                you_need_more_cross_2.click()
                print(f"{task.account.name}: insufficient {item.resource_type} - pausing build for 1 hour")
                task.pause(60)
                break
        count += 1
    go(home)
    # get_build_time(task)

def y_diff(image_a, image_b):
    a_result = image_a.find()
    b_result = image_b.find()
    print("y_diff:", a_result, b_result)
    if a_result and b_result:
        y_gap = b_result[1] - a_result[1]
        return y_gap

def get_build_time(task):
    go(builder_panel)
    sleep(1)
    time_str = builder_time(save=True)
    time_sec = parse_time(time_str)
    try:
        time_min = int(time_sec / 60) + 1
    except:
        time_min = 20
    if get_builder_count() > 0: time_min = 1

    time_min = min(time_min, 120)
    print("Get build time:", time_min)
    return time_min


BUILD_DIR = os.path.join(BASE_DIR, 'images', 'build')
RESOURCE_TYPES = ('gold', 'elixir', 'dark_elixir')

_all_builds = []

class Build:
    def __init__(self, name):
        self.name = name
        self.image = None
        self.resource_type = None
        for resource_type in RESOURCE_TYPES:
            path = os.path.join('images', 'build', resource_type, f'{name}.jpg')
            if os.path.exists(os.path.join(BASE_DIR, path)):
                self.image = Image(path, name=name)
                self.resource_type = resource_type
                break
        if self.image is None:
            print(f"Build: no image found for '{name}' in {RESOURCE_TYPES}")
        _all_builds.append(self)

    def show(self, dur=500):
        if self.image is None:
            print(f"Build: no image to show for '{self.name}'")
            return
        self.image.show(dur)

def find_item_on_build_panel(build_list):
    for item in build_list:
        position = item.image.find()
        if position:
            return position, item
    return None
def load_builds():
    builds = []
    for resource_type in RESOURCE_TYPES:
        dir_path = os.path.join(BASE_DIR, 'images', 'build', resource_type)
        if not os.path.isdir(dir_path):
            continue
        for filename in sorted(os.listdir(dir_path)):
            if not filename.lower().endswith('.jpg'):
                continue
            builds.append(Build(os.path.splitext(filename)[0]))
    return builds

build_list = load_builds()

