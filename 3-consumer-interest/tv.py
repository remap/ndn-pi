#######
# TODO
# Get Jeff T's response about how to verify interest

import time
import subprocess
import sys

from pyndn import Face
from pyndn import Name
from pyndn.security import KeyChain
from pyndn import KeyLocatorType

class TV(object):
    def __init__(self):
        self._face = Face("localhost")
        self._keyChain = KeyChain()
        self._certificateName = self._keyChain.getDefaultCertificateName()
        self._face.setCommandSigningInfo(self._keyChain, self._certificateName)

    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        keyLocator = interest.getKeyLocator()
        print "KEY:", keyLocator, keyLocator.getType(), keyLocator.getKeyName().toUri(), keyLocator.getKeyData()
        if keyLocator.getType() == KeyLocatorType.KEYNAME:
            print keyLocator.getKeyName()
        elif keyLocator.getType() == KeyLocatorType.KEY_LOCATOR_DIGEST:
            print keyLocator.getKeyData()
        # check interest
        # check tv status
        # turn on and play
        print "onInterest"
        #proc = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #(out, err) = proc.communicate(input="as")
        #subprocess.check_call(["omxplayer", "-o", "hdmi", "/home/pi/YOUSHALLNOTPASS.mp4"])
        # publish state data

    def onRegisterFailed(self, prefix):
        print "Prefix register failed:", prefix.toUri()

    def run(self):
        self._face.registerPrefix(Name("/home/tv"), self.onInterest, self.onRegisterFailed)
        while True:
            self._face.processEvents()
            time.sleep(0.01)

if __name__ == "__main__":
    tv = TV()
    tv.run()
