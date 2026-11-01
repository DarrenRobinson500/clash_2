from image import Image
from utilities import *
from nav import *
from logic_account import get_current_account

challenges = []

class Challenge:
    def __init__(self, name, unselected_image=None, selected_image=None, run=None):
        self.name = name
        self.unselected_image = unselected_image if unselected_image is not None else Image(f'images/challenges/unselected/{name}.jpg')
        self.selected_image = selected_image if selected_image is not None else Image(f'images/challenges/selected/{name}.jpg')
        self.run = run
        challenges.append(self)

    def __str__(self):
        return self.name

    def show_images(self, dur=500):
        self.unselected_image.show(dur)
        self.selected_image.show(dur)

def start_challenge():
    account = get_current_account()
    if account.active_challenge:
        print("A challenge is already active:", account.active_challenge)
        return account.active_challenge

    go(challenge_loc)
    for challenge in challenges:
        if challenge.selected_image.find():
            account.active_challenge = challenge
            print("A challenge is already active:", account.active_challenge)
            return account.active_challenge

    start_challenge_if_visible(challenges)
    print("Attempting to move")
    time.sleep(1)
    drag((1000, 400), (1000, 200))
    time.sleep(1)
    start_challenge_if_visible(challenges)
    return account.active_challenge

def start_challenge_if_visible(challenges):
    account = get_current_account()
    for challenge in challenges:
        if challenge.unselected_image.find():
            challenge.unselected_image.click()
            if challenge_start.find():
                challenge_start.click()
                account.active_challenge = challenge
                print("Active challenge:", account.active_challenge)
    return account.active_challenge
