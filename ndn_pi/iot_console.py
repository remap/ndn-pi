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

from __future__ import print_function

import logging

from pyndn import Name, Face, Interest, Data, ThreadsafeFace
from pyndn.util import Blob
from pyndn.security import KeyChain
from pyndn.encoding import ProtobufTlv
from pyndn.security.security_exception import SecurityException

from ndn_pi.security import IotIdentityStorage,IotPolicyManager, IotIdentityManager
from commands import CertificateRequestMessage, UpdateCapabilitiesCommandMessage, DeviceConfigurationMessage, DevicePairingInfoMessage

from collections import defaultdict, OrderedDict
import json
import base64

from dialog import Dialog
import logging 
try:
    import asyncio
except ImportError:
    import trollius as asyncio

# more Python 2+3 compatibility
try:
    input = raw_input
except NameError:
    pass

class IotConsole(object):
    """
    This uses the controller's credentials to provide a management interface
    to the user.
    It does not go through the security handshake (as it should be run on the
    same device as the controller) and so does not inherit from the BaseNode.
    """
    def __init__(self, networkName, nodeName):
        super(IotConsole, self).__init__()
        
        self.deviceSuffix = Name(nodeName)
        self.networkPrefix = Name(networkName)
        self.prefix = Name(self.networkPrefix).append(self.deviceSuffix)

        self._identityStorage = IotIdentityStorage()
        self._policyManager = IotPolicyManager(self._identityStorage)
        self._identityManager = IotIdentityManager(self._identityStorage)
        self._keyChain = KeyChain(self._identityManager, self._policyManager)

        self._identityStorage.setDefaultIdentity(self.prefix)

        self._policyManager.setEnvironmentPrefix(self.networkPrefix)
        self._policyManager.setTrustRootIdentity(self.prefix)
        self._policyManager.setDeviceIdentity(self.prefix)
        self._policyManager.updateTrustRules()

        self.foundCommands = {}
        
        # TODO: use xDialog in XWindows
        self.ui = Dialog(backtitle='NDN IoT User Console', height=18, width=78)

        trolliusLogger = logging.getLogger('trollius')
        trolliusLogger.addHandler(logging.StreamHandler())

    def start(self):
        """
        Start up the UI
        """
        self.loop = asyncio.get_event_loop()
        self.face = ThreadsafeFace(self.loop, '')

        controllerCertificateName = self._identityStorage.getDefaultCertificateNameForIdentity(self.prefix)
        self.face.setCommandSigningInfo(self._keyChain, controllerCertificateName)
        self._keyChain.setFace(self.face) # shouldn't be necessarym but doesn't hurt

        self._isStopped = False
        self.face.stopWhen(lambda:self._isStopped)

        self.loop.call_soon(self.displayMenu)
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)
            #self.log('Exception', e)
        finally:
            self._isStopped = True

    def stop(self):
        self._isStopped = True
        
#######
# GUI
#######

    def displayMenu(self):

        menuOptions = OrderedDict([('List network services',self.listCommands),
                                   ('Pair a device',self.pairDevice),
                                   ('Express interest',self.expressInterest),
                                   ('Quit',self.stop)
                       ])
        (retCode, retStr) = self.ui.mainMenu('Main Menu', 
                        menuOptions.keys()) 
                        

        if retCode == Dialog.DIALOG_ESC or retCode == Dialog.DIALOG_CANCEL:
           # TODO: ask if you're sure you want to quit
           self.stop()
        if retCode == Dialog.DIALOG_OK:
            menuOptions[retStr]()


#######
# List all commands
######
    def listCommands(self):
        self._requestDeviceList(self._showCommandList, self.displayMenu)

    def _requestDeviceList(self, successCallback, timeoutCallback):
        self.ui.alert('Requesting services list...', False)
        interestName = Name(self.prefix).append('listCommands')
        interest = Interest(interestName)
        interest.setInterestLifetimeMilliseconds(3000)
        #self.face.makeCommandInterest(interest)
        self.face.expressInterest(interest, 
            self._makeOnCommandListCallback(successCallback),
            self._makeOnCommandListTimeoutCallback(timeoutCallback))

    def _makeOnCommandListTimeoutCallback(self, callback):
        def onCommandListTimeout(interest):
            self.ui.alert('Timed out waiting for services list')
            self.loop.call_soon(callback)
        return onCommandListTimeout

    def _makeOnCommandListCallback(self, callback):
        def onCommandListReceived(interest, data):
            try:
                commandInfo = json.loads(str(data.getContent()))
            except:
                self.ui.alert('An error occured while reading the services list')
                self.loop.call_soon(self.displayMenu)
            else:
                self.foundCommands = commandInfo
                self.loop.call_soon(callback)
        return onCommandListReceived

    def _showCommandList(self):
       try:
            commandList = []
            for capability, commands in self.foundCommands.items():
                commandList.append('{}:'.format(capability))
                for info in commands:
                    signingStr = 'signed' if info['signed'] else 'unsigned'
                    commandList.append('\t{} ({})'.format(info['name'], signingStr))
            if len(commandList) == 0:
                # should not happen
                commandList = ['----NONE----']
            self.ui.menu('Available services', commandList, prefix='', extras=['--no-cancel']) 
       finally:
            self.loop.call_soon(self.displayMenu)

#######
# New device
######

    def pairDevice(self, serial='', pin='', newName=''):
        fields = [Dialog.FormField('Device serial', serial),
                  Dialog.FormField('PIN', pin),
                  Dialog.FormField('Device name', newName)]
        (retCode, retList) = self.ui.form('Device information', fields)
        if retCode == Dialog.DIALOG_OK:
            serial, pin, newName = retList
            if len(serial)==0 or len(pin)==0 or len(newName)==0:
                self.ui.alert('All fields are required')
                self.loop.call_soon(self.pairDevice, serial, pin, newName)
            else:
                try:
                    pinBytes = pin.decode('hex')
                except TypeError:
                    self.ui.alert('Pin is invalid')
                    self.loop.call_soon(self.pairDevice, serial, pin, newName)
                else:
                    self._addDeviceToNetwork(serial, newName, 
                pin.decode('hex'))
        elif retCode == Dialog.DIALOG_CANCEL or retCode == Dialog.DIALOG_ESC:
            self.loop.call_soon(self.displayMenu)

    def _addDeviceToNetwork(self, serial, suffix, pin):
        self.ui.alert('Sending pairing info to gateway...', False)
        # we must encrypt this so no one can see the pin!
        message = DevicePairingInfoMessage()
        message.info.deviceSuffix = suffix
        message.info.deviceSerial = serial
        message.info.devicePin = pin
        rawBytes = ProtobufTlv.encode(message)
        encryptedBytes = self._identityManager.encryptForIdentity(rawBytes, self.prefix)
        encodedBytes = base64.urlsafe_b64encode(str(encryptedBytes))
        interestName = Name(self.prefix).append('addDevice').append(encodedBytes)
        interest = Interest(interestName)
        # todo: have the controller register this console as a listener
        # and update it with pairing status
        interest.setInterestLifetimeMilliseconds(5000)
        self.face.makeCommandInterest(interest)

        self.face.expressInterest(interest, self._onAddDeviceResponse, 
            self._onAddDeviceTimeout)
        
    def _onAddDeviceResponse(self, interest, data):
        try:
            responseCode = int(str(data.getContent()))
            if responseCode == 202:
                self.ui.alert('Gateway received pairing info')
            else:
                self.ui.alert('Error encountered while sending pairing info')
        except:
            self.ui.alert('Exception encountered while decoding gateway reply')
        finally:
            self.loop.call_soon(self.displayMenu)

    def _onAddDeviceTimeout(self, interest):
        self.ui.alert('Timed out sending pairing info to gateway')
        self.loop.call_soon(self.displayMenu)
        

######
# Express interest
#####

   
    def expressInterest(self):
        if len(self.foundCommands) == 0:
            self._requestDeviceList(self._showInterestMenu, self._showInterestMenu)
        else:
            self.loop.call_soon(self._showInterestMenu)

    def _showInterestMenu(self):
        # display a menu of all available interests, on selection allow user to
        # (1) extend it
        # (2) send it signed/unsigned
        # NOTE: should it add custom ones to the list?
        commandSet = set()
        wildcard = '<Enter Interest Name>'
        try:
            for commands in self.foundCommands.values():
                commandSet.update([c['name'] for c in commands])
            commandList = list(commandSet)
            commandList.append(wildcard)
            (returnCode, returnStr) = self.ui.menu('Choose a command', 
                                        commandList, prefix=' ')
            if returnCode == Dialog.DIALOG_OK:
                if returnStr == wildcard:
                    returnStr = self.networkPrefix.toUri()
                self.loop.call_soon(self._expressCustomInterest, returnStr)
            else:
                self.loop.call_soon(self.displayMenu)
        except:
            self.loop.call_soon(self.displayMenu)

    def _expressCustomInterest(self, interestName):
        #TODO: make this a form, add timeout field
        try:
            handled = False
            (returnCode, returnStr) = self.ui.prompt('Send interest', 
                                        interestName,
                                        preExtra = ['--extra-button', 
                                                  '--extra-label', 'Signed',
                                                  '--ok-label', 'Unsigned'])
            if returnCode==Dialog.DIALOG_ESC or returnCode==Dialog.DIALOG_CANCEL:
                self.loop.call_soon(self.expressInterest)
            else:
                interestName = Name(returnStr)
                doSigned = (returnCode == Dialog.DIALOG_EXTRA)
                interest = Interest(interestName)
                interest.setInterestLifetimeMilliseconds(5000)
                interest.setChildSelector(1)
                interest.setMustBeFresh(True)
                if (doSigned):
                    self.face.makeCommandInterest(interest) 
                self.ui.alert('Waiting for response to {}'.format(interestName.toUri()), False) 
                self.face.expressInterest(interest, self.onDataReceived, self.onInterestTimeout)
        except:
            self.loop.call_soon(self.expressInterest)

    def onInterestTimeout(self, interest):
        try:
            self.ui.alert('Interest timed out:\n{}'.format(interest.getName().toUri()))
        except:
            self.ui.alert('Interest timed out')
        finally:
            self.loop.call_soon(self.expressInterest)

    def onDataReceived(self, interest, data):
        try:
            dataString = '{}\n\n'.format(data.getName().toUri())
            dataString +='Contents:\n{}'.format(repr(data.getContent().toRawStr()))
            self.ui.alert(dataString)
        except:
            self.ui.alert('Exception occured displaying data contents')
        finally:
            self.loop.call_soon(self.expressInterest)
    
if __name__ == '__main__':
    import sys
    try:
        with open('/tmp/ndn-iot/iot.conf') as nameFile:
            info = nameFile.readline()
            networkName, controllerName = info.strip().split()
    except IOError as e:
            if e.errno == 2:
                print ('Cannot connect to gateway. Please ensure that it is running.')
            else:
                print ('Unknown error {} encountered. Exiting...'.format(e.errno))
            sys.exit(1)

    n = IotConsole(networkName, controllerName)
    n.start()
