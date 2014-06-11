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

from pyndn import Name
from pyndn import Interest
from pyndn import Exclude
from pyndn.encoding import ProtobufTlv
# This include is produced by:
# protoc --python_out=. cec_messages.proto
import app.cec_messages_pb2 as pb
import json
import logging
logging.basicConfig(level=logging.INFO)

class Consumer(object):
    def __init__(self, loop, face, keyChain, deviceManager):
        self._countExpressedInterests = 0
        self._callbackCountData = 0
        self._callbackCountUniqueData = 0
        self._callbackCountTimeout = 0

        self._loop = loop
        self._face = face
        self._keyChain = keyChain

        self._deviceManager = deviceManager

    # Pir Consumption
    def onDataPir(self, interest, data):
        self._callbackCountData += 1
        logging.debug("Got data: " + data.getName().toUri())
        logging.debug("\tContent: " + data.getContent().toRawStr())

        # Extract info from data packet
        payload = json.loads(data.getContent().toRawStr())
        pirId = data.getName().get(2).toEscapedString()
        timeComponent = data.getName().get(3)
        timestamp = int(timeComponent.toEscapedString())
        pirVal = payload["pir"]

        # Update pirStatus information: add data, exclude last received timestamp
        pir = self._deviceManager.getPir(pirId)
        pir.status.setExcludeUpTo(timeComponent)
        if pir.status.addData(timestamp, pirVal):
            self._callbackCountUniqueData += 1

        logging.info("pir " + str(pirId) + " " + str(pirVal) + " at " + str(timestamp))
        self.controlTV()

    def onTimeoutPir(self, interest):
        self._callbackCountTimeout += 1
        logging.debug("Timeout interest: " + interest.getName().toUri())

    def expressInterestPirAndRepeat(self):
        logging.debug("callbackCountUniqueData: " + str(self._callbackCountUniqueData) + ", callbackCountTimeout: " + str(self._callbackCountTimeout))

        # Express interest for each pir we have discovered
        for pir in self._deviceManager.getPirs():
            interest = Interest(Name("/home/pir").append(pir.id))
            interest.setExclude(pir.status.getExclude())
            interest.setInterestLifetimeMilliseconds(1000.0)
            interest.setChildSelector(1)

            self._face.expressInterest(interest, self.onDataPir, self.onTimeoutPir)
            self._countExpressedInterests += 1
            logging.debug("Sent interest: " + interest.getName().toUri())
            logging.debug("\tExclude: " + interest.getExclude().toUri())
            logging.debug("\tLifetime: " + str(interest.getInterestLifetimeMilliseconds()))
 
        # Reschedule again in 0.5 sec
        self._loop.call_later(0.5, self.expressInterestPirAndRepeat)

    # Cec Control
    def onDataCec(self, interest, data):
        print "onDataCec"

    def onTimeoutCec(self, interest):
        print "onTimeoutCec"

    def controlTV(self):
        count = 0
        for pir in self._deviceManager.getPirs():
            if pir.status.getLastValue():
                count += 1
        if count >= 2:
            # TODO: Send command interest to TV
            logging.info("turn on tv")
            for cec in self._deviceManager.getCecs():
                message = pb.CommandMessage()
                message.destination = pb.TV
                message.commands.append(pb.AS)
                message.commands.append(pb.SLEEP)
                message.commands.append(pb.SLEEP)
                message.commands.append(pb.PLAY)
                encodedMessage = ProtobufTlv.encode(message)
                interest = Interest(Name("/home/cec").append(cec.id).append(encodedMessage))
                # interest = Interest(Name("/home/cec").append(cec.id).append("play"))
                # self._face.makeCommandInterest(interest)
                self._face.expressInterest(interest, self.onDataCec, self.onTimeoutCec)
        elif count == 0:
            # TODO: Send command interest to TV
            logging.info("STATUSES: " + str(self._remoteDevices)) # TODO: Cleanup
            logging.info("turn off tv")
            for cec in self._deviceManager.getCecs():
                message = pb.CommandMessage()
                message.destination = pb.TV
                message.commands.append(pb.STANDBY)
                encodedMessage = ProtobufTlv.encode(message)
                interest = Interest(Name("/home/cec").append(cec.id).append(encodedMessage))
                # interest = Interest(Name("/home/cec").append(cec.id).append("play"))
                # self._face.makeCommandInterest(interest)
                self._face.expressInterest(interest, self.onDataCec, self.onTimeoutCec)
