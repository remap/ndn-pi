import random

class FakePir():
    def __init__(self):
        self._prevVal = False

    def read(self):
        if random.random() < 0.1:
            self._prevVal = not self._prevVal
        return self._prevVal

if __name__ == "__main__":
    pir = FakePir()
    while True:
        v = pir.read()
        print v
        sleep(1)
