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

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        super(LedNode, self).__init__()
        # set up our pin commands

        self.pinList = [24, 17]
        for pinNumber in self.pinList:
            GPIO.setup(pinNumber, GPIO.OUT)
            onCommand = Name('setLight').append(str(pinNumber)).append('on')
            offCommand = Name('setLight').append(str(pinNumber)).append('off')
            self.addCommand(onCommand, self.onLightCommand,
                 ['led', 'light'], False)
            self.addCommand(offCommand, self.onLightCommand,
                 ['led', 'light'], False)

    def onLightCommand(self, interest):
        response = Data(interest.getName())
        # commands are .../setLight/pinNumber/[on|off]
        interestName = interest.getName()
        try:
            pinNumber = int(interestName.get(self.prefix.size()+1).toEscapedString())
            if pinNumber not in self.pinList:
                raise RuntimeError('Bad pin number')
            commandTypeComponent = interest.getName().get(self.prefix.size()+2)
            commandType = commandTypeComponent.toEscapedString()
            if commandType == 'on':
                GPIO.output(pinNumber, GPIO.HIGH)
            elif commandType == 'off':
                GPIO.output(pinNumber, GPIO.LOW)
            else:
                raise RuntimeError('BadCommand')
            response.setContent('ACK')
        except (IndexError, RuntimeError, ValueError):
            #malformed interest
            response.setContent('NACK')
        return response

if __name__ == '__main__':
    node = LedNode()
    node.start()
