import os
from utilities import BASE_DIR
from logic_read import Read
from image import anchor

builder_count = Read("builder_count", anchor=anchor, region=(520, 40, 100, 40), confidence=0.92, fixed_region=True)
builder_time = Read("builder_time", anchor=anchor, region=(540, 130, 200, 30), fixed_region=True)
builder_base_count = Read("builder_count", anchor=anchor, region=(570, 40, 100, 40), confidence=0.92, fixed_region=True)

gold = Read("gold", anchor=anchor, region=(940, 44, 160, 30), confidence=0.76, char_confidence={'1': 0.8}, mask=True, template_dir="resources", fixed_region=True)
elixir = Read("elixir", anchor=anchor, region=(940, 94, 160, 35), confidence=0.65, mask=True, template_dir="resources", fixed_region=True)

gold._forget_region()
elixir._forget_region()
builder_count._forget_region()
builder_base_count._forget_region()

# Opponent's "Available Loot" counters shown top-left during an attack —
# smaller font than the home-screen counters above, so its own digit
# templates ('loot') and a deprioritized '1' (see low_priority_chars on
# Read) to stop it winning ties against wider digits' strokes.
enemy_gold = Read("enemy_gold", anchor=anchor, region=(-10, 98, 150, 32), confidence=0.65, mask=True, template_dir="loot", low_priority_chars={'1'})
enemy_elixir = Read("enemy_elixir", anchor=anchor, region=(-10, 128, 150, 32), confidence=0.65, mask=True, template_dir="loot", low_priority_chars={'1'})

# Reads gold from a saved jpg instead of a live screenshot, for testing the
# gold template/confidence settings offline against a captured screen.

# gold_from_file = Read(
#     "gold_from_file", region=(0, 0, 206, 48), confidence=0.76, mask=True, template_dir="resources",
#     image_path=os.path.join(BASE_DIR, 'images', 'read', 'resources', 'screenshots', '8.jpg')
# )

# print(f"{int(gold_from_file()):,}")
# print(gold_from_file(return_details=True))
