import RPi.GPIO as gpio
from time import sleep

PIR_PIN = 12

class Pir():
    def __init__(self):
        gpio.setmode(gpio.BOARD)
        gpio.setup(PIR_PIN, gpio.IN)

    def read(self):
        return bool(gpio.input(PIR_PIN))

    def monitor(self):
        while True:
            v = self.read()
            print v
            sleep(1)

if __name__ == "__main__":
    pir = Pir()
    pir.monitor()
