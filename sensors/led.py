import RPi.GPIO as gpio
from time import sleep

LED = 11

gpio.setmode(gpio.BOARD)
gpio.setup(LED, gpio.OUT)

gpio.output(LED, True)
sleep(1)
gpio.output(LED, False)
