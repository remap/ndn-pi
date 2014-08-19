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

import time
from pyndn import Name
from pyndn import Interest
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyChain

import subprocess
from os.path import expanduser, join
from sensors.pir import Pir
from util.common import Common
import struct
import json

class PirPublisher(object):
    def __init__(self):
        self._serial = Common.getSerial()
        self._pir = Pir(12)
        self._prevPirVal = self._pir.read()

        self._face = Face("localhost")
        self._keyChain = KeyChain()
        self._certificateName = self._keyChain.getDefaultCertificateName()
        self._face.setCommandSigningInfo(self._keyChain, self._certificateName)

        self._face.registerPrefix(Name("/home/dev"), self.onInterestDev, self.onRegisterFailed)
        self._face.registerPrefix(Name("/home/pir"), self.onInterestPir, self.onRegisterFailed)

        self._count = 0
        
    def onInterestDev(self, prefix, interest, transport, registeredPrefixId):
        print "Recv interest:", interest.getName().toUri(), "at prefix", prefix.toUri()
        # TODO: Check exclude filter
        
        data = Data(Name(prefix).append(self._serial))

        payload = { "functions" : [{ "type" : "pir", "id" : str(self._serial) + str(12) }] }   # TODO: self._pir.getPin()
        content = json.dumps(payload)
        data.setContent(content)

        data.getMetaInfo().setFreshnessPeriod(60000) # 1 minute, in milliseconds

        self._keyChain.sign(data, self._certificateName)
        encodedData = data.wireEncode()
        transport.send(encodedData.toBuffer())

    def onInterestPir(self, prefix, interest, transport, registeredPrefixId):
        pirVal = self._pir.read()

        # CHECK EXCLUDE FILTER
        # TODO: if interest exclude doesn't match timestamp from last tx'ed data
        # then resend data

        if pirVal != self._prevPirVal:
            timestamp = int(time.time() * 1000) # in milliseconds
            data = Data(Name(prefix).append(self._serial + str(12)).append(str(timestamp)))

            payload = { "pir" : pirVal, "count" : self._count, "src" : "1" }
            content = json.dumps(payload)
            data.setContent(content)

            data.getMetaInfo().setFreshnessPeriod(60000) # 1 minute, in milliseconds

            self._keyChain.sign(data, self._certificateName)
            encodedData = data.wireEncode()
            transport.send(encodedData.toBuffer())
            print "Sent data:", data.getName().toUri(), "with content", content

            # TODO: Save last data

            self._prevPirVal = pirVal
            self._count += 1

    def onRegisterFailed(self, prefix):
        print "Register failed for prefix", prefix.toUri()

    def run(self):
        while True:
            self._face.processEvents()
            # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
            time.sleep(0.01)    

        self._face.shutdown()

if __name__ == "__main__":
    pirPublisher = PirPublisher()
    pirPublisher.run()
