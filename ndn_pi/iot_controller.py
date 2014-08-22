
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

from ndn_pi.commands.cert_request_pb2 import CertificateRequestMessage
from commands.update_capabilities_pb2 import UpdateCapabilitiesCommandMessage

from pyndn.util.boost_info_parser import BoostInfoParser
from ndn_pi.iot_node import IotNode
from pyndn.security.security_exception import SecurityException

from collections import defaultdict

try:
    import asyncio
except ImportError:
    import trollius as asyncio

class IotController(IotNode):
    """
    The controller class has a few built-in commands:
        - listDevices: return the names and capabilities of all attached devices
        - certificateRequest: takes public key information and returns name of
            new certificate
        - updateCapabilities: should be sent periodically from IotNodes to update their
           command lists
    """
    def __init__(self, configFilename):
        super(IotController, self).__init__(configFilename)

        # the controller keeps a directory of device prefix->capabilities
        self._directory = defaultdict(list)

    def createCertificateIfNecessary(self, commandParamsTlv):
        # look up the certificate and return its name if it exists
        # if not, generate one, install it,  and return its name

        # NOTE: should we always generate?
        message = CertificateRequestMessage()
        ProtobufTlv.decode(message, commandParamsTlv.getValue())

        keyComponents = message.command.keyName.components
        keyName = Name("/".join(keyComponents))

        self.log.debug("Key name: " + keyName.toUri())

        try:
            certificateName = self._identityStorage.getDefaultCertificateNameForKey(keyName)
            return self._identityStorage.getCertificate(certificateName)
        except SecurityException:
            if not self._policyManager.getEnvironmentPrefix().match(keyName):
                # we do not issue certs for keys outside of our network
                return None

            keyDer = Blob(message.command.keyBits)
            keyType = message.command.keyType
            publicKey = PublicKey(keyType, keyDer)
            certificate = self.createCertificateForKey(keyName, publicKey)
            self._identityStorage.addCertificate(certificate)
            return certificate

    def createCertificateForKey(self, keyName, publicKey):
        timestamp = (time.time())

        # TODO: put the 'KEY' part after the environment prefix to be responsible for cert delivery
        certificateName = keyName.getPrefix(-1).append('KEY').append(keyName.get(-1))
        certificateName.append("ID-CERT").append(Name.Component(struct.pack(">l", timestamp)))        

        certificate = IdentityCertificate(certificateName)
        # certificate expects time in milliseconds
        certificate.setNotBefore(timestamp)
        certificate.setNotAfter((timestamp + 30*86400)) # about a month

        certificate.setPublicKeyInfo(publicKey)

        # ndnsec likes to put the key name in a subject description
        sd = CertificateSubjectDescription("2.5.4.41", keyName.toUri())
        certificate.addSubjectDescription(sd)

        # sign this new certificate
        certificate.encode()
        self._keychain.sign(certificate, self._defaultCertName)

        return certificate

    def updateDeviceCapabilities(self, messageComponent):
        message = UpdateCapabilitiesCommandMessage()
        ProtobufTlv.decode(message, messageComponent)

        # we assume the sender is the one who signed the interest...
        signature = self._policyManager._extractSignature(interest)
        certificateName = signature.getKeyLocator().getKeyName()
        senderIdentity = IdentityCertificate.certificateNameToPublicKeyName(certificateName).getPrefix(-1)

        # we remove all the old capabilities for the sender
        for keyword in self._directory:
            self._directory[keyword] = [uri for uri in self._directory[keyword] 
                    if not senderIdentity.match(Name(uri))]

        # then we add the ones from the message
        for capability in message.capabilities:
            capabilityPrefix = Name()
            for component in capability.commandPrefix.components:
                capabilityPrefix.append(component)
            commandUri = capabilityPrefix.toUri()
            for keyword in capability.keywords:
                if capabilityPrefix not in self._directory[keyword]:
                    self._directory[keyword].add(capabilityPrefix.toUri())

        print self._directory



        

        


    def onCommandReceived(self, prefix, interest, transport, prefixId):
        # handle the built-in commands, else use default behavior
        afterPrefix = interest.getName().get(prefix.size()).toEscapedString()
        if afterPrefix == "listDevices":
            #compose device list
            self.log.debug("Received device list request")
            environmentName = self._policyManager.getEnvironmentPrefix()
            deviceList = '\n'.join(self._identityStorage.getIdentitiesMatching(environmentName))

            dataName = Name(interest.getName()).append(Name.Component.fromNumber(int(time.time())))
            response = Data(dataName)
            response.setContent(deviceList)
            self.sendData(response, transport)
        elif afterPrefix == "certificateRequest":
            #build and sign certificate
            self.log.debug("Received certificate request")
            paramsComponent = interest.getName().get(prefix.size()+1)
            certData = self.createCertificateIfNecessary(paramsComponent)

            response = Data(interest.getName())
            if certData is not None:
                response.setContent(certData.wireEncode())
                response.getMetaInfo().setFreshnessPeriod(10000) # should be good even longer
            else:
                reponse.setContent("Denied")
            self.sendData(response, transport)
        elif afterPrefix == "updateCapabilities":
            # needs to be signed!
            def onVerifiedCapabilities(interest):
                response = Data(interest.getName())
                response.setContent(str(time.time()))
                self.sendData(response, transport)
                messageComponent = interest.get(prefix.size()+1)
                self.updateDeviceCapabilities(messageComponent)
            self._keyChain.verifyInterest(interest, 
                    onVerifiedCapabilities, self.verificationFailed)
        else:
            super(IotController, self).onCommandReceived(prefix, interest, transport, prefixId)

    def onStartup(self):
        if not self._policyManager.hasRootSignedCertificate():
            #this is an ERROR - we are the root!
            self.log.critical("Controller has no certificate! Try running ndn-config.")
            self.stop()

