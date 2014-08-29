
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
from sys import stdin, stdout
try:
    import asyncio
except ImportError:
    import trollius as asyncio
    from trollius import Return, From

class ConsoleNode(IotNode):
    def __init__(self, configFile):
        super(ConsoleNode, self).__init__(configFile)
        self._networkListing = {}
        self._shouldSign = False

    def setupComplete(self):
        self._loop.call_soon(self.getDeviceList)
        self._loop.call_soon(self.displayMenu)
        self._loop.add_reader(stdin, self.handleUserInput)

    def onDeviceListTimeout(self, interest):
        #try again
        self.log.warn('Timeout on device list')
        self._loop.call_later(5, self.getDeviceList)
        self._loop.call_soon(self.displayMenu)

    def onReceivedList(self, interest, data):
        self._networkListing = json.loads(data.getContent().toRawStr())
        self._loop.call_later(30, self.getDeviceList)

    def displayMenu(self):
        self._lastPresentedList = self._networkListing.copy()
        signingStr = 'ON' if self._shouldSign else 'OFF'
        menuStr = 'Signing is {}\n'.format(signingStr)
        menuStr += 'Available commands:\n\n'
        for capability, commands in self._lastPresentedList.items():
            menuStr += '{}:\n'.format(capability)
            for info in commands:
                signingStr = 'signed' if info['signed'] else 'unsigned'
                menuStr += '\t{} ({})\n'.format(info['name'], signingStr)
        menuStr += 'Enter an interest name to send, "sign" to toggle signing, or "quit" to exit'

        print(menuStr)
        print ("> ", end="")
        stdout.flush()

    def interestTimedOut(self, interest):
        print("Timed out waiting for: {}".format(interest.getName().toUri()))
        self._loop.call_soon(self.displayMenu)

    def onDataReceived(self, interest, data):
        print("Received {}: ".format(data.getName().toUri()))
        print(data.getContent().toRawStr())
        self._loop.call_soon(self.displayMenu)

    def handleUserInput(self):
        inputStr = stdin.readline()
        if inputStr.upper().startswith('Q'):
            self._isStopped = True
        elif inputStr.upper().startswith('S'):
            self._shouldSign = not self._shouldSign
            self._loop.call_soon(self.displayMenu)
        elif not inputStr.startswith('/'):
            controllerName = self._policyManager.getTrustRootIdentity().toUri()
            helpStr = 'Interest names should start with /\n'
            helpStr += 'e.g. {}/listDevices'.format(controllerName)
            print(helpStr)
            self._loop.call_soon(self.displayMenu)
        else:
            interest = Interest(Name(inputStr))
            interest.setChildSelector(1)
            self._face.expressInterest(interest, self.onDataReceived, self.interestTimedOut)

            

    def getDeviceList(self):
        interestName = Name(self._policyManager.getTrustRootIdentity()).append('listDevices')
        self._face.expressInterest(interestName, self.onReceivedList, self.onDeviceListTimeout)

if __name__ == '__main__':
    import sys
    import os
    try:
	    fileName = sys.argv[1]
    except IndexError:
        fileName = '/usr/local/etc/ndn/iot/default.conf'
    node = ConsoleNode(fileName)
    node.start()
