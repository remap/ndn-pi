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
from app.remote_device import RemoteDevice
import json
import logging
logging.basicConfig(level=logging.INFO)

class DeviceManager(object):
    def __init__(self, loop, face, keyChain):
        self._loop = loop
        self._face = face
        self._keyChain = keyChain

        self._remoteDevices = []

        # TODO: NFD hack: remove once NFD forwarding fixed
        self._oneTimeoutAlready = False

    def onDataDiscovery(self, interest, data):
        logging.debug("Received data: " + data.getName().toUri())
        logging.debug("\tContent: " + data.getContent().toRawStr())

        # TODO: save device for each Pir so I can remove pirs if no response
        payload = json.loads(data.getContent().toRawStr())
        for func in payload["functions"]:
            type = func["type"]
            id = func["id"]
            if not any(x.type == type and x.id == id for x in self._remoteDevices):
                logging.info("New device discovered: " + type + " " + id)
                self._remoteDevices.append(RemoteDevice(type, id))

        # Reissue interest for "/home/dev" excluding devId just received
        devId = data.getName().get(2)
        interest.getExclude().appendComponent(devId)
        self.expressDiscoveryInterest(interest)
        logging.info("Reissue discovery interest for \"/home/dev/\", excluding already discovered devices")

    def onTimeoutDiscovery(self, interest):
        logging.debug("Timeout interest: " + interest.getName().toUri())
        logging.info("Discovery complete, rescheduling again in 600 seconds")
        logging.info("Devices discovered: " + str(self._remoteDevices))

        # TODO: NFD hack: uncomment once NFD forwarding fixed
        # self._loop.call_later(600, self.initDiscovery)

        # TODO: NFD hack: remove once NFD forwarding fixed
        if self._oneTimeoutAlready:
            self._oneTimeoutAlready = False
            self._loop.call_later(600, self.initDiscovery)
        else:
            self._oneTimeoutAlready = True

    def expressDiscoveryInterest(self, interest):
        self._face.expressInterest(interest, self.onDataDiscovery, self.onTimeoutDiscovery)
        logging.debug("Sent interest: " + interest.getName().toUri())
        logging.debug("\tExclude: " + interest.getExclude().toUri())
        logging.debug("\tLifetime: " + str(interest.getInterestLifetimeMilliseconds()))

    def initDiscovery(self):
        logging.info("Begin discovery, issue discovery interest for \"/home/dev\"")
        interest = Interest(Name("/home/dev"))
        interest.setInterestLifetimeMilliseconds(4000.0)
        interest.setMinSuffixComponents(2)
        interest.setMaxSuffixComponents(2)
        # includes implicit digest so to match "/home/dev/<dev-id>" must have 2 components

        # Express initial discovery interest
        self.expressDiscoveryInterest(interest)

        # TODO: NFD hack: remove once NFD forwarding fixed
        interest = Interest(Name("/home/localdev"))
        interest.setInterestLifetimeMilliseconds(4000.0)
        interest.setMinSuffixComponents(2)
        interest.setMaxSuffixComponents(2)
        self.expressDiscoveryInterest(interest)

    def getPirs(self):
        return [ x for x in self._remoteDevices if x.type == "pir" ]

    def getPir(self, pirId):
        return next((x for x in self._remoteDevices if x.type == "pir" and x.id == pirId), None)

    def getCecs(self):
        return [ x for x in self._remoteDevices if x.type == "cec" ]
