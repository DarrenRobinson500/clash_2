from logic_nav import *
from image import *

def go_builder_base():
    for x in range(3):
        move(-300, 300)
        if boat.find():
            boat.click()
            break


def go_to_main():
    for x in range(3):
        move(300, -300)
        if boat_back.find():
            boat_back.click()
            break

def go_to_challenge():
    moves = [(0, -300), (0, -300), (300, 0), (-300, 0), (-300, 0)]
    for move_ind in moves:
        move(move_ind[0], move_ind[1])
        if challenge_caravan.find():
            challenge_caravan.click()
            break


# ---- Locations ----
# Pycharm — scanned last, so a game loc always wins when both are visible
# (it used to tie with Builder Base at order=5 and win by definition order,
# leaving go() stuck toggling the game window from the taskbar).
pycharm = Loc(pycharm_tools, order=6)

# Home
home = Loc(builder, name='home', order=4)
builder_panel = Loc([builder, suggested_upgrades], name='builder_panel', order=3)
chat_loc = Loc(challenge_button, name="Chat", order=1)
chat_groups_loc = Loc(chat_groups, order=1)
chat_donations = Loc(donation_resource, order=1)
challenge_loc = Loc(challenge_tab, order=3)

# Change account
settings = Loc(settings_image, name='settings', order=3)
switch_accounts = Loc(switch_accounts_image, order=2)

# Attack
army = Loc(attack_button, order=2)
army_battle = Loc(battle_button, order=2)
# Recognised by Next *or* End Battle: End Battle usually appears a moment
# before Next slides in. end_battle used to be an Auto instead, which meant
# go() clicked it mid-transition while waiting for this screen and bailed out
# of the attack.
attack_selecting_opponent_image = Image(['images/nav/attack/next_button.jpg',
                                         'images/nav/attack/end_battle.jpg',
                                         'images/nav/attack/end_battle_2.jpg'])
attack_selecting_opponent = Loc(attack_selecting_opponent_image, order=3)
return_home = Loc(return_home_button, order=4)
find_a_match = Loc(find_a_match_button, order=1)

# Builder Base
builder_base = Loc(master_builder, name="Builder Base", order=5)
builder_base_panel = Loc([master_builder, suggested_upgrades], name='Builder base panel', order=3)
builder_find_now = Loc(builder_find_now_button, name="Builder find now", order=2)
builder_attack = Loc(builder_attacker_image, name="Builder Attack", order=2)
builder_choose_army = Loc(choose_army, order=1)


# ---- Actions: loc.add_action(action, destination) ----
# Refocusing the game lands on whatever screen it was last left on.
pycharm.add_action(icon_toolbar.click, None)

home.add_action(builder.click, builder_panel)
home.add_action(settings_button.click, settings)
home.add_action(army_button.click, army_battle)
home.add_action(go_builder_base, builder_base)
home.add_action(chat.click, chat_loc)
home.add_action(go_to_challenge, challenge_loc)

builder_panel.add_action(builder.click, home)
builder_panel.add_action(settings_button.click, settings)
builder_panel.add_action(army_button.click, army_battle)

chat_loc.add_action(chat_close.click, home)
chat_loc.add_action(settings_button.click, settings)

chat_groups_loc.add_action(chat_groups_exit.click, chat_loc)
chat_groups_loc.add_action(settings_button.click, settings)

chat_donations.add_action(donate.click, chat_loc)

challenge_loc.add_action(challenge_cross.click, home)

settings.add_action(switch_accounts_button.click, switch_accounts)
# Returns to whichever base settings was opened from.
settings.add_action(close_settings.click, [home, builder_base])

switch_accounts.add_action(settings_image.click, settings)

army.add_action(close_army.click, home)
# Starts an attack search (costs gold) — only take it when attacking is the point.
army.add_action(attack_button.click, attack_selecting_opponent, waypoint=False)

army_battle.add_action(battle_button.click, find_a_match)
army_battle.add_action(close_army.click, home)

attack_selecting_opponent.add_action(end_battle.click, home)

return_home.add_action(return_home_button.click, home)

find_a_match.add_action(find_a_match_button.click, army)

builder_base.add_action(master_builder.click, builder_base_panel)
builder_base.add_action(builder_attack_button.click, builder_find_now)
builder_base.add_action(go_to_main, home)
builder_base.add_action(settings_button.click, settings)
builder_base.add_action(builder_choose_army_button.click, builder_choose_army)

builder_base_panel.add_action(master_builder.click, builder_base)
builder_base_panel.add_action(settings_button.click, settings)

builder_find_now.add_action(press_esc, builder_base)
# Starts a builder attack — only take it when attacking is the point.
builder_find_now.add_action(builder_find_now_button.click, builder_attack, waypoint=False)

builder_attack.add_action(lambda: end_battle_builder.click() or surrender.click() or return_home_button_builder.click(),
                          builder_base, name="exit_builder_attack")

builder_choose_army.add_action(choose_army_cross.click, builder_base)
