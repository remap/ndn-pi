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
import json
import random

class LedUserNode(IotNode):
    def __init__(self):
        super(LedUserNode, self).__init__()
        self._ledCommands = []

    def setupComplete(self):
        self.loop.call_soon(self.requestDeviceList)
        self.loop.call_later(1, self.sendRandomCommand)

    def onListReceived(self, interest, data):
        # the list is send at json
        deviceDict = json.loads(data.getContent().toRawStr())
        try:
            ledCommands = deviceDict['led']
            self._ledCommands = [info['name'] for info in ledCommands]
        except (IndexError, KeyError, TypeError):
            self.log.debug('Did not find LED commands')
        finally:
            self.loop.call_later(5, self.requestDeviceList)

    def onCommandAck(self, interest, data):
        pass

    def onCommandTimeout(self, interest):
        pass

    def sendRandomCommand(self):
        try:
            chosenCommand = random.choice(self._ledCommands)
            interest = Interest(Name(chosenCommand))
            self.log.debug('Sending command {}'.format(chosenCommand))
            # uncomment the following line to sign interests (slower than unsigned)
            #self.face.makeCommandInterest(interest)
            self.face.expressInterest(interest, self.onCommandAck, self.onCommandTimeout)
        except IndexError:
            pass
        finally:
            self.loop.call_later(1, self.sendRandomCommand)

    def onListTimeout(self, interest):
        self.log.debug('Timed out asking for device list')
        self.loop.call_later(15, self.requestDeviceList)

    def requestDeviceList(self):
        commandName = self._policyManager.getTrustRootIdentity().append('listDevices')
        interest = Interest(commandName)
        self.face.makeCommandInterest(interest)

        self.face.expressInterest(interest, self.onListReceived, self.onListTimeout)


if __name__ == '__main__':
    import logging
    node = LedUserNode()
    node.start()
