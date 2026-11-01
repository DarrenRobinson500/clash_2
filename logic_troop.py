import os
import cv2
import numpy as np
import pyautogui
from logic_image import Image, BASE_DIR
import time


class Troop:
    def __init__(self, name, icon=None, base="main", donate_icon=None, army_image=None):
        self.name = name
        self.base = base
        troop_dir = 'troops_builder' if base == "builder" else 'troops'
        # Not every troop has had its icon captured yet — leave it None rather
        # than letting Image() print a missing-file ERROR for each one.
        icon_path = f'images/{troop_dir}/{name}.jpg'
        self.icon = icon if icon is not None else (
            Image(icon_path) if os.path.exists(os.path.join(BASE_DIR, icon_path)) else None
        )
        donate_path = f'images/troops/donate/{name}.jpg'
        self.donate_icon = donate_icon if donate_icon is not None else (
            Image(donate_path) if os.path.exists(os.path.join(BASE_DIR, donate_path)) else None
        )
        army_path = f'images/troops/army/{name}.jpg'
        self.army_image = army_image if army_image is not None else (
            Image(army_path) if os.path.exists(os.path.join(BASE_DIR, army_path)) else None
        )
        select_path = f'images/{troop_dir}/select/{name}.jpg'
        self.select_icon = Image(select_path) if os.path.exists(os.path.join(BASE_DIR, select_path)) else None
        self.last_pos = None

    def donate_click(self):
        if not self.donate_icon:
            return False
        donated = False
        while True:
            pos = self.donate_icon.find()
            if not pos:
                break
            x, y = pos
            region = (x - 10, y - 10, 20, 20)
            screenshot = pyautogui.screenshot(region=region)
            hsv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2HSV)
            if hsv[:, :, 1].mean() <= 30:
                break
            self.donate_icon.click(position=pos)
            print(f"Donated {self.name}")
            time.sleep(0.2)
            donated = True
        return donated

    def click(self):
        # Image.click() already only clicks when its template is found on
        # screen (and no-ops with a printed message otherwise), so a Troop's
        # icon being absent just means it can't currently be selected.
        if not self.icon:
            return False
        pos = self.icon.click()
        if pos:
            self.last_pos = pos
        return pos
