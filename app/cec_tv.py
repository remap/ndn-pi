from pyndn import Name
from util.common import Common
import subprocess

class CecTv(object):
    def __init__(self, loop, face, keyChain, discoveree):
        self._loop = loop
        self._face = face
        self._keyChain = keyChain

        self._serial = Common.getSerial()

        discoveree.addFunction("cec", self._serial)

        # Register /home/cec/<cec-id> to listen for command interests to control tv
        self._face.registerPrefix(Name("/home/cec").append(self._serial), self.onInterestCec, self.onRegisterFailed)
        
    def onInterestCec(self, prefix, interest, transport, registeredPrefixId):
        print "onInterestCec", interest.getName().toUri()
        # check command interest name
        # verify command interest
        #self._face.verifyCommandInterest(interest)
        # check tv status
        # turn on and play
        #proc = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #(out, err) = proc.communicate(input="as")
        #subprocess.check_call(["omxplayer", "-o", "hdmi", "/home/pi/YOUSHALLNOTPASS.mp4"])
        # publish state data

    def onRegisterFailed(self, prefix):
        print "Register failed for prefix", prefix.toUri()
