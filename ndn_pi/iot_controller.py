
import logging
import time
import sys
import struct

from pyndn import Name, Face, Interest, Data, ThreadsafeFace
from pyndn.util import Blob
from pyndn.security import KeyChain
from pyndn.security.identity import IdentityManager
from pyndn.security.policy import ConfigPolicyManager
from pyndn.security.certificate import IdentityCertificate, PublicKey, CertificateSubjectDescription
from pyndn.encoding import ProtobufTlv

from iot_identity_storage import IotIdentityStorage
from iot_policy_manager import IotPolicyManager

from ndn_pi.commands.cert_request_pb2 import CertificateRequestMessage
from commands.update_capabilities_pb2 import UpdateCapabilitiesCommandMessage

from pyndn.util.boost_info_parser import BoostInfoParser
from ndn_pi.iot_node import IotNode
from pyndn.security.security_exception import SecurityException

from collections import defaultdict
import json

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
    It is unlikely that you will need to subclass this node type.
    """
    def __init__(self, configFilename):
        super(IotController, self).__init__(configFilename)

        # the controller keeps a directory of capabilities->names
        self._directory = defaultdict(list)

        #add the built-ins
        self._insertIntoCapabilities('listDevices', 'directory', False)
        self._insertIntoCapabilities('updateCapabilities', 'capabilities', True)
        self._insertIntoCapabilities('certificateRequest', 'certificate', False)

    def _insertIntoCapabilities(self, commandName, keyword, isSigned):
        """
        Add a capability that is not listed in the configuration.
        """
        newUri = Name(self.prefix).append(Name(commandName)).toUri()
        self._directory[keyword].append({'signed':isSigned, 'name':newUri})

    def _createCertificateIfNecessary(self, commandParamsTlv):
        """
        Extracts a public key name and key bits from a command interest name component.
        Look up the certificate corresponding to the key and return its full network 
        name if it exists. If not, generate one, install it,  and return its name.
        """
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
            certificate = self._createCertificateForKey(keyName, publicKey)
            self._identityStorage.addCertificate(certificate)
            return certificate

    def _createCertificateForKey(self, keyName, publicKey):
        """
        Generate an IdentityCertificate from the public key information given.
        """
        timestamp = (time.time())

        # TODO: put the 'KEY' part after the environment prefix to be responsible for cert delivery
        certificateName = keyName.getPrefix(-1).append('KEY').append(keyName.get(-1))
        certificateName.append("ID-CERT").append(Name.Component(struct.pack(">l", timestamp)))        

        certificate = IdentityCertificate(certificateName)
        # certificate expects time in milliseconds
        certificate.setNotBefore(timestamp*1000)
        certificate.setNotAfter((timestamp*1000 + 30*86400)) # about a month

        certificate.setPublicKeyInfo(publicKey)

        # ndnsec likes to put the key name in a subject description
        sd = CertificateSubjectDescription("2.5.4.41", keyName.toUri())
        certificate.addSubjectDescription(sd)

        # sign this new certificate
        certificate.encode()
        self._keyChain.sign(certificate, self._keyChain.getDefaultCertificateName())

        return certificate

    def _updateDeviceCapabilities(self, interest):
        """
        Take the received capabilities update interest and update our directory listings.
        """
        # we assume the sender is the one who signed the interest...
        signature = self._policyManager._extractSignature(interest)
        certificateName = signature.getKeyLocator().getKeyName()
        senderIdentity = IdentityCertificate.certificateNameToPublicKeyName(certificateName).getPrefix(-1)

        # get the params from the interest name
        messageComponent = interest.getName().get(self.prefix.size()+1)
        message = UpdateCapabilitiesCommandMessage()
        ProtobufTlv.decode(message, messageComponent.getValue())
        # we remove all the old capabilities for the sender
        for keyword in self._directory:
            self._directory[keyword] = [cap for cap in self._directory[keyword] 
                    if not senderIdentity.match(Name(cap['name']))]

        # then we add the ones from the message
        for capability in message.capabilities:
            capabilityPrefix = Name()
            for component in capability.commandPrefix.components:
                capabilityPrefix.append(component)
            commandUri = capabilityPrefix.toUri()
            if not senderIdentity.match(capabilityPrefix):
                self.log.warn("Node {} tried to register another prefix: {}".format(
                    senderIdentity.toUri(),commandUri))
            for keyword in capability.keywords:
                if capabilityPrefix not in self._directory[keyword]:
                    listing = {'signed':capability.needsSignature,
                            'name':capabilityPrefix.toUri()}
                    self._directory[keyword].append(listing)

    def _prepareCapabilitiesList(self, interestName):
        """
        Responds to a directory listing request with JSON
        """
        
        try:
            suffix = interestName.get(self.prefix.size()+1).toEscapedString()
        except IndexError:
            suffix = None

        dataName = Name(interestName).append(Name.Component.fromNumber(int(time.time())))
        response = Data(dataName)
        if suffix is None:
            toJsonify = self._directory
        else:
            toJsonify = self._directory[suffix]

        response.setContent(json.dumps(toJsonify))

        return response

    def _onCommandReceived(self, prefix, interest, transport, prefixId):
        """
        Does not handle commands set in ndn-config, only the built in commands.
        """
        interestName = interest.getName()

        #if it is a certificate name, serve the certificate
        foundCert = self._identityStorage.getCertificate(interestName)
        if foundCert is not None:
            self.log.debug("Serving certificate request")
            transport.send(foundCert.wireEncode().buf())
            return

        afterPrefix = interestName.get(prefix.size()).toEscapedString()
        if afterPrefix == "listDevices":
            #compose device list
            self.log.debug("Received device list request")
            response = self._prepareCapabilitiesList(interestName)
            self.sendData(response, transport)
        elif afterPrefix == "certificateRequest":
            #build and sign certificate
            self.log.debug("Received certificate request")
            paramsComponent = interest.getName().get(prefix.size()+1)
            certData = self._createCertificateIfNecessary(paramsComponent)

            response = Data(interest.getName())
            if certData is not None:
                response.setContent(certData.wireEncode())
                response.getMetaInfo().setFreshnessPeriod(10000) # should be good even longer
            else:
                reponse.setContent("Denied")
            self.sendData(response, transport)
        elif afterPrefix == "updateCapabilities":
            # needs to be signed!
            self.log.debug("Received capabilities update")
            def onVerifiedCapabilities(interest):
                response = Data(interest.getName())
                response.setContent(str(time.time()))
                self.sendData(response, transport)
                self._updateDeviceCapabilities(interest)
            self._keyChain.verifyInterest(interest, 
                    onVerifiedCapabilities, self.verificationFailed)
        else:
            response = super(IotController, self).unkownCommandResponse()
            transport.send(response.wireEncode().buf())

    def onStartup(self):
        if not self._policyManager.hasRootSignedCertificate():
            #this is an ERROR - we are the root!
            self.log.critical("Controller has no certificate! Try running ndn-config with the configuration file.")
            self.stop()


if __name__ == '__main__':
    try:
        fileName = sys.argv[1]
    except IndexError:
        fileName = '/usr/local/etc/ndn/iot/controller.conf'
      
    
    n = IotController(fileName)
    n.start()
