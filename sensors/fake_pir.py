import random

class FakePir():
    def __init__(self, pin):
        self._pin = pin
        self._prevVal = False

    def getPin(self):
        return self._pin

    def read(self):
        if random.random() < 0.1:
            self._prevVal = not self._prevVal
        return self._prevVal

if __name__ == "__main__":
    pir = FakePir(12)
    while True:
        v = pir.read()
        print v
        sleep(1)
