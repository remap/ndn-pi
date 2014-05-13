import time
from pyndn import Name
from pyndn import Data
from pyndn import Face
from pyndn import Interest
from pyndn.security import KeyChain

class Echo(object):
    def __init__(self, face, keyChain, certificateName):
        self._face = face
        self._keyChain = keyChain
        self._certificateName = certificateName
        self._responseCount = 0

    def run(self, prefix):
        self._face.registerPrefix(prefix, self.onInterest, self.onRegisterFailed)
        # TODO: Turn this into while True
        while self._responseCount < 2:
            self._face.processEvents()
            time.sleep(0.01)

    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        self._responseCount += 1
        commandInterest = interest # for naming clarity, since we respond to interest with interest
        print "Received command interest:", commandInterest.getName().toUri()

        # Respond to interest with data ack
        data = Data(interest.getName())
        data.setContent("ACK")
        self._keyChain.sign(data, self._certificateName)
        encodedData = data.wireEncode()
        transport.send(encodedData.toBuffer())

        # Send interest requesting data
        responseInterest = Interest(Name(commandInterest.getName().getSubName(4)))
        responseInterest.setInterestLifetimeMilliseconds(3000)
        self._face.expressInterest(responseInterest, self.onData, self.onTimeout)

    def onRegisterFailed(self, prefix):
        raise RegisterPrefixError('Register prefix failed')

    def onData(self, interest, data):
        self._responseCount += 1
        print "Interest:", interest.getName().toUri(), "got data named:", data.getName().toUri(), "with content:", data.getContent().toRawStr()

    def onTimeout(self, interest):
        self._responseCount += 1
        print "Interest:", interest.getName().toUri(), "timed out"

if __name__ == "__main__":
    face = Face("localhost")
    keyChain = KeyChain()
    face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())
    echo = Echo(face, keyChain, keyChain.getDefaultCertificateName())

    prefix = Name("/home/all/command")
    print "Register prefix", prefix.toUri()
    echo.run(prefix)

    face.shutdown()
