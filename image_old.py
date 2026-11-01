from logic_image import *

# Pycharm
pycharm_tools = Image('images/nav/global/pycharm_tools.jpg')
# icon_toolbar = Image(['images/nav/icon_toolbar.jpg', 'images/nav/icon_toolbar_2.jpg'])
anchor = Image('images/global/anchor.jpg')
clash_icon = Image('images/global/clash_icon.jpg')

# Home
builder = Image(['images/nav/builder.jpg', 'images/nav/builder_goblin.jpg'], glide_towards=True)
builder_goblin = Image('images/nav/builder_goblin.jpg')
settings_button = Image('images/nav/settings_button.jpg')
switch_accounts_button = Image('images/nav/switch_accounts_button.jpg')
upgrades_in_progress = Image('images/nav/upgrades_in_progress.jpg')
suggested_upgrades = Image(['images/nav/suggested_upgrades.jpg', 'images/nav/suggested_upgrades_2.jpg', 'images/nav/suggested_upgrades_3.jpg'])
other_upgrades = Image(['images/nav/other_upgrades.jpg', 'images/nav/other_upgrades_2.jpg', 'images/nav/other_upgrades_3.jpg', 'images/nav/other_upgrades_4.jpg'])
chat = Image('images/nav/home/chat.jpg', glide_towards=True)
chat_close = Image('images/nav/home/chat_close.jpg', glide_towards=True)
challenge_button = Image('images/nav/home/challenge_button.jpg')

# Build
you_need_more = Image('images/build/you_need_more.jpg')
you_need_more_cross_1 = Image('images/build/you_need_more_cross_1.jpg')
you_need_more_cross_2 = Image('images/build/you_need_more_cross_2.jpg')

# Request and Donate
request_castle = Image('images/nav/home/request_castle.jpg')
request_send = Image('images/nav/home/request_send.jpg')
donate = Image('images/nav/home/donate.jpg')
chat_groups = Image('images/nav/home/chat_groups.jpg')
chat_groups_exit = Image('images/nav/home/chat_groups_exit.jpg')
donation_resource = Image('images/nav/home/donation_resource.jpg')

# Accounts
id_sinner = Image('images/accounts/id_sinner.jpg')
id_daz = Image('images/accounts/id_daz.jpg')
id_ragnar = Image(['images/accounts/id_ragnar.jpg', 'images/accounts/id_ragnar_2.jpg'])

switch_sinner = Image('images/accounts/switch_sinner.jpg')
switch_daz = Image('images/accounts/switch_daz.jpg')
switch_ragnar = Image('images/accounts/switch_ragnar.jpg')

settings_image = Image('images/nav/settings.jpg')
switch_accounts_image = Image('images/nav/switch_accounts.jpg')
close_settings = Image('images/nav/change_account/close_settings.jpg')

# Builder Base
boat = Image(['images/nav/builder/boat.jpg', 'images/nav/builder/boat_2.jpg', 'images/nav/builder/boat_3.jpg'], scalable=True)
boat_back = Image('images/nav/builder/boat_back.jpg', scalable=True)
master_builder = Image('images/nav/builder/master_builder.jpg', glide_towards=True)
builder_attack_button = Image(['images/nav/builder/builder_attack_button.jpg', 'images/nav/builder/builder_attack_button_2.jpg'])
builder_find_now_button = Image('images/nav/builder/builder_find_now_button.jpg')
builder_attacker_image = Image('images/nav/builder/builder_attacker.jpg')

# Build
upgrade = Image('images/build/upgrade.jpg')
confirm = Image('images/build/confirm.jpg')

# Attack
army_button = Image('images/nav/attack/army_button.jpg')
battle_button = Image('images/nav/attack/battle_button.jpg')
find_a_match_button = Image('images/nav/attack/find_a_match_button.jpg')
attack_button = Image('images/nav/attack/attack_button.jpg')
next_button = Image('images/nav/attack/next_button.jpg')
end_battle = Image('images/nav/attack/end_battle.jpg')
end_battle_okay = Image('images/nav/attack/end_battle_okay.jpg')
return_home_button = Image(['images/nav/attack/return_home_button.jpg', 'images/nav/box/box claim reward.jpg'])
close_army = Image('images/nav/attack/close_army.jpg')

# Attack Builder
two_stars = Image(['images/attack_builder/two_stars.jpg', 'images/attack_builder/two_stars_2.jpg'])
surrender = Image('images/attack_builder/surrender.jpg')
end_battle_builder = Image('images/attack_builder/end_battle.jpg')
end_battle_builder_okay = Image('images/attack_builder/end_battle_okay.jpg')
return_home_button_builder = Image(['images/attack_builder/return_home_builder.jpg', 'images/attack_builder/return_home_builder_2.jpg'])
machine_not_activated = Image('images/troops_builder/activation/machine not activated.jpg')
machine_activated = Image('images/troops_builder/activation/machine activated.jpg')
chopper_not_activated = Image('images/troops_builder/activation/chopper not activated.jpg')
chopper_activated = Image('images/troops_builder/activation/chopper activated.jpg')
builder_choose_army_button = Image('images/nav/builder/builder_choose_army_button.jpg')
choose_army = Image('images/nav/builder/choose_army.jpg')
choose_army_cross = Image('images/nav/builder/choose_army_cross.jpg')
remove_troop_button = Image(['images/nav/builder/remove_troop_button.jpg', 'images/nav/builder/remove_troop_button_2.jpg'])
battle_begins_in = Image(['images/attack_builder/battle_begins_in.jpg'])
builder_return_home = Image('images/attack_builder/builder_return_home.jpg')
builder_star_bonus_okay = Image('images/attack_builder/builder_star_bonus_okay.jpg')
speed_up = Image('imaages/attack_builder/speed_up.jpg')

SPOTS_DIR = os.path.join(BASE_DIR, 'images', 'attack_builder', 'spots')
def load_spots():
    rel = os.path.relpath(SPOTS_DIR, BASE_DIR)
    return [Image(os.path.join(rel, fname), scalable=True) for fname in sorted(os.listdir(SPOTS_DIR))]

builder_attack_spots = load_spots()


# Resouorces
gold_icon = Image('images/resources/gold.jpg', scalable=True)
elixir_icon = Image('images/resources/elixir.jpg', scalable=True)
dark_elixir_icon = Image('images/resources/dark_elixir.jpg', scalable=True)

builder_gold_icon = Image('images/resources/builder_gold.jpg', scalable=True)
builder_elixir_icon = Image('images/resources/builder_elixir.jpg', scalable=True)
builder_gem = Image('images/resources/builder_gem.jpg', scalable=True)
builder_clock = Image('images/resources/builder_clock.jpg', scalable=True)
builder_clock_boost = Image('images/resources/builder_clock_boost.jpg', scalable=True)
builder_clock_boost_2 = Image('images/resources/builder_clock_boost_2.jpg', scalable=True)

directory = os.path.join(BASE_DIR, 'images', 'resources', 'elixir_cart')
rel_dir = os.path.relpath(directory, BASE_DIR)
elixir_cart = Image([os.path.join(rel_dir, f) for f in sorted(os.listdir(directory))], scalable=True)
elixir_cart_collect = Image('images/resources/elixir_cart_collect.jpg')
elixir_cart_cross = Image('images/resources/elixir_cart_cross.jpg')

directory = os.path.join(BASE_DIR, 'images', 'attack', 'resources')
rel_dir = os.path.relpath(directory, BASE_DIR)
attack_resource = Image([os.path.join(rel_dir, f) for f in sorted(os.listdir(directory))], count=True)

# Box
directory = os.path.join(BASE_DIR, 'images', 'nav_old', 'box')
box = Image([os.path.join('images', 'nav', 'box', f) for f in sorted(os.listdir(directory))])
auto_images.append(box)

# Challenge
challenge_caravan = Image(['images/nav/challenge/challenge_caravan.jpg', 'images/nav/challenge/challenge_caravan_2.jpg'], scalable=True)
challenge_tab = Image('images/nav/challenge/challenges_tab.jpg')
challenge_cross = Image('images/nav/challenge/challenge_cross.jpg')
challenge_start = Image('images/nav/challenge/start.jpg')

