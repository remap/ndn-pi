#!/usr/bin/python
# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Adeola Bannis <thecodemaiden@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
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

from __future__ import print_function
from ndn_pi.iot_node import IotNode
from pyndn import Name, Data, Interest
import RPi.GPIO as GPIO

class LedNode(IotNode):
    def __init__(self, pinNumber):
        super(LedNode, self).__init__()

        # can we tell if the pin number is invalid?
        self.pinNumber = pinNumber
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pinNumber, GPIO.OUT)
    
        onCommand = Name('setLight').append('on')
        offCommand = Name('setLight').append('off')
        self.addCommand(onCommand, self.onLightCommand, ['led', 'light'],
            False)
        self.addCommand(offCommand, self.onLightCommand, ['led', 'light'],
            False)

        self.blinkPWM = None

    def onLightCommand(self, interest):
        self.log.debug("Light command")
        response = Data(interest.getName())
        try:
            commandTypeComponent = interest.getName().get(self.prefix.size()+1)
            commandType = commandTypeComponent.toEscapedString()
            if commandType == 'on':
                GPIO.output(self.pinNumber, GPIO.HIGH)
            elif commandType == 'off':
                GPIO.output(self.pinNumber, GPIO.LOW)
            else:
                raise RuntimeError('BadCommand')
            response.setContent('ACK')
        except IndexError, RuntimeError:
            #malformed interest
            response.setContent('NACK')
        return response

    def onBlinkCommand(self, interest):
        self.log.debug("Blink command")
        response = Data(interest.getName())
        if self.blinkPWM is None:
            self.blinkPWM = GPIO.PWM(self.pinNumber, 2.0)
            self.blinkPWM.start(50)
        else:
            self.blinkPWM.stop()
            self.blinkPWM = None
        response.setContent('ACK')
        return response

if __name__ == '__main__':
    import sys
    try:
	    pinNumber = int(sys.argv[1])
    except IndexError, ValueError:
        pinNumber = 24
    node = LedNode(pinNumber)
    node.start()
