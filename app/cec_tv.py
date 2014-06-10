from pyndn import Name
from util.common import Common
import app.cec_messages_pb2 as pb
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
        self._face.registerPrefix(Name("/home/cec").append(self._serial).append("capabilities"), self.onInterestCecCapabilities, self.onRegisterFailed)
        
    def processCommands(self, commands):
        # TODO: FORK SEPARATE THREAD FOR THIS
        print "processCommands:", commands
        for command in commands:
            pass
            #if command is pb.SLEEP:
                #time.sleep(1)
            #if command is pb.YOUSHALLNOTPASS:
                #Run you shall not pass

    def onInterestCec(self, prefix, interest, transport, registeredPrefixId):
        print "onInterestCec", interest.getName().toUri()
        # check command interest name
        # verify command interest
        #self._face.verifyCommandInterest(interest)
        #message = pb.CommandMessage()
        #ProtobufTlv.decode(message, interest.getName().get(3).getValue()) 
        # check tv status
        # turn on and play
        #proc = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #(out, err) = proc.communicate(input="as")
        #time.sleep(2.25)
        #subprocess.check_call(["omxplayer", "-o", "hdmi", "/home/pi/YOUSHALLNOTPASS.mp4"])
        # publish state data
        #proc = subprocess.Popen(["cec-client", "-s", "-d", "1"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #(out, err) = proc.communicate(input="standby 0")

    def onInterestCecCapabilities(self, prefix, interest, transport, registeredPrefixId):
        print "onInterestCecCapabilities", interest.getName().toUri()

        #data = Data(Name(prefix))
        # set capabilities
        #capabilitiesMessage = pb.CapabilitiesMessage()
        #content = capabilities.SerializeToString()
        #data.setContent(content)
        #data.getMetaInfo().setFreshnessPeriod(60000) # 1 minute, in milliseconds

        #self._keyChain.sign(data, self._keyChain.getDefaultCertificateName())
        #encodedData = data.wireEncode()
        #transport.send(encodedData.toBuffer())

    def onRegisterFailed(self, prefix):
        print "Register failed for prefix", prefix.toUri()
