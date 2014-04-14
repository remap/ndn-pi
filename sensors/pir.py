import RPi.GPIO as gpio
from time import sleep

PIR = 12

gpio.setmode(gpio.BOARD)
gpio.setup(PIR, gpio.IN)

def readPir():
    pirVal = gpio.input(PIR)
    if pirVal:
        return "True"
    else:
        return "False"

def monitorPir():
    while True:
        v = readPir()
        print v
        sleep(1)

if __name__ == "__main__":
    monitorPir()
