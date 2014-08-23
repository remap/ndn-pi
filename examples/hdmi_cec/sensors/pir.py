# Copyright (C) 2014 Regents of the University of California.
# Author: Spencer Sutterlin <ssutterlin1@ucla.edu>
# 
# This file is part of ndn-pi (Named Data Networking - Pi).
#
# ndn-pi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU General Public License is in the file COPYING.

import RPi.GPIO as gpio
from time import sleep

class Pir(object):
    def __init__(self, pin):
        self._pin = pin
        gpio.setmode(gpio.BCM)
        gpio.setup(self._pin, gpio.IN)

    def getPin(self):
        return self._pin

    def read(self):
        return bool(gpio.input(self._pin))

if __name__ == "__main__":
    pir = Pir(18)
    while True:
        v = pir.read()
        print v
        sleep(1)
