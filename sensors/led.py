import RPi.GPIO as gpio
from time import sleep

LED_PIN = 11

class Led():
    def __init__(self):
        gpio.setmode(gpio.BOARD)
        gpio.setup(LED_PIN, gpio.OUT)

    def set(self, val):
        gpio.output(LED_PIN, val)

    def flash(self):
        self.set(False)
        sleep(2)
        self.set(True)
        sleep(2)
        self.set(False)

if __name__ == "__main__":
    led = Led()
    led.flash()
