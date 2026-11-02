from image import *

def get_time():
    clash_icon.click()
    time.sleep(0.3)
    get_image((1100, 77), (1159, 102), "4")
    time.sleep(1)
    extract_time("4")

def get_gold(number, filename):
    clash_icon.click()
    time.sleep(0.3)
    y = 40 * number
    get_image((1000, y), (1140, y + 26), filename)
    time.sleep(2)
    extract_time(filename)

def create_number(filename, x):
    # 12, 35, 55, 82
    y = 4
    x_d, y_d = 10, 16
    source = filename + "_white.png"
    image = extract_image(source, (x, y), (x + x_d, y + y_d), filename + "b")
    if image is not None:
        # Nearest-neighbour keeps the pixels crisp so the crop edges are easy to judge.
        zoom = 20
        cv2.imshow("create_number", cv2.resize(image, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_NEAREST))
        cv2.waitKey(6000)
        cv2.destroyAllWindows()

# filename = "5"
# get_gold(3, filename)
# create_number(filename, 112)
