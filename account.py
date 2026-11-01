from logic_account import *
from logic_building import Destroy
from image import *
from troop import *


ragnar = Account("ragnar", id_ragnar, switch_ragnar)
daz = Account("daz", id_daz, switch_daz)
sinner = Account("sinner", id_sinner, switch_sinner)
# daz.resources_max = [10000000, 4000000, 0]
# sinner.resources_max = [21000000, 14000000, 0]

ragnar.gold_max = [9000000, 4700000]
ragnar.elixir_max = [9000000, 4300000]
ragnar.dark_max = [200000, 0]

daz.gold_max = [10000000, 5100000]
daz.elixir_max = [10000000, 5100000]
daz.dark_max = [200000, 0]

sinner.gold_max = [22500000, 6500000]
sinner.elixir_max = [23000000, 6500000]
sinner.dark_max = [370000, 0]

# ragnar.build_type = 1

