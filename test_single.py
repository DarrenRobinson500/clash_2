import sys
sys.path.insert(0, r'C:\Users\darre\PycharmProjects\clash')
import cv2
import numpy as np
import os
from logic_build import _bright_segments

TESTING_DIR = r'C:\Users\darre\PycharmProjects\clash\images\numbers\testing'
DIGIT_DIR = r'C:\Users\darre\PycharmProjects\clash\images\numbers\builder_time'

img = cv2.imread(os.path.join(TESTING_DIR, '107519886.jpg'))

import logic_build
builder._digit_templates = None
builder._letter_templates = None

templates = builder._load_templates()
letter_templates = builder._load_letter_templates()

max_h = max(t.shape[0] for t in templates.values())
max_w = max(t.shape[1] for t in templates.values())
print(f'max_h={max_h}, max_w={max_w}, cell_w={max_w}')

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
timer_regions = []
for r0, r1 in _bright_segments(gray.max(axis=1) > 150):
    col_blocks = _bright_segments(gray[r0:r1, :].max(axis=0) > 150)
    for c0, c1 in col_blocks:
        timer_regions.append((r0, r1, c0, c1))
print(f'timer_regions: {timer_regions}')

def in_timer(y, x):
    return any(r0 - max_h <= y <= r1 and c0 <= x <= c1 for r0, r1, c0, c1 in timer_regions)

cell_w = max_w
digit_cells = {}
for digit, tmpl in templates.items():
    result = cv2.matchTemplate(img, tmpl, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(result >= 0.78)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if not in_timer(y, x): continue
        conf = float(result[y, x])
        cell = (x // cell_w, y // max_h)
        if cell not in digit_cells or conf > digit_cells[cell][3]:
            digit_cells[cell] = (int(y), int(x), digit, conf)

print('Digits:', sorted((x, y, d, f'{c:.2f}') for y, x, d, c in digit_cells.values()))

letter_cells = {}
for letter, tmpl in letter_templates.items():
    lw = tmpl.shape[1]
    lcell_w = lw + 2
    result = cv2.matchTemplate(img, tmpl, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(result >= 0.75)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if not in_timer(y, x): continue
        conf = float(result[y, x])
        cell = (x // lcell_w, y // max_h)
        if cell not in letter_cells or conf > letter_cells[cell][3]:
            letter_cells[cell] = (int(y), int(x), letter, conf)

print('Letters:', sorted((x, y, l, f'{c:.2f}') for y, x, l, c in letter_cells.values()))
