
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

from commands.cert_request_pb2 import CertificateRequestMessage
from commands.list_capabilities_pb2 import ListCapabilitiesMessage

from pyndn.util.boost_info_parser import BoostInfoParser

try:
    import asyncio
except ImportError:
    import trollius as asyncio

class IotNode(object):
    def __init__(self, configFilename):
        super(IotNode, self).__init__()

        self.config = BoostInfoParser()
        self.config.read(configFilename)

        prefix = config["environment/deviceName"][0].getValue()
        
        self.prefix = Name(prefix)
        self._identityStorage = IotIdentityStorage()
        self._identityManager = IdentityManager()
        self._policyManager = IotPolicyManager(self._identityStorage, configFilename)
        self.keychain = KeyChain(self._identityManager, self._policyManager)
        self._identityStorage.setDefaultIdentity(self.prefix)

        self._registrationFailures = 0
    
    def prepareLogging(self):
        self.log = logging.getLogger(str(self.__class__))
        self.log.setLevel(logging.DEBUG)
        logFormat = "%(asctime)-15s %(name)-20s %(funcName)-20s (%(levelname)-8s):\n\t%(message)s"
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter(logFormat))
        sh.setLevel(logging.INFO)
        # without this, a lot of ThreadsafeFace errors get swallowed up
        logging.getLogger("trollius").addHandler(sh)
        self.log.addHandler(sh)


    def start(self):
        self.loop = asyncio.get_event_loop()
        self.face = ThreadsafeFace(self.loop, self.address)
        self.face.setCommandSigningInfo(self.keychain, self.keychain.getDefaultCertificateName())
        self.face.registerPrefix(self.prefix, self.onCommandReceived, self.onRegisterFailed)
        self.keychain.setFace(self.face)

        self.loop.call_soon(self.onStartup)

        self._isStopped = False
        self.face.stopWhen(lambda:self._isStopped)
        try:
            self.loop.run_forever()
        except Exception as e:
            self.log.error(str(e))
        finally:
            self.stop()

    def getLogger(self):
        return self.log

    def stop(self):
        print 'Stopping...'
        self.log.info("Shutting down")
        self.loop.close()
        self.face.shutdown()

    def onStartup(self):
        if not self.hasRootSignedCertificate(self):
            self.loop.call_soon(self.sendCertificateRequest)
        else:
            self.loop.call_soon(self.updateCapabilities)

    def updateCapabilities(self):
        self.log.info('Updating capabilities')
        pass

    def sendCertificateRequest(self):
        """
        We compose a command interest with our public key info so the trust 
        anchor can sign us a certificate
        
        """

        defaultKey = self._identityStorage.getDefaultKeyNameForIdentity()
        self.log.debug("Found key: " + defaultKey.toUri())

        message = CertificateRequestMessage()
        message.command.keyType = self._identityStorage.getKeyType(defaultKey)
        message.command.keyBits = self._identityStorage.getKey(defaultKey).toRawStr()

        for component in range(defaultKey.size()):
            message.command.keyName.components.append(defaultKey.get(component).toEscapedString())

        paramComponent = ProtobufTlv.encode(message)

        interestName = Name(self._policyManager.getTrustRootIdentity()).append("certificateRequest").append(paramComponent)
        interest = Interest(interestName)
        interest.setInterestLifetimeMilliseconds(10000) # takes a tick to verify and sign
        self.face.makeCommandInterest(interest)

        self.log.debug("Certificate request: "+interest.getName().toUri())
        self.face.expressInterest(interest, self.onCertificateReceived, self.onCertificateTimeout)
   

    def onCertificateTimeout(self, interest):
        #give up?
        self.log.warn("Timed out trying to get certificate")
        pass


    def onCertificateReceived(self, interest, data):
        def processValidCertificate(interest):
            # if we were successful, the content of this data is a signed cert
            try:
                newCert = IdentityCertificate()
                newCert.wireDecode(data.getContent())
                self.log.debug("Received certificate:\n"+str(newCert))
                self._identityManager.addCertificate(newCert)
                self._identityManager.setDefaultCertificateForKey(newCert)
            except Exception as e:
                self.log.exception("Could not import new certificate", exc_info=True)
        def certificateValidationFailed(interest):
            self.log.warn("Certificate from controller is invalid!")

        self.keychain.verifyData(data, processValidCertificate, certificateValidationFailed)
        self.loop.call_later(5, self.updateCapabilities)

    def dispatchValidCommand(self, commandStr, interest, transport):
        if commandStr == 'setRGB':
            dataOut = self.handleLightingCommand(interest)
        else:
            dataOut = Data(interestName)
            dataOut.setContent("BAD COMMAND")
        self.keychain.sign(dataOut, self.keychain.getDefaultCertificateName())

        encodedData = dataOut.wireEncode()
        transport.send(encodedData.toBuffer())
        self.log.debug("Sent data named " + dataOut.getName().toUri())


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

