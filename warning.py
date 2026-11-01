warnings = []

class Warning:
    def __init__(self, text):
        self.text = text
        warnings.append(self)
        # print("Warning added:", self.text)

    def __str__(self):
        return self.text

Warning("war status")