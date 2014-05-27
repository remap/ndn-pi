import RPi.GPIO as gpio
from time import sleep
import sys

class Led():
    def __init__(self, pin):
        self._pin = pin
        gpio.setmode(gpio.BOARD)
        gpio.setup(self._pin, gpio.OUT)

    def set(self, val):
        gpio.output(self._pin, val)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print """Usage: python led.py <pin>
<pin>  pin number of led according to board numbering system (P1-##)"""
    led = Led(int(sys.argv[1]))
    led.set(False)
    sleep(2)
    led.set(True)
    sleep(2)
    led.set(False)
