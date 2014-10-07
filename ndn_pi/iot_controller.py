from __future__ import print_function

import logging
import time
import sys
import os
import struct

from pyndn import Name, Face, Interest, Data, ThreadsafeFace
from pyndn.util import Blob
from pyndn.util.boost_info_parser import BoostInfoParser
from pyndn.security import KeyChain
from pyndn.security.certificate import IdentityCertificate, PublicKey, CertificateSubjectDescription
from pyndn.encoding import ProtobufTlv
from pyndn.security.security_exception import SecurityException

from base_node import BaseNode, Command

from commands import CertificateRequestMessage, UpdateCapabilitiesCommandMessage, DeviceConfigurationMessage
from security import HmacHelper, IotUserPasswordStore

from collections import defaultdict
import json

try:
    import asyncio
except ImportError:
    import trollius as asyncio

# more Python 2+3 compatibility
try:
    input = raw_input
except NameError:
    pass

#TODO: put a timeout on HMAC from initial configuration 
#TODO: on reconfiguration, delete user keys+certs
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
    def __init__(self, configFileName=None):
        super(IotController, self).__init__()
        
        if configFileName is None:
            configFileName = os.path.join(os.environ['HOME'], '.ndn', 'iot_gateway.conf')
        try:
            configReader = BoostInfoParser()
            configReader.read(configFileName)
            self.networkPrefix = Name(configReader['networkName'])
            self.deviceSuffix = Name('gateway')
            self.prefix = Name(self.networkPrefix).append(self.deviceSuffix)
        except:
            self.networkPrefix = None
            self.deviceSuffix = None
            self.prefix = Name(self.configurationPrefix)

            self._policyManager.setEnvironmentPrefix(self.networkPrefix)
            self._policyManager.setTrustRootIdentity(self.prefix)
            self._policyManager.setDeviceIdentity(self.prefix)
            self._policyManager.updateTrustRules()


        # the controller keeps a directory of capabilities->names
        self._directory = defaultdict(list)

        # keep track of who's still using HMACs
        # key is device serial, value is the HmacHelper
        self._hmacDevices = {}

        # our capabilities
        self._baseDirectory = {}

        # display the list command
        # TODO: should probably be 'listCommands'
        # 'listDevices' should show identity-serial mappings
        self._insertIntoCapabilities('listDevices', 'directory', False)

    def _insertIntoCapabilities(self, commandName, keyword, isSigned):
        newUri = Name(self.prefix).append(Name(commandName)).toUri()
        self._baseDirectory[keyword] = [{'signed':isSigned, 'name':newUri}]

    def beforeLoopStart(self):
        if self.networkPrefix is not None:
            self.onReboot()
        else:
            self.onFirstBoot()

#======================#
# Unconfigured Gateway #
#======================#

    def onFirstBoot(self):
        """
        This is called on the first boot after a 'device reset'
        """
        self.face.setCommandSigningInfo(self._keyChain, self.getDefaultCertificateName())
        pin = HmacHelper.generatePin() 
        self._hmacSigner = HmacHelper(pin)
        print('Waiting for user configuration....')
        print('Gateway serial:{}\nGateway PIN: {}'.format(self.getSerial(),
            str(pin).encode('hex'))) 
        self.face.registerPrefix(self.prefix, self.onConfigurationMessage, 
            self.onRegisterFailed)

    def onConfigurationMessage(self, prefix, interest, transport, prefixId):
        # we check to see if there is a component added to our prefix, with
        # a DeviceConfiguration message, signed with our HMAC
        interestName  = interest.getName()
        response = Data(interestName)
        
        if (interestName == prefix):
            # just searching for waiting gateways, return our serial
            serialAsComponent = Name.Component(self.getSerial())
            if not interest.getExclude().matches(serialAsComponent):
                response.getMetaInfo().setFreshnessPeriod(1000)
                response.setContent(self.getSerial())
                transport.send(response.wireEncode().buf())
            return
        elif (str(interestName[prefix.size()].getValue()) == self.getSerial()):
            success = False
            if self._hmacSigner.verifyInterest(interest):
                try:
                    message = DeviceConfigurationMessage()
                    ProtobufTlv.decode(message, interestName[prefix.size()+1].getValue())
                    networkNameComponents = message.configuration.networkPrefix.components
                    self.networkPrefix = Name('/'.join(networkNameComponents))
                    self.deviceSuffix = Name('gateway')
                    self.prefix = Name(self.networkPrefix).append(self.deviceSuffix)

                    response.setContent('202') 
                    success = True
                    
                except:
                    self.log.exception('Could not parse configuration message', exc_info=True)
                    response.setContent('400')
            else:
                response.setContent('401') 

            response.getMetaInfo().setFreshnessPeriod(2000)
            self._hmacSigner.signData(response)
            transport.send(response.wireEncode().buf())

            if success:
                self._policyManager.setEnvironmentPrefix(self.networkPrefix)
                self._policyManager.setTrustRootIdentity(self.prefix)
                self._policyManager.setDeviceIdentity(self.prefix)

                self._policyManager.updateTrustRules()

                self.configurePrefixId = prefixId
                self.face.removeRegisteredPrefix(self.configurePrefixId)

                # we do not save these settings to disk until a user has been
                # configured
                # save settings to disk for next boot
                configFileName = os.path.join(os.environ['HOME'], '.ndn', 'iot_gateway.conf')
                #self.saveSettingsToDisk(configFileName)
                self.loop.call_soon(self.onReboot)
    
    def saveSettingsToDisk(self, filename):
        config = BoostInfoParser()
        config.readPropertyList({'networkName': self.networkPrefix.toUri()})
        config.write(filename)


    def createCredentials(self):
        newKey = self._identityManager.generateRSAKeyPairAsDefault(
            self.prefix, isKsk=True)
        newCert = self._identityManager.selfSign(newKey)
        self._identityManager.addCertificateAsDefault(newCert)

#====================#
# Configured Gateway #
#====================#

    def onReboot(self):
        self._directory.update(self._baseDirectory)
        if not self._policyManager.hasRootSignedCertificate():
            # make one....
            self.log.warn('Generating controller certificate...')
            self.createCredentials()
        self.face.setCommandSigningInfo(self._keyChain, self.getDefaultCertificateName())
        self.face.registerPrefix(self.prefix, 
            self._onCommandReceived, self.onRegisterFailed)
        self.loop.call_soon(self.onStartup)


    # TODO: deviceSuffix will be replaced by deviceSerial
    def _addDeviceToNetwork(self, deviceSerial, newDeviceSuffix, pin):
        h = HmacHelper(pin)
        self._hmacDevices[deviceSerial] = h

        d = DeviceConfigurationMessage()

        for source, dest in [(self.networkPrefix, d.configuration.networkPrefix),
                             (self.deviceSuffix, d.configuration.controllerName),
                             (newDeviceSuffix, d.configuration.deviceSuffix)]:
            for i in range(source.size()):
                component = source.get(i)
                dest.components.append(component.getValue().toRawStr())

        interestName = Name('/localhop/configure').append(Name(deviceSerial))
        encodedParams = ProtobufTlv.encode(d)
        interestName.append(encodedParams)
        interest = Interest(interestName)
        h.signInterest(interest)

        self.face.expressInterest(interest, self._deviceAdditionResponse,
            self._deviceAdditionTimedOut)

    def _deviceAdditionTimedOut(self, interest):
        deviceSerial = str(interest.getName().get(2).getValue())
        self.log.warn("Timed out trying to configure device " + deviceSerial)
        # don't try again
        self._hmacDevices.pop(deviceSerial)

    def _deviceAdditionResponse(self, interest, data):
        status = data.getContent().toRawStr()
        deviceSerial = str(interest.getName().get(2).getValue())
        hmacChecker = self._hmacDevices[deviceSerial]
        if (hmacChecker.verifyData(data)): 
            self.log.info("Received {} from {}".format(status, deviceSerial))
        else:
            self.log.warn("Received invalid HMAC from {}".format(deviceSerial))
        
######
# Certificate signing
######
    

    def _handleCertificateRequest(self, interest, transport):
        """
        Extracts a public key name and key bits from a command interest name 
        component. Generates a certificate if the request is verifiable.

        This takes either RSA signed or HMAC'ed requests
        """
        signature = HmacHelper.extractInterestSignature(interest)
        signatureName = signature.getKeyLocator().getKeyName()
        
        def _onVerifiedCertRequest(interest, hmacSigner=None):
            # the interest parameter is needed for compatibility
            # with PyNDN's verification callback
            message = CertificateRequestMessage()
            commandParamsTlv = interest.getName()[self.prefix.size()+1]
            ProtobufTlv.decode(message, commandParamsTlv.getValue())

            response = Data(interest.getName())
            certData = None
            try:
                certData = self._createCertificateFromRequest(message)
            except SecurityException:
                self.log.warn('Could not create device certificate')
            else:
                self.log.info('Creating certificate for device {}'.format(signatureName.toUri()))

            if certData is not None:
                response.setContent(certData.wireEncode())
                response.getMetaInfo().setFreshnessPeriod(10000) # should be good even longer
            else:
                response.setContent("Denied")

            doKeySign = hmacSigner is None
            if not doKeySign:
                hmacSigner.signData(response)
            self.sendData(response, transport, doKeySign)


        if signatureName[0].toEscapedString() == 'localhop':
            deviceSerial = str(signatureName.get(-1).getValue())
            hmac = None
            try:
                hmac = self._hmacDevices[deviceSerial]
                if hmac.verifyInterest(interest):
                    # remove this hmac; another request will require a new pin
                    self._hmacDevices.pop(deviceSerial)
                    _onVerifiedCertRequest(interest, hmac)
            except KeyError:
                self.log.warn('Received certificate request for device with no registered key')
        else:
            self._keyChain.verifyInterest(interest, _onVerifiedCertRequest, self.verificationFailed)


    def _createCertificateFromRequest(self, message):
        """
        Generate an IdentityCertificate from the public key information given.
        """
        # TODO: Verify the certificate was actually signed with the private key
        # matching the public key we are issuing a cert for!!

        keyComponents = message.command.keyName.components
        keyName = Name("/".join(keyComponents))

        self.log.debug("Key name: " + keyName.toUri())

        if not self.networkPrefix.match(keyName):
            # we do not issue certs for keys outside of our network
            return None

        keyDer = Blob(message.command.keyBits)
        keyType = message.command.keyType

        try:
            self._identityStorage.addKey(keyName, keyType, keyDer)
        except SecurityException:
            # assume this is due to already existing?
            pass

        certificate = self._identityManager.generateCertificateForKey(keyName)

        self._keyChain.sign(certificate, self.getDefaultCertificateName())
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

        self.log.info('Updating capabilities for {}'.format(senderIdentity.toUri()))

        # get the params from the interest name
        messageComponent = interest.getName().get(self.prefix.size()+1)
        message = UpdateCapabilitiesCommandMessage()
        ProtobufTlv.decode(message, messageComponent.getValue())
        # we remove all the old capabilities for the sender
        tempDirectory = defaultdict(list)
        for keyword in self._directory:
            tempDirectory[keyword] = [cap for cap in self._directory[keyword] 
                    if not senderIdentity.match(Name(cap['name']))]

        # then we add the ones from the message
        for capability in message.capabilities:
            capabilityPrefix = Name()
            for component in capability.commandPrefix.components:
                capabilityPrefix.append(component)
            commandUri = capabilityPrefix.toUri()
            if not senderIdentity.match(capabilityPrefix):
                self.log.error("Node {} tried to register another prefix: {} - ignoring update".format(
                    senderIdentity.toUri(),commandUri))
            else:    
                for keyword in capability.keywords:
                    allUris = [info['name'] for info in tempDirectory[keyword]]
                    if capabilityPrefix not in allUris:
                        listing = {'signed':capability.needsSignature,
                                'name':commandUri}
                        tempDirectory[keyword].append(listing)
        self._directory= tempDirectory

    def _prepareCapabilitiesList(self, interestName):
        """
        Responds to a directory listing request with JSON
        """
        
        dataName = Name(interestName).append(Name.Component.fromNumber(int(time.time())))
        response = Data(dataName)

        response.setContent(json.dumps(self._directory))

        return response

#########
# User certificates
#########

    def _createUserCertificate(self, requestMessage):
        

#####
# Interest handling
####

    def _onCommandReceived(self, prefix, interest, transport, prefixId):
        """
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
                #TODO: delay ACK until we've checked the validity
                response = Data(interest.getName())
                response.setContent(str(time.time()))
                self.sendData(response, transport)
                self._updateDeviceCapabilities(interest)
            self._keyChain.verifyInterest(interest, 
                    onVerifiedCapabilities, self.verificationFailed)
        elif afterPrefix == "addUser":
            # also needs to be signed - either with hmac or with another user's
            # certificate
            pass
        else:
            response = Data(interest.getName())
            response.setContent("500")
            response.getMetaInfo().setFreshnessPeriod(1000)
            transport.send(response.wireEncode().buf())

    def onStartup(self):
        self.log.info('Controller is ready')

if __name__ == '__main__':
    n = IotController()
    n.start()
