from logic_challenge import *
from troop import *

builder_building = Challenge("builder_building", run=lambda account: account.attack_builder())
builder_archer_tower = Challenge("builder_archer_tower", run=lambda account: account.attack_builder())
builder_fire_cracker = Challenge("builder_fire_cracker", run=lambda account: account.attack_builder())
builder_percent = Challenge("builder_percent", run=lambda account: account.attack_builder())
builder_air_bombs = Challenge("builder_air_bombs", run=lambda account: account.attack_builder())

builder_barbs = Challenge("builder_barbs", run=lambda account: account.attack_builder_troop(barb_b))
builder_cannon = Challenge("builder_cannon", run=lambda account: account.attack_builder_troop(cannon_b))
builder_baby_dragon = Challenge("builder_baby_dragon", run=lambda account: account.attack_builder_troop(baby_dragon_b))
builder_walls = Challenge("builder_walls", run=lambda account: account.attack_builder_troop(bomber_b))
builder_stars = Challenge("builder_stars", run=lambda account: account.attack_builder_troop())

