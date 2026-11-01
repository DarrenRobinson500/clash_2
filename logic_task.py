import time
from logic_nav import go
from logic_account import Accounts, get_current_account
from status import *

_STATUS_TIME_FILE = os.path.join(BASE_DIR, 'last_status.json')


def _load_last_status():
    try:
        with open(_STATUS_TIME_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return 0


def _save_last_status(t):
    with open(_STATUS_TIME_FILE, 'w') as f:
        json.dump(t, f)

Tasks = []


class Task:
    def __init__(self, name, account, loc, run_function, fixed_time, default_time=None, time_function=None, next_run=None):
        self.name = name
        self.account = account
        self.loc = loc
        self.run_function = run_function
        self.fixed_time = fixed_time
        self.time_function = time_function
        self.default_time = default_time  # minutes
        self.next_run = next_run if next_run is not None else time.time()
        self.next_run_override = None
        Tasks.append(self)

    def pause(self, minutes):
        # Lets run_function force the next_run instead of the normal
        # time_function/default_time scheduling below (e.g. "you need more"
        # in build() means retrying immediately is pointless).
        self.next_run_override = time.time() + minutes * 60

    def run(self):
        self.account.switch()
        go(self.loc)
        self.run_function(self)
        if self.next_run_override is not None:
            self.next_run = self.next_run_override
            self.next_run_override = None
            return
        # default_time and time_function both give minutes, not seconds.
        minutes = self.default_time if self.fixed_time else (self.time_function(self) or self.default_time)
        self.next_run = time.time() + minutes * 60


def run_tasks(tasks=None, status_check=True):
    get_current_account(force=True)
    if tasks is None:
        tasks = Tasks
    last_status = _load_last_status()
    while True:
        if status_check and time.time() - last_status >= 3600:
            try:
                get_status()
                last_status = time.time()
            except Exception as e:
                print(f"get_status failed: {e}. Retrying in 15 minutes.")
                last_status = time.time() - 3600 + 15 * 60
            _save_last_status(last_status)

        now = time.time()
        due = [t for t in tasks if t.next_run <= now]
        if due:
            current = get_current_account()
            task = min(due, key=lambda t: (t.account is not current, t.next_run))
            print(f"\nRunning task: {task.name}")
            try:
                task.run()
            except Exception as e:
                print(f"Task {task.name} failed: {e}. Retrying in 15 minutes.")
                task.next_run = time.time() + 15 * 60
            continue

        upcoming = sorted(tasks, key=lambda t: t.next_run)
        print("\nUpcoming tasks:")
        for t in upcoming:
            print(f"{t.name}: {time.strftime('%H:%M:%S', time.localtime(t.next_run))}")
        for account in Accounts:
            gold, elixir, dark_elixir = account.resources
            print(f"{account.name}: {gold:,} {elixir:,} {dark_elixir:,}")

        time.sleep(max(upcoming[0].next_run - time.time(), 0))

_save_last_status(time.time() - 1800)