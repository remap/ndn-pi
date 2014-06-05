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

class Discoveree(object):
    def __init__(self, loop, face, keyChain):
        self._serial = Common.getSerial()
        self._loop = loop
        self._face = face
        self._keyChain = keyChain
        self._functions = []
        self._face.registerPrefix(Name("/home/dev"), self.onInterestDev, self.onRegisterFailed)

    def onInterestDev(self, prefix, interest, transport, registeredPrefixId):
        print "Recv interest:", interest.getName().toUri(), "at prefix:", prefix.toUri()
        print "\texclude:", interest.getExclude().toUri()
        if interest.getExclude().matches(Name.Component(self._serial)):
            print "Discard interest, we are excluded already"
            return

        data = Data(Name(prefix).append(self._serial))

        payload = { "functions" : self._functions }
        content = json.dumps(payload)
        data.setContent(content)

        data.getMetaInfo().setFreshnessPeriod(4000) # 4 seconds, in milliseconds

        self._keyChain.sign(data, self._keyChain.getDefaultCertificateName())
        encodedData = data.wireEncode()
        transport.send(encodedData.toBuffer())

    def onRegisterFailed(self, prefix):
        print "Register failed for prefix", prefix.toUri()

    def addFunction(self, type, id):
        self._functions.append({ "type" : type, "id" : id })

    def removeFunction(self, type, id):
        raise RuntimeError("removeFunction is not implemented")


class PirPublisher(object):
    def __init__(self, loop, face, keyChain, discoveree, pirPin):
        self._pir = Pir(pirPin)
        self._pirId = Common.getSerial() + str(self._pir.getPin())
        self._prevTimestamp = int(time.time() * 1000) # in milliseconds
        self._prevPirVal = self._pir.read()

        self._loop = loop
        self._face = face
        self._keyChain = keyChain

        discoveree.addFunction("pir", self._pirId)

        self._face.registerPrefix(Name("/home/pir").append(self._pirId), self.onInterestPir, self.onRegisterFailed)

        self._count = 0
        
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

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    face = ThreadsafeFace(loop, "localhost")
    keyChain = KeyChain()
    face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())
    discoveree = Discoveree(loop, face, keyChain)
    pirPublisher = PirPublisher(loop, face, keyChain, discoveree, 12)
    pirPublisher = PirPublisher(loop, face, keyChain, discoveree, 7)
    loop.run_forever()
    face.shutdown()
