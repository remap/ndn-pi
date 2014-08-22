
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

from iot_identity_storage import IotIdentityStorage
from iot_policy_manager import IotPolicyManager

from commands.cert_request_pb2 import CertificateRequestMessage
from commands.update_capabilities_pb2 import UpdateCapabilitiesCommandMessage

from pyndn.util.boost_info_parser import BoostInfoParser
from pyndn.security.security_exception import SecurityException

try:
    import asyncio
except ImportError:
    import trollius as asyncio

class IotNode(object):
    """
    There is a built-in 'ping' command that takes precedence over user-defined
    ping (if any)
    """
    def __init__(self, configFilename):
        super(IotNode, self).__init__()

        self.config = BoostInfoParser()
        self.config.read(configFilename)

        self._identityStorage = IotIdentityStorage()
        self._identityManager = IdentityManager(self._identityStorage)
        self._policyManager = IotPolicyManager(self._identityStorage, configFilename)

        deviceSuffix = self.config["device/deviceName"][0].value
        self.prefix = Name(self._policyManager.getEnvironmentPrefix()).append(deviceSuffix)
        
        self._keyChain = KeyChain(self._identityManager, self._policyManager)
        self._identityStorage.setDefaultIdentity(self.prefix)

        self._registrationFailures = 0
        self._certificateTimeouts = 0
        self.prepareLogging()

        self._setupComplete = False
    
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
        self._loop = asyncio.get_event_loop()
        self._face = ThreadsafeFace(self._loop, '')
        self._face.setCommandSigningInfo(self._keyChain, self._keyChain.getDefaultCertificateName())
        self._face.registerPrefix(self.prefix, self.onCommandReceived, self.onRegisterFailed)
        self._keyChain.setFace(self._face)

        self._loop.call_soon(self.onStartup)

        self._isStopped = False
        self._face.stopWhen(lambda:self._isStopped)
        try:
            self._loop.run_forever()
        except Exception as e:
            self.log.error(str(e))
        finally:
            self.stop()

    def getLogger(self):
        return self.log

    def stop(self):
        self.log.info("Shutting down")
        self._loop.close()
        self._face.shutdown()

    def onStartup(self):
        if not self._policyManager.hasRootSignedCertificate():
            self._loop.call_soon(self.sendCertificateRequest)
        else:
            self._loop.call_soon(self.updateCapabilities)

    def setupComplete(self):
        """
        The user can use this entry point to search for other devices, set up
        control logic, etc
        """
        pass

    def onCapabilitiesAck(self, interest, data):
        self.log.debug('Received {}'.format(data.getName().toUri()))
        # todo: check it?
        if not self._setupComplete:
            self._setupComplete = True
            self._loop.call_soon(self.setupComplete)

    def onCapabilitiesTimeout(self, interest):
        #try again in 30s
        self.log.debug('Timeout waiting for capabilities update')
        self._loop.call_later(30, self.updateCapabilities)

    def updateCapabilities(self):
        """
        Send the controller a list of our commands.
        """ 
        fullCommandName = Name(self._policyManager.getTrustRootIdentity()
                ).append('updateCapabilities')
        capabilitiesMessage = UpdateCapabilitiesCommandMessage()
        try:
            allCommands = self.config["device/command"]
        except KeyError:
            pass # no commands
        else:
            for command in allCommands:
                commandName = Name(self.prefix).append(command["name"][0].value)
                capability = capabilitiesMessage.capabilities.add()
                for i in range(commandName.size()):
                    capability.commandPrefix.components.append(
                            str(commandName.get(i).getValue()))
                for node in command["keyword"]:
                    capability.keywords.append(node.value)
                try:
                    command["authorize"]
                    capability.needsSignature = True
                except KeyError:
                    pass

        encodedCapabilities = ProtobufTlv.encode(capabilitiesMessage)
        fullCommandName.append(encodedCapabilities)
        interest = Interest(fullCommandName)
        interest.setInterestLifetimeMilliseconds(3000)
        self._face.makeCommandInterest(interest)
        self._face.expressInterest(interest, self.onCapabilitiesAck, self.onCapabilitiesTimeout)
     
       
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
        self._face.makeCommandInterest(interest)

        self.log.debug("Certificate request: "+interest.getName().toUri())
        self._face.expressInterest(interest, self.onCertificateReceived, self.onCertificateTimeout)
   

    def onCertificateTimeout(self, interest):
        #give up?
        self.log.warn("Timed out trying to get certificate")
        if self._certificateTimeouts > 5:
            self.log.critical("Trust root cannot be reached, exiting")
            self._isStopped = True
        else:
            self._certificateTimeouts += 1
            self._loop.call_soon(self.sendCertificateRequest)
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

        self._keyChain.verifyData(data, processValidCertificate, certificateValidationFailed)
        self._loop.call_later(5, self.updateCapabilities)

    def sendData(self, data, transport, sign=True):
        if sign:
            self._keyChain.sign(data, self._keyChain.getDefaultCertificateName())
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
        certData = self._identityStorage.getCertificate(interest.getName())
        if certData is not None:
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
                    self._keyChain.verifyInterest(interest, 
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
            self._face.registerPrefix(self.prefix, self.onCommandReceived, self.onRegisterFailed)
        else:
            self.log.critical("Could not register device prefix, ABORTING")
            self._isStopped = True

    @staticmethod
    def getSerial():
        with open('/proc/cpuinfo') as f:
            for line in f:
                if line.startswith('Serial'):
                    return line.split(':')[1].strip()


