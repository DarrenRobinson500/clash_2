import cv2
import os

TESTING_DIR = r'C:\Users\darre\PycharmProjects\clash\images\numbers\testing'
DIGIT_DIR = r'C:\Users\darre\PycharmProjects\clash\images\numbers\builder_time'

def load(fname):
    return cv2.imread(os.path.join(TESTING_DIR, fname))

def save(img, name):
    path = os.path.join(DIGIT_DIR, f'{name}.jpg')
    cv2.imwrite(path, img)
    print(f'  {name}.jpg  shape={img.shape}')

R = slice(7, 22)  # consistent row range for all templates

# 96747015.jpg = "59m 28s" (long-timer, dark background)
# cols: 22-29="5", 30-38="9", 39-50="m", 55-62="2", 64-72="8", 73-80="s"
img = load('96747015.jpg')
print('96747015.jpg (59m 28s):')
save(img[R, 22:30], '5')
save(img[R, 30:39], '9')
save(img[R, 39:51], 'm')
save(img[R, 55:63], '2')
save(img[R, 64:73], '8')
save(img[R, 73:81], 's')

# 96798851.jpg = "58m 36s" (long-timer)
# cols: 56-63="3", 64-72="6"
img = load('96798851.jpg')
print('96798851.jpg (58m 36s):')
save(img[R, 56:64], '3')
save(img[R, 64:73], '6')

# 96425090.jpg = "4m 47s" (short-timer, green bar)
# cols: 26-33="4", 62-69="7"
img = load('96425090.jpg')
print('96425090.jpg (4m 47s):')
save(img[R, 26:34], '4')
save(img[R, 62:70], '7')
