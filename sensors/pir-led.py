import RPi.GPIO as gpio
from time import sleep

PIR = 12
LED = 11

gpio.setmode(gpio.BOARD)
gpio.setup(PIR, gpio.IN)
gpio.setup(LED, gpio.OUT)

pirState = False
pirVal = False

# TODO: how to package this data up?
while True:
    # pirVal = gpio.input(PIR)
    pirVal = rand(pirState)
    if (pirState == False and pirVal == True) or (pirState == True and pirVal == False):
        gpio.output(LED, pirVal)
        pirState = pirVal
    sleep(1)
