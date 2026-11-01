import cv2
import numpy as np
import os

TESTING_DIR = r'C:\Users\darre\PycharmProjects\clash\images\numbers\testing'

def bright_segs(mask, min_gap=2):
    segs, start, gap = [], None, 0
    for i, v in enumerate(mask):
        if v:
            if start is None: start = i
            gap = 0
        elif start is not None:
            gap += 1
            if gap >= min_gap:
                segs.append((start, i - gap + 1))
                start, gap = None, 0
    if start is not None:
        segs.append((start, len(mask)))
    return segs

for fname in sorted(os.listdir(TESTING_DIR)):
    if not fname.endswith('.jpg'): continue
    img = cv2.imread(os.path.join(TESTING_DIR, fname))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f'\n=== {fname} ({img.shape[1]}x{img.shape[0]}) ===')
    print(f'  Max brightness col profile: {gray.max(axis=0).tolist()}')
    row_segs = bright_segs(gray.max(axis=1) > 150)
    print(f'  Row bright segments (>150): {row_segs}')
    for r0, r1 in row_segs:
        col_segs = bright_segs(gray[r0:r1].max(axis=0) > 150)
        print(f'    Row {r0}-{r1} col segments: {col_segs}')
        for c0, c1 in col_segs:
            crop = img[r0:r1+1, c0:c1+1]
            print(f'      Col {c0}-{c1}: shape {crop.shape}')
