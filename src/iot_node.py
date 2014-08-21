
import logging
import time
import sys

from pyndn import Name, Face, Interest, Data, ThreadsafeFace
from pyndn.security import KeyChain
from pyndn.security.identity import IdentityManager
from pyndn.security.policy import ConfigPolicyManager
from pyndn.security.certificate import IdentityCertificate
from pyndn.encoding import ProtobufTlv

from iot_identity_storage import IotIdentityStorage
from iot_policy_manager import IotPolicyManager

from commands.cert_request_pb2 import CertificateRequestMessage
#from commands.list_capabilities_pb2 import ListCapabilitiesMessage

from pyndn.util.boost_info_parser import BoostInfoParser
from pyndn.security.security_exception import SecurityException

try:
    import asyncio
except ImportError:
    import trollius as asyncio

class IotNode(object):
    def __init__(self, configFilename):
        super(IotNode, self).__init__()

        self.config = BoostInfoParser()
        self.config.read(configFilename)

        self._identityStorage = IotIdentityStorage()
        self._identityManager = IdentityManager(self._identityStorage)
        self._policyManager = IotPolicyManager(self._identityStorage, configFilename)

        deviceSuffix = self.config["device/deviceName"][0].value
        self.prefix = Name(self._policyManager.getEnvironmentPrefix()).append(deviceSuffix)
        
        self.keychain = KeyChain(self._identityManager, self._policyManager)
        self._identityStorage.setDefaultIdentity(self.prefix)

        self._registrationFailures = 0
        self._certificateTimeouts = 0
        self.prepareLogging()
    
    def prepareLogging(self):
        self.log = logging.getLogger(str(self.__class__))
        self.log.setLevel(logging.DEBUG)
        logFormat = "%(asctime)-15s %(name)-20s %(funcName)-20s (%(levelname)-8s):\n\t%(message)s"
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter(logFormat))
        sh.setLevel(logging.DEBUG)
        # without this, a lot of ThreadsafeFace errors get swallowed up
        logging.getLogger("trollius").addHandler(sh)
        self.log.addHandler(sh)

    def start(self):
        self.loop = asyncio.get_event_loop()
        self.face = ThreadsafeFace(self.loop, '')
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
        self.log.info("Shutting down")
        self.loop.close()
        self.face.shutdown()

    def onStartup(self):
        if not self._policyManager.hasRootSignedCertificate():
            self.loop.call_soon(self.sendCertificateRequest)
        else:
            self.loop.call_soon(self.updateCapabilities)

    def updateCapabilities(self):
        fullCommandName = Name(self._policyManager.getTrustRootIdentity()).append('listDevices')
        def onListReceived(interest, data):
            print "Device list:\n\t{}".format(data.getContent().toRawStr())
        def onListTimeout(interest):
            print "Timed out on device list"

        self.face.expressInterest(Name(fullCommandName), onListReceived, onListTimeout)
        

    def sendCertificateRequest(self):
        """
        We compose a command interest with our public key info so the trust 
        anchor can sign us a certificate
        
        """

        defaultKey = self._identityStorage.getDefaultKeyNameForIdentity(self.prefix)
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
        if self._certificateTimeouts > 5:
            self.log.critical("Trust root cannot be reached, exiting")
            self._isStopped = True
        else:
            self._certificateTimeouts += 1
            self.loop.call_soon(self.sendCertificateRequest)
        pass


    def onCertificateReceived(self, interest, data):
        def processValidCertificate(interest):
            # if we were successful, the content of this data is a signed cert
            try:
                newCert = IdentityCertificate()
                newCert.wireDecode(data.getContent())
                self.log.debug("Received certificate:\n"+str(newCert))
                try:
                    self._identityManager.addCertificate(newCert)
                except SecurityException:
                    pass # can't tell existing certificat from another error
                self._identityManager.setDefaultCertificateForKey(newCert)
            except Exception as e:
                self.log.exception("Could not import new certificate", exc_info=True)
        def certificateValidationFailed(interest):
            self.log.warn("Certificate from controller is invalid!")

        self.keychain.verifyData(data, processValidCertificate, certificateValidationFailed)
        self.loop.call_later(5, self.updateCapabilities)

    def sendData(self, data, transport, sign=True):
        if sign:
            self.keychain.sign(data, self.keychain.getDefaultCertificateName())
        transport.send(data.wireEncode().buf())

    def verificationFailed(dataOrInterest):
        self.log.info("Received invalid" + dataOrInterest.getName().toUri())

    def makeVerifiedCommandDispatch(function, transport):
        def onVerified(interest):
            self.log.info("Verified: " + interest.getName().toUri())
            responseData = function(interest)
            self.sendData(responseData, transport)
        return onVerified

    def onCommandReceived(self, prefix, interest, transport, prefixId):
        # if this is a cert request, we can serve it from our store (if it exists)
        # else we must look in our command list to see if this requires verification
        # we dispatch directly or after verification as necessary
        try:
            certData = self._identityStorage.getCertificate(interest.getName())
        except:
            pass
        else:
            # if we sign the certificate, we lose the controller's signature!
            self.sendData(certData, transport, False)
            return

        # what to do when we can't serve a request
        def onUnknownCommand():
            # send an error message
            responseData = Data(Name(interest.getName()).append("unknown"))
            responseData.setContent("Unknown command name")
            responseData.getMetaInfo().setFreshnessPeriod(1000) # expire soon
            self.sendData(responseData, transport)

        # now we look for the first command that matches in our config
        allCommands = self.config["device/command"]
        for command in allCommands:
            fullCommandName = Name(self.prefix).append(command["name"][0].value)
            if fullCommandName.match(interest.getName()):
                dispatchFunctionName = command["functionName"][0].value
                try:
                    func = self.__getattribute__(dispatchFunctionName)
                except AttributeError:
                    # command not implemented
                    onUnknownCommand()
                    return
            
                try:
                    command["authorize"][0]
                except KeyError:
                    # no need to authorize, just run
                    responseData = func(interest)
                    self.sendData(responseData, transport)
                    return 
            
                # requires verification
                try:
                    self.keychain.verifyInterest(interest, 
                            self.makeVerifiedCommandDispatch(func, transport),
                            self.verificationFailed)
                    # if verification fails, it will time out
                    return
                except Exception as e:
                    self.log.exception("Exception while verifying command", exc_info=True)
                    onUnknownCommand()
                    return
        #if we get here, we really don't know this command
        onUnknownCommand()
        return
                

    def onRegisterFailed(self, prefix):
        self.log.error("Could not register " + prefix.toUri())
        if self._registrationFailures < 5:
            self._registrationFailures += 1
            self.log.error("Retry: {}/{}".format(self._registrationFailures, 5)) 
            self.face.registerPrefix(self.prefix, self.onCommandReceived, self.onRegisterFailed)
        else:
            self.log.critical("Could not register device prefix, ABORTING")
            self._isStopped = True


