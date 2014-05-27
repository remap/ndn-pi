import RPi.GPIO as gpio
from time import sleep
import sys

class Pir():
    def __init__(self, pin):
        self._pin = pin
        gpio.setmode(gpio.BOARD)
        gpio.setup(self._pin, gpio.IN)

    def read(self):
        return bool(gpio.input(self._pin))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print """Usage: python pir.py <pin>
<pin>  pin number of pir sensor according to board numbering system (P1-##)"""
        exit()
    pir = Pir(int(sys.argv[1]))
    while True:
        v = pir.read()
        print v
        sleep(1)
