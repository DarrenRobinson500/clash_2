from troop import *
from logic_read import *
from logic_build import *
from utilities import *
from warning import *

Accounts = []
_current_account = None

# Persists which account was last known active across separate process runs
# (e.g. main.py is a fresh one-shot script each time), so a new process
# doesn't have to pay for a go(home) trip just to re-detect it via
# identifier_icon every single run. Verified on load with a single
# identifier_icon.find() in case the account was switched outside of this
# script; if that misses, get_current_account() does the full detection.
CURRENT_ACCOUNT_FILE = os.path.join(BASE_DIR, 'current_account.json')


def pct(value, maximum):
    return f"{value / maximum:.0%}" if value is not None and maximum else ""

def status_by_next_build():
    bases = [(account, x) for account in Accounts for x in [0, 1]]
    bases.sort(key=lambda b: b[0].next_build_time[b[1]] or datetime.min)
    first_low = (None, None)
    text_for_file = f"{datetime.now().strftime('%b %d, %I:%M%p')}\n\n"
    for account, x in bases:
        text = account.status_line(x)
        text_for_file += text + "\n"
        print(text)
        resource_pc = account.resource_pc(x)
        if first_low[0] is None and resource_pc < .9:
            first_low = (account, x + 1)
    text_for_file += "\n"
    for warning in warnings:
        text_for_file += warning.text + "\n"
    write_to_file(text_for_file)
    return first_low

def _load_persisted_account():
    if not os.path.exists(CURRENT_ACCOUNT_FILE):
        return None
    with open(CURRENT_ACCOUNT_FILE) as f:
        name = json.load(f).get('name')
    return next((a for a in Accounts if a.name == name), None)

def _save_persisted_account(account):
    with open(CURRENT_ACCOUNT_FILE, 'w') as f:
        json.dump({'name': account.name}, f)

def get_goblins():
    go(saved_recipe)
    time.sleep(0.3)
    use.click()
    if army_okay.find():
        army_okay.click()
    if army_okay.find():
        army_okay.click()

    go(attack_2)
    if activate.find():
        activate.click()
        time.sleep(0.3)
        boost_elixir.click()


class Account:
    def __init__(self, name, identifier_icon, switch_icon, army=None, army_builder=None, resources=None, resources_max=None, build_type=0, attack_limit=0):
        self.name = name
        self.identifier_icon = identifier_icon
        self.switch_icon = switch_icon
        self.army = army
        self.army_builder = army_builder
        self.resources = resources if resources is not None else [0, 0, 0]
        self.resources_max = resources_max if resources_max is not None else [0, 0, 0]
        self.gold = [None, None]
        self.gold_max = [None, None]
        self.elixir = [None, None]
        self.elixir_max = [None, None]
        self.dark = [None, None]
        self.dark_max = [None, None]
        self.next_build_time = [None, None]
        self.next_research_time = [None, None]
        self.build_type = build_type
        self.walls = False
        self.donator = None
        self.attack_limit = attack_limit
        self.active_challenge = None
        self.deploy_click_count = 1
        self.build_list_orig = []
        self.build_list = []
        self.build_b_list_orig = []
        self.build_b_list = []
        self.build_string = []
        Accounts.append(self)

    def __str__(self):
        return self.name

    def get_build_string(self, x):
        build_item = ""
        if x == 0: b_list = self.build_list
        elif x == 1: b_list = self.build_b_list
        else: return
        if b_list:
            build_item = f"   Next build: {self.build_list[0]}"
        return build_item

    def read_resources(self, base_no):
        # self.switch()  # no-ops if self is already the active account
        time.sleep(0.3)
        if base_no == 0: go(home)
        if base_no == 1: go(home_1)
        time.sleep(0.5)
        self.gold[base_no] = to_int(Read("gold", template_dir="resources", anchor=anchor, region=(1020, 40, 120, 25), confidence=0.75, fixed_region=True, black_and_white=True)(), 0)
        self.elixir[base_no] = to_int(Read("elixir", template_dir="resources", anchor=anchor, region=(1020, 80, 120, 25), confidence=0.75, fixed_region=True, black_and_white=True)(), 0)
        if base_no == 0:
            self.dark[base_no] = to_int(Read("dark", template_dir="resources", anchor=anchor, region=(1020, 120, 120, 25), confidence=0.75, fixed_region=True, black_and_white=True, white_threshold=110)(), 0)
        # print("Read resources:", self.gold[base_no], self.elixir[base_no], self.dark[base_no])

    def sufficient_resources(self, base):
        self.read_resources(base)
        try:
            result = self.resource_pc(base) > 0.95
            if result:
                print(f"Sufficient resources ({self.resource_string(base)})")
            return result
        except:
            return False

    def gold_pc(self, x):
        if self.gold_max[x] != 0:
            return self.gold[x] / self.gold_max[x]
        return 0

    def elixir_pc(self, x):
        if self.elixir_max[x] != 0:
            return self.elixir[x] / self.elixir_max[x]
        return 0

    def dark_pc(self, x):
        if self.dark[x] and self.dark_max[x] != 0:
            return self.dark[x] / self.dark_max[x]
        return 0

    def resource_pc(self, x):
        count = 3
        if x == 1: count = 2
        return (self.gold_pc(x) + self.elixir_pc(x) + self.dark_pc(x)) / count

    def resource_string(self, x):
        return f"{self.gold_pc(x):>4.0%} {self.elixir_pc(x):>4.0%} {self.dark_pc(x):>4.0%} {self.resource_pc(x):>4.0%} "

    def resource_string_2(self, x):
        return f"{self.dark[x]:,}"

    def status_line(self, x):
        build_time = friendly_time_from_now(self.next_build_time[x]) or "Ready"
        research_time = friendly_time_from_now(self.next_research_time[x]) or "Ready"
        return f"{self.name + '_' + str(x + 1):<10} | {build_time:<15} | {research_time:<15} | {self.resource_string(x)} | {self.build_string[x]} | {self.get_build_string(x)}"

    def status(self):
        for x in [0,1]:
            print(self.status_line(x))

    def switch(self):
        global _current_account
        if get_current_account() is self:
            return
        while True:
            go(switch_panel)
            self.switch_icon.click()
            if self.identifier_icon.wait(duration=20):
                break
            # A popup may be hiding the icon — clear it and retry straight away
            # before falling back to the long wait.
            clicked = check_autos()
            if clicked:
                print(f"switch: {self.name}'s identifier icon never appeared — cleared {clicked}, retrying")
                continue
            print(f"switch: {self.name}'s identifier icon never appeared — waiting 15m and retrying")
            time.sleep(15 * 60)
            check_autos()
        _current_account = self
        _save_persisted_account(self)

    def set_build_list(self, build_list):
        self.build_list_orig = self.get_build_list(build_list)
        self.build_list = self.build_list_orig.copy()

    def set_build_b_list(self, build_list):
        self.build_b_list_orig = self.get_build_list(build_list)
        self.build_b_list = self.build_b_list_orig.copy()

    def get_build_list(self, build_list):
        unwanted = []
        for building_name in build_list:
            image = get_building(building_name)
            if not image and building_name not in ["wall_g", "wall_e"]:
                print("Not found:", building_name)
                unwanted.append(building_name)
        result = [s for s in build_list if s not in unwanted]
        return result

    def build(self): self.build_base(1)
    def build_b(self): self.build_base(2)
    def build_base(self, base):
        if len(self.build_list_orig) > 0 and len(self.build_list) == 0: self.build_list = self.build_list_orig.copy()
        if len(self.build_b_list_orig) > 0 and len(self.build_b_list) == 0: self.build_b_list = self.build_b_list_orig.copy()

        if base == 1:
            self.build_walls()
            list_to_use = self.build_list
            base_to_use = home
        else:
            list_to_use = self.build_b_list
            base_to_use = home_1

        if not list_to_use: return
        build_item = list_to_use[0]
        print("Build:", build_item)

        self.switch()
        go(base_to_use)
        if click_building(build_item, base):
            confirm(build_item)
        else:
            print("Build: couldn't find:", build_item)
        list_to_use.pop(0)

    def build_walls(self):
        if not self.walls: return
        go(home)
        gold_function = Read("gold", template_dir="resources", anchor=anchor, region=(1020, 40, 120, 25), confidence=0.75, fixed_region=True, black_and_white=True)
        elixir_function = Read("elixir", template_dir="resources", anchor=anchor, region=(1020, 80, 120, 25), confidence=0.75, fixed_region=True, black_and_white=True)
        limit = 5000000
        for function, wall_type in [(gold_function, "wall_g"), (elixir_function, "wall_e")]:
            while to_int(function()) > limit:
                print("Build wall:", wall_type)
                if click_building(wall_type, 1):
                    confirm(wall_type)
                else:
                    print("Build: couldn't find:", wall_type)
                time.sleep(0.5)
                build_panel_close.click()
                time.sleep(0.5)

    def start_challenge(self):
        self.switch()
        import logic_challenge
        return logic_challenge.start_challenge()

    def run_challenge(self):
        self.switch()
        if not self.active_challenge:
            self.start_challenge()
        if not self.active_challenge:
            print("Couldn't start a challenge")
            return
        result = self.active_challenge.run(self)
        self.active_challenge = None
        return result

    def collect_resources(self):
        self.switch()  # no-ops if self is already the active account
        go(home)
        move(0, 300)
        gold_icon.click()
        elixir_icon.click()
        dark_elixir_icon.click()
        self.read_resources(0)
        move(-300, 0)
        move(300, -300)

    def attack(self, task=None, count=10):
        self.switch()
        # self.read_resources(1)
        if self.sufficient_resources(0): return
        # print(f"Attack (start): {self.resource_string(0)}")
        if self.start_attack():
            for x in range(count):
                self.attack_single()
                # print(f"Goblin run: {x + 1} ({time.time() - start_time:.0f}s): {self.gold[0]:,}")
                if self.sufficient_resources(0):
                    print(f"Goblin run ({self}): Sufficient resources ({self.resource_string(0)})")
                    return
                print(f"Attack: {x + 1} {self.resource_string(0)}")
                start_time = time.time()

    def attack_single(self):
        go(attack_3)
        time.sleep(0.5)
        resource_limit = 500000
        read_enemy_gold = Read("enemy_gold", template_dir="resources", anchor=anchor, region=(16, 92, 120, 25), confidence=0.72, fixed_region=True, black_and_white=True)
        resource = read_enemy_gold(as_int=True)
        # print("Resource:", resource)
        # None = unreadable — treat it as not worth attacking and skip.
        while resource is None or resource < resource_limit:
            attack_next.click()
            time.sleep(0.5)
            attack_next.wait()
            resource = read_enemy_gold(as_int=True)
            # print("Resource:", resource, resource_limit)
            resource_limit -= 50000
        for troop in [bomber, super_goblin]:
            troop.click()
            lines = [
                [(64, 352), (471, 49)],
                [(636, 44), (1048, 340)],
                [(1048, 340), (735, 582)],
                [(386, 587), (64, 352)]
            ]
            for a, b in lines:
                line_click(a, b, 90)

        time.sleep(3)
        prev_resource = resource
        resource = read_enemy_gold(as_int=True)
        # print("Post Launch Resource:", resource)
        # None = unreadable — treat it as not worth attacking and skip.
        while resource != prev_resource:
            time.sleep(2)
            prev_resource = resource
            resource = read_enemy_gold(as_int=True)
            # print("Post Launch Resource:", resource, prev_resource)
        # print("Waited long enough:", resource, prev_resource)

        time.sleep(3)
        self.finish_attack()

    def start_attack(self):
        print("Start Attack")
        go(home)
        zoom(-20)
        go(attack_2)
        if not super_goblin.army_image.find():
            print("Getting super goblin")
            get_goblins()
        return True

    def finish_attack(self):
        back_home = False
        while not back_home:
            for x in [surrender, attack_end_battle, surrender_okay, return_home, ]:
                x.click()
                time.sleep(0.2)
            if home.find():
                back_home = True
            else:
                check_autos()

    def attack_builder_5(self):
        self.switch()
        print(f"Builder attack: 0 ({self.resource_string(1)})")
        for x in range(10):
            if self.sufficient_resources(1): return
            print(f"Builder attack: {x + 1} ({self.resource_string(1)})")
            self.attack_builder()
        self.collect_builder_elixir()

    def attack_builder(self):
        go(attack_b_2)
        deploy_spots = [(1100, 330), (20, 330), (20, 400)]
        deployed = False
        deploy_x, deploy_y = None, None

        # Deploy Hero and get deploy spot
        for x, y in deploy_spots:
            if deployed:
                continue
            click_at(150, 650)
            click_at(x, y)
            time.sleep(0.2)
            if not battle_begins_in.find():
                deployed = True
                deploy_x = x
                deploy_y = y

        # Deploy others
        click_at(230, 650)
        for x in range(1, 7):
            click_at(deploy_x, deploy_y)

        # Activate
        for x in range(0, 7):
            time.sleep(2)
            click_at(230 + x * 85, 650)
        time.sleep(2)
        click_at(155, 650)

        # Finish
        finished = False
        time_at_start = time.time()
        deadline = time_at_start + 30

        while not finished:
            if time.time() > deadline or two_stars.find(
                    confidence=0.85) or attack_b_finish_1.find() or attack_b_finish_2.find():
                go(home_1)
                finished = True
            if home_1.find(): finished = True
            time.sleep(0.5)

    def collect_builder_elixir(self):
        move(300, -300)
        if elixir_cart.find():
            elixir_cart.click()
            elixir_cart_collect.click()
            elixir_cart_cross.click()
        move(-300, 300)

    def donate(self, task=None):
        self.switch()  # no-ops if self is already the active account
        go(chat)
        time.sleep(0.2)
        count = 0
        if donate.find():
            while donate.find() and count < 4:
                donate.click()
                time.sleep(0.5)
                for z in range(4):
                    if donation_resource.find():
                        for x in [log_thrower, dragon, baby_dragon, electro, balloon, rocket_balloon, dragon_rider, healer, super_barb, wizard, archer, miner, rage, minion, lightning, freeze, invisibility, poison, ice_golam, stone_slammer, blimp, wall_wrecker, bowler, goblin, headhunter, bat, barb, giant, bomber]:
                            x.donate_click()
                            # time.sleep(1.5)
                    if z < 3 and donation_resource.find():
                        a = (800, 300)
                        b = (400, 300)
                        drag(a, b)
                        time.sleep(1)
                count += 1
        else:
            print("No donations")
        go(home)

    def request(self):
        go(home)
        chat.click()
        time.sleep(1)
        request_castle.click()
        request_send.click()
        time.sleep(1)
        chat_close.click()



def get_current_account(force=False):
    # print("Get current account")
    global _current_account
    if not force:
        if _current_account:
            return _current_account
    if home_1.find():
        pass
    else:
        go(home)
    for account in Accounts:
        # print(account.name, account.identifier_icon.find())
        if account.identifier_icon.find():
            _current_account = account
            _save_persisted_account(account)
            return account
    return None

