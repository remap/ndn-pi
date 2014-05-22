import time
from pyndn import Name
from pyndn import Interest
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyChain

import subprocess
from os.path import expanduser, join
from sensors.pir import Pir
import struct
import json

def getSerial():
    with open('/proc/cpuinfo') as f:
        for line in f:
            if line.startswith('Serial'):
                return line.split(':')[1].strip()

class PirPublisher(object):
    def __init__(self):
        self._serial = getSerial()
        self._pir = Pir()
        self._prevPirVal = self._pir.read()

        self._face = Face("localhost")
        self._keyChain = KeyChain()
        self._certificateName = self._keyChain.getDefaultCertificateName()
        self._face.setCommandSigningInfo(self._keyChain, self._certificateName)

#        self._face.registerPrefix(Name("/home/dev" + self._serial), self.onInterestDev, self.onRegisterFailed)
        self._face.registerPrefix(Name("/home/pir"), self.onInterestPir, self.onRegisterFailed)

        self._count = 0
        
    def onInterestDev(self, prefix, interest, transport, registeredPrefixId):
        print "Got interest for", interest.getName().toUri(), "at prefix", prefix.toUri()

    def onInterestPir(self, prefix, interest, transport, registeredPrefixId):
        pirVal = self._pir.read()

#        if pirVal != self._prevPirVal:
        timestamp = int(time.time() * 1000) # in milliseconds
#        data = Data(prefix.append("dev").append(self._serial).append("pir").append("0").append(str(timestamp)))
        data = Data(interest.getName())

        payload = { "pir" : pirVal, "count" : self._count }
        content = json.dumps(payload)
        data.setContent(content)

        self._keyChain.sign(data, self._certificateName)
        encodedData = data.wireEncode()
        transport.send(encodedData.toBuffer())
        print "Sent content", content

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
