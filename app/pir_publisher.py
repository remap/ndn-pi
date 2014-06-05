import time
from pyndn import Name
from pyndn import Interest
from pyndn import Data
from pyndn import ThreadsafeFace
from pyndn.security import KeyChain

import subprocess
from os.path import expanduser, join
from sensors.pir import Pir
from util.common import Common
import struct
import json
import logging

try:
    import asyncio
except ImportError:
    import trollius as asyncio

logging.basicConfig(level=logging.INFO)

class PirPublisher(object):
    def __init__(self):
        self._serial = Common.getSerial()
        self._pir = Pir(12)
        self._prevTimestamp = int(time.time() * 1000) # in milliseconds
        self._prevPirVal = self._pir.read()

        self._loop = asyncio.get_event_loop()
        self._face = ThreadsafeFace(self._loop, "localhost")
        self._keyChain = KeyChain()
        self._certificateName = self._keyChain.getDefaultCertificateName()
        self._face.setCommandSigningInfo(self._keyChain, self._certificateName)

        self._face.registerPrefix(Name("/home/dev"), self.onInterestDev, self.onRegisterFailed)
        self._face.registerPrefix(Name("/home/pir").append(self._serial + str(12)), self.onInterestPir, self.onRegisterFailed)

        self._count = 0
        
    def onInterestDev(self, prefix, interest, transport, registeredPrefixId):
        print "Recv interest:", interest.getName().toUri(), "at prefix", prefix.toUri()
        # TODO: Check exclude filter
        
        data = Data(Name(prefix).append(self._serial))

        payload = { "functions" : [{ "type" : "pir", "id" : str(self._serial) + str(12) }] }   # TODO: self._pir.getPin()
        content = json.dumps(payload)
        data.setContent(content)

        data.getMetaInfo().setFreshnessPeriod(4000) # 4 seconds, in milliseconds

        self._keyChain.sign(data, self._certificateName)
        encodedData = data.wireEncode()
        transport.send(encodedData.toBuffer())

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

            self._keyChain.sign(data, self._certificateName)
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

            self._keyChain.sign(data, self._certificateName)
            encodedData = data.wireEncode()
            transport.send(encodedData.toBuffer())
            print "Sent data:", data.getName().toUri(), "with content", content

            # TODO: Save last data

            self._prevTimestamp = timestamp
            self._prevPirVal = pirVal
            self._count += 1

    def onRegisterFailed(self, prefix):
        print "Register failed for prefix", prefix.toUri()

    def run(self):
        self._loop.run_forever()
        self._face.shutdown()

if __name__ == "__main__":
    pirPublisher = PirPublisher()
    pirPublisher.run()
