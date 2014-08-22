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
from pyndn import Data
from sensors.pir import Pir
from util.common import Common
import time
import json
try:
    import asyncio
except ImportError:
    import trollius as asyncio

class PirPublisher(object):
    def __init__(self, loop, face, keyChain, discoveree, pirPin):
        self._loop = loop
        self._face = face
        self._keyChain = keyChain

        self._pir = Pir(pirPin)
        self._pirId = Common.getSerial() + str(self._pir.getPin())
        self._prevTimestamp = int(time.time() * 1000) # in milliseconds
        self._prevPirVal = self._pir.read()
        self._count = 0

        discoveree.addFunction("pir", self._pirId)

        self._face.registerPrefix(Name("/home/pir").append(self._pirId), self.onInterestPir, self.onRegisterFailed)

    def onInterestPir(self, prefix, interest, transport, registeredPrefixId):
        pirVal = self._pir.read()

        # If interest exclude doesn't match timestamp from last tx'ed data
        # then resend data
        if not interest.getExclude().matches(Name.Component(str(self._prevTimestamp))):
            print "Received interest without exclude ACK:", interest.getExclude().toUri()
            print "\tprevious timestamp:", str(self._prevTimestamp)
            data = Data(Name(prefix).append(str(self._prevTimestamp)))

            payload = { "pir" : self._prevPirVal, "count" : self._count }
            content = json.dumps(payload)
            data.setContent(content)

            data.getMetaInfo().setFreshnessPeriod(1000) # 1 second, in milliseconds

            self._keyChain.sign(data, self._keyChain.getDefaultCertificateName())
            encodedData = data.wireEncode()
            transport.send(encodedData.toBuffer())
            print "Sent data:", data.getName().toUri(), "with content", content

        # 
        if pirVal != self._prevPirVal:
            timestamp = int(time.time() * 1000) # in milliseconds
            data = Data(Name(prefix).append(str(timestamp)))

            payload = { "pir" : pirVal, "count" : self._count }
            content = json.dumps(payload)
            data.setContent(content)

            data.getMetaInfo().setFreshnessPeriod(1000) # 1 second, in milliseconds

            self._keyChain.sign(data, self._keyChain.getDefaultCertificateName())
            encodedData = data.wireEncode()
            transport.send(encodedData.toBuffer())
            print "Sent data:", data.getName().toUri(), "with content", content

            # TODO: Save last data

            self._prevTimestamp = timestamp
            self._prevPirVal = pirVal
            self._count += 1

    def onRegisterFailed(self, prefix):
        print "Register failed for prefix", prefix.toUri()
