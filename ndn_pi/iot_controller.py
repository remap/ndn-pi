
import logging
import time
import sys
import struct

from pyndn import Name, Face, Interest, Data, ThreadsafeFace
from pyndn.util import Blob
from pyndn.security import KeyChain
from pyndn.security.certificate import IdentityCertificate, PublicKey, CertificateSubjectDescription
from pyndn.encoding import ProtobufTlv

from base_node import BaseNode

from ndn_pi.commands.cert_request_pb2 import CertificateRequestMessage
from commands.update_capabilities_pb2 import UpdateCapabilitiesCommandMessage
from commands.configure_device_pb2 import DeviceConfigurationMessage

from pyndn.security.security_exception import SecurityException

from hmac_helper import HmacHelper

from collections import defaultdict
import json

try:
    import asyncio
except ImportError:
    import trollius as asyncio

class IotController(BaseNode):
    """
    The controller class has a few built-in commands:
        - listDevices: return the names and capabilities of all attached devices
        - certificateRequest: takes public key information and returns name of
            new certificate
        - updateCapabilities: should be sent periodically from IotNodes to update their
           command lists
        - addDevice: add a device based on HMAC
    It is unlikely that you will need to subclass this.
    """
    def __init__(self, configFilename):
        super(IotController, self).__init__(configFilename)
        
        self.deviceSuffix = Name(self.config["device/controllerName"][0].value)
        self.networkPrefix = Name(self.config["device/environmentPrefix"][0].value)
        self.prefix = Name(self.networkPrefix).append(self.deviceSuffix)
        self._identityStorage.setDefaultIdentity(self.prefix)
        
        # the controller keeps a directory of capabilities->names
        self._directory = defaultdict(list)

        # keep track of who's still using HMACs
        # key is device serial, value is the HmacHelper
        self._hmacDevices = {}

        # add the built-ins
        self._insertIntoCapabilities('listDevices', 'directory', False)
        self._insertIntoCapabilities('updateCapabilities', 'capabilities', True)

    def _insertIntoCapabilities(self, commandName, keyword, isSigned):
        """
        Add a capability that is not listed in the configuration.
        """
        newUri = Name(self.prefix).append(Name(commandName)).toUri()
        self._directory[keyword].append({'signed':isSigned, 'name':newUri})

    def _beforeLoopStart(self):
        self._face.registerPrefix(self.prefix, 
            self._onCommandReceived, self.onRegisterFailed)
        self._loop.call_soon(self.onStartup)


######
# Initial configuration
#######
    # TODO: deviceSuffix will be replaced by deviceSerial
    def _addDeviceToNetwork(self, deviceSerial, deviceSuffix, salt=''):
        saltedKey = deviceSerial+salt
        h = HmacHelper(saltedKey)
        self._hmacDevices[deviceSuffix] = h

        d = DeviceConfigurationMessage()
        for i in range(self.networkPrefix.size()):
            component = self.networkPrefix.get(i)
            d.configuration.networkPrefix.components.append(component.toEscapedString())
         
        for i in range(self.deviceSuffix.size()):
            component = self.deviceSuffix.get(i)
            d.configuration.controllerName.components.append(component.toEscapedString())
        interestName = Name('/localhop/configure').append(Name(deviceSuffix))
        encodedParams = ProtobufTlv.encode(d)
        interestName.append(encodedParams)
        interest = Interest(interestName)
        h.signInterest(interest)

        self._face.expressInterest(interest, self._deviceAdditionResponse,
            self._deviceAdditionTimedOut)

    def _deviceAdditionTimedOut(self, interest):
        deviceSuffix = str(interest.getName().get(2).getValue())
        self.log.warn("Timed out trying to configure device " + deviceSuffix)
        # don't try again
        self._hmacDevices.pop(deviceSuffix)

    def _deviceAdditionResponse(self, interest, data):
        status = data.getContent().toRawStr()
        deviceSuffix = str(interest.getName().get(2).getValue())
        hmacChecker = self._hmacDevices[deviceSuffix]
        if (hmacChecker.verifyData(data)): 
            self.log.info("Received {} from {}".format(status, deviceSuffix))
        else:
            self.log.warn("Received invalid HMAC from {}".format(deviceSuffix))
        

######
# Certificate signing
######

    def _handleCertificateRequest(self, interest, transport):
        """
        Extracts a public key name and key bits from a command interest name 
        component. Generates a certificate if the request is verifiable.

        This expects an HMAC signed interest.
        """
        commandParamsTlv = interest.getName().get(self.prefix.size()+1)

        message = CertificateRequestMessage()
        ProtobufTlv.decode(message, commandParamsTlv.getValue())

        keyComponents = message.command.keyName.components
        keyName = Name("/".join(keyComponents))
        identityName = keyName.getPrefix(-1)

        self.log.debug("Key name: " + keyName.toUri())

        suffixStart = self.networkPrefix.size()
        deviceSuffix = identityName.getSubName(suffixStart).toUri().strip('/')

        response = Data(interest.getName())
        certData = None
        hmac = None
        try:
            hmac = self._hmacDevices[deviceSuffix]
            if hmac.verifyInterest(interest):
                certData = self._createCertificateFromRequest(message)
        except KeyError, SecurityException:
            pass

        if certData is not None:
            response.setContent(certData.wireEncode())
            response.getMetaInfo().setFreshnessPeriod(10000) # should be good even longer
        else:
            response.setContent("Denied")
        if hmac is not None:
            hmac.signData(response)
        self.sendData(response, transport, False)

    def _createCertificateFromRequest(self, message):
        """
        Generate an IdentityCertificate from the public key information given.
        """
        # TODO: Verify the certificate was actually signed with the private key
        # matching the public key we are issuing a cert for!!
        keyComponents = message.command.keyName.components
        keyName = Name("/".join(keyComponents))

        if not self._policyManager.getEnvironmentPrefix().match(keyName):
            # we do not issue certs for keys outside of our network
            return None

        keyDer = Blob(message.command.keyBits)
        keyType = message.command.keyType
        publicKey = PublicKey(keyType, keyDer)

        timestamp = (time.time())

        # TODO: put the 'KEY' part after the environment prefix 
        # to be responsible for cert delivery
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
        # store it for later use + verification
        self._identityStorage.addCertificate(certificate)
        return certificate

######
# Device Capabilities
######

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

#####
# Interest handling
####

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
            self._handleCertificateRequest(interest, transport)

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
            response = Data(interest.getName())
            response.setContent("500")
            response.getMetaInfo().setFreshnessPeriod(1000)
            transport.send(response.wireEncode().buf())

    def onStartup(self):
        if not self._policyManager.hasRootSignedCertificate():
            #this is an ERROR - we are the root!
            self.log.critical("Controller has no certificate! Try running ndn-config with the configuration file.")
            self.stop()
        # for testing
        else:
            serial = '00000000534733c2'
            suffix = 'default'
            self._loop.call_later(5, self._addDeviceToNetwork, serial, suffix)
            


if __name__ == '__main__':
    try:
        fileName = sys.argv[1]
    except IndexError:
        fileName = '/usr/local/etc/ndn/iot/controller.conf'
      
    
    n = IotController(fileName)
    n.start()
