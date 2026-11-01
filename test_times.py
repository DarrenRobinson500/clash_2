import sys
sys.path.insert(0, r'C:\Users\darre\PycharmProjects\clash')
import cv2
import os
from logic_build import next_completion_time

TESTING_DIR = r'C:\Users\darre\PycharmProjects\clash\images\numbers\testing'

images = sorted(os.listdir(TESTING_DIR))
for fname in images:
    if not fname.endswith('.jpg'):
        continue
    path = os.path.join(TESTING_DIR, fname)
    img = cv2.imread(path)
    if img is None:
        print(f'{fname}: could not load')
        continue
    print(f'\n=== {fname} ===')
    result = next_completion_time(img)
    h = result // 3600 if result else 0
    m = (result % 3600) // 60 if result else 0
    s = result % 60 if result else 0
    if result:
        print(f'=> {h}h {m}m {s}s  ({result}s total)')
    else:
        print('=> None')
