
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

from pyndn.util.boost_info_parser import BoostInfoParser
from iot_node import IotNode
from pyndn.security.security_exception import SecurityException

try:
    import asyncio
except ImportError:
    import trollius as asyncio

class IotController(IotNode):
    """
    The controller class has a few built-in commands:
        - listDevices: return the full network names of all attached devices
        - certificateRequest: takes public key information and returns name of
            new certificate
    """
    def __init__(self, configFilename):
        super(IotController, self).__init__(configFilename)

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


    def listAuthorizedDevices(self):
        return matchList


    def onCommandReceived(self, prefix, interest, transport, prefixId):
        # handle the listDevices and certificateRequest commands, else use
        # default behavior
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

            #tell the requester where to get it
            response = Data(interest.getName())
            if certData is not None:
                response.setContent(certData.wireEncode())
                response.getMetaInfo().setFreshnessPeriod(10000) # should be good even longer
            else:
                reponse.setContent("Denied")
            self.sendData(response, transport)
        else:
            super(IotController, self).onCommandReceived(prefix, interest, transport, prefixId)

    def onStartup(self):
        if not self._policyManager.hasRootSignedCertificate():
            #this is an ERROR - we are the root!
            self.log.critical("Controller has no certificate!")
            self.stop()

