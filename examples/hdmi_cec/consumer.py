#!/usr/bin/python
# Copyright (C) 2014 Regents of the University of California.
# Author: Spencer Sutterlin <ssutterlin1@ucla.edu>
# Modified by: Adeola Bannis <thecodemaiden@gmail.com>
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

from pyndn import Name
from pyndn import Interest
from pyndn import Exclude
from pyndn.encoding import ProtobufTlv
from ndn_pi.iot_node import IotNode
# This include is produced by:
# protoc --python_out=. cec_messages.proto
import app.cec_messages_pb2 as pb
from app.remote_device import RemoteDevice
import json

class Consumer(IotNode):
    def __init__(self):
        super(Consumer, self).__init__()
        self._countExpressedInterests = 0
        self._callbackCountData = 0
        self._callbackCountUniqueData = 0
        self._callbackCountTimeout = 0
        self._deviceList = []


    def setupComplete(self):
        #fetch the pir list from the controller
        #once we have at least one pir, we can issue the interests
        self.loop.call_soon(self.requestDeviceList)
        self.loop.call_soon(self.expressInterestPirAndRepeat)

    def getPirs(self):
        return [ x for x in self._deviceList if x.type == "pir" ]

    def getPir(self, pirId):
        return next((x for x in self._deviceList if x.type == "pir" and x.id == pirId), None)

    def getCecs(self):
        return [ x for x in self._deviceList if x.type == "cec" ]

    def getCec(self, cecId):
        return next((x for x in self._deviceList if x.type == "cec" and x.id == cecId), None)

    def requestDeviceList(self):
        # do this periodically, like every 5 seconds
        interestName = Name(self._policyManager.getTrustRootIdentity()).append('listDevices')
        self.face.expressInterest(interestName, self.onDataPirList, self.onPirListTimeout)

    def onDataPirList(self, interest, data):
        payload = json.loads(data.getContent().toRawStr())
        self.log.debug(str(payload))
        newDeviceList = []

        try:
            cecList = payload["cec"]
        except KeyError:
            cecList = []

        for cec in cecList:
            existingCec = self.getCec(cec["name"])
            if existingCec is not None:
                newDeviceList.append(existingCec)
            else:
                newDeviceList.append(RemoteDevice("cec", cec["name"]))

        try:
            pirList = payload["pir"]
        except KeyError:
            pirList = []

        for pir in pirList:
            existingPir = self.getPir(pir["name"])
            if existingPir is not None:
                newDeviceList.append(existingPir)
            else:
                newDeviceList.append(RemoteDevice("pir", pir["name"]))

        self._deviceList = newDeviceList

        self.loop.call_later(5, self.requestDeviceList)

    def onPirListTimeout(self, interest):
        #try again later
        self.loop.call_later(15, self.requestDeviceList)

    def findDeviceIdMatching(self, matchPrefix):
        for d in self._deviceList:
            devName = Name(d.id)
            if devName.match(matchPrefix):
                return devName.toUri()
        return None

    # Pir Consumption
    def onDataPir(self, interest, data):
        self._callbackCountData += 1
        debugStr = "Got data: " + data.getName().toUri()
        debugStr += "\tContent: " + data.getContent().toRawStr()
        self.log.debug(debugStr)

        # Extract info from data packet
        payload = json.loads(data.getContent().toRawStr())
        pirId = self.findDeviceIdMatching(data.getName())
        timeComponent = data.getName().get(-1)
        timestamp = int(timeComponent.toEscapedString())
        pirVal = payload["pir"]

        # Update pirStatus information: add data, exclude last received timestamp
        pir = self.getPir(pirId)
        pir.status.setExcludeUpTo(timeComponent)
        if pir.status.addData(timestamp, pirVal):
            self._callbackCountUniqueData += 1

        self.log.info("pir " + str(pirId) + " " + str(pirVal) + " at " + str(timestamp))
        self.controlTV()

    def onTimeoutPir(self, interest):
        self._callbackCountTimeout += 1
        self.log.debug("Timeout interest: " + interest.getName().toUri())

    def expressInterestPirAndRepeat(self):
        self.log.debug("callbackCountUniqueData: " + str(self._callbackCountUniqueData) + ", callbackCountTimeout: " + str(self._callbackCountTimeout))

        # Express interest for each pir we have discovered
        for pir in self.getPirs():
            interest = Interest(Name(pir.id))
            interest.setExclude(pir.status.getExclude())
            interest.setInterestLifetimeMilliseconds(1000.0)
            interest.setChildSelector(1)

            self.face.expressInterest(interest, self.onDataPir, self.onTimeoutPir)
            self._countExpressedInterests += 1
            debugStr = "Sent interest: " + interest.getName().toUri()
            debugStr += "\tExclude: " + interest.getExclude().toUri()
            debugStr += "\tLifetime: " + str(interest.getInterestLifetimeMilliseconds())
 
            self.log.debug(debugStr)
        # Reschedule again in 0.5 sec
        self.loop.call_later(1.0, self.expressInterestPirAndRepeat)

    # Cec Control
    def onDataCec(self, interest, data):
        print "onDataCec"

    def onTimeoutCec(self, interest):
        print "onTimeoutCec"

    def controlTV(self):
        count = 0
        for pir in self.getPirs():
            if pir.status.getLastValue():
                count += 1
        if count >= 2:
            # TODO: Send command interest to TV
            self.log.info("turn on tv")
            for cec in self.getCecs():
                message = pb.CommandMessage()
                message.destination = pb.TV
                message.commands.append(pb.AS)
                message.commands.append(pb.SLEEP)
                message.commands.append(pb.PLAY)
                encodedMessage = ProtobufTlv.encode(message)
                interest = Interest(Name(cec.id).append(encodedMessage))
                # self.face.makeCommandInterest(interest)
                self.face.expressInterest(interest, self.onDataCec, self.onTimeoutCec)
        elif count == 0:
            # TODO: Send command interest to TV
            self.log.info("turn off tv")
            for cec in self.getCecs():
                message = pb.CommandMessage()
                message.destination = pb.TV
                message.commands.append(pb.STANDBY)
                encodedMessage = ProtobufTlv.encode(message)
                interest = Interest(Name(cec.id).append(encodedMessage))
                # self.face.makeCommandInterest(interest)
                self.face.expressInterest(interest, self.onDataCec, self.onTimeoutCec)

if __name__ == '__main__':
    n = Consumer()
    n.start()
