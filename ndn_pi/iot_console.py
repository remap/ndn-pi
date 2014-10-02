from __future__ import print_function

import logging
import time
import struct

from pyndn import Name, Interest, Data, ThreadsafeFace
from pyndn.util import Blob
from pyndn.security import KeyChain
from pyndn.security.certificate import IdentityCertificate
from pyndn.encoding import ProtobufTlv
from pyndn.security.security_exception import SecurityException

from commands import CertificateRequestMessage
from security import IotIdentityStorage, IotIdentityManager, IotUserKeyStorage, IotPolicyManager

from dialog import Dialog

from collections import namedtuple
import json

# more Python 2+3 compatibility
try:
    import asyncio
except ImportError:
    import trollius as asyncio

try:
    input = raw_input
except NameError:
    pass

UserCredentials = namedtuple('UserCredentials', 'identity keyKey')

class IotConsole(object):
    """
        This is the point of user interaction: you can pair devices, request a listing of
        paired and unpaired devices, and express interests manually.
    """
    def __init__(self):
        super(IotConsole, self).__init__()
        self._identityStorage = IotIdentityStorage()
        self._identityManager = IotIdentityManager(self._identityStorage)
        self._policyManager = IotPolicyManager(self._identityStorage)
        self._userKeyStorage = IotUserKeyStorage()

        self._keyChain = KeyChain(self._identityManager, self._policyManager)
        self.controllerName = None
        self.networkPrefix = None
        self.currentUser = None

        self.ui = Dialog(backtitle='NDN IoT User Console', height=18, width=78)
        self._prepareLogging()
        
    def chooseGateway(self):
        controllerName = ''
        networkName = ''
        while True:
            fields = [Dialog.FormField('Network prefix', networkName),
                      Dialog.FormField('Controller name', controllerName)]

            (retCode, retList) = self.ui.form('Connect to controller', fields)
            if retCode == Dialog.DIALOG_ESC or retCode == Dialog.DIALOG_CANCEL:
                break
            networkName = retList[0]
            controllerName = retList[1]
            
            if len(networkName) == 0 or len(controllerName) == 0:
                self.ui.alert('Please fill in all forms')
            else:
                self.networkPrefix = Name(networkName)
                self.controllerName = Name(networkName).append(controllerName)
                break
        
    def stop(self):
        self._isStopped = True
                
    def start(self):
        self.loop = asyncio.get_event_loop()
        self.face=ThreadsafeFace(self.loop,'')
        self._keyChain.setFace(self.face)

        # initial login
        if not(self._userKeyStorage.hasAnyUsers()):
            self.loop.call_soon(self.createFirstUser)
        else:
            self.loop.call_soon(self.doUserLogin)
        
        self._isStopped = False
        self.face.stopWhen(lambda:self._isStopped)
        
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.log.info('User exited')
        except Exception as e:
            self.log.exception(exc_info=True)
        finally:
            self._isStopped = True
        
    def runMainMenu(self):
        self.ui.alert('Hi!')

##
# Logging
##
    def _prepareLogging(self):
        self.log = logging.getLogger(str(self.__class__))
        self.log.setLevel(logging.DEBUG)
        logFormat = "%(asctime)-15s %(name)-20s %(funcName)-20s (%(levelname)-8s):\n\t%(message)s"
        self._console = logging.StreamHandler()
        self._console.setFormatter(logging.Formatter(logFormat))
        self._console.setLevel(logging.WARN)
        # without this, a lot of ThreadsafeFace errors get swallowed up
        logging.getLogger("trollius").addHandler(self._console)
        self.log.addHandler(self._console)

    def setLogLevel(self, level):
        """
        Set the log level that will be output to standard error
        :param level: A log level constant defined in the logging module (e.g. logging.INFO) 
        """
        self._console.setLevel(level)

########
# Login
########

    def doUserLogin(self):
        userName=''
        password=''
        controllerName = None
        try:
            while len(password) == 0:
                while len(userName) == 0:
                    userName = input('User name: ')
                password = getpass('Password: ')
            userIdentity = Name(self.networkPrefix).append('user').append(userName)
            userKey = self._userKeyStorage.getUserKey(userIdentity, password)
            if userKey.toRawStr() is None:
                print('Incorrect user name or password.\n')
                self.loop.call_soon(self.doUserLogin)
            else:
                self.currentUser = UserCredentials(userIdentity.toUri(), userKey)
                self.loop.call_soon(self.beginInputLoop)
            
        except KeyboardInterrupt: 
            print('Cannot run without user account.')
            self.stop()

    def beginInputLoop(self):
        # begin taking add requests
        if self.controllerName is None:
            self.chooseGateway()
        self._policyManager.setTrustRootIdentity(self.controllerName)
        self._policyManager.setEnvironmentPrefix(self.networkPrefix)
        self._policyManager.se
            
        self.loop.call_soon(self.displayMenu)

    def requestUserCertificate(self, userIdentity):
        if self._controllerName is None:
            self.chooseGateway()

    def createFirstUser(self):
        greeting = "It looks like this is the first time you are running the "
        greeting +=" NDN-IoT console. Please create a user name and password "
        greeting +=" for configuring the network.\n"

        self.ui.alert(greeting)
        #ignore the user response for now 
        created = self.createUser()
        if not created:
            print('Cannot run without user account.')
            self.stop()
        else:
            self.beginInputLoop()

    def createUser(self):
        created = False
        while True:
            userName=''
            formFields = [Dialog.FormField('User name', userName),
                          Dialog.FormField('Password', isPassword=True),
                          Dialog.FormField('Confirm password', isPassword=True)]
            retCode, retList = self.ui.form('New User', formFields)
            if retCode == Dialog.DIALOG_ESC or retCode == Dialog.DIALOG_CANCEL:
                self.ui.alert('User creation aborted')
                break
            userName = retList[0]
            
            if len(retList[0]) == 0 or len(retList[1]) == 0:
                self.ui.alert('Please fill in all fields')
            elif retList[1] != retList[2]:
                self.ui.alert('Passwords do not match')
            else:
                userName = retList[0]
                userPass = retList[1]
                userIdentity = Name(self.networkPrefix).append('user').append(userName)
                userKeyName = self._identityStorage.getNewKeyName(userIdentity, True)
                
                self.ui.alert('Generating network credentials...', False)
                #publicKey, privateKey = self._identityManager._getNewKeyBits(2048)
                #self._identityStorage.addKey(userKeyName, KeyType.RSA, publicKey)
                #self._userKeyStorage.saveUserKey(userIdentity, privateKey, userPass)

                self.ui.alert('Done! User {} created'.format(userName))
                created = True
                break
        return created
        
######
# User interaction
######

    def displayMenu(self):
        menuStr = "\n"
        menuStr += "P)air a new device with serial and PIN\n"
        menuStr += "D)irectory listing\n"
        menuStr += "E)xpress an interest\n"
        menuStr += "Q)uit\n"

        print(menuStr)
        print ("> ", end="")
        

    def listDevices(self):
        menuStr = ''
        for capability, commands in self._directory.items():
            menuStr += '{}:\n'.format(capability)
            for info in commands:
                signingStr = 'signed' if info['signed'] else 'unsigned'
                menuStr += '\t{} ({})\n'.format(info['name'], signingStr)
        print(menuStr)
        self.loop.call_soon(self.displayMenu)

    def onInterestTimeout(self, interest):
        print('Interest timed out: {}'.interest.getName().toUri())

    def onDataReceived(self, interest, data):
        print('Received data named: {}'.format(data.getName().toUri()))
        print('Contents:\n{}'.format(data.getContent().toRawStr()))
    
    def expressInterest(self):
        try:
            interestName = input('Interest name: ')
            if len(interestName):
                toSign = input('Signed? (y/N): ').upper().startswith('Y')
                interest = Interest(Name(interestName))
                interest.setInterestLifetimeMilliseconds(5000)
                interest.setChildSelector(1)
                if (toSign):
                    self.face.makeCommandInterest(interest) 
                self.face.expressInterest(interest, self.onDataReceived, self.onInterestTimeout)
            else:
                print("Aborted")
        except KeyboardInterrupt:
                print("Aborted")
        finally:
                self.loop.call_soon(self.displayMenu)

    def beginPairing(self):
        try:
            deviceSerial = input('Device serial: ') 
            devicePin = input('PIN: ')
            deviceSuffix = input('Node name: ')
        except KeyboardInterrupt:
               print('Pairing attempt aborted')
        else:
            if len(deviceSerial) and len(devicePin) and len(deviceSuffix):
                self._addDeviceToNetwork(deviceSerial, Name(deviceSuffix), 
                    devicePin.decode('hex'))
            else:
               print('Pairing attempt aborted')
        finally:
            self.loop.call_soon(self.displayMenu)

    def handleUserInput(self):
        inputStr = stdin.readline().upper()
        if inputStr.startswith('D'):
            self.listDevices()
        elif inputStr.startswith('P'):
            self.beginPairing()
        elif inputStr.startswith('E'):
            self.expressInterest()
        elif inputStr.startswith('Q'):
            self.stop()
        else:
            self.loop.call_soon(self.displayMenu)
            

#####
# Certificate things
#####
    # taken almost straight from IotNode...
    def _sendCertificateRequest(self, keyIdentity):
        """
        We compose a command interest with our public key info so the controller
        can sign us a certificate that can be used with other nodes in the network.
        """

        keyName = self._identityStorage.getDefaultKeyNameForIdentity(keyIdentity)

        keyType = self._identityStorage.getKeyType(keyName)
        keyDer = self._identityStorage.getKey(keyName)

        message = CertificateRequestMessage()
        message.command.keyType = keyType
        message.command.keyBits = keyDer.toRawStr()

        for component in range(newKeyName.size()):
            message.command.keyName.components.append(keyName.get(component).toEscapedString())

        paramComponent = ProtobufTlv.encode(message)

        interestName = Name(self._controllerName).append("certificateRequest").append(paramComponent)
        interest = Interest(interestName)
        interest.setInterestLifetimeMilliseconds(10000) # takes a tick to verify and sign
        

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

if __name__ == '__main__':
    n = IotConsole()
    n.start()
