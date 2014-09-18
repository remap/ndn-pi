
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

class ViewerNode(IotNode):
    def __init__(self, filename):
        super(ViewerNode, self).__init__(filename)
        self._networkListing = {}
        self._lastPresentedList = []

    def setupComplete(self):
        self.loop.call_soon(self.getDeviceList)
        self.loop.call_soon(self.displayMenu)
        self.loop.add_reader(stdin, self.handleUserInput)

    def onTimeout(self, interest):
        #try again
        self.log.warn('Timeout on device list')
        self.loop.call_later(5, self.getDeviceList)

    def onReceivedList(self, interest, data):
        #print ("Received:\n{}".format(data.getContent().toRawStr()))
        self._networkListing = json.loads(data.getContent().toRawStr())
        self.loop.call_later(30, self.getDeviceList)

    def displayMenu(self):
        menuStr = ''
        try:
            # keep old state in case the device list updates while the user is thinking
            self._lastPresentedList = self._networkListing["led"]
        except KeyError:
            self._lastPresentedList = []
        else:
            i = 1
            for info in self._lastPresentedList:
                signInfo = "signed" if info["signed"] else "unsigned"
                menuStr += '\t{}: {} ({})\n'.format(i, info["name"], signInfo)
                i += 1
            menuStr += 'Enter "on <n>" or "off <n>" to turn an LED on or off\n'
        menuStr += 'Enter "quit" to quit, anything else to refresh device list.'

        print(menuStr)
        print ("> ", end="")
        stdout.flush()


    def interestTimedOut(self, interest):
        self.log.warn("Timed out on light command")
        self.loop.call_soon(self.displayMenu)

    def lightAckReceived(self, interest, data):
        self.log.info("Received ack from lights")
        self.loop.call_soon(self.displayMenu)


    def handleUserInput(self):
        inputStr = stdin.readline()

        if inputStr.upper().startswith('Q'):
            self._isStopped = True
        else:
            inputCommand = inputStr.strip().split()
            try:
                commandType = inputCommand[0]
                chosenIdx = int(inputCommand[1]) - 1
                if commandType == 'off' or commandType == 'on' and chosenIdx >= 0:
                    chosenDevice = self._lastPresentedList[chosenIdx]
                    chosenName = chosenDevice["name"]

                    commandInterest = Interest(Name(chosenName).append(commandType))
                    commandInterest.setInterestLifetimeMilliseconds(5000)
                    if chosenDevice["signed"]:
                        self.face.makeCommandInterest(commandInterest)
                    self.face.expressInterest(commandInterest, self.lightAckReceived, self.interestTimedOut)
                else:
                    self.loop.call_soon(self.displayMenu)
            except IndexError, KeyError:
                self.loop.call_soon(self.displayMenu)
        

    def getDeviceList(self):
        interestName = Name(self._policyManager.getTrustRootIdentity()).append('listDevices')
        self.face.expressInterest(interestName, self.onReceivedList, self.onTimeout)

if __name__ == '__main__':
    import sys
    import os
    try:
	    fileName = sys.argv[1]
    except IndexError:
        fileName = os.path.join(os.path.dirname(__file__), 'viewer.conf')
    node = ViewerNode(fileName)
    node.start()
