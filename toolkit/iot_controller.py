
import logging
import time
import sys

from pyndn import Name, Face, Interest, Data, ThreadsafeFace
from pyndn.security import KeyChain
from pyndn.security.identity import IdentityManager
from pyndn.security.policy import ConfigPolicyManager
from pyndn.security.certificate import IdentityCertificate
from pyndn.encoding import ProtobufTlv

from trust.iot_identity_storage import IotIdentityStorage
from trust.iot_policy_manager import IotPolicyManager

from trust.cert_request_pb2 import CertificateRequestMessage
from trust.list_devices_pb2 import ListDevicesCommandMessage

from pyndn.util.boost_info_parser import BoostInfoParser
from iot_node import IotNode

try:
    import asyncio
except ImportError:
    import trollius as asyncio

class IotController(IotNode):
    def __init__(self, configFilename):
        super(IotController, self).__init__(configFilename)


    def onStartup(self):
        if not self.hasRootSignedCertificate(self):
            #this is an ERROR - we are the root!
            self.log.error("Controller has no certificate!")
            self.stop()

    def onCommandReceived(self, prefix, interest, transport, prefixId):
        # we may have trust-related commands, lighting commands, or a certificate request
        # route appropriately
        def verificationSucceeded(data):
            self.log.info("Verified: " + data.getName().toUri())
            interestName = (interest.getName())
            commandStr = str(interestName.get(self.prefix.size()).toEscapedString())

            self.log.debug("Got command: "+commandStr)
            try:
                self.dispatchValidCommand(commandStr, interest, transport)
            except Exception as e:
                self.log.error(str(e))

        def verificationFailed(data):
            self.log.info("Invalid" + data.getName().toUri())

        try:
            self.keychain.verifyInterest(interest, verificationSucceeded, verificationFailed)
        except Exception as e:
            self.log.error(str(e)+"/"+str(sys.exc_info()))

    def onRegisterFailed(self, prefix):
        self.log.error("Could not register " + prefix.toUri())
        if self._registrationFailures < 5:
            self._registrationFailures += 1
            self.log.error("Retry: {}/{}".format(self._registrationFailures, 5)) 
            self.face.registerPrefix(self.prefix, self.onCommandReceived, self.onRegisterFailed)
        else:
            self.stop()


if __name__ == '__main__':
    
    config = RawConfigParser()
    config.read('config.cfg')

    myPrefix = config.get('lighting', 'prefix')

    l = LightController(prefix=myPrefix)

    try:
        l.start()
    except KeyboardInterrupt:
        l.stop()
