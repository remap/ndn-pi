# TODO: NFD hack: delete file once NFD forwarding fixed
from pyndn import Name
from pyndn import Data
from util.common import Common
import json
try:
    import asyncio
except ImportError:
    import trollius as asyncio

class LocalDiscoveree(object):
    def __init__(self, loop, face, keyChain):
        self._loop = loop
        self._face = face
        self._keyChain = keyChain

        self._serial = Common.getSerial()
        self._functions = []

        self._face.registerPrefix(Name("/home/localdev"), self.onInterestDev, self.onRegisterFailed)

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
