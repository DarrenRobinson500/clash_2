from logic_task import *
from logic_build import *
from attack import *
from read import *
from account import *

# Task("Ragnar build", ragnar, builder_panel, build, False, time_function=get_build_time)
Task("Ragnar attack builder elixir", ragnar, builder_base, attack_builder_5_elixir, True, default_time=120)

Task("Daz build", daz, builder_panel, build, False, time_function=get_build_time)
Task("Daz attack", daz, home, daz.attack, True, default_time=30)
# Task("Daz attack builder elixir", daz, builder_base, attack_builder_5_elixir, True, default_time=120)

# Task("Sinner build", sinner, builder_panel, build, False, time_function=get_build_time)
Task("Sinner donate", sinner, chat_loc, sinner.donate, True, default_time=10)
Task("Sinner attack", sinner, home, sinner.attack, True, default_time=5)
# Task("Sinner attack builder elixir", sinner, builder_base, attack_builder_5_elixir, True, default_time=120)

run_tasks(status_check=False)
