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
from ui_task import UiTask
from pyndn import Name, Data, Interest, Exclude
from pyndn.util import Blob
from pyndn.encoding import ProtobufTlv
from dialog import Dialog
from commands import DeviceConfigurationMessage
from ndn_pi.security import HmacHelper

class ConfigureGatewayTask(UiTask):
    def __init__(self, face, uiController, eventLoop, context, topContext=None):
        super(ConfigureGatewayTask, self).__init__(uiController, eventLoop,
                 context, topContext)
        self.face = face
        self.maxUpdates = 5
        self.timerTask = None
        self.updates = 0
        self.gatewayList = []
        self.refreshFinished = False
        # serial, network name
        self.newNetworkName = None
        self.completionCallback = None

    def onSuccess(self):
        self.loop.call_soon(self.completionCallback, self.newNetworkName)

#####
# Refresh the list of waiting gateways
####
    def showRefreshProgress(self):
        if self.updates < self.maxUpdates:
            self.updates += 1
            self.ui.gauge('Looking for gateways...', self.updates*100/self.maxUpdates)
            self.timerTask = self.loop.call_later(1, self.showRefreshProgress)
        else:
            self.finishRefresh()

    def finishRefresh(self):
        try:
            self.timerTask.cancel()
        finally:
            if not (self.refreshFinished):
                self.ui.gauge('Done', 100)
                self.refreshFinished = True
                self.loop.call_soon(self.showMenu)

    def refreshGatewayList(self): 
        self.updates = 0
        self.gatewayList = []
        self.refreshFinished = False

        i = Interest(Name('/localhop/configure'))
        i.setExclude(Exclude())
        i.setInterestLifetimeMilliseconds(2000)
        i.setMustBeFresh(True)


        self.ui.gauge( 'Looking for gateways', 0)
        self.face.expressInterest(i, self._onGWQueryResponse, self._onGWQueryTimeout)
        self.timerTask = self.loop.call_later(1, self.showRefreshProgress)

    def _onGWQueryResponse(self, interest, data):
        foundSerial = str(data.getContent())
        if foundSerial not in self.gatewayList:
            self.gatewayList.append(foundSerial)

        i = Interest(interest)
        i.getExclude().appendComponent(Name.Component(foundSerial))
        self.face.expressInterest(i, self._onGWQueryResponse, self._onGWQueryTimeout)

    def _onGWQueryTimeout(self, interest):
        # assume we have excluded all reachable, waiting gateways
        self.finishRefresh()   

#####
# Configure chosen gateway
# Could make this a separate task, but not going to
#####
    def _onGatewayConfigureResponse(self, interest, data):
        response = str(data.getContent())
        success = False
        try:
            if int(response) == 202:
                success = True
        finally:
            pass
        if success:
            self.ui.alert('Configuration complete')
            self.onSuccess()
        else:
            self.ui.alert('Gateway returned error "{}"'.format(response))
            self.popAll()

    def _onGatewayConfigurationTimeout(self, interest, data):
        errorStr = "Timed out trying to connect to gateway.\n"
        errorStr +="Please check that the gateway is running and waiting for \
            configuration."
        self.alert(errorStr)
        self.newNetworkName = None
        self.loop.call_soon(self.refreshGatewayList)

    def beginGatewayConfiguration(self, chosenSerial):
        # prompt for device pin and a new controller name
        gatewayPin = ''
        networkName = ''
        while True:
            fields = [Dialog.FormField('Gateway PIN: '),
                      Dialog.FormField('Network name: ')]
            retCode, retList = self.ui.form('Gateway Configuration ({})'.format(chosenSerial),
                fields)
            if retCode == Dialog.DIALOG_ESC or retCode == Dialog.DIALOG_CANCEL:
                self.loop.call_soon(self._gatewayConfigureMenu)
                break

            gatewayPin = retList[0]
            networkName = retList[1]

            if len(gatewayPin) == 0 or len(networkName) == 0:
                self.ui.alert('All fields are required')
            else:
                self.newNetworkName = Name(networkName)
                interestName = Name('/localhop/configure').append(chosenSerial)
                parameters = DeviceConfigurationMessage()
                # deviceSuffix is ignored
                for i in range(len(self.newNetworkName)):
                    parameters.configuration.networkPrefix.components.append(str(self.newNetworkName[i].getValue()))
                # ignored
                parameters.configuration.deviceSuffix.components.append(' ')
                interestName.append(ProtobufTlv.encode(parameters))
                self._hmacHandler = HmacHelper(gatewayPin.decode('hex'))
                
                i = Interest(interestName)
                self._hmacHandler.signInterest(i)
                self.face.expressInterest(i, self._onGatewayConfigureResponse,
                    self._onGatewayConfigurationTimeout)
                
                self.ui.alert('Sending configuration to gateway...', False)
                break


#####
# Main methods
######

    def showMenu(self):
        gatewayItems = self.gatewayList[:]
        menuOptions = ['--extra-button', '--extra-label', 'Refresh']
        hadNone = False
        if len(gatewayItems) == 0:
            gatewayItems = ['None']
            hadNone = True
        (retCode, retStr) = self.ui.menu('Choose a device', 
            gatewayItems, preExtras = menuOptions)

        if  retCode == Dialog.DIALOG_OK:
            if hadNone:
                self.loop.call_soon(self.showMenu)
            else:
                self.loop.call_soon(self.beginGatewayConfiguration, retStr)
        elif retCode == Dialog.DIALOG_EXTRA:
            self.refreshGatewayList()
        else:
            self.pop()


    def run(self, completionCallback):
        self.completionCallback = completionCallback
        if len(self.gatewayList) == 0:
            self.refreshGatewayList()
        else:
            self.showMenu()

class ConfigureGatewayUserTask(UiTask):
    def __init__(self, networkName, face, uiController, eventLoop, context, topContext=None):
        super(ConfigureGatewayUserTask, self).__init__(uiController, eventLoop,
                 context, topContext)
        self.face = face
        self.newNetworkName = Name(networkName)
        self.completionCallback = None

    def promptForUserCredentials(self):
        """
         Request a user name and password that will be used with the gateway
         if a known user key is not available (i.e., registering new public key)

        """

    def run(self, completionCallback):
        self.completionCallback = completionCallback
        self.loop.call_soon(self.promptForUserCredentials)
        
