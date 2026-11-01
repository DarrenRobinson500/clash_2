import os
import cv2
from logic_image import BASE_DIR


class Building:
    def __init__(self, name):
        self.name = name
        folder = os.path.join(BASE_DIR, 'images', 'buildings', name)
        self.images = []
        for fname in sorted(os.listdir(folder)):
            fpath = os.path.join(folder, fname)
            if not os.path.isfile(fpath):
                continue
            image = cv2.imread(fpath)
            if image is not None:
                self.images.append(image)


class Destroy:
    def __init__(self, building_name):
        self.building_name = building_name


class Activate:
    def __init__(self, icon):
        self.icon = icon
