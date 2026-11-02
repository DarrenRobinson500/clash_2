from logic_image import *

# Accounts
id_ragnar = Image('images/accounts/id_ragnar.jpg')
id_daz = Image('images/accounts/id_daz.jpg')
id_sinner = Image('images/accounts/id_sinner.jpg')

switch_sinner = Image('images/accounts/switch_sinner.jpg')
switch_daz = Image('images/accounts/switch_daz.jpg')
switch_ragnar = Image('images/accounts/switch_ragnar.jpg')

home_icon = Image(['images/nav/home/home_icon_10.jpg', 'images/nav/home/home_icon_11.jpg', 'images/nav/home/home_icon_12.jpg', 'images/nav/home/home_icon_16.jpg'])
home_1_icon = Image(['images/nav/home/home_1_icon_9.jpg', 'images/nav/home/home_1_icon_10.jpg'])

# Pycharm
pycharm_tools = Image('images/nav/global/pycharm_tools.jpg')
anchor = Image('images/nav/global/anchor.jpg')
clash_icon = Image(['images/nav/global/clash_icon.jpg', 'images/nav/global/clash_icon_2.jpg'])

# Home
battle = Image('images/nav/home/battle.jpg')

# Attack
find_a_match = Image('images/nav/attack/find_a_match.jpg')
attack_button = Image('images/nav/attack/attack_button.jpg')
attack_2_close = Image('images/nav/attack/attack_2_close.jpg')
attack_next = Image('images/nav/attack/attack_next.jpg')
attack_end_battle = Image('images/nav/attack/end_battle.jpg')
surrender = Image('images/nav/attack/surrender.jpg')
surrender_okay = Image('images/nav/attack/surrender_okay.jpg')
return_home = Image('images/nav/attack/return_home.jpg')
saved_recipe_off = Image('images/nav/attack/saved_recipes_off.jpg')
saved_recipe_on = Image('images/nav/attack/saved_recipes_on.jpg')
army_1 = Image('images/nav/attack/army_1.jpg')
army_okay = Image('images/nav/attack/army_okay.jpg')
use = Image('images/nav/attack/use.jpg')
activate = Image('images/nav/attack/activate.jpg')
boost_elixir = Image('images/nav/attack/boost_elixir.jpg')
attacks_needed = Image(['images/attack/special/two_attacks.jpg', 'images/attack/special/one_attack.jpg'])

# Attack_b
attack_b_find = Image('images/nav/attack_b/attack_b_find.jpg')
attack_b_close = Image('images/nav/attack_b/attack_b_close.jpg')
builder_attacker = Image('images/nav/attack_b/builder_attacker.jpg')
attack_b_end = Image(['images/nav/attack_b/end_battle.jpg', 'images/nav/attack_b/surrender.jpg'])
attack_b_okay = Image('images/nav/attack_b/end_battle_okay.jpg')
attack_b_return_home = Image('images/nav/attack_b/attack_b_return_home.jpg')
two_stars = Image(['images/nav/attack_b/two_stars.jpg', 'images/nav/attack_b/two_stars_2.jpg'])
battle_begins_in = Image(['images/attack_builder/battle_begins_in.jpg'])

# Attack_b elixir cart
directory = os.path.join(BASE_DIR, 'images', 'resources', 'elixir_cart')
rel_dir = os.path.relpath(directory, BASE_DIR)
elixir_cart = Image([os.path.join(rel_dir, f) for f in sorted(os.listdir(directory))], scalable=True)
elixir_cart_collect = Image('images/resources/elixir_cart_collect.jpg')
elixir_cart_cross = Image('images/resources/elixir_cart_cross.jpg')

# Chat
chat_open = Image('images/nav/chat/chat_open.jpg')
chat_close = Image('images/nav/chat/chat_close.jpg')
challenge_button = Image('images/nav/chat/challenge_button.jpg')
donate = Image('images/nav/chat/donate.jpg')
donation_resource = Image('images/nav/chat/donation_resource.jpg')

# Build panel
build_image = Image('images/nav/build_panel/build_image.jpg')
build_panel_close = Image('images/nav/build_panel/build_panel_close.jpg')
buildings_and_heroes = Image('images/nav/build_panel/buildings_and_heroes.jpg')
army_upgrades = Image('images/nav/build_panel/army_upgrades.jpg')
lab_icon = Image(['images/nav/build_panel/lab_icon.jpg', 'images/nav/build_panel/lab_icon_b.jpg'])
lab_icon_1 = Image('images/nav/build_panel/lab_icon_1.jpg')

# Settings
settings_close = Image('images/nav/settings/settings_close.jpg')
switch_button = Image('images/nav/settings/switch_button.jpg')
switch_panel_close = Image('images/nav/settings/switch_panel_close.jpg')

# War
clan_war = Image('images/war/clan_war.jpg')
no_war = Image('images/war/no_war.jpg')

# Builder Base
boat = Image(['images/nav/builder_base/boat.jpg', 'images/nav/builder_base/boat_2.jpg'], scalable=True)
boat_back = Image('images/nav/builder_base/boat_back.jpg', scalable=True)

# Build
buildings = create_image_group("build")

building_confirm = Image([
    'images/build/special/confirm_gold.jpg', 'images/build/special/confirm_elixir.jpg', 'images/build/special/confirm_dark.jpg',
    'images/build/special/confirm_gold_b.jpg',
],
    0.85)

upgrade = Image('images/build/special/upgrade.jpg', scalable=True)

wall_confirm_gold = Image('images/build/special/wall_confirm_gold.jpg')
wall_confirm_elixir = Image('images/build/special/wall_confirm_elixir.jpg')

def get_building(name):
    if name in ["wall_g", "wall_e"]: name = "wall"
    for building in buildings:
        if building.name == name:
            return building
    print(f"get_building: no image named '{name}'")
    return None

# Tidy
trees = create_image_group("trees", scalable=True, confidence=0.75)
remove = Image("images/trees/special/remove.jpg")
cancel = Image("images/trees/special/cancel.jpg", confidence=0.75)

# Resouorces
gold_icon = Image('images/resources/gold.jpg', scalable=True)
elixir_icon = Image('images/resources/elixir.jpg', scalable=True)
dark_elixir_icon = Image('images/resources/dark_elixir.jpg', scalable=True)

capital_gold = Image('images/resources/capital_gold.jpg', scalable=True)
capital_gold_collect = Image('images/resources/capital_gold_collect.jpg')
capital_gold_close = Image('images/resources/capital_gold_close.jpg')


builder_gold_icon = Image('images/resources/builder_gold.jpg', scalable=True)
builder_elixir_icon = Image('images/resources/builder_elixir.jpg', scalable=True)
builder_gem = Image('images/resources/builder_gem.jpg', scalable=True)
builder_clock = Image('images/resources/builder_clock.jpg', scalable=True)
builder_clock_boost = Image('images/resources/builder_clock_boost.jpg', scalable=True)
builder_clock_boost_2 = Image('images/resources/builder_clock_boost_2.jpg', scalable=True)

# Challenge
caravan = Image(["images/nav/challenge/caravan.jpg", "images/nav/challenge/caravan_2.jpg"], scalable=True)
games = Image("images/nav/challenge/games.jpg")
caravan_close = Image("images/nav/challenge/caravan_close.jpg")
challenge_start = Image('images/challenges/challenge_start.jpg')