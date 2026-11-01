# import cv2
# from contextlib import contextmanager
# from build import *
# from account import *
# from logic_account import *
# from nav import *
# mouse_tracker()
# from utilities import
from build_strings import *
from warning import *

def tidy():
    for account in Accounts:
        account.switch()
        go(home)
        zoom(-20)
        time.sleep(0.5)
        remove_trees()

        go(home_1)
        zoom(-20)
        time.sleep(0.5)
        remove_trees()

        a, b = (214, 134), (715, 550)
        drag(a, b, 2)
        time.sleep(0.5)
        remove_trees()
        drag(b, a, 2)

        go(home)

def remove_trees():
    for tree in trees:
        count = 0
        while tree.find() and count < 3:
            tree.click()
            time.sleep(0.5)
            if remove.find():
                remove.click()
                count_2 = 0
                time.sleep(1)
                while cancel.find() and count_2 < 5:
                    count_2 += 1
                    time.sleep(10)
            count += 1


def read_time_2(base_no):
    if base_no == 0:
        base = home
        panel_1 = build_panel
        panel_2 = lab_panel
    else:
        base = home_1
        panel_1 = build_panel_1
        panel_2 = lab_panel_1

    build_time, research_time = can_build_2(base)
    if not build_time:
        go(panel_1)
        time.sleep(0.2)
        build_time = Read("builder_time", anchor=anchor, region=(1100, 77, 60, 25), confidence=0.75, fixed_region=True, black_and_white=True)()
    if not research_time:
        go(panel_2)
        time.sleep(0.2)
        research_time = Read("builder_time", anchor=anchor, region=(1100, 77, 60, 25), confidence=0.75, fixed_region=True, black_and_white=True)()
    go(base)
    return build_time, research_time

def can_build_2(base):
    go(base)
    count_string = Read("builder_count", anchor=anchor, region=(1065, 544, 100, 42), confidence=0.85, fixed_region=True)()
    icon_string = Read("builder_icon", anchor=anchor, region=(1065, 544, 100, 42), confidence=0.92, fixed_region=True)()
    # print("Can build 2:", count_string, icon_string)
    if not count_string or not icon_string: return False, False
    can_build, can_research = False, False
    if count_string[0] != "0" and icon_string[0] != "g": can_build = "Ready"
    if count_string[2] == 1 and count_string[3] == 1: can_research = "Ready"
    return can_build, can_research

def status_cycle(collect_resources=True):
    for account in Accounts:
        account.switch()
        for base_no in [0, 1]:
            build_time, research_time = read_time_2(base_no)
            account.next_build_time[base_no] = time_from_now(build_time)
            account.next_research_time[base_no] = time_from_now(research_time)

            if base_no == 0:
                can_build, count = can_build_2(home)[0], 0
                while can_build and count < 5:
                    account.build()
                    can_build = can_build_2(home)[0]
                    count += 1

            account.read_resources(base_no)

            if base_no == 0:
                if attacks_needed.find():
                    Warning(f"Attacks needed: {account}")

            if collect_resources:
                get_resources(base_no)
        account.status()
    get_war_status()

def click_if_seen(image):
    position = image.find()
    if position:
        image.click(position=position)
    return position

def get_resources(base):
    if base == 0:
        go(home)
        zoom(-20)
        for x in [gold_icon, elixir_icon, dark_elixir_icon]:
            click_if_seen(x)
        move(-100, 150)
        time.sleep(0.7)
        if capital_gold.find():
            for x in [capital_gold, capital_gold_collect, capital_gold_close]:
                x.click()
                time.sleep(0.15)

    if base == 1:
        go(home_1)
        zoom(-20)
        for x in [builder_gold_icon, builder_gem]:
            click_if_seen(x)
        if click_if_seen(builder_clock):
            for x in [builder_clock_boost, builder_clock_boost_2]:
                x.click()
                time.sleep(0.3)

def get_war_status():
    go(chat)
    status = "At war"
    if no_war.find():
        status = "Not at war"
    warnings[0].text = status
    go(home)

def main_loop():
    get_current_account(force=True)
    status_cycle(collect_resources=False)
    tidied = False
    while True:
        print()
        account, base = status_by_next_build()
        if account:
            print(f"Next: {account} base: {base}")

        # Get additional resources
        if account:
            if base == 1:
                account.attack()
            if base == 2:
                account.attack_builder_5()
                account.attack_builder_5()

        sinner.donate()
        if not account:
            if not tidied:
                tidy()
                tidied = True
            else:
                wait(30)
        status_cycle()


heroes = ["king", "queen", "minion", "warden", "champ", "duke"]
# heroes = ['duke']
# ragnar.walls = True
sinner.walls = True

for x in [ragnar, daz]:
    x.set_build_list(heroes)

main_loop()
# status_cycle(collect_resources=False)
