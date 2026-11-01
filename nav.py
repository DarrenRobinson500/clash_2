import logic_nav
from logic_nav import *
from image import *

def go_builder_base():
    zoom(-20)
    for x in range(3):
        move(-100, 150)
        if capital_gold.find():
            for x in [capital_gold, capital_gold_collect, capital_gold_close]:
                x.click()
                time.sleep(0.15)
        if boat.find():
            boat.click()
            break


def go_to_main():
    zoom(-20)
    for x in range(3):
        move(200, -120)
        time.sleep(0.3)
        if boat_back.find():
            boat_back.click()
            break

def go_to_challenge():
    a, b =  (300, 300), (300, 400)
    drag(a, b)
    if caravan.find():
        caravan.click()
        return
    drag(a, b)
    if caravan.find():
        caravan.click()



# ---- Locations ----
# Pycharm
pycharm = Loc(pycharm_tools, name="Pycharm", order=6)
logic_nav._current_loc = pycharm

# Attack
attack_1 = Loc(find_a_match, order=3)
attack_2 = Loc(attack_button, order=3)
attack_3 = Loc(attack_next, order=3)

# Home
home = Loc(home_icon, name='home', order=4)
chat = Loc(challenge_button, name="Chat", order=3)
build_panel = Loc(buildings_and_heroes, name="build_panel", order=3)
lab_panel = Loc(army_upgrades, name="lab_panel", order=3)
settings = Loc("settings", name="settings", order=3)
switch_panel = Loc('switch_panel', name="settings", order=3)

# Builder base
home_1 = Loc(home_1_icon, name="builder_base", order=4)
build_panel_1 = Loc(buildings_and_heroes, name="build_panel_1", order=3)
lab_panel_1 = Loc(army_upgrades, name="lab_panel_1", order=3)

# Attack (builder)
attack_b_1 = Loc(attack_b_find, order=3)
attack_b_2 = Loc(builder_attacker, order=3)
attack_b_finish_1 = Loc(attack_b_okay, order=3)
attack_b_finish_2 = Loc(attack_b_return_home, order=3)
saved_recipe = Loc(army_1, order=3)

challenges = Loc(games, order=3)

Locs = sort_locs()

# ---- Paths ----
path(pycharm, home, clash_icon.click)

# Home
path(home, chat, chat_open.click, chat_close.click)
path(home, build_panel, build_image.click, build_panel_close.click)
path(build_panel, lab_panel, lab_icon.click)
path(lab_panel, home, build_panel_close.click)
path(build_panel_1, lab_panel_1, lab_icon_1.click)
path(lab_panel_1, home_1, build_panel_close.click)

path(home, settings, lambda: click_at(25, 85), settings_close.click, name="settings_button")
path(settings, switch_panel, switch_button.click, switch_button.click)
path(home, home_1, go_builder_base, go_to_main)
path(home_1, build_panel_1, build_image.click, build_panel_close.click)

# Attack
path(home, attack_1, lambda: click_at(45, 640), lambda: click_at(750, 640))
path(attack_1, attack_2, find_a_match.click)
path(attack_2, home, attack_2_close.click)
path(attack_2, attack_3, attack_button.click)
path(attack_3, home, attack_end_battle.click)
path(attack_2, saved_recipe, saved_recipe_off.click, use.click)
path(saved_recipe, attack_3, attack_button.click)

# Attack_b
path(home_1, attack_b_1, lambda: click_at(45, 640), attack_b_close.click)
path(attack_b_1, attack_b_2, attack_b_find.click)
path(attack_b_2, attack_b_finish_1, attack_b_end.click)
path(attack_b_finish_1, attack_b_finish_2, attack_b_okay.click)
path(attack_b_finish_2, home_1, attack_b_return_home.click)

# Games
path(home, challenges, go_to_challenge, caravan_close)

# go(challenges)
# go(home)


