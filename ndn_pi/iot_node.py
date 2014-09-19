# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Adeola Bannis <thecodemaiden@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU General Public License is in the file COPYING.
import logging
import time
import sys

from pyndn import Name, Face, Interest, Data, ThreadsafeFace
from pyndn.security import KeyChain
from pyndn.security.identity import IdentityManager
from pyndn.security.policy import ConfigPolicyManager
from pyndn.security.certificate import IdentityCertificate
from pyndn.encoding import ProtobufTlv

from base_node import BaseNode, Command

from commands.cert_request_pb2 import CertificateRequestMessage
from commands.update_capabilities_pb2 import UpdateCapabilitiesCommandMessage
from commands.configure_device_pb2 import DeviceConfigurationMessage

from pyndn.util.boost_info_parser import BoostInfoParser
from pyndn.security.security_exception import SecurityException

from security.hmac_helper import HmacHelper



default_prefix = Name('/localhop/configure')

try:
    import asyncio
except ImportError:
    import trollius as asyncio

class IotNode(BaseNode):
    """
    This class must be subclassed in order to provide commands or allow user interaction.
    Any setup tasks needed by the user may be place in __init__ or setupComplete as needed.
    """
    def __init__(self):
        """
        Initialize the network and security settings for the node
        :param str configFilename: The path to the configuration file generated by ndn-config
        """
        super(IotNode, self).__init__()
        self.deviceSuffix = None

        self._commands = []        
        
        self.deviceSerial = self.getSerial()

        self.prefix = Name(default_prefix).append(self.deviceSerial)

        self._certificateTimeouts = 0

###
# Startup and shutdown
###
    def _createNewPin(self):
        pin = HmacHelper.generatePin() 
        self._hmacHandler = HmacHelper(pin.decode('hex'))
        return pin
        

    def beforeLoopStart(self):
        print("Serial: {}\nConfiguration PIN: {}".format(self.deviceSerial, self._createNewPin()))
        self.tempPrefixId = self.face.registerPrefix(self.prefix, 
            self._onConfigurationReceived, self.onRegisterFailed)
        print self.tempPrefixId

#####
# Pre-configuration flow
####

    def _extractNameFromField(self, protobufField):
        return Name('/'.join(protobufField.components))

    def _onConfigurationReceived(self, prefix, interest, transport, prefixId):
        # the interest we get here is signed by HMAC, let's verify it
        dataName = Name(interest.getName())
        replyData = Data(dataName)
        if (self._hmacHandler.verifyInterest(interest)):
            # we have a match! decode the controller's name
            configComponent = interest.getName().get(prefix.size())
            replyData.setContent('200')
            self._hmacHandler.signData(replyData, keyName=self.prefix)
            transport.send(replyData.wireEncode().buf())

            environmentConfig = DeviceConfigurationMessage()
            ProtobufTlv.decode(environmentConfig, configComponent.getValue()) 
            networkPrefix = self._extractNameFromField(environmentConfig.configuration.networkPrefix)
            controllerName = self._extractNameFromField(environmentConfig.configuration.controllerName)
            controllerName = Name(networkPrefix).append(controllerName)

            self._policyManager.setEnvironmentPrefix(networkPrefix)
            self._policyManager.setTrustRootIdentity(controllerName)

            self.deviceSuffix = self._extractNameFromField(environmentConfig.configuration.deviceSuffix)

            self._configureIdentity = Name(networkPrefix).append(self.deviceSuffix) 
            self._sendCertificateRequest(self._configureIdentity)
        #else, ignore!
            
    def _onConfigurationRegistrationFailure(self, prefix):
        #this is so bad... try a few times
        if self._registrationFailures < 5:
            self._registrationFailures += 1
            self.log.warn("Could not register {}, retry: {}/{}".format(prefix.toUri(), self._registrationFailures, 5)) 
            self.face.registerPrefix(self.prefix, self._onConfigurationReceived, 
                self._onConfigurationRegistrationFailure)
        else:
            self.log.critical("Could not register device prefix, ABORTING")
            self._isStopped = True

###
# Certificate signing requests
# On startup, if we don't have a certificate signed by the controller, we request one.
###
       
    def _sendCertificateRequest(self, keyIdentity):
        """
        We compose a command interest with our public key info so the controller
        can sign us a certificate that can be used with other nodes in the network.
        """

        #TODO: GENERATE A NEW PUBLIC/PRIVATE PAIR INSTEAD OF COPYING
        makeKey = False
        try:
            defaultKey = self._identityStorage.getDefaultKeyNameForIdentity(keyIdentity)
            newKeyName = defaultKey
        except SecurityException:
            defaultIdentity = self._keyChain.getDefaultIdentity()
            defaultKey = self._identityStorage.getDefaultKeyNameForIdentity(defaultIdentity)
            newKeyName = self._identityStorage.getNewKeyName(keyIdentity, True)
            makeKey = True
             
        self.log.debug("Found key: " + defaultKey.toUri()+ " renaming as: " + newKeyName.toUri())

        keyType = self._identityStorage.getKeyType(defaultKey)
        keyDer = self._identityStorage.getKey(defaultKey)

        if makeKey:
            try:
                privateDer = self._identityManager.getPrivateKey(defaultKey)
            except SecurityException:
                # XXX: is recovery impossible?
                pass
            else:
                try:
                    self._identityStorage.addKey(newKeyName, keyType, keyDer)
                    self._identityManager.addPrivateKey(newKeyName, privateDer)
                except SecurityException:
                    # TODO: key shouldn't exist...
                    pass

        message = CertificateRequestMessage()
        message.command.keyType = keyType
        message.command.keyBits = keyDer.toRawStr()

        for component in range(newKeyName.size()):
            message.command.keyName.components.append(newKeyName.get(component).toEscapedString())

        paramComponent = ProtobufTlv.encode(message)

        interestName = Name(self._policyManager.getTrustRootIdentity()).append("certificateRequest").append(paramComponent)
        print interestName.get(-1).toEscapedString()
        interest = Interest(interestName)
        interest.setInterestLifetimeMilliseconds(10000) # takes a tick to verify and sign
        self._hmacHandler.signInterest(interest, keyName=self.prefix)

        self.log.info("Sending certificate request to controller")
        self.log.debug("Certificate request: "+interest.getName().toUri())
        self.face.expressInterest(interest, self._onCertificateReceived, self._onCertificateTimeout)
   

    def _onCertificateTimeout(self, interest):
        #give up?
        self.log.warn("Timed out trying to get certificate")
        if self._certificateTimeouts > 5:
            self.log.critical("Trust root cannot be reached, exiting")
            self._isStopped = True
        else:
            self._certificateTimeouts += 1
            self.loop.call_soon(self._sendCertificateRequest, self._configureIdentity)
        pass


    def _processValidCertificate(self, data):
        # unpack the cert from the HMAC signed packet and verify
        try:
            newCert = IdentityCertificate()
            newCert.wireDecode(data.getContent())
            self.log.info("Received certificate from controller")
            self.log.debug(str(newCert))

            # NOTE: we download and install the root certificate without verifying it (!)
            # otherwise our policy manager will reject it.
            # we may need a static method on KeyChain to allow verifying before adding
    
            rootCertName = newCert.getSignature().getKeyLocator().getKeyName()
            # update trust rules so we trust the controller
            self._policyManager.setDeviceIdentity(self._configureIdentity) 
            self._policyManager.updateTrustRules()

            def onRootCertificateDownload(interest, data):
                try:
                    self._identityStorage.addCertificate(data)
                except SecurityException:
                    # already exists
                    pass
                self._keyChain.verifyData(newCert, self._finalizeCertificateDownload, self._certificateValidationFailed)

            def onRootCertificateTimeout(interest):
                # TODO: limit number of tries, then revert trust root + network prefix
                # reset salt, create new Hmac key
                self.face.expressInterest(rootCertName, onRootCertificateDownload, onRootCertificateTimeout)

            self.face.expressInterest(rootCertName, onRootCertificateDownload, onRootCertificateTimeout)

        except Exception as e:
            self.log.exception("Could not import new certificate", exc_info=True)
   
    def _finalizeCertificateDownload(self, newCert):
        try:
            self._identityManager.addCertificate(newCert)
        except SecurityException:
            pass # can't tell existing certificat from another error
        self._identityManager.setDefaultCertificateForKey(newCert)

        # unregister localhop prefix, register new prefix, change identity
        self.prefix = self._configureIdentity
        self._policyManager.setDeviceIdentity(self.prefix)

        self.face.setCommandCertificateName(self.getDefaultCertificateName())

        self.face.removeRegisteredPrefix(self.tempPrefixId)
        self.face.registerPrefix(self.prefix, self._onCommandReceived, self.onRegisterFailed)

        self.loop.call_later(5, self._updateCapabilities)

    def _certificateValidationFailed(self, data):
        self.log.error("Certificate from controller is invalid!")
        # remove trust info
        self._policyManager.removeTrustRules()

    def _onCertificateReceived(self, interest, data):
        # if we were successful, the content of this data is an HMAC
        # signed packet containing an encoded cert
        if self._hmacHandler.verifyData(data):
            self._processValidCertificate(data)
        else:
            self._certificateValidationFailed(data)



###
# Device capabilities
# On startup, tell the controller what types of commands are available
##

    def _onCapabilitiesAck(self, interest, data):
        self.log.debug('Received {}'.format(data.getName().toUri()))
        if not self._setupComplete:
            self._setupComplete = True
            self.log.info('Setup complete')
            self.loop.call_soon(self.setupComplete)

    def _onCapabilitiesTimeout(self, interest):
        #try again in 30s
        self.log.info('Timeout waiting for capabilities update')
        self.loop.call_later(30, self._updateCapabilities)

    def _updateCapabilities(self):
        """
        Send the controller a list of our commands.
        """ 
        fullCommandName = Name(self._policyManager.getTrustRootIdentity()
                ).append('updateCapabilities')
        capabilitiesMessage = UpdateCapabilitiesCommandMessage()

        for command in self._commands:
            commandName = Name(self.prefix).append(Name(command.suffix))
            capability = capabilitiesMessage.capabilities.add()
            for i in range(commandName.size()):
                capability.commandPrefix.components.append(
                        str(commandName.get(i).getValue()))

            for kw in command.keywords:
                capability.keywords.append(kw)

            capability.needsSignature = command.isSigned

        encodedCapabilities = ProtobufTlv.encode(capabilitiesMessage)
        fullCommandName.append(encodedCapabilities)
        interest = Interest(fullCommandName)
        interest.setInterestLifetimeMilliseconds(5000)
        self.face.makeCommandInterest(interest)
        signature = self._policyManager._extractSignature(interest)

        self.log.info("Sending capabilities to controller")
        self.face.expressInterest(interest, self._onCapabilitiesAck, self._onCapabilitiesTimeout)
     
###
# Interest handling
# Verification of and responses to incoming (command) interests
##
    def verificationFailed(self, dataOrInterest):
        """
        Called when verification of a data packet or command interest fails.
        :param pyndn.Data or pyndn.Interest: The packet that could not be verified
        """
        self.log.info("Received invalid" + dataOrInterest.getName().toUri())

    def _makeVerifiedCommandDispatch(self, function, transport):
        def onVerified(interest):
            self.log.info("Verified: " + interest.getName().toUri())
            responseData = function(interest)
            self.sendData(responseData, transport)
        return onVerified

    def unknownCommandResponse(self, interest):
        """
        Called when the node receives an interest where the handler is unknown or unimplemented.
        :return: the Data packet to return in case of unhandled interests. Return None
            to ignore and let the interest timeout or be handled by another node.
        :rtype: pyndn.Data
        """
        responseData = Data(Name(interest.getName()).append("unknown"))
        responseData.setContent("Unknown command name")
        responseData.getMetaInfo().setFreshnessPeriod(1000) # expire soon

        return responseData

    def _onCommandReceived(self, prefix, interest, transport, prefixId):

        # first off, we shouldn't be here if we have no configured environment
        # just let this interest time out
        if (self._policyManager.getTrustRootIdentity() is None or
                self._policyManager.getEnvironmentPrefix() is None):
            return

        # if this is a cert request, we can serve it from our store (if it exists)
        certData = self._identityStorage.getCertificate(interest.getName())
        if certData is not None:
            self.log.info("Serving certificate request")
            # if we sign the certificate, we lose the controller's signature!
            self.sendData(certData, transport, False)
            return

        # else we must look in our command list to see if this requires verification
        # we dispatch directly or after verification as necessary

        # now we look for the first command that matches in our config
        self.log.debug("Received {}".format(interest.getName().toUri()))
        
        for command in self._commands:
            fullCommandName = Name(self.prefix).append(Name(command.suffix))
            if fullCommandName.match(interest.getName()):
                dispatchFunc = command.function
                
                if not command.isSigned:
                    responseData = dispatchFunc(interest)
                    self.sendData(responseData, transport)
                else:
                    try:
                        self._keyChain.verifyInterest(interest, 
                                self._makeVerifiedCommandDispatch(dispatchFunc, transport),
                                self.verificationFailed)
                        return
                    except Exception as e:
                        self.log.exception("Exception while verifying command", exc_info=True)
                        self.verificationFailed(interest)
                        return
        #if we get here, just let it timeout
        return

#####
# Setup methods
####
    def addCommand(self, suffix, dispatchFunc, keywords=[], isSigned=True):
        """
        Install a command. When an interest is expressed for 
        /<node prefix>/<suffix>, dispatchFunc will be called with the interest
         name to get the reply data. 

        :param Name suffix: The command name. This will be appended to the node
            prefix.
        
        :param list keywords: A list of strings that can be used to look up this
            command in the controller's directory.
        
        :param function dispatchFunc: A function that is called when the 
            command is received. It must take an Interest argument and return a 
            Data object or None.

        :param boolean isSigned: Whether the command must be signed. If this is
            True and an unsigned command is received, it will be immediately
            rejected, and dispatchFunc will not be called.
        """
        if (suffix.size() == 0):
            raise RuntimError("Command suffix is empty")
        suffixUri = suffix.toUri()

        for command in self._commands:
            if (suffixUri == command.suffix):
                raise RuntimeError("Command is already registered")

        newCommand = Command(suffix=suffixUri, function=dispatchFunc, 
                keywords=tuple(keywords), isSigned=isSigned)

        self._commands.append(newCommand)

    def removeCommand(self, suffix):
        """
        Unregister a command. Does nothing if the command does not exist.

        :param Name suffix: The command name. 
        """
        suffixUri = suffix.ToUri()
        toRemove = None
        for command in self._commands:
            if (suffixUri == command.suffix):
                toRemove = command
                break
        if toRemove is not None:
            self._commands.remove(toRemove)


    def setupComplete(self):
        """
        Entry point for user-defined behavior. After this is called, the 
        certificates are in place and capabilities have been sent to the 
        controller. The node can now search for other devices, set up
        control logic, etc
        """
        pass

