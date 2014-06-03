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

try:
    import asyncio
except ImportError:
    import trollius as asyncio

class PirPublisher(object):
    def __init__(self):
        self._serial = Common.getSerial()
        self._pir = Pir(12)
        self._prevPirVal = self._pir.read()

        self._loop = asyncio.get_event_loop()
        self._face = ThreadsafeFace(self._loop, "localhost")
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
        self._loop.run_forever()
        self._face.shutdown()

if __name__ == "__main__":
    pirPublisher = PirPublisher()
    pirPublisher.run()
