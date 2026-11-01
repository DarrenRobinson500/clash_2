from nav import *

def build_panel_up():
    a = (1000, 600)
    b = (1000, 250)
    drag(a, b, dur=2.5)
    time.sleep(0.5)

def build_panel_up_half():
    a = (1000, 500)
    b = (1000, 400)
    drag(a, b, dur=1)
    time.sleep(0.5)

def build_panel_dowb():
    a = (1000, 600)
    b = (1000, 100)
    for x in range(4):
        drag(a, b, dur=0.5)

def click_building(building_name, base):
    if building_name in ["wall_g", "wall_e"]: building_name = "wall"
    image = get_building(building_name)
    if base == 1: go(build_panel)
    elif base == 2: go(build_panel_2)
    else: return
    found, count = image.find(), 0
    build_panel_up_half()
    while not found and count < 4:
        build_panel_up()
        found = image.find()
        count += 1
    if found:
        image.click()
        return True

def confirm(building_name):
    # print("Confirm:", building_name)
    if building_name == "wall_g":
        time.sleep(2)
        result = upgrade.find_all()
        if result:
            result = result[0]
            pyautogui.click(result[0] + 10, result[1] + 10)
        else:
            print("Couldn't find upgrade")
            return
    if building_name == "wall_e":
        time.sleep(2)
        result = upgrade.find_all()
        if result:
            result = result[-1]
            pyautogui.click(result[0] + 10, result[1] + 10)
        else: return

    building_confirm.click()
    time.sleep(0.3)

